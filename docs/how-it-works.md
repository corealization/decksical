---
icon: lucide/settings
---

# How the theme works

This page explains Decksical's implementation for contributors and for people
who want to adapt the theme for their own use. Decksical is licensed under the
MIT license.

## What a custom theme provides

A Zensical theme supplies the templates and assets that turn rendered Markdown
into web pages. Templates define the page structure, CSS controls its
appearance, and JavaScript adds interactivity. A custom theme can inherit from
an existing theme, replace selected templates or template blocks, override CSS,
and add JavaScript.

Decksical supports Zensical's modern and classic theme variants. It also has an
optional Catppuccin variant, which inherits from the `catppuccin-zensical`
theme. Each variant adds a slide template and assets; ordinary documentation
pages use the inherited templates. A page becomes a slide when its front
matter selects `slide.html`:

```
---
template: slide.html
---
```

The theme is an installed Python package. The documentation project selects
it with `name = "decksical"` under `[project.theme]` in `zensical.toml`.

## Contents of the theme

The theme lives in `src/decksical/`:

| File | Purpose |
| --- | --- |
| `__init__.py` | Makes the directory a Python package. It contains no slide processing logic. |
| [Theme configuration] | Declares `extends: material` so missing templates and assets come from the inherited theme. |
| [Slide template] | Defines the slide page structure and override blocks. |
| [Content partial] | Separates the rendered Markdown into columns when a marker is present. |
| [Navigation partial] | Creates previous, overview, and next links within the deck. |
| [Slide stylesheet] | Sets the presentation layout, image sizing, notes visibility, and print styles. |
| [Slide JavaScript] | Handles keyboard navigation, automatic playback, and notes visibility. |

The repository's [Package configuration] registers the package through the
`mkdocs.themes` entry point:

```toml
[project.entry-points."mkdocs.themes"]
decksical = "decksical"
decksical-catppuccin = "decksical.catppuccin"
```

The key is the theme name used in `zensical.toml`. The value identifies the
Python package containing its resources. If you create a customized version
with a different theme name, update this registration and the name used by
documentation projects.

## The Catppuccin variant

