"""Initialise the PaaS Charm application."""

import pathlib

import jinja2
import yaml

from . import constants, templates


def init() -> None:
    """Initialise the PaaS Charm application."""
    charmcraft_yaml: dict = yaml.safe_load(
        (pathlib.Path() / constants.CHARM_DIR / "charmcraft.yaml").read_text()
    )
    charm_name = charmcraft_yaml["name"]

    print("creating deploy directory and files")
    (pathlib.Path() / constants.DEPLOY_DIR).mkdir(exist_ok=True)
    environment = jinja2.Environment()
    variables_tf_template = environment.from_string(templates.VARIABLES_TF)
    variables_tf = variables_tf_template.render()
    (pathlib.Path() / constants.DEPLOY_DIR / "variables.tf").write_text(variables_tf)
    terraform_tfvars_json_template = environment.from_string(
        templates.TERRAFORM_TFVARS_JSON
    )
    terraform_tfvars_json = terraform_tfvars_json_template.render(app_name=charm_name)
    (pathlib.Path() / constants.DEPLOY_DIR / "terraform.tfvars.json").write_text(
        terraform_tfvars_json
    )
    print("initialised application")
