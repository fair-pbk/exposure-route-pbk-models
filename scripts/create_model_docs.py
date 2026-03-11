import glob
import os
import logging
from pathlib import Path
import libsbml as ls
import yaml
import pandas as pd
from sbmlpbkutils import PbkModelReportGenerator, PbkModelInfosExtractor, RenderMode, \
    DiagramCreator, NamesDisplay

from docs.utils import render_template

MODELS_PATH = './models/'
OUTPUT_PATH = './docs/models/'

# Configure logger for formatted console output
console_logger = logging.getLogger('create_model_docs')
console_logger.setLevel(logging.INFO)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
if not console_logger.handlers:
    console_logger.addHandler(_console_handler)

def create_model_reports():
    # Clear output directory
    if os.path.exists(OUTPUT_PATH):
        console_logger.info(f"Clearing output directory: {OUTPUT_PATH}")
        for root, dirs, files in os.walk(OUTPUT_PATH, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    else:
        os.makedirs(OUTPUT_PATH, exist_ok=True)

    # Generate reports for each model
    sbml_files = glob.glob('./models/**/*.sbml', recursive=True)
    for sbml_file in sbml_files:
        create_model_report(sbml_file)
        collect_model_metadata(sbml_file)

def create_model_report(sbml_file: str):
    console_logger.info(
        "Creating report for SBML file [%s].",
        os.path.basename(sbml_file)
    )

    # Check if SBML file exists
    if not os.path.exists(sbml_file):
        console_logger.error(
            "SBML file [%s] does not exist. Skipping report generation.",
            os.path.basename(sbml_file)
        )
        return

    # Create output directory if it does not exist
    file_dir = os.path.dirname(sbml_file)
    output_dir = os.path.join(OUTPUT_PATH, os.path.relpath(file_dir, MODELS_PATH))
    os.makedirs(output_dir, exist_ok=True)

    # Get model from file
    document = ls.readSBML(sbml_file)
    model = document.getModel()

    # Generate report
    report_file = os.path.join(output_dir, 'summary.md')
    generator = PbkModelReportGenerator(document)

    # Open the file in write mode
    with open(report_file, mode="w", encoding="utf-8") as f:
        # Write the title
        f.write(f"# {Path(sbml_file).stem}\n\n")

        if model.isSetNotes():
            f.write("## Notes\n\n")
            f.write(f"{model.getNotesString()}\n\n")

        # Write the model creators table
        f.write("## Creators\n\n")
        table = generator.get_model_creators()
        if table is not None:
            f.write(table.to_markdown())
            f.write("\n\n")
        else:
            f.write("*not specified*\n\n")

        # Write the model overview table
        f.write("## Overview\n\n")
        table = generator.get_model_overview()
        f.write(table.to_markdown(index=False))
        f.write("\n\n")

        # Generate and write the diagram
        f.write("## Diagram\n\n")
        diagram_file = Path(report_file).with_suffix('.svg')
        diagram_creator = DiagramCreator()
        diagram_creator.create_diagram(
            generator.document,
            diagram_file,
            names_display=NamesDisplay.ELEMENT_IDS_AND_ONTO_IDS,
            draw_species=True,
            draw_reaction_ids=True
        )
        f.write(f"![Diagram]({diagram_file.name})")
        f.write("\n\n")

        # Write compartment infos table
        f.write("## Compartments\n\n")
        if model.getNumCompartments() > 0:
            table = generator.get_compartment_infos()
            f.write(table.to_markdown(index=False))
            f.write("\n\n")
        else:
            f.write("*no compartments defined in the model*\n\n")

        # Write compartment infos table
        f.write("## Species\n\n")
        if model.getNumSpecies() > 0:
            table = generator.get_species_infos()
            f.write(table.to_markdown(index=False))
            f.write("\n\n")
        else:
            f.write("*no species defined in the model*\n\n")

        # Write Transfer equations
        f.write("## Transfer equations\n\n")
        transfer_equations = list(generator.get_transfer_equations_as_str(RenderMode.TEXT).values())
        table = pd.DataFrame({
            'id': [ x['id'] for x in transfer_equations ],
            'from': [ x['reactants'][0] for x in transfer_equations ],
            'to': [ x['products'][0] for x in transfer_equations ],
            'equation': [ f"{x['equation']}" for x in transfer_equations ]
        })
        f.write(table.to_markdown(index=False))
        f.write("\n\n")

        # Write ODEs
        f.write("## ODEs\n\n")
        odes = generator.get_odes_as_str(RenderMode.LATEX)
        for _, equation in odes.items():
            f.write(f"${equation}$\n\n")

        # Write rate rules
        rate_rules = generator.get_rate_rules_as_str(RenderMode.TEXT)
        if len(rate_rules) > 0:
            f.write("## Rate rules\n\n")
            for _, equation in rate_rules.items():
                f.write(f"{equation}\n\n")

        # Write assignment rules
        assignment_rules = generator.get_assignment_rules_as_str(RenderMode.TEXT)
        if len(assignment_rules) > 0:
            f.write("## Assignment rules\n\n")
            table = pd.DataFrame({
                'variable': [ key for key, _ in assignment_rules.items() ],
                'assignment': [ equation for _, equation in assignment_rules.items() ]
            })
            f.write(table.to_markdown(index=False))
            f.write("\n\n")

        # Write assignment rules
        initial_assignments = generator.get_initial_assigments_as_str(RenderMode.TEXT)
        if len(initial_assignments) > 0:
            f.write("## Initial assignments\n\n")
            table = pd.DataFrame({
                'variable': [ key for key, _ in initial_assignments.items() ],
                'assignment': [ equation for _, equation in initial_assignments.items() ]
            })
            f.write(table.to_markdown(index=False))
            f.write("\n\n")

        # Write functions
        function_defs = generator.get_function_as_str(RenderMode.LATEX)
        if len(function_defs) > 0:
            f.write("## Function definitions\n\n")
            for _, equation in function_defs.items():
                f.write(f"${equation}$\n\n")

        # Write compartment infos table
        f.write("## Parameters\n\n")
        if model.getNumParameters() > 0:
            table = generator.get_parameter_infos()
            f.write(table.to_markdown(index=False))
            f.write("\n\n")
        else:
            f.write("*no parameters defined in the model*\n\n")

def get_unit_concistency_check_results(doc: ls.SBMLDocument):
    results = []
    doc.setConsistencyChecks(ls.LIBSBML_CAT_UNITS_CONSISTENCY, True)
    failures = doc.checkConsistencyWithStrictUnits()
    if failures > 0:
        for i in range(failures):
            error = doc.getError(i)
            error_code = error.getErrorId()
            severity = error.getSeverity()
            if severity in { ls.LIBSBML_SEV_ERROR, ls.LIBSBML_SEV_FATAL} \
                and error_code != ls.UndeclaredUnits:
                results.append({
                    "level": "error",
                    "msg": doc.getError(i).getMessage()
                })
            else:
                results.append({
                    "level": "warning",
                    "msg": doc.getError(i).getMessage()
                })
    else:
        results.append({
            "level": "info",
            "msg": "No unit inconsistencies found."
        })
    return results

def collect_model_metadata(sbml_file: str):
    file_dir = os.path.dirname(sbml_file)
    output_dir = os.path.join(OUTPUT_PATH, os.path.relpath(file_dir, MODELS_PATH))
    metadata_file = os.path.join(output_dir, 'metadata.yaml')

    console_logger.info(
        "Creating metadata YAML file [%s] from annotated SBML file [%s].",
        os.path.basename(metadata_file),
        os.path.basename(sbml_file)
    )

    # Load SBML document and get infos extractor
    document = ls.readSBML(sbml_file)
    model = document.getModel()
    infos_extractor = PbkModelInfosExtractor(document)

    # Collect compartment metadata
    compartments_metadata = []
    compartment_infos = infos_extractor.get_compartment_infos()
    for compartment in compartment_infos:
        record = {
            "id": compartment.id,
            "name": compartment.name,
        }
        if compartment.pbpko_bqm_is_class is not None:
            record["pbpko_bqm_is_class"] = {
                "id": compartment.pbpko_bqm_is_class.name.replace("_", ":"),
                "label": str(compartment.pbpko_bqm_is_class.label[0]),
                "iri": compartment.pbpko_bqm_is_class.iri
            }
        compartments_metadata.append(record)

    # Collect species metadata
    species_metadata = []
    species_infos = infos_extractor.get_species_infos()
    for species in species_infos:
        record = {
            "id": species.id,
            "name": species.name
        }
        if species.pbpko_bqm_is_class is not None:
            record["pbpko_bqm_is_class"] = {
                "id": species.pbpko_bqm_is_class.name.replace("_", ":"),
                "label": str(species.pbpko_bqm_is_class.label[0]),
                "iri": species.pbpko_bqm_is_class.iri
            }
        species_metadata.append(record)

    # Collect parameter metadata
    parameters_metadata = []
    parameter_infos = infos_extractor.get_parameter_infos()
    for parameter in parameter_infos:
        record = {
            "id": parameter.id,
            "name": parameter.name
        }
        if parameter.pbpko_bqm_is_class is not None:
            record["pbpko_bqm_is_class"] = {
                "id": parameter.pbpko_bqm_is_class.name.replace("_", ":"),
                "label": str(parameter.pbpko_bqm_is_class.label[0]),
                "iri": parameter.pbpko_bqm_is_class.iri
            }
        parameters_metadata.append(record)

    model_animal_species_metadata = []
    model_animal_species_infos = infos_extractor.get_model_animal_species()
    for item in model_animal_species_infos:
        model_animal_species_metadata.append({
            "id": item.name.replace("_", ":"),
            "label": item.label[0],
            "iri": item.iri
        })

    model_chemicals_metadata = []
    model_chemicals_infos = infos_extractor.get_model_chemicals()
    for item in model_chemicals_infos:
        model_chemicals_metadata.append({
            "id": item.name.replace("_", ":"),
            "label": item.label[0],
            "iri": item.iri
        })

    unit_consistency_check_results = get_unit_concistency_check_results(document)

    # Create metadata dictionary
    metadata = {
        "id": model.getId(),
        "name": model.getName(),
        "applicability_domain": {
            "chemicals": model_chemicals_metadata,
            "species": model_animal_species_metadata
        },
        "num_species": model.getNumSpecies(),
        "num_parameters": model.getNumParameters(),
        "num_reactions": model.getNumReactions(),
        "compartments": compartments_metadata,
        "species": species_metadata,
        "parameters": parameters_metadata,
        "unit_consistency": unit_consistency_check_results
    }

    # Write to YAML
    yaml_output = yaml.dump(metadata, sort_keys=False, indent=2, allow_unicode=True)
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(yaml_output)

def create_overview_report():
    sbml_files = glob.glob('./models/**/*.sbml', recursive=True)
    records = []
    for sbml_file in sbml_files:
        try:
            console_logger.info(
                "Processing SBML file [%s] for overview.",
                os.path.basename(sbml_file)
            )
            filename = os.path.basename(sbml_file)
            file_dir = os.path.dirname(sbml_file)
            report_path = os.path.relpath(file_dir, MODELS_PATH) \
                .replace('\\', '/').replace(' ', '%20')

            # Load metadata
            metadata = None
            output_dir = os.path.join(OUTPUT_PATH, os.path.relpath(file_dir, MODELS_PATH))
            metadata_file = os.path.join(output_dir, 'metadata.yaml')
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = yaml.safe_load(f)

            num_species_unannotated = len([
                s for s in metadata.get('species', [])
                if not s.get('pbpko_bqm_is_class')
            ])
            num_parameters_unannotated = len([
                p for p in metadata.get('parameters', [])
                if not p.get('pbpko_bqm_is_class')
            ])
            num_unit_consistency_errors = len([
                r for r in metadata.get('unit_consistency', [])
                if r.get('level') == 'error'
            ])
            num_unit_consistency_warnings = len([
                r for r in metadata.get('unit_consistency', [])
                if r.get('level') == 'warning'
            ])

            records.append({
                "filename": filename,
                "id": metadata['id'],
                "route": report_path.split('/')[0],
                "chemical_group": report_path.split('/')[1],
                "report_path": f"./models/{report_path}/summary.md",
                "compartments": metadata['compartments'],
                "num_species": metadata.get('num_species', 'N/A'),
                "num_species_unannotated": num_species_unannotated,
                "num_parameters": metadata.get('num_parameters', 'N/A'),
                "num_parameters_unannotated": num_parameters_unannotated,
                "num_unit_consistency_errors": num_unit_consistency_errors,
                "num_unit_consistency_warnings": num_unit_consistency_warnings
            })
        except Exception as e:
            console_logger.error(
                "Error processing SBML file [%s]: %s",
                os.path.basename(sbml_file),
                str(e)
            )

    # Render markdown table
    console_logger.info("Rendering models overview markdown table.")
    render_template(
        name="models-overview",
        output_file="./docs/models-overview.md",
        records=records
    )

def export_annotations():
    sbml_files = glob.glob('./models/**/*.sbml', recursive=True)
    compartment_annotations = []
    species_annotations = []
    parameter_annotations = []
    for sbml_file in sbml_files:
        try:
            console_logger.info(
                "Processing SBML file [%s] for overview.",
                os.path.basename(sbml_file)
            )
            filename = os.path.basename(sbml_file)
            file_dir = os.path.dirname(sbml_file)
            report_path = os.path.relpath(file_dir, MODELS_PATH) \
                .replace('\\', '/').replace(' ', '%20')
            route = report_path.split('/')[0]
            chemical_group = report_path.split('/')[1]

            # Load metadata
            metadata = None
            output_dir = os.path.join(OUTPUT_PATH, os.path.relpath(file_dir, MODELS_PATH))
            metadata_file = os.path.join(output_dir, 'metadata.yaml')
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = yaml.safe_load(f)

            for item in metadata.get('compartments', []):
                pbpko_bqm_is_class = item.get('pbpko_bqm_is_class', None)
                record = {
                    'file': filename,
                    'id': item['id'],
                    'name': item['name'],
                    'route': route,
                    'chemical_group': chemical_group,
                    'bqm_is_class_id': pbpko_bqm_is_class['id'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_label': pbpko_bqm_is_class['label'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_iri': pbpko_bqm_is_class['iri'] if pbpko_bqm_is_class else ''
                }
                compartment_annotations.append(record)

            for item in metadata.get('species', []):
                pbpko_bqm_is_class = item.get('pbpko_bqm_is_class', None)
                record = {
                    'file': filename,
                    'id': item['id'],
                    'name': item['name'],
                    'route': route,
                    'chemical_group': chemical_group,
                    'bqm_is_class_id': pbpko_bqm_is_class['id'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_label': pbpko_bqm_is_class['label'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_iri': pbpko_bqm_is_class['iri'] if pbpko_bqm_is_class else ''
                }
                species_annotations.append(record)

            for item in metadata.get('parameters', []):
                pbpko_bqm_is_class = item.get('pbpko_bqm_is_class', None)
                record = {
                    'file': filename,
                    'id': item['id'],
                    'name': item['name'],
                    'route': route,
                    'chemical_group': chemical_group,
                    'bqm_is_class_id': pbpko_bqm_is_class['id'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_label': pbpko_bqm_is_class['label'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_iri': pbpko_bqm_is_class['iri'] if pbpko_bqm_is_class else ''
                }
                parameter_annotations.append(record)

        except Exception as e:
            console_logger.error(
                "Error processing SBML file [%s]: %s",
                os.path.basename(sbml_file),
                str(e)
            )

    # Write compartment annotations
    df_compartments = pd.DataFrame(compartment_annotations)
    compartments_file = os.path.join(OUTPUT_PATH, 'compartments.csv')
    df_compartments.to_csv(compartments_file, sep=',', encoding='utf-8', index=False, header=True)

    # Write compartment annotations
    df_species = pd.DataFrame(species_annotations)
    species_file = os.path.join(OUTPUT_PATH, 'species.csv')
    df_species.to_csv(species_file, sep=',', encoding='utf-8', index=False, header=True)

    # Write compartment annotations
    df_parameters = pd.DataFrame(parameter_annotations)
    parameters_file = os.path.join(OUTPUT_PATH, 'parameters.csv')
    df_parameters.to_csv(parameters_file, sep=',', encoding='utf-8', index=False, header=True)

    # Write all annotations to excel
    excel_file = os.path.join(OUTPUT_PATH, 'annotations.xlsx')
    with pd.ExcelWriter(excel_file) as writer:
        df_compartments.to_excel(writer, sheet_name='Compartments', index=False, header=True)
        df_species.to_excel(writer, sheet_name='Species', index=False, header=True)
        df_parameters.to_excel(writer, sheet_name='Parameters', index=False, header=True)

if __name__ == '__main__':
    create_model_reports()
    create_overview_report()
    export_annotations()
