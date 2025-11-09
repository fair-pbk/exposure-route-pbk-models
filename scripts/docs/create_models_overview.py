import os
import logging
import glob
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
    records = []
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
