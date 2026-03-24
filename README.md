# Harmonised exposure routes PBK models repository

## Compile models

### Install requirements

To install the requirements, type:

```
pip install -r requirements.txt
```

### Compile models

Converts the Antimony model implementations to SBML and annotates the models:

```
python ./scripts/compile_models.py
```

### Run simulations

Run simulation scenarios:

```
python ./scripts/run_simulations.py
```

### Create model docs

Create model documentation pages:

```
python ./scripts/create_model_docs.py
```

### MkDocs build and serve local

To build type:

```
mkdocs build
```

To serve locally type:

```
mkdocs serve --livereload
```