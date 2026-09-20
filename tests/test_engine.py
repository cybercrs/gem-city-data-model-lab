import unittest

from gem_city_data_model_lab.case_data import ANOMALIES, ER_PROMPTS, FIELD_ASSIGNMENTS, REA_ITEMS
from gem_city_data_model_lab.engine import (
    evaluate_anomalies,
    evaluate_er,
    evaluate_grain,
    evaluate_normalization,
    evaluate_rea,
)


class EngineTests(unittest.TestCase):
    def test_grain_and_key(self):
        correct, _ = evaluate_grain("One product line on one order", "OrderLineID")
        self.assertTrue(correct)
        composite, feedback = evaluate_grain("One product line on one order", "OrderID plus ProductID")
        self.assertFalse(composite)
        self.assertIn("same product", feedback[1])

    def test_all_model_answer_keys(self):
        anomalies = {item["id"]: item["correct"] for item in ANOMALIES}
        normalized = {field: table for field, table, _ in FIELD_ASSIGNMENTS}
        er = {item_id: answer for item_id, _, _, answer in ER_PROMPTS}
        rea = {label: answer for label, answer, _ in REA_ITEMS}
        self.assertTrue(evaluate_anomalies(anomalies)[0])
        self.assertTrue(evaluate_normalization(normalized)[0])
        self.assertTrue(evaluate_er(er)[0])
        self.assertTrue(evaluate_rea(rea)[0])


if __name__ == "__main__":
    unittest.main()
