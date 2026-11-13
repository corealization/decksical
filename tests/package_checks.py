# Copyright (c) 2026 Alex Voss
# SPDX-License-Identifier: MIT
# Licensed under the MIT license. See LICENSE in the project root.

"""Checks for the resources installed from the release wheel."""

import subprocess
import sys
import unittest
from importlib.metadata import entry_points
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory


class PackageTests(unittest.TestCase):

    # Both public theme names resolve to installed theme packages.
    def test_theme_registration(self) -> None:
        registered = entry_points(group="mkdocs.themes")

        for name in ["decksical", "decksical-catppuccin"]:
            with self.subTest(theme=name):
                self.assertEqual(len(registered.select(name=name)), 1)
                theme_file = Path(registered[name].load().__file__)

                self.assertTrue(theme_file.is_file())
                self.assertTrue(theme_file.is_relative_to(sys.prefix))

    # Each registered theme ships its configuration, template, assets, and partials.
    def test_theme_resources(self) -> None:
        registered = entry_points(group="mkdocs.themes")

        for name in ["decksical", "decksical-catppuccin"]:
            with self.subTest(theme=name):
                theme = Path(registered[name].load().__file__).parent

                for resource in [
                    "mkdocs_theme.yml",
                    "decksical.html",
                    "slide.html",
                    "slide-title.html",
                    "shared/decksical.html",
                    "shared/slide.html",
                    "assets/slides/slides.css",
                    "assets/slides/slides.mjs",
                    "partials/slides/content.html",
                    "partials/slides/navigation.html",
                ]:
                    with self.subTest(resource=resource):
                        self.assertTrue((theme / resource).is_file(), resource)

    # Both installed themes build the authoring fixture without missing templates or assets.
    def test_fixture_builds_with_both_themes(self) -> None:
        source = Path(__file__).parent / "fixtures/site"

        for name in ["decksical", "decksical-catppuccin"]:
            with self.subTest(theme=name), TemporaryDirectory() as directory:
                project = Path(directory) / "project"
                copytree(source, project)

                config = project / "zensical.toml"
                config.write_text(
                    config.read_text().replace('name = "decksical"', f'name = "{name}"'),
                    encoding="utf-8",
                )

                subprocess.run(
                    [sys.executable, "-I", "-m", "zensical", "build", "--strict"],
                    cwd=project, check=True,
                )


if __name__ == "__main__":
    unittest.main()
