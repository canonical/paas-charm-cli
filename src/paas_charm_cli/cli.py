"""CLI for PaaS Charm applications."""

import typer

from .deploy import deploy
from .init import init

app = typer.Typer()
app.command()(deploy)
app.command()(init)


if __name__ == "__main__":
    app()
