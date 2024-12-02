"""Deploy the PaaS Charm application."""

import pathlib
import subprocess


def deploy() -> None:
    """Deploy the PaaS Charm application."""
    print("creating rock")
    subprocess.check_output(["rockcraft", "pack"])
    print("creating charm")
    subprocess.check_output(["charmcraft", "pack"], cwd=pathlib.Path() / "charm")
    print("deployed application")
