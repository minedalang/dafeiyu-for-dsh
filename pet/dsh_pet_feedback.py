# -*- coding: utf-8 -*-
"""DSH -> desktop pet presentation hints. No command execution, no network.

Only fixed semantic moods and existing animation assets may be selected.
Untrusted model-written text never chooses file paths or executable commands.
"""
from __future__ import annotations

import re
import json
import os
import time
import uuid
from pathlib import Path

MOODS = frozenset({"search", "watch", "think", "happy", "work", "idle"})
SCENE_STAGES = frozenset({"search", "browse", "play", "summarize"})

_ANIMATION_HINTS = {
    "search": ("寻找", "搜索", "观察", "好奇", "四处", "看书"),
    "watch": ("看电视", "观影", "观看", "看书", "注视", "思考"),
    "think": ("思考", "记录", "写代码", "工作"),
    "happy": ("开心", "庆祝", "跳舞", "欢呼", "蹦", "撒花"),
    "work": ("写代码", "工作", "记录", "敲", "思考"),
}

SCENE_MOODS = {
    "search": "search", "browse": "watch",
    "play": "watch", "summarize": "think",
}
SCENE_TEXTS = {
    "search": "正在B站找有趣的视频～",
    "browse": "正在B站浏览视频信息～",
    "play": "找到播放操作啦，看看有没有播起来～",
    "summarize": "让我整理一下刚才看到的内容～",
}


def select_existing_animation(mood: str, acts: list[str] | tuple[str, ...],
                              idles: list[str] | tuple[str, ...] = ()) -> str | None:
    """Pick *existing* assets, not hallucinated animation filenames.

    No fallback to arbitrary actions: if a mood is unsupported we only show a bubble.
    """
    if mood == "idle":
        return str(idles[0]) if idles else None
    candidates = [str(x) for x in acts if isinstance(x, str)]
    for hint in _ANIMATION_HINTS.get(mood, ()):
        for asset in candidates:
            if hint in asset:
                return asset
    return None


def clean_speech(value: object) -> str:
    if not isinstance(value, str):
        return ""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", value).strip()
    # Not a channel for raw page content, huge pastes or filesystem commands.
    return text[:90] if len(text) <= 90 else ""


def decode_pet_action(record: dict) -> tuple[str, str] | None:
    if not isinstance(record, dict) or record.get("event") != "pet/action":
        return None
    if record.get("action") != "express":
        return None
    mood = record.get("mood")
    if not isinstance(mood, str) or mood not in MOODS:
        return None
    speech = record.get("speech", "")
    if not isinstance(speech, str) or len(speech) > 90:
        return None
    return mood, clean_speech(speech)


def decode_bili_activity(record: dict) -> tuple[str, str] | None:
    if not isinstance(record, dict) or record.get("event") != "dsh/activity":
        return None
    if record.get("site") != "bilibili":
        return None
    stage = record.get("stage")
    if not isinstance(stage, str) or stage not in SCENE_STAGES:
        return None
    return SCENE_MOODS[stage], SCENE_TEXTS[stage]


def write_pet_action_ack(config_dir: Path, record: dict, status: str, detail: str) -> bool:
    """Write an atomic bounded local ack for a model-facing pet_action call.

    Only a canonical UUID from the bridge may be used as filename. Never treat
    the event as a path, execute it, or send it back to the model in full.
    """
    raw = record.get("requestId") if isinstance(record, dict) else None
    try:
        request_id = str(uuid.UUID(raw)) if isinstance(raw, str) else ""
        if request_id != raw:
            return False
    except (ValueError, TypeError, AttributeError):
        return False
    if status not in ("accepted", "rejected"):
        return False
    folder = Path(config_dir).parent / "dsh-pet-bridge" / "acks"
    ack = folder / (request_id + ".json")
    tmp = folder / (request_id + ".tmp")
    payload = {"status": status, "detail": str(detail)[:180], "ts": time.time()}
    try:
        folder.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, ack)
        return True
    except OSError:
        return False

# V8.2: DSH has already perceived the content; the pet validates and presents
# the model's chosen *existing* action without asking a second LLM to decide.
from typing import NamedTuple


class PetDirective(NamedTuple):
    mood: str
    speech: str
    animation: str
    duration_seconds: int
    priority: str


def decode_pet_directive(record: dict) -> PetDirective | None:
    legacy = decode_pet_action(record)
    if legacy is None:
        return None
    mood, speech = legacy
    animation = record.get('animation', '')
    duration = record.get('duration_seconds', 8)
    priority = record.get('priority', 'normal')
    if not isinstance(animation, str) or len(animation) > 120:
        return None
    # Never accept a path, a hidden file, a control code or external URI as
    # an animation. The actual asset-membership check happens at dispatch.
    if any(ch in animation for ch in ('/', '\\', '\x00', '\n', '\r')) or '..' in animation:
        return None
    if type(duration) is not int or not 3 <= duration <= 30:
        return None
    if priority not in ('ambient', 'normal', 'urgent'):
        return None
    if mood == 'idle' and animation:
        return None
    return PetDirective(mood, speech, animation, duration, priority)


def resolve_pet_animation(directive: PetDirective, acts: list[str] | tuple[str, ...],
                          idles: list[str] | tuple[str, ...] = ()) -> str | None:
    if directive.animation:
        # Exact membership only; no fuzzy matching for an explicit name.
        return directive.animation if directive.animation in acts else None
    return select_existing_animation(directive.mood, acts, idles)


def write_pet_animation_catalog(config_dir: Path, acts, idles=()) -> bool:
    """Publish an asset-name-only catalog for DSH pet_animations (atomic)."""
    folder = Path(config_dir).parent / 'dsh-pet-bridge'
    catalog = folder / 'pet-animations.json'
    tmp = folder / ('pet-animations.' + uuid.uuid4().hex + '.tmp')
    # No filenames/paths from untrusted data; no user/agent/chat content.
    def clean(names, limit):
        result = []
        for item in names or ():
            if (isinstance(item, str) and 0 < len(item) <= 120 and
                    not any(ch in item for ch in ('/', '\\', '\x00', '\r', '\n')) and
                    item not in result):
                result.append(item)
                if len(result) >= limit:
                    break
        return result
    try:
        folder.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({
            'schema': 1, 'updated_at': int(time.time()),
            'animations': clean(acts, 256), 'idles': clean(idles, 32),
        }, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, catalog)
        return True
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False
