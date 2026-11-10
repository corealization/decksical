---
icon: lucide/gallery-horizontal-end
decksical:
  autoplay:
    duration: 5
    wrap: true
---

# Example slides

- [Welcome](title.md)
- [Presentations with Zensical](welcome.md)
- [Make your own deck](closing.md)
- [Author a slide](content.md)
- [Code blocks](code.md)
- [Mermaid diagrams](diagrams.md)
- [Full-size image](image.md)
- [Image on the left](image-text.md)
- [Image on the right](image-text-right.md)
- [Two columns of Markdown](columns.md)
- [Use maths](maths.md)
- [Speaker notes](notes.md)

This deck advances automatically: the welcome slide stays for 15 seconds, and
the others stay for 5. After the final slide, it returns to Welcome. Press
**Space** or use the top-right button to pause or resume.

## Edit the presentation

Edit the Markdown files in `docs/example/` with your text editor.
Each file contains one slide. The speaker notes slide also shows an optional
notes block. To change slide order, update the Example deck section under `nav` in `zensical.toml`.

Run `zensical serve` to preview your changes. Use the up-arrow button on a slide
to return to this deck overview.
