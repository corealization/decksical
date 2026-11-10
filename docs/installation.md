---
icon: lucide/package-open
---

# Installation

You need Python 3.11 or later and Zensical 0.1.0 or later. Install the theme
into the virtual environment that also contains Zensical.

## Install from PyPI

```sh
pip install decksical
```

For a project managed with uv, run:

```sh
uv add decksical
```

## Configure Zensical

Select the theme in your own `zensical.toml`:

```toml
[project.theme]
name = "decksical"
```

Keep your existing settings and local overrides. Give each deck its own
section in `nav` in `zensical.toml`, and store its slides as Markdown files in
your project's documentation directory. The installed package provides the
slide template, stylesheet, and keyboard controls.

## Use with Catppuccin

Install Decksical with its Catppuccin extra:

```sh
pip install "decksical[catppuccin]"
```

For a uv project:

```sh
uv add "decksical[catppuccin]"
```

Then select the theme in your `zensical.toml`:

```toml
[project.theme]
name = "decksical-catppuccin"
```

Remove any existing `[[project.theme.palette]]` entries that use `default`
or `slate` to use Catppuccin's inherited light and dark palettes.

Both variants provide the same slide features.

Next, [create your first deck](getting-started.md).

[Catppuccin for Zensical]: https://github.com/jonathan343/catppuccin-zensical
