import os
import logging
import glob
import pandas as pd
import yaml
from jinja2 import Environment, FileSystemLoader

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

def create_models_table():
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
            report_path = os.path.relpath(file_dir, models_path) \
                .replace('\\', '/').replace(' ', '%20')

            # Load metadata
            metadata = None
            output_dir = os.path.join(output_path, os.path.relpath(file_dir, models_path))
            metadata_file = os.path.join(output_dir, 'metadata.yaml')
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = yaml.safe_load(f)

            for item in metadata.get('compartments', []):
                pbpko_bqm_is_class = item.get('pbpko_bqm_is_class', None)
                record = {
                    'file': filename,
                    'id': item['id'],
                    'name': item['name'],
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
    compartments_file = os.path.join(output_path, 'compartments.csv')
    df_compartments.to_csv(compartments_file, sep=',', encoding='utf-8', index=False, header=True)

    # Write compartment annotations
    df_species = pd.DataFrame(species_annotations)
    species_file = os.path.join(output_path, 'species.csv')
    df_species.to_csv(species_file, sep=',', encoding='utf-8', index=False, header=True)

    # Write compartment annotations
    df_parameters = pd.DataFrame(parameter_annotations)
    parameters_file = os.path.join(output_path, 'parameters.csv')
    df_parameters.to_csv(parameters_file, sep=',', encoding='utf-8', index=False, header=True)

    # Write all annotations to excel
    excel_file = os.path.join(output_path, 'annotations.xlsx')
    with pd.ExcelWriter(excel_file) as writer:
        df_compartments.to_excel(writer, sheet_name='Compartments', index=False, header=True)
        df_species.to_excel(writer, sheet_name='Species', index=False, header=True)
        df_parameters.to_excel(writer, sheet_name='Parameters', index=False, header=True)


def render_template(
    name: str,
    **kwargs
):
    # Out file
    output_file = str(kwargs.get('output_file')) if 'output_file' in kwargs \
         else f"docs/{name}.md"

    # Point to templates folder
    env = Environment(loader=FileSystemLoader("./docs/templates"))
    template = env.get_template(f"{name}.md.j2")

    # Render
    markdown_output = template.render(**kwargs)

    # Save to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_output)

if __name__ == '__main__':
    create_models_table()
