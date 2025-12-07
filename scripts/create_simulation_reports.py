import os
import logging
import glob
from docs.doc_utils import render_template
from simulation.simulation import load_config

CONFIGS_PATH = './scenarios/'
OUTPUT_PATH = './docs/simulation/'

# Configure logger for formatted console output
console_logger = logging.getLogger('create_simulation_reports')
console_logger.setLevel(logging.INFO)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
if not console_logger.handlers:
    console_logger.addHandler(_console_handler)

def create_simulation_reports():

    configs = glob.glob(f'./{CONFIGS_PATH}/**/*.yaml', recursive=True)
    for file in configs:
        # Load config
        config = load_config(file)

        # Ensure output path
        out_path = os.path.join(OUTPUT_PATH, config.id)
        os.makedirs(out_path, exist_ok=True)

        # Output file for generated markdown report
        out_file = os.path.join(out_path, f"{config.id}.md")

        # Rendering report
        console_logger.info(f"Rendering scenario report for config {config.id}.")
        render_template(
            name="simulation_report",
            output_file=out_file,
            config=config
        )

if __name__ == '__main__':
    create_simulation_reports()
