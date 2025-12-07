import os
from typing import Dict, List
from dataclasses import dataclass
import numpy as np
import pandas as pd
import tellurium as te
import matplotlib.pyplot as plt
import libsbml as ls
import yaml

from simulation.definitions import Comparison, DosingEvent, ModelInstance, Scenario, SimulationConfig
from simulation.units import AmountUnit, TimeUnit, \
    get_time_unit_alignment_factor, get_amount_unit_alignment_factor

@dataclass
class EventSpec:
    target: str
    trigger: str
    assignment: str

def events_single_continuous(
    event: DosingEvent,
    time_unit_multiplier: float,
    amount_unit_multiplier: float,
    target_mappings: Dict[str, str]
) -> List[EventSpec]:
    if event.duration is None:
        raise ValueError("duration is required for single continous dosing event")
    target = target_mappings[event.target] \
        if event.target in target_mappings.keys() \
        else event.target
    time_start = time_unit_multiplier * event.time
    time_stop = time_unit_multiplier * (event.time + event.duration)
    amount = amount_unit_multiplier * event.amount
    return [
        EventSpec(target, f"(time >= {time_start})", f"{target} + {amount}"),
        EventSpec(target, f"(time >= {time_stop})", "0")
    ]

def repeated_continuous(
    event: DosingEvent,
    time_unit_multiplier: float,
    amount_unit_multiplier: float,
    target_mappings: Dict[str, str]
) -> List[EventSpec]:
    if event.duration is None:
        raise ValueError("duration is required for repeated continous dosing event")
    if event.interval is None:
        raise ValueError("interval is required for repeated continous dosing event")
    target = target_mappings[event.target] \
        if event.target in target_mappings.keys() \
        else event.target
    time_start = time_unit_multiplier * event.time
    time_stop = time_unit_multiplier * (event.time + event.duration)
    interval = time_unit_multiplier * event.interval
    amount = amount_unit_multiplier * event.amount
    return [
        EventSpec(
            target = target,
            trigger = f"(time >= {time_start}) && time % {interval} > {time_start}",
            assignment = f"{target} + {amount}"
        ),
        EventSpec(
            target = target,
            trigger = f"(time >= {time_stop}) && time % {interval} < {time_start}",
            assignment = "0"
        )
    ]

def events_single_bolus(
    event: DosingEvent,
    time_unit_multiplier: float,
    amount_unit_multiplier: float,
    target_mappings: Dict[str, str]
) -> List[EventSpec]:
    target = target_mappings[event.target] \
        if event.target in target_mappings.keys() \
        else event.target
    time = time_unit_multiplier * event.time
    amount = amount_unit_multiplier * event.amount
    trigger = f"(time >= {time})"
    assignment = f"{target} + {amount}"
    return [EventSpec(target, trigger, assignment)]

def events_repeated_bolus(
    event: DosingEvent,
    time_unit_multiplier: float,
    amount_unit_multiplier: float,
    target_mappings: Dict[str, str]
) -> List[EventSpec]:
    if event.interval is None:
        raise ValueError("interval is required for repeated_bolus")
    if event.until is None:
        raise ValueError("until is required for repeated_bolus")
    target = target_mappings[event.target] \
        if event.target in target_mappings.keys() \
        else event.target
    time = time_unit_multiplier * event.time
    interval = time_unit_multiplier * event.interval
    until = time_unit_multiplier * event.until
    amount = amount_unit_multiplier * event.amount
    trigger = f"time >= {time} && time % {interval} == 0 && time < {until}"
    assignment = f"{target} + {amount}"
    return [EventSpec(target, trigger, assignment)]

def dosing_events_to_eventspecs(
    event: DosingEvent,
    time_unit_multiplier: float,
    amount_unit_multiplier: float,
    target_mappings: Dict[str, str]
) -> List[EventSpec]:
    if event.type == "single_bolus":
        return events_single_bolus(
            event,
            time_unit_multiplier,
            amount_unit_multiplier,
            target_mappings
        )
    elif event.type == "repeated_bolus":
        return events_repeated_bolus(
            event,
            time_unit_multiplier,
            amount_unit_multiplier,
            target_mappings
        )
    elif event.type == "single_continuous":
        return events_single_continuous(
            event,
            time_unit_multiplier,
            amount_unit_multiplier,
            target_mappings
        )
    elif event.type == "repeated_continuous":
        return repeated_continuous(
            event,
            time_unit_multiplier,
            amount_unit_multiplier,
            target_mappings
        )
    else:
        raise ValueError(f"Unknown dose_type: {event.type}")

def load_config(path: str) -> SimulationConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    model_instances = [
        ModelInstance(**mi)
        for mi in data["model_instances"]
    ]

    scenarios = []
    for s in data["scenarios"]:
        dosing_events = [DosingEvent(**e) for e in s["dosing_events"]]
        comparisons = [Comparison(**c) for c in s["comparisons"]]

        scenarios.append(
            Scenario(
                id=s["id"],
                label=s["label"],
                duration=s["duration"],
                evaluation_resolution=s["evaluation_resolution"],
                dosing_events=dosing_events,
                comparisons=comparisons,
                time_unit=TimeUnit[s["time_unit"]],
                amount_unit=AmountUnit[s["amount_unit"]],
            )
        )

    return SimulationConfig(
        id=data["id"],
        label=data["label"],
        model_instances=model_instances,
        scenarios=scenarios
    )

