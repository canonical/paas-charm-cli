"""Deploy the PaaS Charm application."""

import subprocess


def deploy() -> None:
    """Deploy the PaaS Charm application."""
    print("creating rock")
    subprocess.check_output(["rockcraft", "pack"])
    print("creating charm")
    subprocess.check_output(["cd", "charm", "&&", "charmcraft", "pack"])
    print("deployed application")
