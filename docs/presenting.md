---
icon: lucide/presentation
---

# Presenting

## Open your deck

Open the first slide from your site's navigation or share its URL directly.
A slide hides the documentation header and sidebars so the content has the
available space. Ordinary documentation pages keep their usual layout.

For a local presentation, start your project's preview server with
`zensical serve`. A published site can be presented directly in the browser.
If you are previewing this repository itself, follow the
[development preview instructions](https://github.com/corealization/decksical#preview-this-repositorys-documentation).

## Move between slides

| Control | Action |
| --- | --- |
| **Right arrow** or the next button | Next slide |
| **Left arrow** or the previous button | Previous slide |
| **Escape** or the up-arrow button | Deck overview, when configured |
| Top-right playback button or **Space** | Pause or resume automatic playback, when enabled |
| **N** | Show or hide speaker notes |

Previous and Next stay within the deck's navigation section. They stop at
the first and last slides; they do not wrap around or jump into another deck.
Escape or the up-arrow button returns to the closest deck overview. Add an
`index.md` page to your deck section to create one. See
[Add a deck overview](authoring.md#add-a-deck-overview) for details.

To hide the navigation arrows until the pointer moves over their area, enable
this project option in `zensical.toml`:

```toml
[project.extra.decksical.navigation]
hide_until_hover = true
```

The arrows also appear when reached by keyboard focus. They stay visible on
touch devices.

Shortcuts leave inputs, editable content, and media controls alone. They also
ignore keys pressed with Shift, Ctrl, Alt, or Command. Click outside those
controls before using the slide shortcuts.

When automatic playback is paused, the top-right button changes to a play icon.
See [Authoring: automatic slide timing](authoring.md#set-automatic-slide-timing)
for the deck-wide default and per-slide overrides.
Your browser remembers whether playback is paused, including after a reload. If
browser storage is unavailable, playback still works, but the choice may not
survive a reload.

## Speaker notes

Notes are hidden by default. Press **N** on a slide with notes to reveal them beneath
the content, then press it again to hide them.

Your browser remembers the preference across slides and page reloads. If
browser storage is blocked or full, the controls still work, but the preference
may not survive a reload. See [Authoring: add speaker notes](authoring.md#add-speaker-notes)
for the Markdown syntax and extension setup.

Notes appear in the same browser view as the slide. If you share or project
that view, your audience can see notes when you reveal them. There is no
separate presenter view. Notes also remain in the published HTML, so they
should not contain confidential information.

## Fullscreen view

Use your browser's full-screen mode to hide its toolbar. Slide text and spacing
adapt to the viewport; two-column layouts stack on narrow screens.
Long slides scroll instead of shrinking their text to fit.

!!! tip "Hide Firefox's tabs and toolbar on macOS"

    If Firefox keeps its tabs and address bar visible in fullscreen, right-click
    an empty area of the tab bar or toolbar and enable **Hide Toolbars**. Move
    the pointer into the slide to let the controls disappear.

    If that option is unavailable, open `about:config`, search for
    `browser.fullscreen.autohide`, and set it to `true`. Click the slide to
    move focus out of the address bar.

## Print a slide

Use the browser's print command on the slide you want to print. Speaker notes
follow their current visibility: press **N** to show them before printing to
include them, or hide them to print just the slide content. Navigation controls
are omitted.

For the best print results, select the Zensical light palette before printing.
Dark palettes may produce low-contrast text or dark code block backgrounds.

Printing includes the current page; it does not collect the entire deck into
one document.
