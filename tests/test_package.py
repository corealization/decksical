# Copyright (c) 2026 Alex Voss
# SPDX-License-Identifier: MIT
# Licensed under the MIT license. See LICENSE in the project root.

"""Check the prebuilt wheel in an independent virtual environment."""

import os
import subprocess
import sys
import unittest
from pathlib import Path
from shutil import copy2, copytree
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):

    def test_wheel_in_clean_environment(self) -> None:
        wheels = list((ROOT / "dist").glob("*.whl"))
        if len(wheels) != 1:
            self.fail("Expected one wheel in dist/. Run uv build --wheel first; remove stale wheels.")
        wheel = wheels[0]

        with TemporaryDirectory() as directory:
            workspace = Path(directory)

            environment = workspace / "venv"
            subprocess.run(
                ["uv", "venv", "--python", sys.executable, str(environment)],
                cwd=workspace, check=True,
            )

            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python), f"{wheel}[catppuccin]"],
                cwd=workspace, check=True,
            )

            copy2(ROOT / "tests/package_checks.py", workspace)
            copytree(ROOT / "tests/fixtures/site", workspace / "fixtures/site")

            subprocess.run(
                [str(python), "-I", "package_checks.py", "-v"],
                cwd=workspace, check=True,
            )
