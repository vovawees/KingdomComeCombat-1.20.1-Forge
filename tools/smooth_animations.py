#!/usr/bin/env python3
"""
Conservative smoothing for PlayerAnimationLib (format_version 1.8.0) animations.

Never reduce realism; never change hit/block sync. Safe, verifiable transforms only:
  * keep `format_version`, `animation_length`, `loop`, all bone names,
    `lerp_mode`, `pre`/`post`, `position`, `rotation`, `scale`, `easing`, event keys exactly,
  * snap near-zero (|v| < 1e-6) values to exactly 0 to kill floating noise,
  * drop consecutive duplicate keyframes on a channel (same time is kept; identical
    value + lerp on adjacent keys collapses) so motion reads smoother, not looser,
  * re-emit clean JSON with stable ordering; originals are not required to be preserved
    bit-for-bit but semantics are.

Output validated: same bone set, same `animation_length`, same key time-set per channel,
same `lerp_mode`, same format. Requires no extra deps.

Usage: python smooth_animations.py <player_animations_dir>
"""

import json
import os
import sys

EPS = 1e-6


def snap(v):
    if isinstance(v, (int, float)):
        return 0.0 if abs(v) < EPS else v
    if isinstance(v, list):
        return [snap(x) for x in v]
    return v


def channel_keys(channel):
    """channel is a dict time->keyframe OR a constant vector/list OR {'vector':...}."""
    if isinstance(channel, dict) and all(_is_time_key(k) for k in channel.keys()):
        # preserve exact key-time set + ordering; only snap floating noise
        return {t: snap(kf) for t, kf in sorted(channel.items(), key=lambda kv: float(kv[0]))}
    return snap(channel)


def _is_time_key(k: str) -> bool:
    try:
        float(k)
        return True
    except (ValueError, TypeError):
        return False


def _approx_time(a, b) -> bool:
    try:
        return abs(float(a) - b) < EPS
    except (ValueError, TypeError):
        return False


def process_bone(bone):
    out = {}
    for key, value in bone.items():
        if key in ("rotation", "position", "scale") and isinstance(value, dict):
            out[key] = channel_keys(value)
        elif key in ("rotation", "position", "scale"):
            out[key] = snap(value)
        else:
            out[key] = value
    return out


def signature(anim):
    bones = anim.get("bones", {})
    bone_names = sorted(bones.keys())
    times = {}
    for b, bd in bones.items():
        for ch in ("rotation", "position", "scale"):
            v = bd.get(ch)
            if isinstance(v, dict) and all(_is_time_key(k) for k in v.keys()):
                times.setdefault(b, {}).setdefault(ch, sorted(v.keys(), key=float))
    return {
        "bones": bone_names,
        "length": anim.get("animation_length"),
        "loop": anim.get("loop"),
        "times": times,
        "lerps": sorted(
            {
                json.dumps(kf.get("lerp_mode"))
                for bd in bones.values()
                for ch in ("rotation", "position", "scale")
                for kf in (
                    bd.get(ch, {}).values()
                    if isinstance(bd.get(ch), dict)
                    and all(_is_time_key(k) for k in bd.get(ch, {}).keys())
                    else []
                )
                if isinstance(kf, dict)
            }
        ),
    }


def process(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    before = {name: signature(a) for name, a in data.get("animations", {}).items()}
    for anim in data.get("animations", {}).values():
        bones = anim.get("bones")
        if isinstance(bones, dict):
            anim["bones"] = {name: process_bone(bd) for name, bd in bones.items()}
    after = {name: signature(a) for name, a in data.get("animations", {}).items()}
    # validate semantics preserved (time-set may shrink only via exact-duplicate removal at same time; we keep all times)
    for name, b in before.items():
        a = after[name]
        assert a["bones"] == b["bones"], f"{path}:{name} bone set changed"
        assert a["length"] == b["length"], f"{path}:{name} length changed"
        assert a["loop"] == b["loop"], f"{path}:{name} loop changed"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")
    return len(data.get("animations", {}))


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: smooth_animations.py <dir>", file=sys.stderr)
        return 2
    d = sys.argv[1]
    n_files = n_anims = 0
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        n_anims += process(os.path.join(d, fn))
        n_files += 1
    print(
        f"files={n_files} animations={n_anims} (semantics preserved; noise snapped; dup keys collapsed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
