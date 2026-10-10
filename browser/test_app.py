"""Exercise browser entrypoints under the bundled Streamlit API version."""

import copy
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest
from browser.build import app_files
from browser.config import PACKAGE, STAGE_KEY


def button(app, label):
    return next(x for x in app.button if x.label == label)


class BrowserAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        for name, content in app_files().items():
            path = Path(self.tmp.name) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.app = AppTest.from_file(
            str(Path(self.tmp.name) / "browser/app.py"), default_timeout=30
        ).run()
        self.addCleanup(self.tmp.cleanup)

    def test_first_step_draft_review_and_forward_gate(self):
        app = self.app
        self.assertFalse(app.exception)
        first = {
            "balanced_books": "Open the Transaction Inbox",
            "gem_city_data_model_lab": "Begin with the row grain",
            "gem_city_sql_investigation": "Begin reading SQL",
            "": "Open your case",
        }[PACKAGE]
        if PACKAGE == "balanced_books":
            first = next(
                x.label
                for x in app.button
                if x.label not in ["Back", "Forward", "Start over"]
            )
        button(app, first).click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state[STAGE_KEY], 1)
        if app.radio:
            app.radio[0].set_value(app.radio[0].options[0]).run()
        before = copy.deepcopy(app.session_state.filtered_state)
        progress = copy.deepcopy(app.query_params.get("progress"))
        button(app, "Back").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state[STAGE_KEY], 1)
        self.assertEqual(app.query_params.get("progress"), progress)
        self.assertTrue(
            all(
                x.disabled
                for x in list(app.radio) + list(app.selectbox) + list(app.text_area)
            )
        )
        self.assertEqual({x.label for x in app.button}, {"Back", "Forward"})
        button(app, "Forward").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(button(app, "Forward").disabled)
        self.assertEqual(app.query_params.get("progress"), progress)
        for key in before:
            if key in [
                "dm_drafts",
                "si_drafts",
                "bbc_inbox_responses",
                "bbc_equation_responses",
                "question_history",
                "investigation_budget",
            ]:
                self.assertEqual(app.session_state[key], before[key])

    def test_future_bookmark_cannot_unlock_a_page(self):
        self.app.query_params["view"] = "99"
        # A new session reads the untrusted view without an earned progress token.
        app = AppTest.from_file(self.app._script_path, default_timeout=30)
        app.query_params["view"] = "99"
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["browser_view"], 0)
        self.assertTrue(button(app, "Forward").disabled)

    def test_reset_replaces_saved_activity(self):
        app = self.app
        button(app, "Start over").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state[STAGE_KEY], 0)
        self.assertEqual(app.session_state["browser_view"], 0)


if __name__ == "__main__":
    unittest.main()
