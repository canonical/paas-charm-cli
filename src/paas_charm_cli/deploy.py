"""Deploy the PaaS Charm application."""

import json
import pathlib
import re
import subprocess

import jinja2
import yaml

from . import templates

_DEPLOY_DIR = "deploy"
_CHARM_DIR = "charm"


def deploy() -> None:
    """Deploy the PaaS Charm application."""
    deploy_variables = json.loads(
        (pathlib.Path() / _DEPLOY_DIR / "terraform.tfvars.json").read_text()
    )
    charm_info = yaml.safe_load(
        (pathlib.Path() / _CHARM_DIR / "charmcraft.yaml").read_text()
    )

    app_image = _create_upload_image(image_registry=deploy_variables["image_registry"])
    charm_file_name = _create_charm()
    _create_model_deploy_app(
        model_name=deploy_variables["model"]["name"],
        charm_file_name=charm_file_name,
        charm_name=charm_info["name"],
        app_image=app_image,
    )
    _init_terraform(
        charm_name=charm_info["name"], model_name=deploy_variables["model"]["name"]
    )
    _deploy_integrations()

    juju_status_out = subprocess.check_output(
        ["juju", "status"], stderr=subprocess.STDOUT
    ).decode(encoding="utf-8")
    print(juju_status_out)
    print("deployed application")


def _create_upload_image(image_registry: str) -> str:
    """Create the OCI image and upload it to the registry.

    Args:
        image_registry: Where the upload the image.

    Returns:
        The name of the image.
    """
    print("creating rock")
    rock_info = yaml.safe_load((pathlib.Path() / "rockcraft.yaml").read_text())
    rockcraft_pack_out = subprocess.check_output(
        ["rockcraft", "pack"], stderr=subprocess.STDOUT
    ).decode(encoding="utf-8")
    print(rockcraft_pack_out)
    rock_name = re.search(
        "^Packed (.+\\.rock)", rockcraft_pack_out, re.MULTILINE
    ).group(1)
    print("uploading rock to registry")
    app_image = f"{image_registry}/{rock_info['name']}:{rock_info['version']}"
    skopeo_copy_out = subprocess.check_output(
        [
            "rockcraft.skopeo",
            "--insecure-policy",
            "copy",
            "--dest-tls-verify=false",
            f"oci-archive:{rock_name}",
            f"docker://{app_image}",
        ],
        stderr=subprocess.STDOUT,
    ).decode(encoding="utf-8")
    print(skopeo_copy_out)

    return app_image


def _create_charm() -> str:
    """Pack the charm.

    Returns:
        The name of the created charm.
    """
    print("creating charm")
    charmcraft_pack_out = subprocess.check_output(
        ["charmcraft", "pack"],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / _CHARM_DIR,
    ).decode(encoding="utf-8")
    print(charmcraft_pack_out)
    return re.search("^Packed (.+\\.charm)", charmcraft_pack_out, re.MULTILINE).group(1)


def _create_model_deploy_app(
    model_name: str, charm_file_name: str, charm_name: str, app_image: str
) -> None:
    """Create the model if it doesn't exist and deploy the app.

    Args:
        model_name: The name of the model to deploy the app into.
        charm_file_name: The name of the charm file on disk.
        charm_name: The name of the charm for the app.
        app_image: The name of the image for the app.
    """
    print("deploying app")
    full_model_name = _create_get_model(model_name=model_name)
    _deploy_refresh_app(
        full_model_name=full_model_name,
        charm_name=charm_name,
        charm_file_name=charm_file_name,
        app_image=app_image,
    )

    juju_status_out = subprocess.check_output(
        ["juju", "status"], stderr=subprocess.STDOUT
    ).decode(encoding="utf-8")
    print(juju_status_out)


