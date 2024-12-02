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

    print("creating and uploading rock")
    rock_info = yaml.safe_load((pathlib.Path() / "rockcraft.yaml").read_text())
    rockcraft_pack_out = subprocess.check_output(["rockcraft", "pack"]).decode(
        encoding="utf-8"
    )
    rock_name = re.search(
        "^Packed (.+\\.rock)", rockcraft_pack_out, re.MULTILINE
    ).group(1)
    subprocess.check_output(
        [
            "rockcraft.skopeo",
            "--insecure-policy",
            "copy",
            "--dest-tls-verify=false",
            f"oci-archive:{rock_name}",
            f"docker://{deploy_variables['image_registry']}/"
            f"{rock_info['name']}:{rock_info['version']}",
        ]
    )

    print("creating charm")
    subprocess.check_output(["charmcraft", "pack"], cwd=pathlib.Path() / "charm")
    print("deployed application")
