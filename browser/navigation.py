"""Keep the viewed page separate from the lesson's earned position."""

from browser.config import PACKAGE, STAGE_KEY

VIEW_KEY = "browser_view"
VIEW_PARAM = "view"


def positions():
    if PACKAGE == "balanced_books":
        from balanced_books.case_data import TRANSACTIONS, RECORDABLE_TRANSACTIONS

        return (
            [(0, 0)]
            + [(1, i) for i in range(len(TRANSACTIONS))]
            + [(2, i) for i in range(len(RECORDABLE_TRANSACTIONS))]
            + [(3, 0), (4, 0)]
        )
    from browser.config import RENDERERS

    return [(i, 0) for i in range(len(RENDERERS))]


def frontier(state):
    stage = state[STAGE_KEY]
    index = (
        state.get("bbc_inbox_index", 0)
        if stage == 1
        else state.get("bbc_equation_index", 0)
        if stage == 2
        else 0
    )
    return positions().index((stage, index if PACKAGE == "balanced_books" else 0))


def restore_view(state, raw):
    try:
        view = int(raw) if isinstance(raw, str) else -1
    except ValueError:
        view = -1
    state[VIEW_KEY] = view if 0 <= view <= frontier(state) else frontier(state)


def move(state, direction):
    if direction not in (-1, 1):
        raise ValueError("Use Back or Forward")
    view = state[VIEW_KEY] + direction
    if 0 <= view <= frontier(state):
        state[VIEW_KEY] = view
        state["browser_scroll"] = True
        return True
    return False


def display_position(state):
    return positions()[state[VIEW_KEY]]


def reviewing(state):
    return state[VIEW_KEY] < frontier(state)
