"""Separate browser entrypoint; the live server application stays unchanged."""

import runpy
from pathlib import Path

import streamlit as st

from browser.config import PACKAGE, STAGE_KEY, RENDERERS, HERO, RESET
from browser.navigation import (
    VIEW_KEY,
    VIEW_PARAM,
    frontier,
    restore_view,
    move,
    positions,
    display_position,
    reviewing,
)
from browser.ui import CSS, LiveUI, ReviewUI

app = runpy.run_path(
    str(Path(__file__).with_name("shared_app.py")), run_name="browser_renderer"
)
globals_ = app["initialize_state"].__globals__
app["initialize_state"]()
if VIEW_KEY not in st.session_state:
    restore_view(st.session_state, st.query_params.get(VIEW_PARAM))


def reset():
    if reviewing(st.session_state):
        return
    if PACKAGE:
        app["reset_saved_progress"](st.session_state, st.query_params)
    else:
        for key in list(st.session_state):
            del st.session_state[key]
        app["initialize_state"]()
    st.session_state[VIEW_KEY] = 0
    st.session_state["browser_form_drafts"] = {}
    st.session_state["browser_live_drafts"] = {}
    st.session_state["browser_scroll"] = True
    st.query_params[VIEW_PARAM] = "0"


def can_advance():
    stage = st.session_state[STAGE_KEY]
    if reviewing(st.session_state):
        return False
    if PACKAGE == "balanced_books":
        if stage == 0:
            return True
        if stage == 1:
            item = app["TRANSACTIONS"][st.session_state.bbc_inbox_index]
            return item.id in st.session_state.bbc_inbox_feedback
        if stage == 2:
            item = app["RECORDABLE_TRANSACTIONS"][st.session_state.bbc_equation_index]
            return item.id in st.session_state.bbc_equation_feedback
        return stage == 3 and bool(st.session_state.bbc_statement_completion)
    if PACKAGE == "gem_city_data_model_lab":
        from gem_city_data_model_lab.engine import is_correct_stage
        from gem_city_data_model_lab.progress import STAGE_KEYS

        return (
            stage == 0
            or stage in STAGE_KEYS
            and is_correct_stage(stage, st.session_state[STAGE_KEYS[stage]])
        )
    if PACKAGE == "gem_city_sql_investigation":
        return (
            stage == 0
            or stage == 1
            and app["evaluate_reading"](st.session_state.si_reading)[0]
            or stage == 2
            and app["evaluate_missing"](st.session_state.si_missing)[0]
            or stage == 3
            and app["evaluate_amount"](st.session_state.si_amount)[0]
            or stage == 4
            and all(st.session_state.si_custom[r]["passed"] for r in app["ROUTES"])
        )
    return (
        stage == 0
        and bool(st.session_state.route)
        or stage in (1, 2)
        or stage == 3
        and bool(st.session_state.evidence_history)
        or stage == 4
        and bool(st.session_state.pressure_history)
        or stage == 5
        and bool(st.session_state.conclusion_history)
    )


def set_stage(stage):
    target = positions().index((stage, 0))
    if target != frontier(st.session_state) + 1 or not can_advance():
        return
    st.session_state[STAGE_KEY] = stage
    st.session_state[VIEW_KEY] = target
    st.session_state["browser_scroll"] = True
    if not PACKAGE:
        st.rerun()


def advance_item():
    if not can_advance():
        return
    target = frontier(st.session_state) + 1
    stage, index = positions()[target]
    st.session_state[STAGE_KEY] = stage
    if stage == 1:
        st.session_state.bbc_inbox_index = index
    elif stage == 2:
        st.session_state.bbc_equation_index = index
    st.session_state[VIEW_KEY] = target
    st.session_state["browser_scroll"] = True


def guard(fn):
    def guarded(*args, **kwargs):
        if not reviewing(st.session_state):
            return fn(*args, **kwargs)

    return guarded


