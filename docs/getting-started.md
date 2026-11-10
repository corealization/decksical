---
icon: lucide/rocket
---

# Get started

Create a small deck in an existing Zensical project. First,
[install and configure the theme](installation.md).

## Write your first slide

Create `docs/slides/first.md`:

```
---
template: slide.html
---

# Authoring process

- Write in **Markdown**.
- Add slides to navigation
- Add speaker notes when you need them.
```

The front matter selects the slide template. The rest is ordinary Markdown.

## Add a second slide

Create `docs/slides/next.md`:

```
---
template: slide.html
---

# What comes next?

- Pick one thing you want your audience to remember.
- Stick to one idea per slide.
```

## Put the deck in your navigation

In `zensical.toml`, add a section for the deck to your existing `nav` list:

```toml
[project]
nav = [
  { "My deck" = [
    { "First slide" = "slides/first.md" },
    { "Next slide" = "slides/next.md" },
  ] },
]
```

Each deck gets its own section. The order of the entries determines the
presentation order.

## Preview the deck

From your project directory, run:

```sh
zensical serve
```

For a uv project:

```sh
uv run zensical serve
```

Open **My deck → First slide** in the browser. Press **Right arrow** to go
forward, **Left arrow** to go back, and hit **Escape** or click the **up-arrow
button** to return to the deck overview.

Explore the [authoring reference](authoring.md) for layouts and notes, or
read [Presenting](presenting.md) before giving your talk.