def run_config(
    config: SimulationConfig,
    out_path: str,
    force_recompute: bool
):
    for scenario in config.scenarios:
        for instance in config.model_instances:
            # Simulation output csv file
            out_file = os.path.join(out_path, f"{scenario.id}-{instance.id}.csv")
            run_scenario(
                instance,
                scenario,
                out_file,
                force_recompute
            )

        # Plot combined instances scenario results
        plot_scenario_results(
            config.model_instances,
            scenario,
            out_path
        )

def run_scenario(
    instance: ModelInstance,
    scenario: Scenario,
    out_file: str,
    force_recompute: bool
):
    print(f"Running scenario {scenario.id} for instance {instance.id}")

    # Skip if output already available and no forced recalculation
    if os.path.exists(out_file) and not force_recompute:
        print(f"Skipping scenario {scenario.id}: results already available")
        return

    # Load the model
    sbml_file = instance.model_path
    ls_document = ls.readSBML(sbml_file)
    ls_model = ls_document.getModel()
    rr_model = te.loadSBMLModel(sbml_file)

    # Simulation time and amount unit alignment
    time_unit_multiplier = get_time_unit_alignment_factor(ls_model, scenario.time_unit)
    amount_unit_multiplier = get_amount_unit_alignment_factor(ls_model, scenario.amount_unit)

    # Get events from scenario
    event_specs = create_rr_events(
        scenario.dosing_events,
        time_unit_multiplier,
        amount_unit_multiplier,
        instance.target_mappings
    )

    # Set boundary condition for continuous targets
    continuous_targets = set(
        r.target for r in scenario.dosing_events if r.type == 'single_continuous' \
            or r.type == 'repeated_continuous'
    )
    for target in continuous_targets:
        rr_model.setBoundary(instance.target_mappings[target], True)

    # Set events
    event_count = 0
    for ev in event_specs:
        event_count += 1
        eid = f"ev_{event_count}"
        rr_model.addEvent(eid, False, ev.trigger, False)
        rr_model.addEventAssignment(eid, ev.target, ev.assignment, False)
    rr_model.regenerateModel(True, True)

    # Set instance parametrisation
    if instance.param_file is not None:
        load_parametrisation(rr_model, instance.param_file)

    # Define the output selections
    output_ids = set(instance.target_mappings.get(output.id, output.id) for output in scenario.comparisons)
    selections = ['time'] + list(output_ids)

    # Determine duration and steps
    duration = int(scenario.duration * time_unit_multiplier)
    evaluation_steps = int(scenario.evaluation_resolution * duration / time_unit_multiplier) + 1

    print(f"- Time unit multiplier: {time_unit_multiplier}")
    print(f"- Amount unit multiplier: {amount_unit_multiplier}")
    print(f"- Duration: {duration}")
    print(f"- Steps: {evaluation_steps}")

    # Simulate the PBPK model
    results = rr_model.simulate(0, duration, evaluation_steps, selections)

    # Create output folder if not exists
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    # Write results file
    df = pd.DataFrame(results, columns=selections)

    # Align output times and amounts to target units
    df['time'] = df['time'].apply(lambda v: v / time_unit_multiplier)
    for output in output_ids:
        df[output] = df[output].apply(lambda v: v / amount_unit_multiplier)
    df.to_csv(out_file, index=False)

def plot_scenario_results(
    instances: list[ModelInstance],
    scenario: Scenario,
    out_path: str
):
    for comparison in scenario.comparisons:
        # Create figure
        fig, ax = plt.subplots(figsize=(7, 5))

        # Loop over instance results and plot
        for instance in instances:
            # Get instance scenario output file
            out_file = os.path.join(out_path, f"{scenario.id}-{instance.id}.csv")
            output_df = pd.read_csv(out_file)

            # Extract time and output variable from output
            times = output_df['time'].to_numpy(dtype=float)
            values = output_df[instance.target_mappings.get(comparison.id, comparison.id)].to_numpy(dtype=float)

            # Plot lines
            ax.plot(times, values, linewidth=1, label=instance.label)

        # Set plot layout
        ax.set_xlabel(f'Time ({str(scenario.time_unit)})', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'{comparison.label} ({str(scenario.amount_unit)})', fontsize=12, fontweight='bold')
        ax.set_title(f'{scenario.label} - {comparison.label}', fontsize=14)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

        # Set output file
        out_file = os.path.join(out_path, f"{scenario.id}-{comparison.id}.png")
        plt.tight_layout()
        plt.legend()
        plt.savefig(out_file)
        plt.close()

def create_rr_events(
    events: List[DosingEvent],
    time_unit_multiplier: float,
    amount_unit_multiplier: float,
    target_mappings: Dict[str, str]
) -> List[EventSpec]:
    out: List[EventSpec] = []
    for e in events:
        out.extend(dosing_events_to_eventspecs(
            e,
            time_unit_multiplier,
            amount_unit_multiplier,
            target_mappings
        ))
    return out

def load_parametrisation(model, filename):
    df = pd.read_csv(filename)
    df['Value'] = df['Value'].astype(float)
    for index, row in df.iterrows():
        model[str(row['Parameter'])] = row['Value']
