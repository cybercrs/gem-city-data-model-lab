"""Student-facing Streamlit app for order-to-cash data modeling."""

from __future__ import annotations

import hashlib
import random
from html import escape

import streamlit as st

from gem_city_data_model_lab.case_data import (
    ANOMALIES,
    ANOMALY_OPTIONS,
    COMPANY_NAME,
    ER_FOREIGN_KEY_OPTIONS,
    ER_PROMPTS,
    ER_RELATIONSHIP_OPTIONS,
    FIELD_ASSIGNMENTS,
    GRAIN_OPTIONS,
    KEY_OPTIONS,
    NORMALIZED_TABLES,
    RAW_COLUMNS,
    RAW_ROWS,
    REA_ITEMS,
    REA_OPTIONS,
    TABLE_OPTIONS,
)
from gem_city_data_model_lab.engine import (
    evaluate_anomalies,
    evaluate_er,
    evaluate_grain,
    evaluate_normalization,
    evaluate_rea,
)
from gem_city_data_model_lab.progress import (
    SNAPSHOT_PARAM,
    activity_defaults,
    record_attempt,
    reset_saved_progress,
    restore_session_state,
    sync_progress_query,
)
from gem_city_data_model_lab.theme import APP_CSS


st.set_page_config(
    page_title="Gem City Data Model Lab",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STAGE_LABELS = ("Brief", "1. Grain", "2. Anomalies", "3. Normalize", "4. E-R", "5. REA", "Complete")


def initialize_state() -> None:
    if "dm_restore_attempted" not in st.session_state:
        restored = restore_session_state(st.session_state, st.query_params.get(SNAPSHOT_PARAM))
        st.session_state.dm_restore_attempted = True
        if restored:
            st.session_state.dm_scroll_to_top = True
    for key, value in activity_defaults().items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_stage(stage: int) -> None:
    st.session_state.dm_stage = stage
    st.session_state.dm_scroll_to_top = True


def restart() -> None:
    reset_saved_progress(st.session_state, st.query_params)
    st.session_state.dm_scroll_to_top = True


def save_draft(group: str, answer_key: str, widget_key: str) -> None:
    """Persist an unfinished choice outside widget state so refresh can restore it."""

    drafts = {key: dict(value) for key, value in st.session_state.dm_drafts.items()}
    group_answers = dict(drafts[group])
    value = st.session_state.get(widget_key)
    if value is None:
        group_answers.pop(answer_key, None)
    else:
        group_answers[answer_key] = str(value)
    drafts[group] = group_answers
    st.session_state.dm_drafts = drafts


def replace_draft(group: str, answers: dict[str, str]) -> None:
    drafts = {key: dict(value) for key, value in st.session_state.dm_drafts.items()}
    drafts[group] = dict(answers)
    st.session_state.dm_drafts = drafts


def shuffled(items: tuple | list, salt: str) -> list:
    """Return a stable per-student order that survives reruns and refreshes."""

    digest = hashlib.sha256(f"{st.session_state.dm_shuffle_seed}:{salt}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    ordered = list(items)
    rng.shuffle(ordered)
    if len(ordered) > 1 and ordered == list(items):
        ordered = ordered[1:] + ordered[:1]
    return ordered


def selected_index(options: tuple | list, selected: str | None) -> int | None:
    return list(options).index(selected) if selected in options else None


def render_scroll_reset() -> None:
    """Reset after navigation without overriding student-initiated scrolling."""

    if not st.session_state.pop("dm_scroll_to_top", False):
        return
    st.iframe(
        """
        <script>
        (() => {
          const parent = window.parent;
          const main = parent.document.querySelector('section[data-testid="stMain"]');
          if (!main) return;
          let cancelled = false;
          let finished = false;
          const scrollingKeys = new Set(['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' ']);
          const cancel = () => { cancelled = true; cleanup(); };
          const cancelKey = (event) => { if (scrollingKeys.has(event.key)) cancel(); };
          const cleanup = () => {
            parent.removeEventListener('wheel', cancel);
            parent.removeEventListener('touchstart', cancel);
            parent.removeEventListener('keydown', cancelKey);
          };
          const reset = () => {
            if (finished) return;
            finished = true;
            if (!cancelled) main.scrollTo({ top: 0, left: 0, behavior: 'auto' });
            cleanup();
          };
          parent.addEventListener('wheel', cancel, { passive: true });
          parent.addEventListener('touchstart', cancel, { passive: true });
          parent.addEventListener('keydown', cancelKey);
          parent.requestAnimationFrame(() => parent.requestAnimationFrame(reset));
          parent.setTimeout(reset, 120);
        })();
        </script>
        """,
        height=1,
        tab_index=-1,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="kicker">ORDER-TO-CASH DATA MODELING</div>
          <h1>Gem City Data Model Lab</h1>
          <p>Turn a fragile order export into a database that can preserve the facts, support reliable reports, and explain the business process.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stage_row() -> None:
    current = int(st.session_state.dm_stage)
    pills = []
    for index, label in enumerate(STAGE_LABELS):
        status = "complete" if index < current else "active" if index == current else ""
        pills.append(f'<div class="stage-pill {status}">{escape(label)}</div>')
    st.markdown(f'<div class="stage-row">{"".join(pills)}</div>', unsafe_allow_html=True)


def render_feedback(label: str, correct: bool, explanation: str, selected: str = "") -> None:
    status = "correct" if correct else ""
    result = "Correct" if correct else "Reconsider"
    selection = f" Your answer: {escape(selected)}." if selected else ""
    st.markdown(
        f'<div class="feedback {status}"><strong>{escape(label)} — {result}.</strong>{selection} {escape(explanation)}</div>',
        unsafe_allow_html=True,
    )


def render_schema() -> None:
    cards = []
    for table, fields in NORMALIZED_TABLES.items():
        field_html = "".join(f"<div>{escape(field)}</div>" for field in fields)
        cards.append(f'<section class="schema-table"><h4>{escape(table)}</h4>{field_html}</section>')
    st.markdown(f'<div class="schema-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_raw_table() -> None:
    """Render the source export compactly without horizontal scrolling."""

    column_widths = (8, 6.5, 10.5, 8.5, 13, 9, 7, 12, 8, 7.5, 10)
    header_labels = {
        "OrderLineID": "Order<br>Line ID",
        "OrderID": "Order<br>ID",
        "OrderDate": "Order<br>Date",
        "CustomerID": "Customer<br>ID",
        "CustomerName": "Customer<br>Name",
        "CustomerCity": "Customer<br>City",
        "ProductID": "Product<br>ID",
        "ProductName": "Product<br>Name",
        "StandardPrice": "Standard<br>Price",
        "Quantity": "Quantity",
        "ActualUnitPrice": "Actual Unit<br>Price",
    }
    header_html = "".join(
        f'<th scope="col" width="{width}%" style="width:{width}%">{header_labels[column]}</th>'
        for column, width in zip(RAW_COLUMNS, column_widths)
    )
    body_rows = []
    for row in RAW_ROWS:
        cells = []
        for column, value in zip(RAW_COLUMNS, row):
            display = f"${value:,.2f}" if column in {"StandardPrice", "ActualUnitPrice"} else str(value)
            cells.append(f"<td>{escape(display)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f'<div class="source-table-wrap"><table class="source-table">'
        f'<thead><tr>{header_html}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render_briefing() -> None:
    st.markdown('<div class="eyebrow">The design problem</div>', unsafe_allow_html=True)
    st.header(f"One export is doing too many jobs at {COMPANY_NAME}")
    st.markdown(
        "The controller can read the current export, but customer, product, order, and line-item facts are repeated in the same rows. You will decide what one row means, expose the risks in that structure, and redesign the data before representing the process with E-R and REA models."
    )
    st.markdown(
        '<div class="principle"><strong>Case assumption</strong> Every order in this activity has been fulfilled, so the order can be treated as the sale event when you build the REA model.</div>',
        unsafe_allow_html=True,
    )
    render_raw_table()
    st.caption("This is synthetic course data. Dollar amounts are shown per unit.")
    st.button("Begin with the row grain", type="primary", width="stretch", on_click=set_stage, args=(1,))


def render_grain() -> None:
    st.markdown('<div class="eyebrow">Step 1</div>', unsafe_allow_html=True)
    st.header("Determine what one row represents")
    st.markdown(
        '<p class="lead">Before choosing tables or relationships, identify the grain—the business fact captured by one row. Then determine which visible field uniquely identifies each row at that grain.</p>',
        unsafe_allow_html=True,
    )
    with st.expander("Inspect the source export", expanded=True):
        render_raw_table()

    response = dict(st.session_state.dm_grain)
    draft = dict(st.session_state.dm_drafts["grain"])
    response_correct = bool(response) and evaluate_grain(response.get("grain", ""), response.get("key", ""))[0]
    if not response_correct:
        if response:
            st.info("Revise either answer below, then select Check revised answers.")
        grain = st.radio(
            "What does one row represent?",
            GRAIN_OPTIONS,
            index=selected_index(GRAIN_OPTIONS, draft.get("grain")),
            key="widget_dm_grain",
            on_change=save_draft,
            args=("grain", "grain", "widget_dm_grain"),
        )
        key_choice = st.radio(
            "Which visible field is the best primary key for that row grain?",
            KEY_OPTIONS,
            index=selected_index(KEY_OPTIONS, draft.get("key")),
            key="widget_dm_key",
            on_change=save_draft,
            args=("grain", "key", "widget_dm_key"),
        )
        button_label = "Check revised answers" if response else "Check the grain and key"
        submitted = st.button(button_label, type="primary", width="stretch")
        if submitted:
            if grain is None or key_choice is None:
                st.warning("Answer both questions before checking your reasoning.")
            else:
                response = {"grain": grain, "key": key_choice}
                replace_draft("grain", response)
                st.session_state.dm_grain = response
                record_attempt(st.session_state, "grain")
                if not evaluate_grain(response["grain"], response["key"])[0]:
                    st.rerun()

    if response:
        correct, messages = evaluate_grain(response.get("grain", ""), response.get("key", ""))
        render_feedback("Row grain", response.get("grain") == GRAIN_OPTIONS[3], messages[0], response.get("grain", ""))
        render_feedback("Primary key", response.get("key") == KEY_OPTIONS[3], messages[1], response.get("key", ""))
        st.markdown(
            '<div class="principle"><strong>Foreign-key direction</strong> Orders does not need a list of OrderLineIDs. Each OrderLines row carries one OrderID foreign key, so every line points back to its parent order. Many child rows may repeat the same OrderID.</div>',
            unsafe_allow_html=True,
        )
        if correct:
            st.button("Continue to the anomalies", type="primary", width="stretch", on_click=set_stage, args=(2,))


def render_anomalies() -> None:
    st.markdown('<div class="eyebrow">Step 2</div>', unsafe_allow_html=True)
    st.header("Expose what can go wrong")
    st.markdown(
        '<p class="lead"><strong>Your task:</strong> Read each situation and classify it as an insertion, update, or deletion anomaly. Focus on which business fact the flat table prevents, makes inconsistent, or removes unintentionally.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="principle"><strong>Classification guide</strong> Insertion: a new fact cannot be recorded independently. Update: one fact is repeated and can become inconsistent. Deletion: removing one record also erases a different fact that should remain.</div>',
        unsafe_allow_html=True,
    )
    response = dict(st.session_state.dm_anomalies)
    draft = dict(st.session_state.dm_drafts["anomalies"])
    ordered_items = shuffled(ANOMALIES, "anomaly-question-order")
    response_correct = bool(response) and evaluate_anomalies(response)[0]
    if not response_correct:
        if response:
            st.info("Revise any classification below, then select Check revised answers.")
        answers = {}
        for index, item in enumerate(ordered_items, start=1):
            st.markdown(
                f'<div class="case-card"><strong>Situation {index}</strong><br>{escape(item["scenario"])}</div>',
                unsafe_allow_html=True,
            )
            options = shuffled(ANOMALY_OPTIONS, f'anomaly-answer-order:{item["id"]}')
            widget_key = f"widget_dm_anomaly_{item['id']}"
            answers[item["id"]] = st.radio(
                f"Identify the anomaly in situation {index}",
                options,
                index=selected_index(options, draft.get(item["id"])),
                key=widget_key,
                on_change=save_draft,
                args=("anomalies", item["id"], widget_key),
                horizontal=True,
            )
        button_label = "Check revised answers" if response else "Classify the anomalies"
        submitted = st.button(button_label, type="primary", width="stretch")
        if submitted:
            if any(value is None for value in answers.values()):
                st.warning("Classify all three situations before checking your work.")
            else:
                response = {key: str(value) for key, value in answers.items()}
                replace_draft("anomalies", response)
                st.session_state.dm_anomalies = response
                record_attempt(st.session_state, "anomalies")
                if not evaluate_anomalies(response)[0]:
                    st.rerun()

    if response:
        correct, details = evaluate_anomalies(response)
        details_by_id = {str(detail["id"]): detail for detail in details}
        for index, item in enumerate(ordered_items, start=1):
            detail = details_by_id[item["id"]]
            explanation = f"The best classification is {detail['answer']}. {detail['explanation']}"
            render_feedback(f"Situation {index}", bool(detail["correct"]), explanation, str(detail["selected"]))
        if correct:
            st.button("Continue to normalization", type="primary", width="stretch", on_click=set_stage, args=(3,))


def render_normalization() -> None:
    st.markdown('<div class="eyebrow">Step 3</div>', unsafe_allow_html=True)
    st.header("Give each fact one appropriate home")
    st.markdown(
        '<p class="lead"><strong>Your task:</strong> Organize the information according to normalization rules. Assign each non-key field to the table whose primary key determines that fact, keeping historical transaction facts on the order line.</p>',
        unsafe_allow_html=True,
    )
    response = dict(st.session_state.dm_normalization)
    draft = dict(st.session_state.dm_drafts["normalization"])
    ordered_assignments = shuffled(FIELD_ASSIGNMENTS, "normalization-question-order")
    response_correct = bool(response) and evaluate_normalization(response)[0]
    if not response_correct:
        if response:
            st.info("Revise any table assignment below, then select Check revised answers.")
        answers = {}
        columns = st.columns(2)
        for index, (field, _, _) in enumerate(ordered_assignments):
            widget_key = f"widget_dm_normalize_{field}"
            with columns[index % 2]:
                answers[field] = st.selectbox(
                    f"{field} belongs in",
                    TABLE_OPTIONS,
                    index=selected_index(TABLE_OPTIONS, draft.get(field)),
                    key=widget_key,
                    placeholder="Choose a table",
                    on_change=save_draft,
                    args=("normalization", field, widget_key),
                )
        button_label = "Check revised answers" if response else "Check the table assignments"
        submitted = st.button(button_label, type="primary", width="stretch")
        if submitted:
            if any(value is None for value in answers.values()):
                st.warning("Assign every field before checking the model.")
            else:
                response = {key: str(value) for key, value in answers.items()}
                replace_draft("normalization", response)
                st.session_state.dm_normalization = response
                record_attempt(st.session_state, "normalization")
                if not evaluate_normalization(response)[0]:
                    st.rerun()

    if response:
        correct, details = evaluate_normalization(response)
        details_by_field = {str(detail["field"]): detail for detail in details}
        for field, _, _ in ordered_assignments:
            detail = details_by_field[field]
            explanation = f"Correct table: {detail['answer']}. {detail['explanation']}"
            render_feedback(str(detail["field"]), bool(detail["correct"]), explanation, str(detail["selected"]))
        if correct:
            st.subheader("The normalized structure")
            render_schema()
            st.markdown(
                '<div class="principle"><strong>Normal forms in the redesign</strong> Separate line rows eliminate repeating product groups (1NF). Product facts leave the line table (2NF). Customer facts leave the order table (3NF).</div>',
                unsafe_allow_html=True,
            )
            st.button("Continue to the E-R model", type="primary", width="stretch", on_click=set_stage, args=(4,))


def render_er() -> None:
    st.markdown('<div class="eyebrow">Step 4</div>', unsafe_allow_html=True)
    st.header("Connect the entities")
    st.markdown('<p class="lead">The junction table resolves the conceptual many-to-many relationship between Orders and Products into two one-to-many relationships.</p>', unsafe_allow_html=True)
    response = dict(st.session_state.dm_er)
    draft = dict(st.session_state.dm_drafts["er"])
    response_correct = bool(response) and evaluate_er(response)[0]
    if not response_correct:
        if response:
            st.info("Revise any relationship below, then select Check revised answers.")
        answers = {}
        for item_id, label, explanation, _ in ER_PROMPTS:
            options = ER_FOREIGN_KEY_OPTIONS if item_id == "foreign_keys" else ER_RELATIONSHIP_OPTIONS
            widget_key = f"widget_dm_er_{item_id}"
            answers[item_id] = st.radio(
                label,
                options,
                index=selected_index(options, draft.get(item_id)),
                key=widget_key,
                help=explanation,
                horizontal=item_id != "foreign_keys",
                on_change=save_draft,
                args=("er", item_id, widget_key),
            )
        button_label = "Check revised answers" if response else "Check the E-R model"
        submitted = st.button(button_label, type="primary", width="stretch")
        if submitted:
            if any(value is None for value in answers.values()):
                st.warning("Complete all four model choices before checking your work.")
            else:
                response = {key: str(value) for key, value in answers.items()}
                replace_draft("er", response)
                st.session_state.dm_er = response
                record_attempt(st.session_state, "er")
                if not evaluate_er(response)[0]:
                    st.rerun()

    if response:
        correct, details = evaluate_er(response)
        for detail in details:
            explanation = f"Correct answer: {detail['answer']}. {detail['explanation']}"
            render_feedback(str(detail["label"]), bool(detail["correct"]), explanation, str(detail["selected"]))
        if correct:
            st.markdown(
                """
                <div class="diagram" aria-label="Entity relationship model">
                  <div class="entity">Customers</div><div class="connector">1 → many</div><div class="entity">Orders</div><div class="connector">1 → many</div><div class="entity">OrderLines</div>
                </div>
                <div class="diagram" aria-label="Product to order line relationship">
                  <div class="entity">Products</div><div class="connector">1 → many</div><div class="entity">OrderLines</div><div class="connector">many lines reconstruct</div><div class="entity">One order</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button("Continue to the REA model", type="primary", width="stretch", on_click=set_stage, args=(5,))


def render_rea() -> None:
    st.markdown('<div class="eyebrow">Step 5</div>', unsafe_allow_html=True)
    st.header("Explain the economic exchange")
    st.markdown(
        '<p class="lead"><strong>Your task:</strong> Classify each element as a resource, event, or agent. REA shifts attention from table storage to what changes economically, what action causes the change, and who participates.</p>',
        unsafe_allow_html=True,
    )
    response = dict(st.session_state.dm_rea)
    draft = dict(st.session_state.dm_drafts["rea"])
    ordered_items = shuffled(REA_ITEMS, "rea-question-order")
    response_correct = bool(response) and evaluate_rea(response)[0]
    if not response_correct:
        if response:
            st.info("Revise any classification below, then select Check revised answers.")
        answers = {}
        columns = st.columns(2)
        for index, (label, _, _) in enumerate(ordered_items):
            widget_key = f"widget_dm_rea_{label.lower().replace(' ', '_')}"
            with columns[index % 2]:
                answers[label] = st.selectbox(
                    f"{label} is a",
                    REA_OPTIONS,
                    index=selected_index(REA_OPTIONS, draft.get(label)),
                    key=widget_key,
                    placeholder="Choose a category",
                    on_change=save_draft,
                    args=("rea", label, widget_key),
                )
        button_label = "Check revised answers" if response else "Check the REA classifications"
        submitted = st.button(button_label, type="primary", width="stretch")
        if submitted:
            if any(value is None for value in answers.values()):
                st.warning("Classify all six elements before checking the model.")
            else:
                response = {key: str(value) for key, value in answers.items()}
                replace_draft("rea", response)
                st.session_state.dm_rea = response
                record_attempt(st.session_state, "rea")
                if not evaluate_rea(response)[0]:
                    st.rerun()

    if response:
        correct, details = evaluate_rea(response)
        details_by_label = {str(detail["label"]): detail for detail in details}
        for label, _, _ in ordered_items:
            detail = details_by_label[label]
            explanation = f"Correct category: {detail['answer']}. {detail['explanation']}"
            render_feedback(str(detail["label"]), bool(detail["correct"]), explanation, str(detail["selected"]))
        if correct:
            st.subheader("The exchange, organized around its two events")
            st.markdown(
                """
                <div class="rea-example" aria-label="REA model organized by sale and cash receipt events">
                  <section class="rea-event-card">
                    <div class="rea-event-label">GIVE EVENT</div>
                    <h4>Sale</h4>
                    <div><strong>Participating agents</strong><span>Customer + Employee</span></div>
                    <div><strong>Resource effect</strong><span>Inventory decreases</span></div>
                  </section>
                  <div class="rea-duality"><span>duality</span><strong>Sale ↔ Cash Receipt</strong></div>
                  <section class="rea-event-card">
                    <div class="rea-event-label">RECEIVE EVENT</div>
                    <h4>Cash Receipt</h4>
                    <div><strong>Participating agents</strong><span>Customer + Employee</span></div>
                    <div><strong>Resource effect</strong><span>Cash increases</span></div>
                  </section>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Customer is the external agent; Employee is the internal agent. Both participate in each event in this simplified order-to-cash model.")
            st.button("Complete the model review", type="primary", width="stretch", on_click=set_stage, args=(6,))


def render_debrief() -> None:
    st.markdown('<div class="eyebrow">Model complete</div>', unsafe_allow_html=True)
    st.header("The design can now answer accounting questions without duplicating the facts")
    st.success("You established the grain, removed the anomaly-producing repetitions, connected the tables, and explained the exchange through REA.")
    st.subheader("Original flat export")
    render_raw_table()
    st.caption("The export is easy to read, but each row mixes customer, order, product, and order-line facts.")
    st.subheader("Redesigned normalized structure")
    render_schema()
    st.markdown(
        """
        <div class="comparison-grid">
          <section class="comparison-card problem">
            <div class="comparison-label">ORIGINAL DESIGN</div>
            <h4>Facts repeat across transaction rows</h4>
            <p>Customer names and cities, product descriptions and standard prices, and order dates appear every time a related line appears. One missed edit can create conflicting versions of the same fact; deleting a last line can erase facts that should remain.</p>
          </section>
          <section class="comparison-card better">
            <div class="comparison-label">NORMALIZED DESIGN</div>
            <h4>Each fact has one authoritative home</h4>
            <p>Primary keys identify the master and transaction records. Foreign keys reconnect them when a report needs the full story. Quantity and the actual price charged remain on OrderLines because they describe that specific sale.</p>
          </section>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="principle"><strong>Why this is better</strong> Normalization does not discard information. It stores each fact at the correct grain, reduces inconsistent updates, allows customers and products to exist before a sale, preserves master data when transactions are removed, and still reconstructs the original view through joins.</div>',
        unsafe_allow_html=True,
    )
    st.subheader("How the three views work together")
    st.markdown(
        "The normalized schema decides where each fact is stored. The E-R model shows how records reconnect through primary and foreign keys. The REA model explains why those records exist: a sale reduces inventory, a cash receipt increases cash, and internal and external agents participate in the events."
    )
    st.markdown(
        '<div class="principle"><strong>Reporting implication</strong> Sales are reconstructed from OrderLines as Quantity × ActualUnitPrice. A receivable analysis would compare fulfilled orders with their related cash-receipt records rather than relying on a duplicated order total.</div>',
        unsafe_allow_html=True,
    )
    attempts = st.session_state.dm_attempts
    revisions = sum(max(0, value - 1) for value in attempts.values())
    col1, col2, col3 = st.columns(3)
    col1.metric("Design stages completed", "5 of 5")
    col2.metric("Reasoning checks", sum(attempts.values()))
    col3.metric("Revisions", revisions)
    st.caption("Keep this tab or bookmark its current URL if you want to return to this completed model.")


st.markdown(APP_CSS, unsafe_allow_html=True)
