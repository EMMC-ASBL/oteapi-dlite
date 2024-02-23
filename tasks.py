"""Repository management tasks powered by `invoke`.

More information on `invoke` can be found at http://www.pyinvoke.org/.
"""

# pylint: disable=import-outside-toplevel,too-many-locals
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from invoke import task

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Tuple


TOP_DIR = Path(__file__).parent.resolve()


def update_file(
    filename: Path, sub_line: "Tuple[str, str]", strip: "Optional[str]" = None
) -> None:
    """Utility function for tasks to read, update, and write files"""
    lines = [
        re.sub(sub_line[0], sub_line[1], line.rstrip(strip))
        for line in filename.read_text(encoding="utf8").splitlines()
    ]
    filename.write_text("\n".join(lines) + "\n", encoding="utf8")


@task(help={"version": "oteapi-dlite version to set"})
def setver(_, version=""):
    """Sets the oteapi-dlite version."""
    match = re.fullmatch(
        (
            r"v?(?P<version>[0-9]+(\.[0-9]+){2}"  # Major.Minor.Patch
            r"(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"  # pre-release
            r"(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?)"  # build metadata
        ),
        version,
    )
    if not match:
        sys.exit(
            "Error: Please specify version as "
            "'Major.Minor.Patch(-Pre-Release+Build Metadata)' or "
            "'vMajor.Minor.Patch(-Pre-Release+Build Metadata)'"
        )
    version = match.group("version")

    update_file(
        TOP_DIR / "oteapi_dlite" / "__init__.py",
        (r'__version__ = (\'|").*(\'|")', f'__version__ = "{version}"'),
    )

    print(f"Bumped version to {version}.")
