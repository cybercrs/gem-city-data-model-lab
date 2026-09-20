"""Evaluation functions for the data-model activity."""

from __future__ import annotations

from collections.abc import Mapping

from .case_data import (
    ANOMALIES,
    ER_PROMPTS,
    FIELD_ASSIGNMENTS,
    GRAIN_CORRECT,
    KEY_CORRECT,
    REA_ITEMS,
)


def evaluate_grain(grain: str, key_choice: str) -> tuple[bool, list[str]]:
    feedback: list[str] = []
    if grain == GRAIN_CORRECT:
        feedback.append("The row grain is correct: each row records one product line on one order.")
    else:
        feedback.append("Look for what makes two rows with the same OrderID different. The ProductID, quantity, and actual price change by line.")
    if key_choice == KEY_CORRECT:
        feedback.append("The visible OrderLineID gives every line its own identity, even if the same product appears twice on one order.")
    elif key_choice == "OrderID plus ProductID":
        feedback.append("That composite key works only if the same product can never appear twice on one order. The case does not promise that restriction.")
    else:
        feedback.append("Neither OrderID nor ProductID is unique at the order-line grain.")
    return grain == GRAIN_CORRECT and key_choice == KEY_CORRECT, feedback


def evaluate_anomalies(responses: Mapping[str, str]) -> tuple[bool, list[dict[str, object]]]:
    details = []
    for item in ANOMALIES:
        selected = responses.get(item["id"], "")
        details.append(
            {
                "id": item["id"],
                "correct": selected == item["correct"],
                "selected": selected,
                "answer": item["correct"],
                "explanation": item["explanation"],
            }
        )
    return all(detail["correct"] for detail in details), details


def evaluate_normalization(responses: Mapping[str, str]) -> tuple[bool, list[dict[str, object]]]:
    details = []
    for field, table, explanation in FIELD_ASSIGNMENTS:
        selected = responses.get(field, "")
        details.append(
            {
                "field": field,
                "correct": selected == table,
                "selected": selected,
                "answer": table,
                "explanation": explanation,
            }
        )
    return all(detail["correct"] for detail in details), details


def evaluate_er(responses: Mapping[str, str]) -> tuple[bool, list[dict[str, object]]]:
    details = []
    for item_id, label, explanation, answer in ER_PROMPTS:
        selected = responses.get(item_id, "")
        details.append(
            {
                "id": item_id,
                "label": label,
                "correct": selected == answer,
                "selected": selected,
                "answer": answer,
                "explanation": explanation,
            }
        )
    return all(detail["correct"] for detail in details), details


def evaluate_rea(responses: Mapping[str, str]) -> tuple[bool, list[dict[str, object]]]:
    details = []
    for label, answer, explanation in REA_ITEMS:
        selected = responses.get(label, "")
        details.append(
            {
                "label": label,
                "correct": selected == answer,
                "selected": selected,
                "answer": answer,
                "explanation": explanation,
            }
        )
    return all(detail["correct"] for detail in details), details


def is_correct_stage(stage: int, responses: Mapping[str, object]) -> bool:
    if stage == 1:
        return responses.get("grain") == GRAIN_CORRECT and responses.get("key") == KEY_CORRECT
    if stage == 2:
        return all(responses.get(item["id"]) == item["correct"] for item in ANOMALIES)
    if stage == 3:
        return all(responses.get(field) == table for field, table, _ in FIELD_ASSIGNMENTS)
    if stage == 4:
        return all(responses.get(item_id) == answer for item_id, _, _, answer in ER_PROMPTS)
    if stage == 5:
        return all(responses.get(label) == answer for label, answer, _ in REA_ITEMS)
    return stage in {0, 6}
