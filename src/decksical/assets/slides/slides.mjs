/*
Copyright (c) 2026 Alex Voss
SPDX-License-Identifier: MIT
Licensed under the MIT license. See LICENSE in the project root.
*/

const NOTES_KEY = "decksical:notes-visible";
const AUTOPLAY_PAUSED_KEY = "decksical:autoplay-paused";

const state = {
  notesVisible: withLocalStorage((storage) => storage.getItem(NOTES_KEY)) === "true",
};

const playback = {
  timer: null,
  deadline: 0,
  remaining: 0,
  duration: 0,
  active: false,
  paused: withLocalStorage((storage) => storage.getItem(AUTOPLAY_PAUSED_KEY)) === "true",
};

/**
 * Run a callback with localStorage, returning undefined if storage fails.
 *
 * Accessing localStorage or executing the callback can throw DOMExceptions
 * expected under normal circumstances: SecurityError when privacy settings or
 * origin restrictions deny access, and QuotaExceededError when a write exceeds
 * the storage allowance. We ignore these but rethrow unexpected errors.
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage#exceptions
 * @see https://developer.mozilla.org/en-US/docs/Web/API/Storage/setItem#exceptions
 */
function withLocalStorage(operation) {
  try {
    return operation(localStorage);
  } catch (error) {
    if (!(error instanceof DOMException &&
        ["SecurityError", "QuotaExceededError"].includes(error.name))) throw error;
  }
}

/**
 * Keep the CSS visibility state and native details controls in sync.
 */
function setNotesVisibility(slide, visible) {
  slide.classList.toggle("slide--notes-visible", visible);
  for (const note of slide.querySelectorAll("details.notes")) note.open = visible;
}

/**
 * Apply the saved preference to the current slide; notes start hidden.
 */
function applyNotesPreference() {
  const slide = document.querySelector(".slide");

  if (slide) setNotesVisibility(slide, state.notesVisible);
}

/**
 * Toggle notes, save the preference, and move focus out of hidden notes.
 */
function toggleNotes(slide) {
  const notes = slide.querySelectorAll("details.notes");
  if (!notes.length) return;

  const visible = !slide.classList.contains("slide--notes-visible");
  setNotesVisibility(slide, visible);

  state.notesVisible = visible;
  withLocalStorage((storage) => storage.setItem(NOTES_KEY, String(visible)));

  if (!visible && [...notes].some((note) => note.contains(document.activeElement))) {
    slide.tabIndex = -1;
    slide.focus({ preventScroll: true });
  }
}

/**
 * Follow the requested footer link if a destination exists.
 */
function navigateSlide(direction) {
  const link = document.querySelector(`.slide__navigation a[rel="${direction}"]`);
  if (!link) return;

  link.click();
}

/**
 * Schedule the next slide using its configured duration.
 */
function scheduleNextSlide(delay) {
  playback.remaining = delay;
  playback.deadline = performance.now() + delay;
  playback.timer = window.setTimeout(() => {
    playback.timer = null;
    const next = document.querySelector('.slide__navigation a[rel="next"]');
    const wrap = document.querySelector(".slide__autoplay-wrap");
    if (next) next.click();
    else if (wrap) wrap.click();
  }, delay);
}

/**
 * Show the playback control and label the action it will perform.
 */
function updatePlaybackControl(slide) {
  const control = slide.querySelector(".slide__playback-toggle");
  const pauseIcon = control?.querySelector('[data-playback-icon="pause"]');
  const playIcon = control?.querySelector('[data-playback-icon="play"]');
  if (!control || !pauseIcon || !playIcon) return;

  const label = playback.paused ? "Resume automatic playback" : "Pause automatic playback";
  control.hidden = !playback.active;
  control.setAttribute("aria-label", label);
  control.title = label;
  pauseIcon.hidden = playback.paused;
  playIcon.hidden = !playback.paused;
}

/**
 * Start the timer for the current slide, or clear it when playback is disabled.
 */
