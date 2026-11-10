# Copyright (c) 2026 Alex Voss
# SPDX-License-Identifier: MIT
# Licensed under the MIT license. See LICENSE in the project root.

"""Run the browser suite across every supported configuration."""

import os
import subprocess
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSERS = ["chromium", "firefox"]
THEMES = ["decksical", "decksical-catppuccin"]
VARIANTS = ["modern", "classic"]


def main() -> int:
    failures: list[str] = []
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_slides.py",
        "-v",
    ]

    for browser, theme, variant in product(BROWSERS, THEMES, VARIANTS):
        configuration = f"{browser}, {theme}, {variant}"
        print(f"\n=== Browser tests: {configuration} ===", flush=True)
        environment = os.environ.copy()
        environment["DECKSICAL_TEST_BROWSER"] = browser
        environment["DECKSICAL_TEST_THEME"] = theme
        environment["DECKSICAL_TEST_VARIANT"] = variant

        result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
        if result.returncode:
            failures.append(configuration)

    if failures:
        print("\nFailed configurations:", file=sys.stderr)
        for configuration in failures:
            print(f"- {configuration}", file=sys.stderr)
        return 1

    print("\nAll browser test configurations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
