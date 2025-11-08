import glob
import os
from pathlib import Path
import libsbml as ls
import logging
import yaml

from sbmlpbkutils import PbkModelReportGenerator
from sbmlpbkutils import PbkModelInfosExtractor

models_path = './models/'
output_path = './docs/models/'

# Configure logger for formatted console output
console_logger = logging.getLogger('compile_models')
console_logger.setLevel(logging.INFO)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
if not console_logger.handlers:
    console_logger.addHandler(_console_handler)

def create_reports():
    # Clear output directory
    if os.path.exists(output_path):
        console_logger.info(f"Clearing output directory: {output_path}")
        for root, dirs, files in os.walk(output_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    else:
        os.makedirs(output_path, exist_ok=True)

    # Generate reports for each model
    sbml_files = glob.glob('./models/**/*.sbml', recursive=True)
    for sbml_file in sbml_files:
        create_report(sbml_file)
        get_model_metadata(sbml_file)

def create_report(sbml_file: str):
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
    output_dir = os.path.join(output_path, os.path.relpath(file_dir, models_path))
    os.makedirs(output_dir, exist_ok=True)

    # Generate report
    document = ls.readSBML(sbml_file)
    report_file = os.path.join(output_dir, 'summary.md')
    generator = PbkModelReportGenerator(document)
    generator.create_md_report(report_file)

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

def get_model_metadata(sbml_file: str):
    file_dir = os.path.dirname(sbml_file)
    output_dir = os.path.join(output_path, os.path.relpath(file_dir, models_path))
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

if __name__ == '__main__':
    create_reports()
