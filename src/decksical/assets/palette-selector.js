(() => {
  const initializePalettePicker = () => {
    const palette = document.querySelector('[data-md-component="palette"]');
    if (!palette || palette.classList.contains("decksical-palette-enhanced")) {
      return;
    }

    const radios = Array.from(
      palette.querySelectorAll('input.md-option[type="radio"][name="__palette"]'),
    ).filter((radio) => radio.id);
    if (radios.length < 2) {
      return;
    }

    const labels = new Map(
      Array.from(palette.querySelectorAll("label[for]"), (label) => [
        label.htmlFor,
        label.title
          .replace(/^Switch to\s+/i, "")
          .replace(/\s+palette$/i, "")
          .trim(),
      ]),
    );
    const picker = document.createElement("select");
    picker.className = "decksical-palette-picker";
    picker.setAttribute("aria-label", "Select color palette");

    const orderedRadios = [...radios].sort((a, b) => {
      const rank = (radio) => {
        const scheme = radio.dataset.mdColorScheme || "";
        if (scheme.startsWith("catppuccin-")) return 1;
        if (scheme === "tokyo-night") return 2;
        return 0;
      };
      return rank(a) - rank(b);
    });

    for (const radio of orderedRadios) {
      const option = document.createElement("option");
      option.value = radio.id;
      option.textContent =
        labels.get(radio.id) ||
        (radio.dataset.mdColorScheme || radio.id).replaceAll("-", " ");
      picker.append(option);
    }

    const activeScheme = document.body.dataset.mdColorScheme;
    const selected =
      radios.find((radio) => radio.checked) ||
      radios.find((radio) => radio.dataset.mdColorScheme === activeScheme) ||
      radios[0];
    picker.value = selected.id;
    picker.addEventListener("change", () => {
      radios.find((radio) => radio.id === picker.value)?.click();
    });
    palette.addEventListener("change", (event) => {
      if (radios.includes(event.target)) {
        picker.value = event.target.id;
      }
    });

    palette.append(picker);
    palette.classList.add("decksical-palette-enhanced");
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializePalettePicker, {
      once: true,
    });
  } else {
    initializePalettePicker();
  }
})();
