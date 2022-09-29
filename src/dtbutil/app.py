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
            carryon: str = console.input(prompt="Continue? [Y/N] ", emoji=False)
            if carryon.lower() != "y":
                raise typer.Abort()
        console.print(" OK", style="bold green")


@app.command()
def trim(
    infile: List[Path] = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Source device tree blob file(s)",
    ),
    backup: bool = typer.Option(
        False,
        "--backup",
        "-b",
        help="Create a backup of the original file(s) before trimming",
    ),
    suffix: str = typer.Option(
        "bak",
        "--suffix",
        "-s",
        help="Suffix to append to backup files, if --backup is specified",
    ),
):
    for file in infile:
        if backup:
            bakfile = Path(f"{file}.{suffix}")
            if bakfile.exists():
                err_console.print(
                    f"Backup file [bold purple]{bakfile}[/] already exists, will not overwrite.",
                    style="bold red",
                )
                continue
            else:
                console.print(f"Backing up [bold blue]{file}[/] to [bold purple]{bakfile}[/] ...", end="")
                try:
                    bakfile.write_bytes(file.read_bytes())
                except Exception as e:
                    err_console.print(f"Error backing up {file} to {bakfile}: {e}")
                    continue
                console.print(" OK", style="bold green")
        else:
            bakfile = None

        try:
            console.print(f"Trimming [bold blue]{file}[/] ", end="")
            with file.open("rb") as f:
                # check for DTB magic
                magic = f.read(4)
                if magic != b"\xd0\x0d\xfe\xed":
                    err_console.print(
                        f"File [bold blue]{file}is not a valid device tree blob.", style="bold red"
                    )
                    err_console.print(f"Magic number is {magic.hex()}, expected d00dfeed")
                    continue

                filesize = file.stat().st_size
                dtbsize = int.from_bytes(f.read(4), "big")
                console.print(f"to {dtbsize} bytes ...", end="")

                if filesize == dtbsize:
                    console.print(" no change", style="bold yellow")
                    if isinstance(backup, Path):
                        bakfile.unlink()  # type: ignore
                    continue
                elif filesize < dtbsize:
                    err_console.print(" WARNING", style="bold red")
                    err_console.print(
                        f"File size ({filesize} bytes) is below {dtbsize} bytes from DTB header, will not trim.",
                        style="yellow",
                    )
                    continue
                else:
                    console.print(
                        f"from [bold purple]{filesize}[/] to [bold green]{dtbsize}[/] bytes ...", end=""
                    )
                    f.truncate(dtbsize)
                    console.print(" OK", style="bold green")
        except Exception as e:
            err_console.print(f"Error trimming {file}: {e}")
            carryon: str = console.input(prompt="Continue? [Y/N] ", emoji=False)
            if carryon.lower() != "y":
                raise typer.Abort()
