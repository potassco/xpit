"""
Test cases for main application functionality.
"""

from pathlib import Path
from typing import Union

TEST_DIR = parent = Path(__file__).resolve().parent


def read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    Read file at path and return contents as string.
    """
    with open(path, "r", encoding=encoding) as f:
        return f.read()