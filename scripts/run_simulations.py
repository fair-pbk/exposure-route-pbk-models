import glob
import os
import logging
from docs.doc_utils import render_template
from simulation.simulation import run_config
from simulation.simulation import load_config

CONFIGS_PATH = './scenarios/'
OUTPUT_PATH = 'docs/simulation'

# Configure logger for formatted console output
console_logger = logging.getLogger('create_simulation_reports')
console_logger.setLevel(logging.INFO)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
if not console_logger.handlers:
    console_logger.addHandler(_console_handler)

def create_simulation_reports(force_recompute: bool):
    configs = glob.glob(f'./{CONFIGS_PATH}/**/*.yaml', recursive=True)
    for file in configs:
        file_dir = os.path.dirname(file)

        # Load config
        config = load_config(file)

        # Create output directory if it does not exist
        out_path = os.path.join(OUTPUT_PATH, os.path.relpath(file_dir, CONFIGS_PATH))

        # Ensure output path
        os.makedirs(out_path, exist_ok=True)

        # Run simulations
        console_logger.info(f"Running simulation config {file}")
        run_config(
            config = config,
            out_path = out_path,
            force_recompute = force_recompute
        )

        # Rendering report
        console_logger.info(f"Rendering scenario report for config {config.id}.")
        render_template(
            name="simulation_report",
            output_file=os.path.join(out_path, f"{config.id}.md"),
            config=config
        )

if __name__ == '__main__':
    create_simulation_reports(True)