function initializePlayback() {
  window.clearTimeout(playback.timer);
  playback.timer = null;

  const slide = document.querySelector(".slide");
  if (!slide) {
    playback.active = false;
    playback.remaining = 0;
    return;
  }

  const next = document.querySelector('.slide__navigation a[rel="next"]');
  const wrap = slide.querySelector(".slide__autoplay-wrap");
  const duration = Number(slide.dataset.autoplayDuration) * 1000;
  if ((!next && !wrap) || !Number.isFinite(duration) || duration <= 0) {
    playback.active = false;
    playback.remaining = 0;
    updatePlaybackControl(slide);
    return;
  }

  playback.active = true;
  playback.duration = duration;
  playback.remaining = duration;
  if (slide.dataset.autoplayStartPaused === "true") playback.paused = true;
  updatePlaybackControl(slide);

  if (!playback.paused) scheduleNextSlide(duration);
}

/**
 * Pause or resume slide timing and update the playback control.
 */
function togglePlayback() {
  if (!playback.active) return false;

  const slide = document.querySelector(".slide");
  if (!slide) return false;

  playback.paused = !playback.paused;
  withLocalStorage((storage) => {
    storage.setItem(AUTOPLAY_PAUSED_KEY, String(playback.paused));
  });
  updatePlaybackControl(slide);

  if (playback.paused) {
    window.clearTimeout(playback.timer);
    playback.timer = null;
    playback.remaining = Math.max(0, playback.deadline - performance.now());
  } else {
    scheduleNextSlide(playback.remaining);
  }

  return true;
}

/**
 * Check if the event target is (part of) an interactive element that 
 * we should pass the event through to.
 */
function isTypingOrMediaTarget(target) {
  return target instanceof Element && target.closest(`
    input,
    textarea,
    select,
    [contenteditable]:not([contenteditable="false"]),
    [role="textbox"],
    audio,
    video
  `) !== null;
}

/**
 * Let Space keep its usual activation behavior on links and buttons.
 */
function isSpaceControlTarget(target) {
  return target instanceof Element && target.closest(`
    a[href],
    button,
    [role="button"]
  `) !== null;
}

/**
 * Code run on page load - "main"
 */

// Restore notes on the first load
applyNotesPreference();
initializePlayback();

// Restore preferences and reset the timer after Zensical's instant navigation.
document$.subscribe(() => {
  applyNotesPreference();
  initializePlayback();
});

document.addEventListener("click", (event) => {
  if (!(event.target instanceof Element)) return;
  if (!event.target.closest(".slide__playback-toggle")) return;

  togglePlayback();
});

// Handle keyboard shortcuts for slide navigation, playback, and speaker notes.
// Listen on document so shortcuts keep working after instant navigation 
// replaces the slide.
document.addEventListener("keydown", (event) => {
  const slide = document.querySelector(".slide");
  const handledKeys = ["ArrowLeft", "ArrowRight", "Escape", "n", " "];
  if (!slide || !handledKeys.includes(event.key)) return;

  // Leave modified keys, typing, and media controls to their usual handlers.
  if (event.defaultPrevented || event.repeat || event.isComposing ||
      event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  if (isTypingOrMediaTarget(event.target)) return;
  if (event.key === " " && isSpaceControlTarget(event.target)) return;

  if (event.key === " ") {
    if (!togglePlayback()) return;
  } else if (event.key === "n") {
    toggleNotes(slide);
  } else if (event.key === "Escape") {
    const overview = document.querySelector(".slide__navigation .slide__overview");
    if (!overview) return;
    overview.click();
  } else if (event.key === "ArrowLeft") {
    navigateSlide("prev");
  } else if (event.key === "ArrowRight") {
    navigateSlide("next");
  }

  event.stopPropagation();
  // Let Escape keep its browser default, including exiting fullscreen mode.
  if (event.key !== "Escape") event.preventDefault();
});
