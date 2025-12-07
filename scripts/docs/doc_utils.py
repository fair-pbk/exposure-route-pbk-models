import os
from jinja2 import Environment, FileSystemLoader

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
