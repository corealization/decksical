---
icon: lucide/square-pen
---

# Authoring

Reference for slide files, deck structure, layouts, and speaker notes. For a
complete first deck, follow [Get started](getting-started.md). For keyboard
controls and delivery, see [Presenting](presenting.md).

## Write a slide

Give each deck its own section under `nav` in `zensical.toml`. List the
slide files directly in that section, in presentation order.

Create one Markdown file per slide. Add this front matter:

```yaml
---
template: slide.html
---
```

Previous and Next links stay within the section and stop at ordinary
documentation pages or nested sections. A nested section defines a separate deck.

## Title slide

Decksical includes a centered layout for title slides. Add a logo with the
`.decksical-title-logo` class to activate it. The layout centers the logo and
heading vertically and horizontally. Add an optional tagline with the
`.decksical-title-tagline` class:

```
![Project logo](images/logo.svg){ .decksical-title-logo }

# Project name

A short tagline
{ .decksical-title-tagline }
```

Use a logo to activate the layout and add a heading for the title. The tagline
is optional. The example uses [attribute lists](#arrange-images-and-text) to
add the classes.

## Add code

Use backticks for short code, such as `#!yaml template: slide.html` or a
function name. Use a fenced block for longer examples and add the language name
after the opening backticks to enable syntax highlighting:

````
```python
def greet(name):
    return f"Hello, {name}!"
```
````

Decksical uses Zensical's code colors, so highlighted code follows the active
theme variant. For configuration and inline highlighting syntax, see
Zensical's [code blocks guide](https://zensical.org/docs/authoring/code-blocks/).
For example, `#!yaml template: slide.html` highlights the slide template
setting as YAML. Plain backticks, such as `slide.html`, need no language marker.

## Add diagrams

Write Mermaid diagrams in fenced code blocks. Zensical renders them using the
active theme colors. The example project already enables Mermaid; see
Zensical's [diagrams guide](https://zensical.org/docs/authoring/diagrams/) for
configuration and supported diagram types.

[View the Mermaid example](example/diagrams.md).

## Set automatic slide timing

Set a default duration in seconds in the deck's `index.md` front matter. Slides
advance automatically after that duration; the final slide stays open.

```yaml
---
decksical:
  autoplay:
    duration: 5
---
```

Override the duration on an individual slide by adding the same setting to its
front matter:

```yaml
---
template: slide.html
decksical:
  autoplay:
    duration: 15
---
```

The example deck uses a 5-second default and gives its opening slide 15 seconds.
Use the top-right playback button or press **Space** to pause or resume. The
button shows a play icon while paused. Without a duration setting, slides use
manual navigation.

By default, automatic playback stops on the last slide. To make it return to
the first slide and continue, set `wrap` in the deck overview's front matter:

```yaml
decksical:
  autoplay:
    duration: 5
    wrap: true
```

This setting affects automatic playback only; the Next arrow still stops at the
last slide.

## Arrange images and text

Enable these Markdown extensions if your project does not already use them:

```toml
[project.markdown_extensions]
attr_list = {}
```

### Full-size image

Add the `slide-image` class to a Markdown image:

```
![Description of the image](images/diagram.svg){ .slide-image }
```

The image uses the slide's full content width and a height of 75% of the
window. It keeps its proportions and shows the whole image without cropping.
Leave out the slide heading for an image-only slide. Speaker notes go after
the image. Press **N** to show or hide them.

[View the full-size image example](example/image.md).

### Two columns

To create a two-column layout, add a column-break marker between the content for the left and right columns:

```
![Description of the image](images/diagram.svg)

<!-- column-break -->

## Explain the image

- Write your text in **Markdown**.
- Include paragraphs, lists, or links.
```

Content before the marker stays in the left column. Content after it goes to
the right column. To put an image on the right, place it after the marker.
Images fill the width of their column and keep their proportions.

Either column can contain headings, text, lists, code, or images. Use one `<!-- column-break -->` marker per slide, on its own line with blank lines before and after it. An initial slide heading spans both columns. Speaker notes at the end also span both columns. On narrow screens, content stacks in source order.

[View the image-left example](example/image-text.md) or
[the image-right example](example/image-text-right.md), or
[the text-only example](example/columns.md).

## Add speaker notes

Enable the details extension if your project does not already use it:

```toml
[project.markdown_extensions]
pymdownx.details = {}
```

Place a closed notes block after the slide content:

```
??? notes "Speaker notes"

    Write your notes here. Indent all note content by four spaces.

    - Markdown lists work here.
    - Links and emphasis work too.
```

Notes are hidden by default. Omit the block on slides that do not need notes.

See [Presenting: speaker notes](presenting.md#speaker-notes) for how to reveal
notes, how their visibility is remembered, and what your audience can see.

## Add a deck overview

The up arrow returns to the nearest index page above the slide in the site
navigation. Add an `index.md` page to the deck's navigation section to provide
an overview. The arrow is absent when no ancestor section has an index page.