def _create_get_model(model_name: str) -> str:
    """Create the model if it doesn't exist or get the full name of the model if it does.

    Args:
        model_name: The name of the model to be created.

    Returns:
        The full name of the model.
    """
    """Create or get the full model name."""
    juju_models = json.loads(
        subprocess.check_output(
            ["juju", "models", "--format", "json"],
            stderr=subprocess.STDOUT,
        ).decode(encoding="utf-8")
    )
    full_model_name: str | None = next(
        (
            model["name"]
            for model in juju_models["models"]
            if model["name"].split("/")[1] == model_name
        ),
        None,
    )
    if full_model_name:
        return full_model_name

    juju_add_model_out = subprocess.check_output(
        ["juju", "add-model", model_name],
        stderr=subprocess.STDOUT,
    ).decode(encoding="utf-8")
    print(juju_add_model_out)
    full_model_name_match = re.search(
        "^^Added '(.*)' model.* user '(.*)'$", juju_add_model_out
    )
    return f"{full_model_name_match.group(2)}/{full_model_name_match.group(1)}"


def _deploy_refresh_app(
    full_model_name: str, charm_name: str, charm_file_name: str, app_image: str
) -> None:
    """Deploy or refresh the app.

    Args:
        full_model_name: The model to deploy the app into.
        charm_name: The name of the charm to be deployed.
        charm_file_name: The name of the charm file to be deployed.
        app_image: The name of the image for the app.
    """
    juju_status_for_model = json.loads(
        subprocess.check_output(
            ["juju", "status", "--model", full_model_name, "--format", "json"],
            stderr=subprocess.STDOUT,
        ).decode(encoding="utf-8")
    )
    app_deployed = charm_name in juju_status_for_model["applications"]

    if not app_deployed:
        juju_deploy_out = subprocess.check_output(
            [
                "juju",
                "deploy",
                f"./{charm_file_name}",
                charm_name,
                "--resource",
                f"flask-app-image={app_image}",
            ],
            stderr=subprocess.STDOUT,
            cwd=pathlib.Path() / _CHARM_DIR,
        ).decode(encoding="utf-8")
        print(juju_deploy_out)
        return

    juju_refresh_out = subprocess.check_output(
        [
            "juju",
            "refresh",
            charm_name,
            "--path",
            f"./{charm_file_name}",
            "--resource",
            f"flask-app-image={app_image}",
            "--model",
            full_model_name,
        ],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / _CHARM_DIR,
    ).decode(encoding="utf-8")
    print(juju_refresh_out)


def _init_terraform(charm_name: str, model_name: str) -> None:
    """Initialise terraform and import model and app.

    Args:
        charm_name: The name of the charm for the app.
        model_name: The name of the model the app is deployed in.
    """
    print("initialising terraform and importing model and app")
    environment = jinja2.Environment()
    main_tf_template = environment.from_string(templates.MAIN_TF)
    main_tf = main_tf_template.render(
        model_resource_name=charm_name, app_name=charm_name
    )
    print(main_tf)
    (pathlib.Path() / _DEPLOY_DIR / "main.tf").write_text(main_tf)
    terraform_init_out = subprocess.check_output(
        ["terraform", "init"],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / _DEPLOY_DIR,
    ).decode(encoding="utf-8")
    print(terraform_init_out)
    terraform_model_import_out = subprocess.check_output(
        ["terraform", "import", f"juju_model.{model_name}", model_name],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / _DEPLOY_DIR,
    ).decode(encoding="utf-8")
    print(terraform_model_import_out)
    terraform_app_import_out = subprocess.check_output(
        [
            "terraform",
            "import",
            f"juju_application.{charm_name}",
            f"{model_name}:{charm_name}",
        ],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / _DEPLOY_DIR,
    ).decode(encoding="utf-8")
    print(terraform_app_import_out)


def _deploy_integrations() -> None:
    """Deploy integrations for the app."""
    print("deploying integrations")
    terraform_plan_out = subprocess.check_output(
        ["terraform", "plan"],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / _DEPLOY_DIR,
    ).decode(encoding="utf-8")
    print(terraform_plan_out)
    terraform_apply_out = subprocess.check_output(
        ["terraform", "apply", "-auto-approve"],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / _DEPLOY_DIR,
    ).decode(encoding="utf-8")
    print(terraform_apply_out)
