"""Navigation regression checks independent of Streamlit runtime."""

import copy
import unittest
from browser.config import PACKAGE, STAGE_KEY
from browser.navigation import VIEW_KEY, frontier, move, restore_view, positions


class BrowserNavigationTests(unittest.TestCase):
    def test_future_views_are_rejected_without_earning_progress(self):
        state = {STAGE_KEY: 0}
        for raw in ["99", "-1", "invalid", None]:
            restore_view(state, raw)
            self.assertEqual(state[VIEW_KEY], 0)
            self.assertFalse(move(state, 1))
            self.assertEqual(state[STAGE_KEY], 0)

    def test_review_only_changes_view_and_scroll(self):
        state = {
            STAGE_KEY: 1,
            "bbc_inbox_index": 2,
            "answers": {"saved": "answer"},
            "attempts": 3,
            "drafts": {"unfinished": "choice"},
        }
        restore_view(state, None)
        earned = frontier(state)
        before = copy.deepcopy(state)
        for _ in range(earned):
            self.assertTrue(move(state, -1))
        self.assertFalse(move(state, -1))
        for _ in range(earned):
            self.assertTrue(move(state, 1))
        self.assertFalse(move(state, 1))
        for key, value in before.items():
            self.assertEqual(state[key], value)
        self.assertEqual(frontier(state), earned)

    def test_every_meaningful_page_has_a_unique_position(self):
        pages = positions()
        self.assertEqual(len(pages), len(set(pages)))
        self.assertEqual(pages[0], (0, 0))
        if PACKAGE == "balanced_books":
            self.assertGreater(len(pages), 20)
