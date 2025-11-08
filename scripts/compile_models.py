import os
import glob
import uuid
import tellurium as te
import libsbml as ls
import logging
from pathlib import Path

from sbmlpbkutils import PbkModelValidator
from sbmlpbkutils import AnnotationsTemplateGenerator
from sbmlpbkutils import PbkModelAnnotator
from sbmlpbkutils import ParametrisationsTemplateGenerator

models_path = './models/'
output_path = './models/'

# Configure logger for formatted console output
console_logger = logging.getLogger('compile_models')
console_logger.setLevel(logging.INFO)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
if not console_logger.handlers:
    console_logger.addHandler(_console_handler)

def create_file_logger(logfile: Path) -> logging.Logger:
    logger = logging.getLogger(uuid.uuid4().hex)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile, 'w+')
    formatter = logging.Formatter('[%(levelname)s] - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

def compile_models():
    models = glob.glob('./models/**/*.ant', recursive=True)
    for file in models:
        compile_model(file)

def compile_model(file: str):
    try:
        filename = os.path.basename(file)
        file_dir = os.path.dirname(file)

        # Create output directory if it does not exist
        output_dir = os.path.join(output_path, os.path.relpath(file_dir, models_path))
        os.makedirs(output_dir, exist_ok=True)

        # Convert Antimony to SBML
        sbml_file = Path(os.path.join(output_dir, filename)).with_suffix('.sbml')
        console_logger.info(
            "Creating SBML file [%s] from Antimony file [%s].",
            os.path.basename(sbml_file),
            filename
        )
        r = te.loada(file)
        r.exportToSBML(sbml_file, current = False)

        # Annotate SBML model
        document = ls.readSBML(sbml_file)
        annotations_file = Path(file).with_suffix('.annotations.csv')
        if not os.path.exists(annotations_file):
            # create annotations (csv) file if it does not exist
            console_logger.info(
                "Annotations file not found: creating annotations file [%s].",
                os.path.basename(annotations_file)
            )
            model = document.getModel()
            annotations_template_generator = AnnotationsTemplateGenerator()
            annotations = annotations_template_generator.generate(model)
            annotations.to_csv(annotations_file, index=False)

        # Create annotated SBML file
        annotated_sbml_file = Path(sbml_file).with_suffix('.sbml')
        annotator = PbkModelAnnotator()
        annotations_log_file = Path(sbml_file).with_suffix('.annotations.log')
        logger = create_file_logger(annotations_log_file)
        console_logger.info(
            "Creating annotated SBML file [%s] with annotations file [%s].",
            os.path.basename(annotated_sbml_file),
            os.path.basename(annotations_file)
        )
        annotator.annotate(
            document,
            str(annotations_file),
            logger = logger
        )
        ls.writeSBML(document, str(annotated_sbml_file))

        # Create parametrisations file
        parametrisation_file = Path(sbml_file).with_suffix('.params.csv')
        if not os.path.exists(parametrisation_file):
            # create parametrisations (csv) file if it does not exist
            console_logger.info(
                "Parametrisations file not found: creating parametrisations file [%s].",
                os.path.basename(parametrisation_file)
            )
            model = document.getModel()
            parametrisations_template_generator = ParametrisationsTemplateGenerator()
            (instances, parametrisations) = parametrisations_template_generator.generate(model)
            parametrisations.to_csv(parametrisation_file, index=False)

        # Validate annotated SBML file
        validation_log_file = Path(sbml_file).with_suffix('.validation.log')
        validator = PbkModelValidator()
        logger = create_file_logger(validation_log_file)
        validator.validate(str(annotated_sbml_file), logger)

    except Exception as e:
        console_logger.error("Error processing model file [%s]: %s", os.path.basename(file), str(e))

if __name__ == '__main__':
    compile_models()

