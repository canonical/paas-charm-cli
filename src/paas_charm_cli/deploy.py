"""Deploy the PaaS Charm application."""

import json
import pathlib
import re
import subprocess

import jinja2
import yaml

from . import templates


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
            f"docker://{app_image}",
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
        "^Packed (.+\\.charm)", charmcraft_pack_out, re.MULTILINE
    ).group(1)

    print("deploying app")
    juju_add_model_out = subprocess.check_output(
        ["juju", "add-model", deploy_variables["model"]["name"]],
        stderr=subprocess.STDOUT,
    ).decode(encoding="utf-8")
    print(juju_add_model_out)
    juju_deploy_out = subprocess.check_output(
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
    print(juju_deploy_out)
    juju_status_out = subprocess.check_output(
        ["juju", "status"], stderr=subprocess.STDOUT
    ).decode(encoding="utf-8")
    print(juju_status_out)

    print("deploying integrations")
    environment = jinja2.Environment()
    main_tf_template = environment.from_string(templates.MAIN_TF)
    main_tf = main_tf_template.render(
        model_resource_name=charm_info["name"],
        app_name=charm_info["name"],
    )
    print(main_tf)
    (pathlib.Path() / "deploy" / "main.tf").write_text(main_tf)
    terraform_init_out = subprocess.check_output(
        ["terraform", "init"], stderr=subprocess.STDOUT, cwd=pathlib.Path() / "deploy"
    ).decode(encoding="utf-8")
    print(terraform_init_out)
    terraform_plan_out = subprocess.check_output(
        ["terraform", "plan"], stderr=subprocess.STDOUT, cwd=pathlib.Path() / "deploy"
    ).decode(encoding="utf-8")
    print(terraform_plan_out)
    terraform_apply_out = subprocess.check_output(
        ["terraform", "apply", "-auto-approve"],
        stderr=subprocess.STDOUT,
        cwd=pathlib.Path() / "deploy",
    ).decode(encoding="utf-8")
    print(terraform_apply_out)
    juju_status_out = subprocess.check_output(
        ["juju", "status"], stderr=subprocess.STDOUT
    ).decode(encoding="utf-8")
    print(juju_status_out)

    print("deployed application")