`decksical-catppuccin` inherits the `catppuccin` theme from the optional
[`catppuccin-zensical` package](installation.md#use-with-catppuccin). Its
configuration and slide wrapper live in
`src/decksical/catppuccin/`.
The slide wrapper extends the shared slide template and adds Catppuccin's
stylesheet in the `styles` block. This stylesheet is only loaded by the
Catppuccin variant, which adds no JavaScript of its own.

The wheel includes the shared assets and partials in both theme directories.
Both slide wrappers extend `shared/slide.html`. The common template lives in
`src/decksical/shared/` and is included in both theme directories.
The wheel's `force-include` mappings in `pyproject.toml` include the shared
source files at these additional paths without creating temporary copies.
Edit the common source files to change both variants, or edit the Catppuccin
wrapper to change only that variant.

## How a slide page is assembled

Zensical renders the Markdown first and makes the resulting HTML available
to the template as `page.content`. The slide template extends `base.html`
and replaces its `content` and `footer` blocks. The inherited base supplies
the surrounding HTML document and the rest of Zensical's page infrastructure.

The `styles` block calls `super()` to retain the inherited stylesheets and
adds the slide stylesheet in the HTML head. [Instant navigation](https://zensical.org/docs/setup/navigation/#instant-navigation)
synchronizes head elements when changing pages, including this stylesheet.

The `content` block wraps the rendered content in a `.slide` section. Its nested
`slide_content` block includes `partials/slides/content.html` to render the body.
The `footer` block contains a `slide_navigation` block that includes
`partials/slides/navigation.html`. The footer sits after the main content,
inside the container that [instant navigation](https://zensical.org/docs/setup/navigation/#instant-navigation)
updates.

A nested `slide_scripts` block loads the JavaScript module inside
the content container, where [instant navigation](https://zensical.org/docs/setup/navigation/#instant-navigation)
executes incoming scripts.
You can override `styles`, `slide_content`, `slide_navigation`, or `slide_scripts`
separately, or replace the enclosing `content` and `footer` blocks. These override
points are defined in `slide.html`, since including templates cannot override
blocks inside their partials.

These classes connect the template to the stylesheet and script:

| Class | Role |
| --- | --- |
| `.slide` | Identifies a slide page and contains its content and notes. |
| `.slide__content` | Contains the rendered slide body. |
| `.slide__columns` | Holds the two columns when a column-break marker is present. |
| `.slide__column` | Contains one column's content. |
| `.slide__navigation` | Contains previous, overview, and next links. |
| `.slide__footer` | Wraps navigation below the main content. |
| `.slide--notes-visible` | Records that notes should be visible on the current slide. |

Keep the selectors in the CSS and JavaScript aligned with any classes you
change in the template.

## How columns and images work

Decksical can arrange slide content in two columns and display images at
column or slide width.
For a slide without a [column-break marker](authoring.md#two-columns), the
template outputs `page.content` directly. For a two-column slide, it splits
the rendered HTML at the first literal `<!-- column-break -->` marker and
puts each side in its own `.slide__column` container.

An initial level-one heading is placed before the column containers. A
trailing `<details class="notes">` block is placed after them. The heading
and notes therefore use the full slide width. CSS Grid gives the two columns
equal widths and a gutter. Below `48rem`, the columns stack in source order.
The first element in each column has no top margin.

This separation uses string operations on rendered HTML. It assumes one
marker, an optional initial level-one heading, and notes at the end of the
slide. If you introduce different marker syntax or change the HTML generated
for notes, update the corresponding strings in the content partial.

Images inside columns fill the column width and retain their proportions.
An image with the `slide-image` class instead fills the slide content width
and a `75dvh` image area. `object-fit: contain` keeps the whole image visible.
The `attr_list` Markdown extension lets authors add this class to an image.

## How navigation works

Each deck occupies its own section under `nav` in `zensical.toml`. The template
finds the current page among the children of its immediate navigation parent.
It adds previous and next links only when the adjacent sibling also selects
`slide.html`. An ordinary page or a nested section interrupts slide navigation.
Slides do not need a separate deck identifier in their front matter.

The overview link points to the nearest ancestor section's non-slide index
page. It is omitted when no such index exists. The links use Lucide icons
included from the inherited theme's `.icons/lucide/` directory.

The Left and Right keyboard handlers click these same links. If you change
how the template chooses adjacent slides, keyboard navigation follows the
new links automatically. Keep `rel="prev"` and `rel="next"` on the links,
since the script uses those attributes to find them.

## How automatic playback works

The slide template places the resolved duration in a `data-autoplay-duration`
attribute. A slide's `duration` metadata overrides the value on the nearest
ancestor index page. A slide can set `start_paused: true` to wait for the
presenter to start playback. Without a resolved duration, the slide does not
auto-advance.

The script schedules one timer for the current slide and resets it when
Zensical's `document$` observable signals instant navigation. Space or the
top-right playback button pauses the timer, stores the remaining time in module
state, and changes its icon to Play; either control resumes it. The button
switches between Lucide's pause and play icons. The timer clicks the same Next
link as manual keyboard navigation, and stops when there is no next slide.

## How speaker notes work

The `pymdownx.details` Markdown extension renders an author's notes block
as a `<details class="notes">` element. The stylesheet hides notes unless
the slide has the `.slide--notes-visible` class.

Pressing N changes that class, opens or closes the notes, and stores the
choice under `decksical:notes-visible` in local storage. The preference
applies to slides on the same site origin. A customized version can use a
different storage key to keep its notes preference separate.

The module restores the preference when it first loads and subscribes to
Zensical's `document$` observable to restore it after
[instant navigation](https://zensical.org/docs/setup/navigation/#instant-navigation).
Its keyboard listener is attached to `document` and acts only when a `.slide`
is present. Shortcuts ignore editable fields, modifier keys, repeated key
presses, and input composition.

Hidden notes remain in the published HTML. Printing preserves their current
visibility and hides navigation controls.

## Customize the theme source

Change `slides.css` for typography, spacing, image sizes, column proportions,
and the stacking breakpoint. Rules using `body:has(.slide)` hide the inherited
header, sidebars, footer, and other documentation controls on slide pages.
Rules scoped to `.slide` style slide content, including hiding heading
permalink controls. Preserve that scope when adding styles that should apply
only to slides.

Change `slide.html` for page structure and override points. Change the content
partial for column grouping and the navigation partial for deck links.
The slide template extends `base.html` directly, so an override of
`main.html` affects ordinary pages rather than slide pages. A documentation
project can also use `custom_dir` to override theme files locally.

The Decksical theme provides `decksical.html` as a base for local page
overrides. It extends Zensical's base and loads the Catppuccin stylesheet when
the Catppuccin theme is selected. Extend it from any local `main.html` override
so site-specific block changes, such as the announcement, keep that theme
setup:

```jinja
{% extends "decksical.html" %}

{% block announce %}
  Your announcement here.
{% endblock %}
```

Change `slides.mjs` for keyboard shortcuts, automatic playback, and notes
behavior. Layout is handled by the template and CSS. Preserve the restoration
after instant navigation when adding state that must follow the current slide.

Some behavior belongs to the consuming project's configuration. For example,
`font = false` selects system fonts, Markdown extensions determine the HTML
available to the template, and `nav` determines slide grouping and order.
These settings are described in the [authoring instructions].

[authoring instructions]: authoring.md
[Content partial]: https://github.com/corealization/decksical/blob/main/src/decksical/partials/slides/content.html
[Navigation partial]: https://github.com/corealization/decksical/blob/main/src/decksical/partials/slides/navigation.html
[Package configuration]: https://github.com/corealization/decksical/blob/main/pyproject.toml
[Slide JavaScript]: https://github.com/corealization/decksical/blob/main/src/decksical/assets/slides/slides.mjs
[Slide stylesheet]: https://github.com/corealization/decksical/blob/main/src/decksical/assets/slides/slides.css
[Slide template]: https://github.com/corealization/decksical/blob/main/src/decksical/shared/slide.html
[Theme configuration]: https://github.com/corealization/decksical/blob/main/src/decksical/mkdocs_theme.yml
