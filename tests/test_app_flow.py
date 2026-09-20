import unittest

from streamlit.testing.v1 import AppTest

from gem_city_data_model_lab.case_data import ANOMALIES, ER_PROMPTS, FIELD_ASSIGNMENTS, REA_ITEMS
from gem_city_data_model_lab.progress import SNAPSHOT_PARAM, decode_snapshot


def button(app: AppTest, label: str):
    return next(item for item in app.button if item.label == label)


class AppFlowTests(unittest.TestCase):
    def test_complete_student_flow(self):
        app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
        self.assertFalse(app.exception)
        button(app, "Begin with the row grain").click().run()

        app.radio(key="widget_dm_grain").set_value("One product line on one order")
        app.radio(key="widget_dm_key").set_value("OrderLineID")
        button(app, "Check the grain and key").click().run()
        button(app, "Continue to the anomalies").click().run()

        for item in ANOMALIES:
            app.radio(key=f"widget_dm_anomaly_{item['id']}").set_value(item["correct"])
        button(app, "Classify the anomalies").click().run()
        button(app, "Continue to normalization").click().run()

        for field, table, _ in FIELD_ASSIGNMENTS:
            app.selectbox(key=f"widget_dm_normalize_{field}").set_value(table)
        button(app, "Check the table assignments").click().run()
        button(app, "Continue to the E-R model").click().run()

        for item_id, _, _, answer in ER_PROMPTS:
            app.radio(key=f"widget_dm_er_{item_id}").set_value(answer)
        button(app, "Check the E-R model").click().run()
        button(app, "Continue to the REA model").click().run()

        for label, answer, _ in REA_ITEMS:
            key = f"widget_dm_rea_{label.lower().replace(' ', '_')}"
            app.selectbox(key=key).set_value(answer)
        button(app, "Check the REA classifications").click().run()
        button(app, "Complete the model review").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["dm_stage"], 6)
        self.assertTrue(any("model complete" in item.value.lower() for item in app.markdown))

    def test_partial_selection_is_saved_in_the_url(self):
        app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
        button(app, "Begin with the row grain").click().run()
        app.radio(key="widget_dm_grain").set_value("One product line on one order")
        app.run()

        token = app.query_params[SNAPSHOT_PARAM]
        restored = decode_snapshot(token[0] if isinstance(token, list) else token)
        self.assertIsNotNone(restored)
        self.assertEqual(restored["dm_stage"], 1)
        self.assertEqual(restored["dm_drafts"]["grain"]["grain"], "One product line on one order")

    def test_progress_pills_match_numbered_steps(self):
        app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
        rendered = "\n".join(item.value for item in app.markdown)
        for label in ("Brief", "1. Grain", "2. Anomalies", "3. Normalize", "4. E-R", "5. REA", "Complete"):
            self.assertIn(label, rendered)

    def test_wrong_answer_can_be_revised_and_checked_in_one_action(self):
        app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
        button(app, "Begin with the row grain").click().run()

        app.radio(key="widget_dm_grain").set_value("One order")
        app.radio(key="widget_dm_key").set_value("OrderID")
        button(app, "Check the grain and key").click().run()

        self.assertEqual(app.radio(key="widget_dm_grain").value, "One order")
        self.assertEqual(app.radio(key="widget_dm_key").value, "OrderID")
        self.assertTrue(any(item.label == "Check revised answers" for item in app.button))

        app.radio(key="widget_dm_grain").set_value("One product line on one order")
        app.radio(key="widget_dm_key").set_value("OrderLineID")
        button(app, "Check revised answers").click().run()

        self.assertEqual(app.session_state["dm_grain"]["grain"], "One product line on one order")
        self.assertEqual(app.session_state["dm_grain"]["key"], "OrderLineID")
        self.assertTrue(any(item.label == "Continue to the anomalies" for item in app.button))
        self.assertFalse(any(item.label.startswith("Revise") for item in app.button))


if __name__ == "__main__":
    unittest.main()
