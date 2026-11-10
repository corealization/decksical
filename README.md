<img src="docs/assets/decksical_logo.svg" alt="" width="72" align="right">

# Decksical

Decksical is a simple theme for Markdown slides built with [Zensical].

> **Note:** Decksical is in beta. I am still working on making it behave consistently and on introducing automated tests and CI workflows. The original rich prototype was written with Codex but has seen many iterations and I have spent much time trying to ensure that the result is human-readable and can be maintained with or without the help of AI agents.

For bug reports and feature requests, see [CONTRIBUTING.md].

## Usage

### Install the theme

Install Decksical from PyPI into the same environment as Zensical. You need
Python 3.11 or later and Zensical 0.1.0 or later. If you want to use Catppuccin, also install [catppuccin-zensical]:


```sh
pip install decksical
pip install catppuccin-zensical
```

For a project managed with uv:

```sh
uv add decksical
uv add catppuccin-zensical
```

### Configure Zensical

In your own project's `zensical.toml`, set the theme name to `decksical` (or `decksical-catppuccin`):

```toml
[project.theme]
name = "decksical"
# name = "decksical-catppuccin"
```

Pages keep their their default layout unless the slide template is explicitly used.

Run `zensical serve` from your project directory. If you use uv, run
`uv run zensical serve`.

You can configure [light and dark mode in Catppuccin].

## Authoring

Write one Markdown file per slide. Set `template: slide.html` in its front
matter. Then list the slides in presentation order in `zensical.toml`.

Read the [documentation] for setup, authoring, and presenting instructions, or open the [example slide deck].

## Related project

[zensical-slides] turns existing Zensical documentation content into a presentation, splitting it into slides at headings. Decksical expects presentation content to be written specifically as slides, with one Markdown file per slide.

## Development

Repository setup, preview, testing, release, and CI instructions are in the
[Development guide](docs/development.md).

[CONTRIBUTING.md]: CONTRIBUTING.md
[Catppuccin for Zensical]: https://github.com/jonathan343/catppuccin-zensical
[documentation]: https://corealization.github.io/decksical/
[example slide deck]: https://corealization.github.io/decksical/example/title/
[Zensical]: https://zensical.org
[light and dark mode in Catppuccin]: https://jonathan343.github.io/catppuccin-zensical/configuration/#light-dark-with-a-toggle
[zensical-slides]: https://github.com/BeyondMagic/zensical-slides
