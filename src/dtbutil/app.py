import readline
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich.text import Text

from dtbutil import __version__
from dtbutil.console import console, err_console

app = typer.Typer()


def version_callback(value: bool):
    if value:
        console.print(f"{__package__} v{__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version"
    ),
):
    readline.parse_and_bind("tab: complete")
    pass


@app.command()
def todts(
    infile: List[Path] = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Source device tree blob file(s)",
    ),
    outpath: Path = typer.Option(
        None,
        "--outpath",
        "-o",
        dir_okay=True,
        file_okay=True,
        writable=True,
        help="Output directory for device tree source files. Default is the same directory as the input file.",
    ),
):
    DTC_ARGS = ["dtc", "-qI", "dtb", "-O", "dts", "-@", "-H", "epapr", "-o"]

    for path in infile:
        if outpath is None:
            outfile = path.with_suffix(".dts")
        elif outpath.is_dir():
            outfile = outpath / path.with_suffix(".dts").name
        elif outpath.is_file() and len(infile) == 1:
            outfile = outpath
        else:
            raise typer.BadParameter(
                "Output path must be a directory if more than one input file is specified."
            )

        try:
            console.print(f"Converting [bold blue]{path}[/] to [bold yellow]{outfile}[/] ...", end="")
            subprocess.check_call(DTC_ARGS + [outfile, path])
        except subprocess.CalledProcessError as e:
            err_console.print(f"Error converting {path} to {outfile}: {e}")
            carryon = console.input(prompt="Continue? [Y/N] ", emoji=False, default="N")  # type: ignore
            if carryon.lower() != "y":
                raise typer.Abort()
        console.print(" OK", style="bold green")


if __name__ == "__main__":
    app()
