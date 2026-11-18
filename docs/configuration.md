---
icon: lucide/settings-2
---

# Configuration and customization

Decksical uses Zensical's `zensical.toml` for site configuration. This page
covers the settings that shape decks and their appearance. For the full
configuration reference, see Zensical's guides to
[navigation](https://zensical.org/docs/setup/navigation/) and
[colors](https://zensical.org/docs/setup/colors/).

## Define decks with `nav`

Zensical's `nav` setting controls the site's navigation. A nested section can
also define a deck: list its overview and slide pages as children, in the order
they should be presented.

```toml
nav = [
  { "Guides" = "guides/index.md" },
  { "My presentation" = [
    { "Overview" = "slides/index.md" },
    { "Welcome" = "slides/welcome.md" },
    { "The problem" = "slides/problem.md" },
    { "The solution" = "slides/solution.md" },
  ] },
]
```

Each slide page selects `slide.html` in its front matter. Include an `index.md`
overview as the first page in every deck section. It is an ordinary
documentation page that provides the deck's landing and return destination for
the up-arrow and **Escape**. Without one, Previous and Next still work, but the
up-arrow is hidden and Escape has no destination. See
[Authoring: add a deck overview](authoring.md#add-a-deck-overview).

## Configure slide navigation

Deck navigation arrows can stay hidden until the pointer moves over their
area. Add this Decksical option under `project.extra`:

```toml
[project.extra.decksical.navigation]
hide_until_hover = true
```

The arrows remain visible when reached by keyboard focus and on touch devices.
For the controls and keyboard shortcuts, see [Presenting](presenting.md).

## Choose a theme and palette

Select a Decksical theme under `[project.theme]`. The regular theme supports
Zensical's `modern` and `classic` variants. The Catppuccin theme is an
optional alternative; see [Installation](installation.md#use-with-catppuccin)
for its package extra and theme name.

```toml
[project.theme]
name = "decksical"
variant = "modern" # or "classic"
```

Zensical palettes can set the light and dark schemes and provide a palette
toggle. Add or adjust `[[project.theme.palette]]` entries in the same
`zensical.toml`; each entry defines a scheme and the label/icon for switching
to the next one. Zensical displays its palette cycle control by default. The
Decksical documentation replaces that control with a dropdown so readers can
choose directly from its many theme examples. This is a docs-site customization
loaded through `extra_javascript`; Decksical projects keep Zensical's standard
control. The selected palette applies site-wide, including ordinary pages and
slides.

## Override ordinary documentation pages

If your project has a local `main.html` override, make it extend Decksical's
`decksical.html` template. This preserves Decksical's page setup, including the
Catppuccin stylesheet on ordinary pages when using that variant:

```jinja
{% extends "decksical.html" %}

{% block announce %}
  Your announcement here.
{% endblock %}
```

See [How the theme works](how-it-works.md#customize-the-theme-source) for how
the wrapper fits into the theme.

## Customize colors with `extra.css`

CSS customizations belong to the site project, not the Decksical package. Add
an `extra.css` file under the documentation directory and list it in the
`[project]` section:

```toml
[project]
extra_css = ["assets/stylesheets/extra.css"]
```

For example, a named dark palette can override Zensical's color variables in
that stylesheet:

```css
[data-md-color-scheme="tokyo-night"] {
  color-scheme: dark;
  --md-default-bg-color: #1a1b26;
  --md-default-fg-color: #c0caf5;
  --md-primary-fg-color: #7aa2f7;
  --md-accent-fg-color: #7dcfff;

  /* Reconnect these root-defined colors to this scheme's variables. */
  --md-typeset-color: var(--md-default-fg-color);
  --md-typeset-a-color: var(--md-primary-fg-color);
}
```

To make the named scheme selectable, add it to the palette list and mark
custom primary and accent colors:

```toml
[[project.theme.palette]]
scheme = "tokyo-night"
primary = "custom"
accent = "custom"
toggle.icon = "lucide/moon"
toggle.name = "Switch to Tokyo Night"
```

The Tokyo Night example in this documentation also adapts code syntax,
admonition icons, and other colors in `extra.css`. See the [example slides](example/index.md).
Zensical lists the available [color variables](https://zensical.org/docs/setup/colors/)
and [syntax highlighting variables](https://zensical.org/docs/authoring/code-blocks/).
