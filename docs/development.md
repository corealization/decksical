---
icon: lucide/code
---

# Development

This page provides instructions for previewing and building Decksical's documentation, running its checks, and preparing a release.

## Preview the documentation

```sh
./serve.sh
```

Use `serve.sh` during development when previewing this repository. It syncs the
Catppuccin dependency, rebuilds and reinstalls the wheel so the preview uses the
current theme files, then starts Zensical. For an ordinary project, use
`zensical serve` or `uv run zensical serve` instead.

## Build the documentation

```sh
./build.sh
```

Use `build.sh` to build the documentation with the packaged theme. It follows
the same wheel-installation steps as `serve.sh` and runs Zensical's one-off
strict build, which exits when complete. The generated site is written to
`site/`.

## Run browser tests

Prepare the development environment:

```sh
uv sync --locked --extra catppuccin
```

Install OS dependencies separately through your distribution's package manager.
For example, on Debian, installing the distribution browsers also installs
their runtime libraries:

```sh
sudo apt update
sudo apt install chromium firefox-esr
```

The test run downloads and launches the browser revision required by Playwright. System-installed browsers are only needed to provide OS dependencies.

Build and install the wheel, then run the suite with Chromium or Firefox:

```sh
uv build --wheel
uv pip install --no-deps --reinstall dist/*.whl
uv run --no-sync python -m unittest discover -s tests -p test_slides.py -v
DECKSICAL_TEST_BROWSER=firefox uv run --no-sync python -m unittest discover -s tests -p test_slides.py -v
```

We test the wheel because editable installs lack Catppuccin's packaged shared resources. Use `uv run --no-sync` so uv does not restore the editable install. Keep one wheel in `dist/`; rebuild and reinstall it after changing theme files. Run `uv sync --locked --extra catppuccin` to restore the editable development install.

The tests are run with Chromium, the Decksical theme, and the modern variant by default. Set:

- `DECKSICAL_TEST_BROWSER=firefox` to select Firefox,
- `DECKSICAL_TEST_THEME=decksical-catppuccin` to select Catppuccin, or
- `DECKSICAL_TEST_VARIANT=classic` to select Zensical's classic variant.

To run all combinations locally, use:

```sh
uv run --no-sync python tests/run_browser_matrix.py
```

The runner starts a separate test process for each combination and reports any that fail. CI runs the same combinations in parallel through its workflow matrix.

## Run package integration tests

```sh
uv build --wheel
uv run python -m unittest discover -s tests -p test_package.py -v
```

The test requires one wheel in `dist/` and uv. It installs the wheel in a clean environment, checks its resources, and builds a fixture with both themes.

## Check Python code

Run Ruff and ty. uv prepares the development environment automatically:

```sh
uv run ruff check .
uv run ty check
```

The Python checks workflow runs both commands on pushes to `main`.

## Prepare a release

1. Choose the next version and update `version` in `pyproject.toml`. Run `uv lock` to update `uv.lock`, then `uv sync --locked` to verify the lock file matches the project.

2. Commit both files, merge the change to `main`, and make sure the checks pass. Create a signed, annotated tag on that commit. The tag must match the package version, including its `v` prefix:

   ```sh
   git tag -s -m "Decksical 0.1.3" v0.1.3
   git push origin v0.1.3
   ```

   Replace `0.1.3` with the version you chose. 

3. The Release wheel workflow runs on the tag push. It checks that the tag matches `pyproject.toml`, builds the wheel, tests it in a clean environment, and creates a draft GitHub release with the wheel attached. Rerun the workflow for a transient CI failure. If the tag points to the wrong version or code, correct the version and create a new tag.

4. Open the draft release on GitHub. Review the generated Markdown notes, edit the title or notes as needed, and confirm the wheel is attached. Publish the draft when it is ready. Treat the published tag as final; do not move or reuse it for a correction.

5. Publishing the GitHub release starts the Documentation workflow, which builds and deploys the docs from that release's tag. Check that workflow completes.

The release workflow does not automatically publish to PyPI yet. 

## GitHub Actions

The Documentation workflow builds and publishes the site to GitHub Pages when a GitHub release is published. It checks out the release tag, so the published docs match that release rather than unreleased changes on `main`. The documentation is hosted under the custom domain `docs.corealization.com/decksical` so that hosting arrangements can be changed if needed.

The Browser tests workflow runs on pushes to `main` with the locked versions. Its daily run at 07:23 UTC tests the latest Zensical and Catppuccin theme releases across both themes, browsers, and Zensical variants. GitHub may delay scheduled runs, and the workflow must be on the default branch.

You can also run the workflow manually and select **Test the latest published Zensical and Catppuccin theme versions**. This changes only the CI environment, not the lock file.

To test the latest releases locally, first build and install the wheel as above,
then upgrade Zensical and Catppuccin and run the full browser matrix:

```sh
uv pip install --upgrade zensical catppuccin-zensical
uv run --no-sync python tests/run_browser_matrix.py
```

Run `uv sync --locked --extra catppuccin` to restore the locked development
environment afterwards.
