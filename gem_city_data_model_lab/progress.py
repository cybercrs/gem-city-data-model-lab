"""Anonymous, validated URL progress for the data-model activity."""

from __future__ import annotations

import base64
import json
import secrets
import zlib
from collections.abc import MutableMapping
from typing import Any

from .case_data import (
    ANOMALIES,
    ANOMALY_OPTIONS,
    ER_FOREIGN_KEY_OPTIONS,
    ER_PROMPTS,
    ER_RELATIONSHIP_OPTIONS,
    FIELD_ASSIGNMENTS,
    GRAIN_OPTIONS,
    KEY_OPTIONS,
    REA_ITEMS,
    REA_OPTIONS,
    TABLE_OPTIONS,
)
from .engine import is_correct_stage

SNAPSHOT_PARAM = "progress"
SNAPSHOT_VERSION = 2
MAX_TOKEN_LENGTH = 8_000
MAX_JSON_BYTES = 16_000

STAGE_KEYS = {
    1: "dm_grain",
    2: "dm_anomalies",
    3: "dm_normalization",
    4: "dm_er",
    5: "dm_rea",
}


def activity_defaults() -> dict[str, Any]:
    return {
        "dm_stage": 0,
        "dm_shuffle_seed": secrets.randbits(63),
        "dm_drafts": {
            "grain": {},
            "anomalies": {},
            "normalization": {},
            "er": {},
            "rea": {},
        },
        "dm_grain": {},
        "dm_anomalies": {},
        "dm_normalization": {},
        "dm_er": {},
        "dm_rea": {},
        "dm_attempts": {},
        "dm_scroll_to_top": False,
    }