globals_[RESET] = reset
globals_["set_stage" if PACKAGE else "advance_to"] = set_stage
if PACKAGE == "balanced_books":
    globals_.update(advance_inbox=advance_item, advance_equation=advance_item)
    for name in ["submit_inbox_answer", "submit_equation_answer"]:
        globals_[name] = guard(app[name])

# Preserve current BBC drafts across Streamlit's unrendered-widget cleanup.
if PACKAGE == "balanced_books":
    drafts = st.session_state.setdefault("browser_live_drafts", {})
    for prefix in ["inbox_choice_", "equation_choice_"]:
        for key in list(st.session_state):
            if key.startswith(prefix):
                drafts[key] = st.session_state[key]
    for key, value in drafts.items():
        if key not in st.session_state:
            st.session_state[key] = value

st.markdown(app["APP_CSS"], unsafe_allow_html=True)
st.markdown(CSS, unsafe_allow_html=True)
app[HERO]()
view = st.session_state[VIEW_KEY]
review = reviewing(st.session_state)
with st.container(
    key="browser_navigation",
    horizontal=True,
    horizontal_alignment="right",
    vertical_alignment="center",
    gap="xsmall",
):
    st.caption(f"Page {view + 1} of {len(positions())}", width="content")
    st.button(
        "Back",
        width=44,
        key="browser_back",
        help="Back: review the previous reached page. Earlier pages are read-only.",
        disabled=view == 0,
        on_click=move,
        args=(st.session_state, -1),
    )
    st.button(
        "Forward",
        width=44,
        key="browser_forward",
        help="Forward: review the next reached page. Use the existing validation controls to unlock a new page.",
        disabled=view == frontier(st.session_state),
        on_click=move,
        args=(st.session_state, 1),
    )
if review:
    st.info("Review only. Return to your current page to continue the activity.")
else:
    st.button("Start over", key="browser_reset", on_click=reset)

stage = st.session_state[STAGE_KEY]
inbox, equation = (
    st.session_state.get("bbc_inbox_index"),
    st.session_state.get("bbc_equation_index"),
)
try:
    shown_stage, shown_index = display_position(st.session_state)
    st.session_state[STAGE_KEY] = shown_stage
    if PACKAGE == "balanced_books":
        if shown_stage == 1:
            st.session_state.bbc_inbox_index = shown_index
        elif shown_stage == 2:
            st.session_state.bbc_equation_index = shown_index
    if review:
        globals_["st"] = ReviewUI()
    elif not PACKAGE:
        globals_["st"] = LiveUI()
    # BBC's stage row has a column-owned reset button, so omit that mutation in review.
    if PACKAGE != "balanced_books":
        app["render_stage_row" if PACKAGE else "render_progress"]()
    elif not review:
        app["render_stage_row"]()
    if review and PACKAGE == "balanced_books" and shown_stage == 3:
        st.header("Statement Builder — completed work")
        app["render_completed_statements"]()
        st.caption(
            "The three statements were finalized before this page became available for review."
        )
    else:
        app[RENDERERS[shown_stage]]()
finally:
    # Only review projects an earlier stage. Live renderers may advance via component completion.
    if review:
        st.session_state[STAGE_KEY] = stage
        if PACKAGE == "balanced_books":
            st.session_state.bbc_inbox_index, st.session_state.bbc_equation_index = (
                inbox,
                equation,
            )
    if PACKAGE:
        app["sync_progress_query"](st.session_state, st.query_params)
    st.query_params[VIEW_PARAM] = str(st.session_state[VIEW_KEY])

if st.session_state.pop("browser_scroll", False):
    st.iframe(
        """<script>requestAnimationFrame(()=>requestAnimationFrame(()=>window.parent.document.querySelector('section[data-testid="stMain"]')?.scrollTo({top:0,left:0,behavior:'auto'})));</script>""",
        height=1,
        tab_index=-1,
    )
if not PACKAGE:
    st.caption(
        "Your choices remain only in this browser session. Refreshing or closing this page starts a new investigation."
    )
