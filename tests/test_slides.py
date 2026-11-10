# Copyright (c) 2026 Alex Voss
# SPDX-License-Identifier: MIT
# Licensed under the MIT license. See LICENSE in the project root.

"""Theme behavior checks, plus a documentation smoke test."""

import os
import re
import subprocess
import sys
import unittest
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from shutil import copy2, copytree
from tempfile import TemporaryDirectory, mkdtemp
from threading import Thread
from urllib.parse import urlparse

from playwright.sync_api import (
    BrowserContext,
    ConsoleMessage,
    FloatRect,
    Frame,
    Locator,
    Page,
    Request,
    expect,
    sync_playwright,
)
from playwright.sync_api import (
    Error as PlaywrightError,
)

import decksical

ROOT = Path(__file__).resolve().parents[1]
# Cover mobile stacking and a typical desktop layout.
VIEWPORTS = ((375, 812), (1440, 900))
# Exercise desktop columns at a 4:3 size, a short screen, and a large screen.
DESKTOP_VIEWPORTS = ((1024, 768), (1440, 600), (1920, 1080))


def build_site(project: Path) -> None:
    subprocess.run(
        [sys.executable, "-I", "-m", "zensical", "build"], cwd=project, check=True,
    )



class SlideTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        if not Path(decksical.__file__).is_relative_to(sys.prefix):
            raise RuntimeError(
                "Browser tests require an installed wheel. "
                "Run uv build --wheel, then uv pip install --no-deps --reinstall dist/*.whl, "
                "and run the tests with uv run --no-sync."
            )

        cls.configure_test_run()
        cls.create_workspace()
        cls.start_server()
        cls.build_fixture()
        cls.start_browser()

    @classmethod
    def configure_test_run(cls) -> None:
        cls.theme_name = os.environ.get("DECKSICAL_TEST_THEME", "decksical")
        if cls.theme_name not in ("decksical", "decksical-catppuccin"):
            raise ValueError(
                "DECKSICAL_TEST_THEME must be decksical or decksical-catppuccin",
            )

        cls.browser_name = os.environ.get("DECKSICAL_TEST_BROWSER", "chromium")
        if cls.browser_name not in ("chromium", "firefox"):
            raise ValueError("DECKSICAL_TEST_BROWSER must be chromium or firefox")

        cls.variant = os.environ.get("DECKSICAL_TEST_VARIANT", "modern")
        if cls.variant not in ("modern", "classic"):
            raise ValueError("DECKSICAL_TEST_VARIANT must be modern or classic")

    @classmethod
    def create_workspace(cls) -> None:
        cls.resources = ExitStack()
        cls.addClassCleanup(cls.resources.close)
        cls.workdir = Path(cls.resources.enter_context(TemporaryDirectory()))

    @classmethod
    def start_server(cls) -> None:
        # Serve the built test sites in-process instead of managing a `zensical
        # serve` process.
        server = cls.resources.enter_context(ThreadingHTTPServer(
            ("127.0.0.1", 0),
            partial(SimpleHTTPRequestHandler, directory=str(cls.workdir)),
        ))
        cls.server_url = f"http://127.0.0.1:{server.server_port}"
        cls.base_url = f"{cls.server_url}/fixture/site"

        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        cls.resources.callback(thread.join)
        cls.resources.callback(server.shutdown)

    @classmethod
    def build_fixture(cls) -> None:
        fixture = cls.workdir / "fixture"
        copytree(ROOT / "tests" / "fixtures" / "site", fixture)
        cls.configure_fixture(fixture)
        build_site(fixture)

    @classmethod
    def configure_fixture(cls, fixture: Path) -> None:
        config = fixture / "zensical.toml"
        config.write_text(
            config.read_text().replace('name = "decksical"', f'name = "{cls.theme_name}"')
            .replace('[project.theme]', f'[project.theme]\nvariant = "{cls.variant}"', 1)
            .replace('[project]', f'[project]\nsite_url = "{cls.base_url}/"', 1),
            encoding="utf-8",
        )

    @classmethod
    def start_browser(cls) -> None:
        command = [sys.executable, "-m", "playwright", "install"]
        if cls.browser_name == "chromium":
            command.append("--only-shell")

        subprocess.run([*command, cls.browser_name], check=True)

        playwright = cls.resources.enter_context(sync_playwright())
        cls.browser = cls.resources.enter_context(getattr(playwright, cls.browser_name).launch())

    def prepare_documentation(self) -> Path:
        project = self.workdir / "documentation"
        project.mkdir()
        copytree(ROOT / "docs", project / "docs")
        copytree(ROOT / "overrides", project / "overrides")
        copy2(ROOT / "zensical.toml", project / "zensical.toml")
        config = project / "zensical.toml"

        # Omit the upstream repository statistics widget from this offline smoke test.
        settings = re.sub(r'^repo_url = .*\n', '', config.read_text(), flags=re.MULTILINE)
        settings = settings.replace(
            '[project.theme]', f'[project.theme]\nvariant = "{self.variant}"', 1,
        )
        config.write_text(
            re.sub(
                r'^name = "decksical(?:-catppuccin)?"$', f'name = "{self.theme_name}"',
                settings, flags=re.MULTILINE,
            ), encoding="utf-8",
        )
        return project

    @contextmanager
    def page(
        self, path: str | None = None, width: int = 1440, height: int = 900,
        javascript: bool = True,
    ) -> Iterator[Page]:
        with self.browser.new_context(
            viewport={"width": width, "height": height}, java_script_enabled=javascript,
        ) as context:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = context.new_page()
            errors = self.watch_page_errors(page)

            try:
                if path is not None:
                    page.goto(f"{self.base_url}/{path}", wait_until="networkidle")
                yield page
                self.assertEqual(errors, [])
            except Exception as failure:
                self.save_failure_trace(context, width, height, failure)
                raise

    def watch_page_errors(self, page: Page) -> list[str]:
        errors: list[str] = []

        def record_console_error(message: ConsoleMessage) -> None:
            if message.type == "error":
                errors.append(message.text)

        def record_remote_request(request: Request) -> None:
            url = urlparse(request.url)
            is_mathjax = url.hostname == "unpkg.com" and url.path.startswith(
                ("/mathjax@3/", "/mathjax@3.")
            )
            if url.hostname != "127.0.0.1" and not is_mathjax:
                errors.append(f"Remote request: {request.url}")

        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", record_console_error)
        page.on("request", record_remote_request)

        return errors

    def save_failure_trace(
        self, context: BrowserContext, width: int, height: int, failure: Exception,
    ) -> None:
        try:
            artifacts = ROOT / "test-results"
            artifacts.mkdir(exist_ok=True)
            name = f"{self.browser_name}-{self._testMethodName}-{width}-{height}-"
            directory = Path(mkdtemp(prefix=name, dir=artifacts))
            context.tracing.stop(path=str(directory / "trace.zip"))
        except (OSError, PlaywrightError) as error:
            failure.add_note(f"Could not save browser trace: {error}")

    def visible_box(self, locator: Locator) -> FloatRect:
        expect(locator).to_be_visible()
        box = locator.bounding_box()
        if box is None:
            self.fail(f"No layout box for {locator}")
        return box

    def column_boxes(self, page: Page) -> tuple[FloatRect, FloatRect]:
        columns = page.locator(".slide__column")
        expect(columns).to_have_count(2)
        first_column, second_column = columns.all()
        return self.visible_box(first_column), self.visible_box(second_column)

    def assert_shortcut_ignored(self, page: Page, keys: str) -> None:
        navigations: list[str] = []

        def record_navigation(frame: Frame) -> None:
            if frame == page.main_frame:
                navigations.append(frame.url)

        page.on("framenavigated", record_navigation)
        try:
            page.keyboard.press(keys)
            # Observe delayed navigation before accepting an ignored shortcut.
            page.wait_for_timeout(500)
            self.assertEqual(navigations, [], f"Unexpected navigation after {keys}")
        finally:
            page.remove_listener("framenavigated", record_navigation)

    # Normal behavior
    # Right Arrow advances after entering a deck through instant navigation.
    def test_right_arrow_advances_after_entering_deck(self) -> None:
        with self.page("") as page:
            page.get_by_role("link", name="Open fixture deck").click()
            expect(page).to_have_url(f"{self.base_url}/deck/first/")
            expect(page.locator(".slide")).to_be_visible()

            page.keyboard.press("ArrowRight")
            expect(page).to_have_url(f"{self.base_url}/deck/plain/")

    # Left Arrow returns to the previous slide.
    def test_left_arrow_returns_to_previous_slide(self) -> None:
        with self.page("deck/plain/") as page:
            page.keyboard.press("ArrowLeft")
            expect(page).to_have_url(f"{self.base_url}/deck/first/")

    # Speaker notes start hidden, including when JavaScript is disabled.
    def test_notes_hidden_by_default(self) -> None:
        for javascript in (False, True):
            with self.subTest(javascript=javascript), self.page(
                "deck/notes/", javascript=javascript,
            ) as page:
                notes = page.locator("details.notes")
                expect(notes).to_have_count(1)
                expect(notes).to_be_hidden()

    # N shows the notes and their content, then hides them again.
    def test_n_toggles_notes(self) -> None:
        with self.page("deck/notes/") as page:
            notes = page.locator("details.notes")
            page.keyboard.press("n")
            expect(notes.locator("ul")).to_be_visible()

            page.keyboard.press("n")
            expect(notes).to_be_hidden()

    # Both notes preferences survive a visit to a slide without notes.
    def test_notes_preference_survives_navigation(self) -> None:
        for visible in (False, True):
            with self.subTest(visible=visible), self.page("deck/notes/") as page:
                page.keyboard.press("n")
                if not visible:
                    page.keyboard.press("n")

                page.keyboard.press("ArrowLeft")
                expect(page).to_have_url(f"{self.base_url}/deck/columns/")
                expect(page.locator("details.notes")).to_have_count(0)

                page.keyboard.press("ArrowRight")
                expect(page).to_have_url(f"{self.base_url}/deck/notes/")
                notes = page.locator("details.notes")
                expect(notes).to_have_count(1)
                if visible:
                    expect(notes).to_be_visible()
                else:
                    expect(notes).to_be_hidden()

    # Both notes preferences survive a full page reload.
    def test_notes_preference_survives_reload(self) -> None:
        for visible in (False, True):
            with self.subTest(visible=visible), self.page("deck/notes/") as page:
                page.keyboard.press("n")
                if not visible:
                    page.keyboard.press("n")

                page.reload(wait_until="networkidle")
                notes = page.locator("details.notes")
                if visible:
                    expect(notes).to_be_visible()
                else:
                    expect(notes).to_be_hidden()

    # Footer controls appear in previous, overview, and next order.
    def test_footer_navigation_layout(self) -> None:
        for width, height in VIEWPORTS:
            with self.subTest(width=width), self.page(
                "deck/plain/", width, height,
            ) as page:
                nav = page.get_by_role("contentinfo").get_by_role(
                    "navigation", name="Slide navigation", exact=True,
                )
                expect(nav).to_be_visible()
                links = [
                    nav.get_by_role("link", name=name, exact=True)
                    for name in ("Previous slide", "Deck overview", "Next slide")
                ]
                previous_box, overview_box, next_box = [
                    self.visible_box(link) for link in links
                ]
                self.assertLess(previous_box["x"], overview_box["x"])
                self.assertLess(overview_box["x"], next_box["x"])

    # The overview control can be activated with the keyboard.
    def test_overview_link_returns_to_deck_index(self) -> None:
        with self.page("deck/plain/") as page:
            page.get_by_role("link", name="Deck overview", exact=True).focus()
            page.keyboard.press("Enter")
            expect(page).to_have_url(f"{self.base_url}/deck/")

    # Ordinary documentation retains its heading permalink controls.
    def test_documentation_heading_permalinks_visible(self) -> None:
        with self.page("deck/") as page:
            link = page.locator("h1 .headerlink")
            expect(link).to_have_count(1)
            self.assertNotEqual(link.evaluate("el => getComputedStyle(el).display"), "none")

    # Instant navigation updates the header and slide stylesheet together.
    def test_documentation_layout_follows_instant_navigation(self) -> None:
        for width, height in VIEWPORTS:
            with self.subTest(width=width), self.page(
                "deck/plain/", width, height,
            ) as page:
                stylesheet = page.locator(
                    'head link[href$="/assets/slides/slides.css"]',
                )
                expect(stylesheet).to_have_count(1)
                expect(page.locator(".md-header")).to_be_hidden()

                page.get_by_role("link", name="Deck overview", exact=True).click()
                expect(page).to_have_url(f"{self.base_url}/deck/")
                expect(page.locator(".md-header")).to_be_visible()
                expect(stylesheet).to_have_count(0)

                page.get_by_role("link", name="Start the presentation").click()
                expect(page).to_have_url(f"{self.base_url}/deck/first/")
                expect(page.locator(".md-header")).to_be_hidden()
                expect(stylesheet).to_have_count(1)

    # Heading permalink controls are hidden on slides.
    def test_slide_heading_permalinks_hidden(self) -> None:
        with self.page("deck/plain/") as page:
            links = page.locator(".slide .headerlink")
            self.assertGreater(links.count(), 0)
            for link in links.all():
                expect(link).to_be_hidden()

    # Printing includes notes only when they are visible on screen.
    def test_print_preserves_notes_visibility(self) -> None:
        for visible in [False, True]:
            with self.subTest(visible=visible), self.page("deck/notes/") as page:
                notes = page.locator("details.notes")
                if visible:
                    page.keyboard.press("n")
                    expect(notes.locator("ul")).to_be_visible()
                else:
                    expect(notes).to_be_hidden()

                page.emulate_media(media="print")

                if visible:
                    expect(notes.locator("ul")).to_be_visible()
                else:
                    expect(notes).to_be_hidden()

    # Printing hides the slide navigation controls.
    def test_print_hides_navigation(self) -> None:
        with self.page("deck/plain/") as page:
            nav = page.get_by_role("navigation", name="Slide navigation", exact=True)
            expect(nav).to_be_visible()
            page.emulate_media(media="print")
            expect(nav).to_be_hidden()

    # Full-size images fit within 75dvh and the space left for content and
    # navigation.
    def test_full_size_image_layout(self) -> None:
        for width, height in (*VIEWPORTS, (1920, 600)):
            with self.subTest(width=width), self.page(
                "deck/image/", width, height,
            ) as page:
                image = page.locator("img.slide-image")
                expect(image).to_be_visible()
                self.assertTrue(image.evaluate("el => el.complete && el.naturalWidth > 0"))
                content_box = self.visible_box(page.locator(".slide__content"))
                image_box = self.visible_box(image)
                self.assertAlmostEqual(image_box["width"], content_box["width"], delta=1)
                padding_top = float(
                    page.locator(".md-content__inner").evaluate(
                        "el => parseFloat(getComputedStyle(el).paddingTop)",
                    )
                )
                footer_box = self.visible_box(page.locator(".slide__footer"))
                available_height = height - padding_top - footer_box["height"]
                self.assertAlmostEqual(
                    image_box["height"], min(height * 0.75, available_height), delta=1,
                )
                self.assertEqual(
                    image.evaluate("el => getComputedStyle(el).objectFit"), "contain",
                )

                page.emulate_media(media="print")
                print_box = self.visible_box(image)
                aspect_ratio = image.evaluate("el => el.naturalHeight / el.naturalWidth")
                self.assertAlmostEqual(
                    print_box["height"], print_box["width"] * aspect_ratio, delta=2,
                )

    # Images fill either of two equal-width columns, with a gutter between them.
    def test_column_image_fills_half_width(self) -> None:
        for width, height in DESKTOP_VIEWPORTS:
            for image_side in ("left", "right"):
                with (
                    self.subTest(width=width, height=height, image_side=image_side),
                    self.page(f"deck/image-{image_side}/", width, height) as page,
                ):
                    first_box, second_box = self.column_boxes(page)
                    image = page.locator(".slide__column img")
                    image_box = self.visible_box(image)
                    self.assertAlmostEqual(first_box["width"], second_box["width"], delta=1)
                    self.assertGreater(second_box["x"], first_box["x"] + first_box["width"])
                    self.assertAlmostEqual(image_box["width"], first_box["width"], delta=1)

    # Text stays beside either image column, with notes hidden or visible.
    def test_column_text_stays_beside_image(self) -> None:
        for width, height in DESKTOP_VIEWPORTS:
            for image_side in ("left", "right"):
                with (
                    self.subTest(width=width, height=height, image_side=image_side),
                    self.page(f"deck/image-{image_side}/", width, height) as page,
                ):
                    text = page.locator(".slide__column").filter(has=page.locator("strong"))
                    image = page.locator(".slide__column img")
                    for visible in (False, True):
                        if visible:
                            page.keyboard.press("n")
                            expect(page.locator("details.notes")).to_be_visible()
                        else:
                            expect(page.locator("details.notes")).to_be_hidden()
                        text_box = self.visible_box(text)
                        image_box = self.visible_box(image)
                        if image_side == "left":
                            self.assertGreaterEqual(
                                text_box["x"], image_box["x"] + image_box["width"] - 1,
                            )
                        else:
                            self.assertLessEqual(
                                text_box["x"] + text_box["width"], image_box["x"] + 1,
                            )

                        self.assertTrue(text.evaluate("el => el.scrollWidth <= el.clientWidth"))

    # Two-column notes appear below both columns instead of inside either column.
    def test_column_notes_follow_both_columns(self) -> None:
        for width, height in VIEWPORTS:
            for image_side in ("left", "right"):
                with self.subTest(width=width, image_side=image_side), self.page(
                    f"deck/image-{image_side}/", width, height,
                ) as page:
                    page.keyboard.press("n")
                    notes = page.locator("details.notes")
                    expect(notes).to_be_visible()
                    notes_box = self.visible_box(notes)
                    columns = page.locator(".slide__column")
                    expect(columns).to_have_count(2)
                    for column in columns.all():
                        column_box = self.visible_box(column)
                        self.assertGreaterEqual(
                            notes_box["y"], column_box["y"] + column_box["height"],
                        )
                    content_box = self.visible_box(page.locator(".slide__content"))
                    self.assertAlmostEqual(notes_box["width"], content_box["width"], delta=1)

    # Image and text columns stack in source order on narrow screens.
    def test_image_columns_stack_in_source_order(self) -> None:
        for image_side in ("left", "right"):
            with (
                self.subTest(image_side=image_side),
                self.page(f"deck/image-{image_side}/", 375, 812) as page,
            ):
                first_box, second_box = self.column_boxes(page)
                self.assertGreaterEqual(second_box["y"], first_box["y"] + first_box["height"])
                self.assertAlmostEqual(first_box["width"], second_box["width"], delta=1)
                self.assertTrue(
                    page.evaluate("document.documentElement.scrollWidth <= innerWidth"),
                )

    # Column splitting preserves Markdown content on the intended side.
    def test_column_markdown_content_preserved(self) -> None:
        with self.page("deck/columns/") as page:
            columns = page.locator(".slide__column")
            expect(columns).to_have_count(2)
            left, right = columns.all()
            expect(left.get_by_role("heading", name="Left heading", exact=True)).to_be_visible()
            expect(left.locator("li")).to_have_text(["First bullet.", "Second bullet."])
            expect(left.locator("strong")).to_have_text("First")
            expect(right.get_by_role("heading", name="Right heading", exact=True)).to_be_visible()
            code = right.locator("pre code")
            expect(code).to_be_visible()
            expect(code).to_have_text('[project.theme]\nname = "decksical"\n')

    # The real documentation renders an ordinary page and a representative image slide.
    def test_documentation_smoke(self) -> None:
        project = self.prepare_documentation()
        build_site(project)

        with self.page() as page:
            base_url = f"{self.server_url}/documentation/site"
            page.goto(base_url, wait_until="networkidle")
            expect(page.locator(".md-header")).to_be_visible()

            credits = page.locator(".md-copyright")
            expect(credits.get_by_role("link", name="Zensical", exact=True)).to_be_visible()
            expect(
                credits.get_by_role("link", name="Decksical", exact=True),
            ).to_be_visible()
            catppuccin_credit = credits.get_by_role(
                "link", name="Catppuccin", exact=True,
            )
            if self.theme_name == "decksical-catppuccin":
                expect(catppuccin_credit).to_be_visible()
            else:
                expect(catppuccin_credit).to_have_count(0)

            page.goto(f"{base_url}/example/image/", wait_until="networkidle")
            expect(page.locator(".slide__content")).to_be_visible()
            expect(page.locator(".md-header")).to_be_hidden()
            if self.theme_name == "decksical-catppuccin":
                expect(page.locator('head link[href$="/catppuccin.css"]')).to_have_count(1)

            image = page.locator("img.slide-image")
            expect(image).to_be_visible()
            self.assertTrue(image.evaluate("el => el.complete && el.naturalWidth > 0"))

            page.goto(f"{base_url}/example/maths/", wait_until="networkidle")
            formula = page.locator(
                ".slide__content > .arithmatex > mjx-container[display='true']",
            )
            expect(formula).to_be_visible()

            note_text = page.locator(".slide .admonition > p:not(.admonition-title)")
            for width, height in ((375, 812), (1440, 900)):
                page.set_viewport_size({"width": width, "height": height})
                note_box = self.visible_box(note_text)
                self.assertLessEqual(note_box["y"] + note_box["height"], height)

    # Exceptional circumstances
    # The first slide has no previous link and ignores Left Arrow.
    def test_first_slide_stops_backward_navigation(self) -> None:
        with self.page("deck/first/") as page:
            expect(page).to_have_url(f"{self.base_url}/deck/first/")
            previous = page.get_by_role("link", name="Previous slide", exact=True)
            expect(previous).to_have_count(0)
            self.assert_shortcut_ignored(page, "ArrowLeft")
            expect(page).to_have_url(f"{self.base_url}/deck/first/")

    # The last slide has no next link and ignores Right Arrow.
    def test_last_slide_stops_forward_navigation(self) -> None:
        with self.page("deck/notes/") as page:
            expect(page).to_have_url(f"{self.base_url}/deck/notes/")
            expect(page.get_by_role("link", name="Next slide", exact=True)).to_have_count(0)
            self.assert_shortcut_ignored(page, "ArrowRight")
            expect(page).to_have_url(f"{self.base_url}/deck/notes/")

    # Storage failures leave shortcuts, notes, and focus handling usable.
    def test_storage_errors_preserve_slide_controls(self) -> None:
        for method, error_name in (
            ("getItem", "SecurityError"),
            ("setItem", "SecurityError"),
            ("setItem", "QuotaExceededError"),
        ):
            with self.subTest(method=method, error=error_name), self.page() as page:
                page.add_init_script(f"""
                    const original = Storage.prototype.{method};
                    Storage.prototype.{method} = function(key, ...args) {{
                        if (key === 'decksical:notes-visible') {{
                            throw new DOMException('Storage unavailable', '{error_name}');
                        }}
                        return original.call(this, key, ...args);
                    }};
                """)
                page.goto(f"{self.base_url}/deck/notes/", wait_until="networkidle")
                notes = page.locator("details.notes")
                expect(notes).to_be_hidden()

                page.keyboard.press("n")
                expect(notes.locator("ul")).to_be_visible()

                page.evaluate("window.storageTestDocument = true")
                page.keyboard.press("ArrowLeft")
                expect(page).to_have_url(f"{self.base_url}/deck/columns/")
                expect(notes).to_have_count(0)
                self.assertTrue(page.evaluate("window.storageTestDocument === true"))

                page.keyboard.press("ArrowRight")
                expect(page).to_have_url(f"{self.base_url}/deck/notes/")
                expect(notes.locator("ul")).to_be_visible()

                notes.locator("summary").focus()
                page.keyboard.press("n")
                expect(notes).to_be_hidden()
                expect(page.locator(".slide")).to_be_focused()

    # Modified shortcut keys do not navigate or reveal notes.
    def test_shortcuts_ignore_modifiers(self) -> None:
        for keys in ("Control+n", "Alt+ArrowLeft", "Shift+ArrowLeft"):
            with self.subTest(keys=keys), self.page("deck/notes/") as page:
                expect(page).to_have_url(f"{self.base_url}/deck/notes/")
                self.assert_shortcut_ignored(page, keys)
                expect(page.locator("details.notes")).to_be_hidden()
                expect(page).to_have_url(f"{self.base_url}/deck/notes/")

    # Shortcut keys leave typing in inputs, textareas, and editable content alone.
    def test_shortcuts_ignore_typing(self) -> None:
        for tag in ("input", "textarea", "div"):
            with self.subTest(tag=tag), self.page("deck/notes/") as page:
                expect(page).to_have_url(f"{self.base_url}/deck/notes/")
                page.evaluate("""tag => {
                    const field = document.createElement(tag);
                    field.id = 'typing-test';
                    if (tag === 'div') field.contentEditable = 'true';
                    document.querySelector('.slide').append(field);
                    field.focus();
                }""", tag)
                self.assert_shortcut_ignored(page, "n")
                expect(page.locator("details.notes")).to_be_hidden()
                self.assert_shortcut_ignored(page, "ArrowLeft")
                expect(page.locator("details.notes")).to_be_hidden()
                expect(page).to_have_url(f"{self.base_url}/deck/notes/")

    # Long content and revealed notes scroll without horizontal overflow.
    def test_long_content_and_notes_scroll_without_overflow(self) -> None:
        for width, height in VIEWPORTS:
            with self.subTest(width=width), self.page(
                "overflow/long/", width, height,
            ) as page:
                hidden_height = page.evaluate("document.documentElement.scrollHeight")
                self.assertGreater(hidden_height, height)

                page.keyboard.press("n")
                expect(page.locator("details.notes")).to_be_visible()
                shown_height = page.evaluate("document.documentElement.scrollHeight")
                self.assertGreater(shown_height, hidden_height)
                self.assertTrue(
                    page.evaluate("document.documentElement.scrollWidth <= innerWidth"),
                )

    # Footer navigation remains reachable after scrolling past long content and notes.
    def test_footer_reachable_after_overflow(self) -> None:
        for width, height in VIEWPORTS:
            with self.subTest(width=width), self.page(
                "overflow/long/", width, height,
            ) as page:
                page.keyboard.press("n")
                expect(page.locator("details.notes")).to_be_visible()
                page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                overview = page.get_by_role("link", name="Deck overview", exact=True)
                expect(overview).to_be_visible()
                expect(overview).to_be_in_viewport(ratio=1)

    # Text longer than an image remains in its original column below the image.
    def test_long_text_stays_in_its_column(self) -> None:
        for image_side in ("left", "right"):
            with (
                self.subTest(image_side=image_side),
                self.page(f"deck/image-{image_side}/") as page,
            ):
                text = page.locator("#long-column-text")
                text_box = self.visible_box(text)
                column_box = self.visible_box(text.locator(".."))
                image_box = self.visible_box(page.locator(".slide__column img"))

                self.assertGreater(
                    text_box["y"] + text_box["height"], image_box["y"] + image_box["height"],
                )
                self.assertGreaterEqual(text_box["x"], column_box["x"] - 1)
                self.assertLessEqual(
                    text_box["x"] + text_box["width"], column_box["x"] + column_box["width"] + 1,
                )

    # Column markers create side-by-side or stacked text without JavaScript.
    def test_column_layout_without_javascript(self) -> None:
        for width, height in VIEWPORTS:
            with self.subTest(width=width), self.page(
                "deck/columns/", width, height, javascript=False,
            ) as page:
                first_box, second_box = self.column_boxes(page)
                self.assertAlmostEqual(first_box["width"], second_box["width"], delta=1)
                if width >= 1440:
                    self.assertGreater(second_box["x"], first_box["x"] + first_box["width"])
                else:
                    self.assertGreater(second_box["y"], first_box["y"] + first_box["height"])
                self.assertTrue(
                    page.evaluate("document.documentElement.scrollWidth <= innerWidth"),
                )

    # Neighboring navigation sections do not link their decks together.
    def test_adjacent_decks_have_separate_navigation(self) -> None:
        for path, link_name, key in (
            ("other/first/", "Previous slide", "ArrowLeft"),
            ("other/second/", "Next slide", "ArrowRight"),
        ):
            with self.subTest(path=path), self.page(path) as page:
                expect(page).to_have_url(f"{self.base_url}/{path}")
                expect(page.get_by_role("link", name=link_name, exact=True)).to_have_count(0)
                self.assert_shortcut_ignored(page, key)
                expect(page).to_have_url(f"{self.base_url}/{path}")

    # A deck without an index page has no overview control.
    def test_overview_omitted_without_index(self) -> None:
        with self.page("other/first/") as page:
            expect(page.get_by_role("link", name="Deck overview", exact=True)).to_have_count(0)


if __name__ == "__main__":
    unittest.main()
