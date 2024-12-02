"""Deploy the PaaS Charm application."""

import json
import pathlib
import re
import subprocess

import yaml


def deploy() -> None:
    """Deploy the PaaS Charm application."""
    deploy_variables = json.loads(
        (pathlib.Path() / "deploy" / "terraform.tfvars.json").read_text()
    )

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
    app_image = f"{deploy_variables['image_registry']}/{rock_info['name']}:{rock_info['version']}"
    skopeo_copy_out = subprocess.check_output(
        [
            "rockcraft.skopeo",
            "--insecure-policy",
            "copy",
            "--dest-tls-verify=false",
            f"oci-archive:{rock_name}",
            app_image,
        ],
        stderr=subprocess.STDOUT,
    ).decode(encoding="utf-8")
    print(skopeo_copy_out)

    print("creating charm")
    charm_info = yaml.safe_load(
        (pathlib.Path() / "charm" / "charmcraft.yaml").read_text()
    )
    charmcraft_pack_out = subprocess.check_output(
        ["charmcraft", "pack"], stderr=subprocess.STDOUT, cwd=pathlib.Path() / "charm"
    ).decode(encoding="utf-8")
    print(charmcraft_pack_out)
    charm_name = re.search(
        "^Packed (.+\\.charm)", rockcraft_pack_out, re.MULTILINE
    ).group(1)

    print("deploying app")
    juju_add_model_out = subprocess.check_output(
        ["juju", "add-model", deploy_variables["model_name"]], stderr=subprocess.STDOUT
    ).decode(encoding="utf-8")
    print(juju_add_model_out)
    juju_deploy_model_out = subprocess.check_output(
        [
            "juju",
            "deploy",
            f"./{charm_name}",
            charm_info["name"],
            "--resource",
            f"flask-app-image={app_image}",
        ],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / "charm",
    ).decode(encoding="utf-8")
    print(juju_deploy_model_out)
    juju_status_out = subprocess.check_output(
        ["juju", "status"], stderr=subprocess.STDOUT
    ).decode(encoding="utf-8")
    print(juju_status_out)

    print("deployed application")
