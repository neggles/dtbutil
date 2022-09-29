from pathlib import Path
from typing import Optional

import typer

from dtbutil import __version__
from dtbutil.console import console, err_console

app = typer.Typer()


def version_callback(value: bool):
    if value:
        console.print(f"{__package__} v{__version__}")
        raise typer.Exit()


@app.command()
def cli(
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback),
):
    console.print("bimp")


if __name__ == "__main__":
    app()
