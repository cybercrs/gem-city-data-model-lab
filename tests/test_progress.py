import unittest

from gem_city_data_model_lab.case_data import ANOMALIES, ER_PROMPTS, FIELD_ASSIGNMENTS, REA_ITEMS
from gem_city_data_model_lab.progress import activity_defaults, decode_snapshot, encode_state, reset_saved_progress


def complete_state():
    state = activity_defaults()
    state["dm_shuffle_seed"] = 34105
    state["dm_stage"] = 6
    state["dm_grain"] = {"grain": "One product line on one order", "key": "OrderLineID"}
    state["dm_anomalies"] = {item["id"]: item["correct"] for item in ANOMALIES}
    state["dm_normalization"] = {field: table for field, table, _ in FIELD_ASSIGNMENTS}
    state["dm_er"] = {item_id: answer for item_id, _, _, answer in ER_PROMPTS}
    state["dm_rea"] = {label: answer for label, answer, _ in REA_ITEMS}
    state["dm_drafts"] = {
        "grain": dict(state["dm_grain"]),
        "anomalies": dict(state["dm_anomalies"]),
        "normalization": dict(state["dm_normalization"]),
        "er": dict(state["dm_er"]),
        "rea": dict(state["dm_rea"]),
    }
    state["dm_attempts"] = {"grain": 1, "anomalies": 1, "normalization": 1, "er": 1, "rea": 1}
    return state


class ProgressTests(unittest.TestCase):
    def test_completed_round_trip(self):
        restored = decode_snapshot(encode_state(complete_state()))
        self.assertIsNotNone(restored)
        self.assertEqual(restored["dm_stage"], 6)
        self.assertNotIn("name", encode_state(complete_state()).lower())

    def test_partial_draft_and_shuffle_seed_round_trip(self):
        state = activity_defaults()
        state["dm_stage"] = 1
        state["dm_shuffle_seed"] = 987654
        state["dm_drafts"]["grain"] = {"grain": "One product line on one order"}
        restored = decode_snapshot(encode_state(state))
        self.assertIsNotNone(restored)
        self.assertEqual(restored["dm_shuffle_seed"], 987654)
        self.assertEqual(restored["dm_drafts"]["grain"]["grain"], "One product line on one order")

    def test_skipped_stage_is_rejected(self):
        state = activity_defaults()
        state["dm_stage"] = 4
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_wrong_prior_answer_is_rejected(self):
        state = complete_state()
        state["dm_grain"]["grain"] = "One order"
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_future_draft_is_rejected(self):
        state = activity_defaults()
        state["dm_stage"] = 1
        state["dm_drafts"]["rea"] = {"Cash": "Resource"}
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_malformed_and_reset(self):
        self.assertIsNone(decode_snapshot("not-valid"))
        destination = complete_state()
        query = {}
        reset_saved_progress(destination, query)
        self.assertEqual(destination["dm_stage"], 0)
        self.assertEqual(destination["dm_drafts"]["grain"], {})
        self.assertIsNotNone(decode_snapshot(query["progress"]))


if __name__ == "__main__":
    unittest.main()