def _encode(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode("ascii").rstrip("=")


def _decode(token: str) -> object:
    padding = "=" * (-len(token) % 4)
    compressed = base64.b64decode(token + padding, altchars=b"-_", validate=True)
    decompressor = zlib.decompressobj()
    raw = decompressor.decompress(compressed, MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES or decompressor.unconsumed_tail:
        raise ValueError("Snapshot too large")
    raw += decompressor.flush(MAX_JSON_BYTES + 1 - len(raw))
    if len(raw) > MAX_JSON_BYTES or decompressor.unused_data:
        raise ValueError("Invalid snapshot")
    return json.loads(raw.decode("utf-8"))


def _string_map(raw: object, allowed_keys: set[str], choices: tuple[str, ...]) -> dict[str, str]:
    if not isinstance(raw, dict) or set(raw) - allowed_keys:
        raise ValueError("Invalid response map")
    if any(not isinstance(value, str) or value not in choices for value in raw.values()):
        raise ValueError("Invalid response")
    return dict(raw)


def validate_snapshot(raw: object) -> dict[str, Any]:
    expected = {"v", "s", "o", "d", "g", "a", "n", "e", "r", "t"}
    if not isinstance(raw, dict) or set(raw) != expected or raw["v"] != SNAPSHOT_VERSION:
        raise ValueError("Unsupported snapshot")
    stage = raw["s"]
    if type(stage) is not int or not 0 <= stage <= 6:
        raise ValueError("Invalid stage")
    shuffle_seed = raw["o"]
    if type(shuffle_seed) is not int or not 0 <= shuffle_seed < 2**63:
        raise ValueError("Invalid shuffle seed")

    grain = _string_map(raw["g"], {"grain", "key"}, tuple(GRAIN_OPTIONS) + tuple(KEY_OPTIONS))
    if "grain" in grain and grain["grain"] not in GRAIN_OPTIONS:
        raise ValueError("Invalid grain")
    if "key" in grain and grain["key"] not in KEY_OPTIONS:
        raise ValueError("Invalid key")
    anomalies = _string_map(raw["a"], {item["id"] for item in ANOMALIES}, ANOMALY_OPTIONS)
    normalization = _string_map(raw["n"], {field for field, _, _ in FIELD_ASSIGNMENTS}, TABLE_OPTIONS)
    er = _string_map(
        raw["e"],
        {item_id for item_id, _, _, _ in ER_PROMPTS},
        tuple(ER_RELATIONSHIP_OPTIONS) + tuple(ER_FOREIGN_KEY_OPTIONS),
    )
    rea = _string_map(raw["r"], {label for label, _, _ in REA_ITEMS}, REA_OPTIONS)

    attempts = raw["t"]
    if not isinstance(attempts, dict) or set(attempts) - {"grain", "anomalies", "normalization", "er", "rea"}:
        raise ValueError("Invalid attempts")
    if any(type(value) is not int or not 1 <= value <= 99 for value in attempts.values()):
        raise ValueError("Invalid attempt count")

    draft_specs = {
        "grain": (1, {"grain": GRAIN_OPTIONS, "key": KEY_OPTIONS}, grain),
        "anomalies": (
            2,
            {item["id"]: ANOMALY_OPTIONS for item in ANOMALIES},
            anomalies,
        ),
        "normalization": (
            3,
            {field: TABLE_OPTIONS for field, _, _ in FIELD_ASSIGNMENTS},
            normalization,
        ),
        "er": (
            4,
            {
                item_id: ER_FOREIGN_KEY_OPTIONS if item_id == "foreign_keys" else ER_RELATIONSHIP_OPTIONS
                for item_id, _, _, _ in ER_PROMPTS
            },
            er,
        ),
        "rea": (5, {label: REA_OPTIONS for label, _, _ in REA_ITEMS}, rea),
    }
    raw_drafts = raw["d"]
    if not isinstance(raw_drafts, dict) or set(raw_drafts) != set(draft_specs):
        raise ValueError("Invalid draft groups")
    drafts: dict[str, dict[str, str]] = {}
    for group, (group_stage, choices_by_key, submitted_response) in draft_specs.items():
        raw_group = raw_drafts[group]
        if not isinstance(raw_group, dict) or set(raw_group) - set(choices_by_key):
            raise ValueError("Invalid draft answers")
        normalized_group: dict[str, str] = {}
        for key, value in raw_group.items():
            if not isinstance(value, str) or value not in choices_by_key[key]:
                raise ValueError("Invalid draft choice")
            normalized_group[key] = value
        if group_stage > stage and normalized_group:
            raise ValueError("Future draft is not allowed")
        if submitted_response and normalized_group != submitted_response:
            raise ValueError("Draft and submitted response disagree")
        drafts[group] = normalized_group

    restored = {
        "dm_stage": stage,
        "dm_shuffle_seed": shuffle_seed,
        "dm_drafts": drafts,
        "dm_grain": grain,
        "dm_anomalies": anomalies,
        "dm_normalization": normalization,
        "dm_er": er,
        "dm_rea": rea,
        "dm_attempts": dict(attempts),
    }
    for prior_stage in range(1, min(stage, 6)):
        if not is_correct_stage(prior_stage, restored[STAGE_KEYS[prior_stage]]):
            raise ValueError("A prior stage is incomplete")
    return restored


def snapshot_from_state(state: MutableMapping[str, Any]) -> dict[str, Any]:
    return {
        "v": SNAPSHOT_VERSION,
        "s": state["dm_stage"],
        "o": state["dm_shuffle_seed"],
        "d": state["dm_drafts"],
        "g": state["dm_grain"],
        "a": state["dm_anomalies"],
        "n": state["dm_normalization"],
        "e": state["dm_er"],
        "r": state["dm_rea"],
        "t": state["dm_attempts"],
    }


def encode_state(state: MutableMapping[str, Any]) -> str:
    return _encode(snapshot_from_state(state))


def decode_snapshot(token: object) -> dict[str, Any] | None:
    if not isinstance(token, str) or not token or len(token) > MAX_TOKEN_LENGTH:
        return None
    try:
        return validate_snapshot(_decode(token))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, zlib.error):
        return None


def restore_session_state(state: MutableMapping[str, Any], token: object) -> bool:
    restored = decode_snapshot(token)
    if restored is None:
        return False
    state.update(restored)
    return True


def sync_progress_query(state: MutableMapping[str, Any], query_params: MutableMapping[str, Any]) -> None:
    token = encode_state(state)
    current = query_params.get(SNAPSHOT_PARAM)
    if isinstance(current, list):
        current = current[0] if current else None
    if current != token:
        query_params[SNAPSHOT_PARAM] = token


def reset_saved_progress(state: MutableMapping[str, Any], query_params: MutableMapping[str, Any]) -> None:
    for key in list(state):
        if key.startswith("dm_") or key.startswith("widget_dm_"):
            del state[key]
    state.update(activity_defaults())
    query_params[SNAPSHOT_PARAM] = encode_state(state)


def record_attempt(state: MutableMapping[str, Any], key: str) -> None:
    attempts = dict(state["dm_attempts"])
    attempts[key] = attempts.get(key, 0) + 1
    state["dm_attempts"] = attempts
