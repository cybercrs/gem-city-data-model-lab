"""Actual Wasm lesson walkthrough; all external browser traffic is blocked."""

import argparse
import json
import threading
import time
import traceback
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from browser.config import PACKAGE
from browser.walkthrough import lesson

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results", type=Path, default=ROOT / "browser/test-results/final"
    )
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    dist = ROOT / "browser/dist"
    results = {
        "checks": [],
        "console_errors": [],
        "page_errors": [],
        "external_requests": [],
        "http_errors": [],
        "not_run": [
            "Hosted HTTPS UI (cloud proxy restriction)",
            "Physical classroom device/browser matrix",
            "Classroom simultaneous cold-start/capacity trial",
        ],
    }

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.startswith("/lesson/"):
                self.path = self.path[len("/lesson") :]
            if self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if self.path == "/app.json":
                config = json.loads((dist / "app.json").read_text())
                config["files"]["browser/app.py"] += (
                    """\nimport sys,json,pyodide\nprint('BROWSER_VERSIONS='+json.dumps({'python':sys.version.split()[0],'streamlit':st.__version__,'pyodide':pyodide.__version__}))\nprint('BROWSER_STATE='+json.dumps({k:v for k,v in st.session_state.to_dict().items() if (k.startswith(('dm_','si_','bbc_')) and not any(w in k for w in ['scroll','restore']) and k not in ['bbc_review_statement','bbc_main_start_over']) or k in ['stage','question_history','evidence_history','pressure_history','conclusion_history','budget_history','investigation_budget','browser_form_drafts']}))\n"""
                )
                payload = json.dumps(config).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            super().do_GET()

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(Handler, directory=str(dist))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            proxy={"server": "http://127.0.0.1:9", "bypass": "127.0.0.1,localhost"},
        )
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        states = {}

        def watch(page):
            def console(m):
                if m.text.startswith("BROWSER_STATE="):
                    states[page] = json.loads(m.text.split("=", 1)[1])
                if m.text.startswith("BROWSER_VERSIONS="):
                    results["runtime"] = json.loads(m.text.split("=", 1)[1])
                if m.type == "error":
                    results["console_errors"].append(m.text)

            page.on("console", console)
            page.on("pageerror", lambda e: results["page_errors"].append(str(e)))
            page.on(
                "request",
                lambda r: results["external_requests"].append(r.url)
                if r.url.startswith("http") and not r.url.startswith(url)
                else None,
            )
            page.on(
                "response",
                lambda r: results["http_errors"].append(
                    {"url": r.url, "status": r.status}
                )
                if r.status >= 400
                else None,
            )
            return page

        page = watch(context.new_page())

        def idle(page=page):
            page.get_by_role("button", name="Back", exact=True).wait_for(timeout=120000)
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                errors = page.locator("[data-testid=stException]").all_text_contents()
                assert not errors, errors
                if (
                    page.locator("[data-test-script-state=notRunning]").count()
                    and page in states
                ):
                    page.wait_for_timeout(300)
                    if page.locator("[data-test-script-state=notRunning]").count():
                        return states[page]
                page.wait_for_timeout(50)
            raise AssertionError("App did not finish rendering")

        def click(label, page=page):
            page.locator("[data-testid=stMain]").get_by_role(
                "button", name=label, exact=True
            ).first.click()
            page.wait_for_timeout(100)
            return idle(page)

        def choose(answer, key=None, page=page):
            if key:
                from browser.walkthrough import radio_label

                scope = page.get_by_role(
                    "radiogroup", name=radio_label(page, key), exact=True
                )
            else:
                scope = page
            scope.get_by_role("radio", name=answer, exact=True)
            scope.locator("label").filter(
                has=page.get_by_role("radio", name=answer, exact=True)
            ).click()
            page.wait_for_timeout(100)
            return idle(page)

        def select(label, answer):
            page.get_by_role("combobox", name=label, exact=True).click()
            page.get_by_role("option", name=answer, exact=True).click()
            page.wait_for_timeout(100)
            idle()

        def check(name):
            results["checks"].append({"name": name, "status": "passed"})
            print("PASSED:", name, flush=True)

        def layout(label):
            nav = page.locator(".st-key-browser_navigation")
            buttons = [
                nav.get_by_role("button", name=n, exact=True)
                for n in ["Back", "Forward"]
            ]
            boxes = [x.bounding_box() for x in buttons]
            assert all(
                44 <= b["width"] <= 45 and 44 <= b["height"] <= 45 for b in boxes
            ), boxes
            assert abs(boxes[0]["y"] - boxes[1]["y"]) <= 1, boxes
            main = page.locator(".block-container").bounding_box()
            assert boxes[0]["x"] >= main["x"] + main["width"] / 2, (main, boxes)
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            results.setdefault("navigation_layout", {})[label] = boxes

        def readonly():
            expect(
                page.get_by_text(
                    "Review only. Return to your current page to continue the activity.",
                    exact=True,
                )
            ).to_be_visible()
            assert [
                text
                for text in page.locator("[data-testid=stMain]")
                .get_by_role("button")
                .all_text_contents()
                if text.strip()
            ] == ["Back", "Forward"]
            for control in ["radio", "combobox", "textbox", "spinbutton"]:
                for x in page.get_by_role(control).all():
                    expect(x).to_be_disabled()

        def review_roundtrip():
            baseline = idle()
            token = urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query).get(
                "progress"
            )
            view = int(
                urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)["view"][0]
            )
            for _ in range(view):
                click("Back")
                readonly()
                assert idle() == baseline, {
                    k: (baseline.get(k), idle().get(k))
                    for k in set(baseline) | set(idle())
                    if baseline.get(k) != idle().get(k)
                }
                assert (
                    urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query).get(
                        "progress"
                    )
                    == token
                )
            for _ in range(view):
                click("Forward")
                assert idle() == baseline, {
                    k: (baseline.get(k), idle().get(k))
                    for k in set(baseline) | set(idle())
                    if baseline.get(k) != idle().get(k)
                }
            expect(
                page.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            check(
                "Full read-only review preserves answers, drafts, attempts and earned progress"
            )

        try:
            page.goto(url + "/lesson/", wait_until="domcontentloaded")
            idle()
            assert results["runtime"]["streamlit"] == "1.57.0"
            assert results["runtime"]["pyodide"] == "0.29.3"
            expect(page.get_by_role("button", name="Back", exact=True)).to_be_disabled()
            expect(
                page.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            layout("desktop")
            page.screenshot(path=str(args.results / "briefing.png"), full_page=True)
            check("Actual stlite/Wasm runtime and subdirectory asset paths")
            lesson(page, click, choose, select, idle, check, args.results, readonly)
            review_roundtrip()
            # Keyboard navigation and focus ring.
            back = page.get_by_role("button", name="Back", exact=True)
            page.keyboard.press("Tab")
            back.focus()
            expect(back).to_be_focused()
            assert (
                back.evaluate("(element)=>getComputedStyle(element).outlineStyle")
                != "none"
            )
            back.press("Enter")
            idle()
            readonly()
            click("Forward")
            check("Keyboard focus and Enter navigation")
            page.set_viewport_size({"width": 390, "height": 844})
            page.locator(".st-key-browser_navigation").scroll_into_view_if_needed()
            layout("narrow")
            page.screenshot(path=str(args.results / "narrow.png"), full_page=True)
            check("390-pixel layout and compact 44-pixel touch targets")
            page.set_viewport_size({"width": 1280, "height": 900})
            page.locator(".st-key-browser_navigation").scroll_into_view_if_needed()
            page.screenshot(path=str(args.results / "completed.png"), full_page=True)
            saved = page.url
            # Independent browser context and tab never inherit session memory.
            other_context = browser.new_context()
            other = watch(other_context.new_page())
            other.goto(url + "/lesson/")
            idle(other)
            expect(
                other.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            assert urllib.parse.parse_qs(urllib.parse.urlsplit(other.url).query)[
                "view"
            ] == ["0"]
            other_context.close()
            check("Independent browser session starts fresh")
            # Future bookmarks are clamped; URL apps resume completed work, Signal starts anew.
            params = urllib.parse.parse_qs(urllib.parse.urlsplit(saved).query)
            params["view"] = ["999"]
            future = url + "/lesson/?" + urllib.parse.urlencode(params, doseq=True)
            page.goto(future)
            idle()
            expect(
                page.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            assert "view=999" not in page.url
            check("Future-view rejection and expected bookmark restoration")
            if PACKAGE:
                page.goto(saved)
                idle()
                click("Back")
                readonly()
                review_saved = page.url
                state = idle()
                page.reload()
                idle()
                readonly()
                assert idle() == state
                copy_page = watch(context.new_page())
                copy_page.goto(review_saved)
                idle(copy_page)
                assert states[copy_page] == state
                copy_page.close()
                click("Forward")
                check("Refresh and bookmarked review restore validated URL progress")
            else:
                assert states[page]["stage"] == 0
                check("Refresh/bookmark starts a new session-only investigation")
            click("Start over")
            expect(
                page.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            page.reload()
            idle()
            assert urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)[
                "view"
            ] == ["0"]
            check("Start over and refresh remain at a fresh activity")
            page.goto(url + "/lesson/?progress=invalid&view=999")
            idle()
            assert urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)[
                "view"
            ] == ["0"]
            check("Invalid saved progress cannot reveal future pages")
            assert not results["external_requests"], results["external_requests"]
            assert not results["page_errors"], results["page_errors"]
            assert not results["console_errors"], results["console_errors"]
            assert not results["http_errors"], results["http_errors"]
            check("No external requests, HTTP asset errors or browser execution errors")
        except Exception:
            results["buttons"] = (
                page.locator("[data-testid=stMain]")
                .get_by_role("button")
                .evaluate_all(
                    '(nodes)=>nodes.map(n=>({text:n.innerText,label:n.getAttribute("aria-label"),testid:n.parentElement.dataset.testid,html:n.outerHTML}))'
                )
            )
            print(results["buttons"], flush=True)
            results["checks"].append(
                {
                    "name": "walkthrough interrupted",
                    "status": "failed",
                    "error": traceback.format_exc(),
                }
            )
            page.screenshot(path=str(args.results / "failure.png"), full_page=True)
            print(traceback.format_exc(), flush=True)
        finally:
            (args.results / "browser-results.json").write_text(
                json.dumps(results, indent=2) + "\n"
            )
            browser.close()
            server.shutdown()
    if any(c["status"] == "failed" for c in results["checks"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
