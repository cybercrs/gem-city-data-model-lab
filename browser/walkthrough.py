from playwright.sync_api import expect
from gem_city_data_model_lab.case_data import (
    ANOMALIES,
    ER_PROMPTS,
    FIELD_ASSIGNMENTS,
    REA_ITEMS,
)


def lesson(page, click, choose, select, idle, check, results, readonly):
    click("Begin with the row grain")
    # Current draft survives a review round-trip and refresh without an attempt.
    choose("One order", "widget_dm_grain")
    baseline = idle()
    click("Back")
    readonly()
    assert idle() == baseline
    click("Forward")
    page.reload()
    idle()
    expect(
        page.get_by_role(
            "radiogroup", name="What does one row represent?", exact=True
        ).get_by_role("radio", name="One order", exact=True)
    ).to_be_checked()
    check("Unsubmitted selection survives review navigation and refresh")
    choose("OrderID", "widget_dm_key")
    click("Check the grain and key")
    assert idle()["dm_attempts"]["grain"] == 1
    expect(page.get_by_role("button", name="Forward", exact=True)).to_be_disabled()
    click("Check revised answers")
    assert idle()["dm_attempts"]["grain"] == 2
    choose("One product line on one order", "widget_dm_grain")
    choose("OrderLineID", "widget_dm_key")
    click("Check revised answers")
    assert idle()["dm_attempts"]["grain"] == 3
    expect(page.get_by_role("button", name="Forward", exact=True)).to_be_disabled()
    click("Continue to the anomalies")
    for item in ANOMALIES:
        choose(item["correct"], "widget_dm_anomaly_" + item["id"])
    click("Classify the anomalies")
    click("Continue to normalization")
    for field, table, _ in FIELD_ASSIGNMENTS:
        select(field + " belongs in", table)
    click("Check the table assignments")
    click("Continue to the E-R model")
    for item_id, _, _, answer in ER_PROMPTS:
        choose(answer, "widget_dm_er_" + item_id)
    click("Check the E-R model")
    click("Continue to the REA model")
    for label, answer, _ in REA_ITEMS:
        select(label + " is a", answer)
    click("Check the REA classifications")
    click("Complete the model review")
    assert idle()["dm_stage"] == 6
    expect(page.get_by_text("Model complete", exact=False)).to_be_visible()
    check(
        "Complete grain, anomalies, normalization, E-R and REA lesson including wrong answers and repeats"
    )


def radio_label(page, key):
    if key == "widget_dm_grain":
        return "What does one row represent?"
    if key == "widget_dm_key":
        return "Which visible field is the best primary key for that row grain?"
    if key.startswith("widget_dm_er_"):
        return next(
            label
            for item_id, label, _, _ in ER_PROMPTS
            if key == "widget_dm_er_" + item_id
        )
    item = next(item for item in ANOMALIES if key == "widget_dm_anomaly_" + item["id"])
    cards = page.locator(".case-card").all_text_contents()
    index = next(i for i, text in enumerate(cards) if item["scenario"] in text)
    return f"Identify the anomaly in situation {index + 1}"
