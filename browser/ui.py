"""Browser-only widget adapters. Review renders expose no mutation controls."""

from contextlib import contextmanager
import streamlit as st

CSS = """<style>
.st-key-browser_navigation button {width:44px;height:44px;min-width:44px;min-height:44px;position:relative;padding:0;border:1px solid #C5CCD8;border-radius:6px;background:transparent;color:#59677A;box-shadow:none;}
.st-key-browser_navigation button::before {content:"";position:absolute;width:20px;height:20px;top:50%;left:50%;transform:translate(-50%,-50%);background:center / contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2359677A' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M19 12H5m0 0 7-7m-7 7 7 7'/%3E%3C/svg%3E");}
.st-key-browser_forward button::before {transform:translate(-50%,-50%) rotate(180deg);}
.st-key-browser_navigation button p {position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0;}
.st-key-browser_navigation button:hover:not(:disabled) {background:#E6EAF1;border-color:#A7B2C3;}
.st-key-browser_navigation button:focus-visible {outline:2px solid #003087;outline-offset:2px;}
.st-key-browser_navigation button:disabled {opacity:.55;}
.st-key-browser_navigation [data-testid="stCaptionContainer"] p {font-size:.75rem;margin:0;color:#59677A;}
</style>"""


class LiveUI:
    """Commit session-only form drafts on change, retaining original submit actions."""

    def __init__(self):
        self.form_id = None

    def __getattr__(self, name):
        return getattr(st, name)

    @contextmanager
    def form(self, key, **kwargs):
        self.form_id = key
        try:
            with st.container():
                yield
        finally:
            self.form_id = None

    def form_submit_button(self, *args, **kwargs):
        return st.button(*args, **kwargs)

    def radio(self, label, *args, **kwargs):
        key = kwargs.get("key") or f"browser_draft_{self.form_id}_{label}"
        kwargs["key"] = key
        drafts = st.session_state.setdefault("browser_form_drafts", {})
        if key not in st.session_state and key in drafts:
            st.session_state[key] = drafts[key]

        def save():
            st.session_state.browser_form_drafts[key] = st.session_state[key]

        kwargs["on_change"] = save
        return st.radio(label, *args, **kwargs)


class ReviewUI(LiveUI):
    def __getattr__(self, name):
        return getattr(st, name)

    def button(self, *args, **kwargs):
        return False

    def form_submit_button(self, *args, **kwargs):
        return False

    def _input(self, name, *args, **kwargs):
        kwargs.update(disabled=True, on_change=None, args=None, kwargs=None)
        # Use distinct review widget IDs; leave the current draft widgets intact.
        if "key" in kwargs:
            original_key = kwargs["key"]
            if name == "text_area":
                kwargs["value"] = st.session_state.get(original_key, "")
            kwargs["key"] = "review_" + original_key
        elif name == "radio" and self.form_id:
            key = f"browser_draft_{self.form_id}_{args[0]}"
            value = st.session_state.get("browser_form_drafts", {}).get(key)
            options = args[1] if len(args) > 1 else kwargs.get("options", [])
            if value in options:
                kwargs["index"] = list(options).index(value)
            kwargs["key"] = "review_" + key
        return getattr(st, name)(*args, **kwargs)

    def radio(self, *args, **kwargs):
        return self._input("radio", *args, **kwargs)

    def selectbox(self, *args, **kwargs):
        return self._input("selectbox", *args, **kwargs)

    def text_area(self, *args, **kwargs):
        return self._input("text_area", *args, **kwargs)

    def number_input(self, *args, **kwargs):
        return self._input("number_input", *args, **kwargs)
