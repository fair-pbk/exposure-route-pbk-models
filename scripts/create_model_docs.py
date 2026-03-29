import glob
import os
import re
import logging
import zipfile
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

    report_title = Path(sbml_file).stem
    report_title = re.sub(r'(\D)(\d)', r'\1 \2', report_title)

    # Get model from file
    document = ls.readSBML(sbml_file)
    model = document.getModel()

    # Generate report
    report_file = os.path.join(output_dir, 'summary.md')
    generator = PbkModelReportGenerator(document)

    # Open the file in write mode
    with open(report_file, mode="w", encoding="utf-8") as f:
        # Write the title
        f.write(f"# {report_title}\n\n")

        if model.isSetNotes():
            f.write("## Notes\n\n")
            f.write(f"{model.getNotesString()}\n\n")

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

def export_parameters(sbml_file: str, model: ls.Model, parameters_metadata: list):
    file_dir = os.path.dirname(sbml_file)
    parameter_files = sorted(
        glob.glob(os.path.join(file_dir, '*.param.csv')) +
        glob.glob(os.path.join(file_dir, '*.params.csv'))
    )

    if not parameter_files:
        return []

    model_id = model.getId() if hasattr(model, 'getId') else Path(sbml_file).stem
    if not model_id:
        model_id = Path(sbml_file).stem

    metadata_lookup = {
        str(item.get('id')): item
        for item in parameters_metadata
        if item.get('id')
    }

    parameterisations = []
    for parameter_file in parameter_files:
        try:
            df = pd.read_csv(parameter_file, dtype=str).fillna('')
        except Exception:
            continue

        columns = {column.strip().lower(): column for column in df.columns}
        parameter_column = columns.get('parameter') or columns.get('id')
        value_column = columns.get('value')
        unit_column = columns.get('unit')
        reference_column = columns.get('reference') or columns.get('description')

        parameters = []
        for _, row in df.iterrows():
            parameter_id = str(row.get(parameter_column, '')).strip() if parameter_column else ''
            metadata = metadata_lookup.get(parameter_id, {})
            raw_value = str(row.get(value_column, '')).strip() if value_column else ''
            unit = str(row.get(unit_column, '')).strip() if unit_column else metadata.get('unit', '')
            reference = str(row.get(reference_column, '')) if reference_column else ''

            if not raw_value:
                console_logger.error(
                    "No value specified for parameter [%s] in parameterisation file [%s] or model [%s].",
                    parameter_id,
                    os.path.basename(parameter_file),
                    os.path.basename(sbml_file)
                )
                value = None
            else:
                try:
                    value = float(raw_value)
                except ValueError:
                    console_logger.error(
                        "Unable to parse numeric value [%s] for parameter [%s] in file [%s].",
                        raw_value,
                        parameter_id,
                        os.path.basename(parameter_file)
                    )
                    value = None

            param = {
                'id': parameter_id,
                'value': value,
                'unit': unit,
                'reference': reference
            }

            pbpko_bqm_is_class = metadata.get('pbpko_bqm_is_class')
            chebi_bqb_is_class = metadata.get('chebi_bqb_is_class')
            if isinstance(pbpko_bqm_is_class, dict):
                param['bqm_is'] = dict(pbpko_bqm_is_class)
            if isinstance(chebi_bqb_is_class, dict):
                param['bqb_is'] = dict(chebi_bqb_is_class)

            parameters.append(param)

        parameterisations.append({
            'filename': os.path.basename(parameter_file),
            'model_id': model_id,
            'parameters': parameters
        })

    return parameterisations


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
                    "msg": doc.getError(i).getMessage().strip()
                })
            else:
                results.append({
                    "level": "warning",
                    "msg": doc.getError(i).getMessage().strip()
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

    name = re.sub(r'(\D)(\d)', r'\1 \2', Path(sbml_file).stem) \
        if not model.getName() else model.getName() 

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
        record["unit"] = compartment.unit
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
        if species.chebi_bqb_is_class is not None:
            record["chebi_bqb_is_class"] = {
                "id": species.chebi_bqb_is_class.name.replace("_", ":"),
                "label": str(species.chebi_bqb_is_class.label[0]),
                "iri": species.chebi_bqb_is_class.iri
            }
        record["unit"] = species.unit
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
        if parameter.chebi_bqb_is_class is not None:
            record["chebi_bqb_is_class"] = {
                "id": parameter.chebi_bqb_is_class.name.replace("_", ":"),
                "label": str(parameter.chebi_bqb_is_class.label[0]),
                "iri": parameter.chebi_bqb_is_class.iri
            }
        record["unit"] = parameter.unit
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

    parametrisations = export_parameters(sbml_file, model, parameters_metadata)

    # Create metadata dictionary
    metadata = {
        "id": model.getId(),
        "name": name,
        "applicability_domain": {
            "chemicals": model_chemicals_metadata,
            "species": model_animal_species_metadata
        },
        "num_compartments": model.getNumCompartments(),
        "num_species": model.getNumSpecies(),
        "num_parameters": model.getNumParameters(),
        "num_reactions": model.getNumReactions(),
        "compartments": compartments_metadata,
        "species": species_metadata,
        "parameters": parameters_metadata,
        "parameterisations": parametrisations,
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
            report_path = os.path.relpath(file_dir, MODELS_PATH).replace('\\', '/')
            route = report_path.split('/')[0]
            chemical_group = report_path.split('/')[1]

            # Load metadata
            metadata = None
            output_dir = os.path.join(OUTPUT_PATH, os.path.relpath(file_dir, MODELS_PATH))
            metadata_file = os.path.join(output_dir, 'metadata.yaml')
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = yaml.safe_load(f)

            num_compartments_unannotated = len([
                s for s in metadata.get('compartments', [])
                if not s.get('pbpko_bqm_is_class')
            ])
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
                "name": metadata['name'],
                "route": route,
                "chemical_group": chemical_group,
                "report_path": f"./models/{report_path.replace(' ', '%20')}/summary.md",
                "compartments": metadata['compartments'],
                "num_compartments": metadata.get('num_compartments', 'N/A'),
                "num_compartments_unannotated": num_compartments_unannotated,
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

    # Write all annotations to excel
    console_logger.info("Creating models overview excel table.")
    excel_file = os.path.join(OUTPUT_PATH, 'models_overview.xlsx')
    df = pd.DataFrame(records)

    # Map compartments list of objects to semicolon-separated ids for spreadsheet export
    if 'compartments' in df.columns:
        df['compartments'] = df['compartments'].apply(
            lambda compartments: ";".join(str(c.get('id', '')) \
                for c in compartments if isinstance(c, dict) and c.get('id') is not None)
            if isinstance(compartments, list) else compartments
        )

    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer, sheet_name='Models overview', index=False, header=True)

def export_models_zip():
    zip_file = os.path.join(OUTPUT_PATH, 'models.zip')
    allowed_extensions = (
        '.ant',
        '.sbml',
        '.annotations.csv',
        '.params.csv'
    )

    if not os.path.isdir(MODELS_PATH):
        console_logger.error('Models path does not exist: %s', MODELS_PATH)
        return

    os.makedirs(OUTPUT_PATH, exist_ok=True)

    console_logger.info('Creating zip archive [%s] from models folder [%s].', zip_file, MODELS_PATH)
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(MODELS_PATH):
            for filename in files:
                if filename.endswith(allowed_extensions):
                    full_path = os.path.join(root, filename)
                    archive_path = os.path.relpath(full_path, MODELS_PATH)
                    archive.write(full_path, archive_path)
                    console_logger.debug('Added file to zip: %s', archive_path)

    console_logger.info('Zip archive created: %s', zip_file)


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
                .replace('\\', '/')
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
                    'unit': item.get('unit', None),
                    'bqm_is_class_id': pbpko_bqm_is_class['id'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_label': pbpko_bqm_is_class['label'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_iri': pbpko_bqm_is_class['iri'] if pbpko_bqm_is_class else ''
                }
                compartment_annotations.append(record)

            for item in metadata.get('species', []):
                pbpko_bqm_is_class = item.get('pbpko_bqm_is_class', None)
                chebi_bqb_is_class = item.get('chebi_bqb_is_class', None)
                record = {
                    'file': filename,
                    'id': item['id'],
                    'name': item['name'],
                    'route': route,
                    'chemical_group': chemical_group,
                    'unit': item.get('unit', None),
                    'bqm_is_class_id': pbpko_bqm_is_class['id'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_label': pbpko_bqm_is_class['label'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_iri': pbpko_bqm_is_class['iri'] if pbpko_bqm_is_class else '',
                    'bqb_is_class_id': chebi_bqb_is_class['id'] if chebi_bqb_is_class else '',
                    'bqb_is_class_label': chebi_bqb_is_class['label'] if chebi_bqb_is_class else '',
                    'bqb_is_class_iri': chebi_bqb_is_class['iri'] if chebi_bqb_is_class else ''
                }
                species_annotations.append(record)

            for item in metadata.get('parameters', []):
                pbpko_bqm_is_class = item.get('pbpko_bqm_is_class', None)
                chebi_bqb_is_class = item.get('chebi_bqb_is_class', None)
                record = {
                    'file': filename,
                    'id': item['id'],
                    'name': item['name'],
                    'route': route,
                    'chemical_group': chemical_group,
                    'unit': item.get('unit', None),
                    'bqm_is_class_id': pbpko_bqm_is_class['id'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_label': pbpko_bqm_is_class['label'] if pbpko_bqm_is_class else '',
                    'bqm_is_class_iri': pbpko_bqm_is_class['iri'] if pbpko_bqm_is_class else '',
                    'bqb_is_class_id': chebi_bqb_is_class['id'] if chebi_bqb_is_class else '',
                    'bqb_is_class_label': chebi_bqb_is_class['label'] if chebi_bqb_is_class else '',
                    'bqb_is_class_iri': chebi_bqb_is_class['iri'] if chebi_bqb_is_class else ''
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


def export_parameterisations():
    sbml_files = glob.glob('./models/**/*.sbml', recursive=True)
    records = []
    for sbml_file in sbml_files:
        try:
            console_logger.info(
                "Processing SBML file [%s] for parameterisations.",
                os.path.basename(sbml_file)
            )
            file_dir = os.path.dirname(sbml_file)
            report_path = os.path.relpath(file_dir, MODELS_PATH).replace('\\', '/')
            path_parts = report_path.split('/')
            route = path_parts[0] if len(path_parts) > 0 else ''
            chemical_group = path_parts[1] if len(path_parts) > 1 else ''

            output_dir = os.path.join(OUTPUT_PATH, os.path.relpath(file_dir, MODELS_PATH))
            metadata_file = os.path.join(output_dir, 'metadata.yaml')
            if not os.path.exists(metadata_file):
                console_logger.warning(
                    "Metadata file not found for SBML file [%s], skipping parameterisations export.",
                    os.path.basename(sbml_file)
                )
                continue

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f)

            for parameterisation in metadata.get('parameterisations', []):
                filename = parameterisation.get('filename', '')
                model_id = parameterisation.get('model_id', metadata.get('id', ''))
                for parameter in parameterisation.get('parameters', []):
                    bqm_is = parameter.get('bqm_is', {})
                    bqb_is = parameter.get('bqb_is', {})
                    records.append({
                        'file': os.path.basename(sbml_file),
                        'route': route,
                        'chemical_group': chemical_group,
                        'model_id': model_id,
                        'parameterisation_file': filename,
                        'parameter_id': parameter.get('id', ''),
                        'value': parameter.get('value', None),
                        'unit': parameter.get('unit', ''),
                        'reference': parameter.get('reference', ''),
                        'bqm_is_id': bqm_is.get('id', '') if isinstance(bqm_is, dict) else str(bqm_is),
                        'bqm_is_label': bqm_is.get('label', '') if isinstance(bqm_is, dict) else '',
                        'bqm_is_iri': bqm_is.get('iri', '') if isinstance(bqm_is, dict) else '',
                        'bqb_is_id': bqb_is.get('id', '') if isinstance(bqb_is, dict) else str(bqb_is),
                        'bqb_is_label': bqb_is.get('label', '') if isinstance(bqb_is, dict) else '',
                        'bqb_is_iri': bqb_is.get('iri', '') if isinstance(bqb_is, dict) else ''
                    })
        except Exception as e:
            console_logger.error(
                "Error exporting parameterisations for SBML file [%s]: %s",
                os.path.basename(sbml_file),
                str(e)
            )

    excel_file = os.path.join(OUTPUT_PATH, 'parameterisations.xlsx')
    df = pd.DataFrame(records)
    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer, sheet_name='Parameterisations', index=False, header=True)

    console_logger.info('Created parameterisations excel file: %s', excel_file)

if __name__ == '__main__':
    create_model_reports()
    create_overview_report()
    export_annotations()
    export_parameterisations()
    export_models_zip()
