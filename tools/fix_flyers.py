#!/usr/bin/env python3
"""修正飛行寶可夢的三個問題：

1. 飛行時翅膀不扇 → 依模型真實骨骼重寫 `animation.poke_<id>.fly`（以翅膀根部為主、子節點跟隨）
2. 飛得太快 → 調降 movement / follow_owner 速度
3. 地面跟隨時往天上飄 → 縮小 float_wander 的垂直範圍與 y_offset

用法：
  python3 tools/fix_flyers.py packs/pokemon [--dry-run]
"""
import json
import os
import re
import sys

WING_RE = re.compile(r"wing", re.I)          # 只認 wing，避免尾巴羽毛跟著亂飛
OPEN_RE = re.compile(r"open|air", re.I)
CONTAINER_RE = re.compile(r"^(wings|wings_open|wings_closed|wings_folded|wings_air)$", re.I)
MAX_CHILD_AMP_COUNT = 4     # 每組翅膀最多再帶 4 根子骨
ARM_RE = re.compile(r"^(arm|arm_left|arm_right|arm\d+|hand.*)$", re.I)

# 動畫參數（玩家可調）
FLAP_LEN = 0.6          # 一次完整扇翅 0.6 秒
ROOT_AMP = 30           # 翅膀根部 ±30°
CHILD_AMP = 11          # 子骨 ±11°
BODY_BOB = 0.9          # 身體上下浮動（像素）
TAIL_AMP = 6

SPEED = {
    "movement": 0.32,       # 原本 0.6
    "follow_multiplier": 0.85,   # 原本 1.4
    "float_wander": {"xz_dist": 8, "y_dist": 2, "y_offset": 0.8, "float_duration": [2.0, 4.0]},
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)


def flyer_ids(bp_dir):
    ids = []
    for fn in sorted(os.listdir(os.path.join(bp_dir, "entities"))):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(bp_dir, "entities", fn)
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        if "navigation.fly" in raw:
            ids.append(fn[:-5])
    return ids


def collect_geometries(rp_dir):
    geos = {}
    root = os.path.join(rp_dir, "models")
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".geo.json"):
                continue
            try:
                data = load(os.path.join(dirpath, fn))
            except Exception:
                continue
            for g in data.get("minecraft:geometry", []):
                ident = g.get("description", {}).get("identifier")
                if ident:
                    geos[ident] = g
    return geos


def side_of(bone):
    name = bone["name"].lower()
    if "left" in name or name.endswith("_l") or re.search(r"_l\d*$", name):
        return "left"
    if "right" in name or name.endswith("_r") or re.search(r"_r\d*$", name):
        return "right"
    pivot = bone.get("pivot", [0, 0, 0])
    return "left" if pivot[0] < 0 else "right"


def pick_bones(geo):
    """回傳 (根翅膀骨, 子翅膀骨)；找不到翅膀就退回手臂"""
    bones = geo.get("bones", [])
    by_name = {b["name"]: b for b in bones}
    children = {}
    for b in bones:
        parent = b.get("parent")
        if parent:
            children.setdefault(parent, set()).add(b["name"])

    wings = [b for b in bones if WING_RE.search(b["name"]) and not CONTAINER_RE.match(b["name"])]
    if wings:
        # 同時存在展開(open/air)與收合(closed/folded)兩組時，只動展開的那組
        opened = [b for b in wings if OPEN_RE.search(b["name"])]
        if opened:
            wings = opened
    if not wings:
        wings = [b for b in bones if ARM_RE.match(b["name"])]
    if not wings:
        return [], []

    wing_names = {b["name"] for b in wings}
    # 根：祖先裡沒有其他翅膀骨
    roots, kids = [], []
    for b in wings:
        anc, cur = [], b.get("parent")
        while cur:
            anc.append(cur)
            cur = by_name.get(cur, {}).get("parent")
        if any(a in wing_names for a in anc):
            kids.append(b)
        else:
            roots.append(b)
    return roots, kids


def keyframes(amp):
    """一個週期的正弦近似：0 → +A → 0 → -A → 0"""
    step = FLAP_LEN / 4.0
    return {
        "0.00": [0, 0, 0],
        f"{step:.2f}": [0, 0, amp],
        f"{step*2:.2f}": [0, 0, 0],
        f"{step*3:.2f}": [0, 0, -amp],
        f"{FLAP_LEN:.2f}": [0, 0, 0],
    }


def build_fly(geo):
    roots, kids = pick_bones(geo)
    if not roots:
        return None, [], []

    anim = {"animation_length": FLAP_LEN, "loop": True, "bones": {}}
    used = []
    for b in roots:
        sgn = 1 if side_of(b) == "left" else -1
        anim["bones"][b["name"]] = {"rotation": keyframes(ROOT_AMP * sgn)}
        used.append((b["name"], ROOT_AMP * sgn, "root"))
    for b in kids[:MAX_CHILD_AMP_COUNT * 2]:
        sgn = 1 if side_of(b) == "left" else -1
        anim["bones"][b["name"]] = {"rotation": keyframes(CHILD_AMP * sgn)}
        used.append((b["name"], CHILD_AMP * sgn, "child"))

    # 身體隨翅膀節奏上下浮，尾巴輕擺
    bones = geo.get("bones", [])
    for name in ("body", "torso", "root", "chest"):
        if any(b["name"] == name for b in bones):
            anim["bones"][name] = {
                "position": {
                    "0.00": [0, 0, 0],
                    f"{FLAP_LEN/2:.2f}": [0, BODY_BOB, 0],
                    f"{FLAP_LEN:.2f}": [0, 0, 0],
                }
            }
            break
    for b in bones:
        if re.match(r"^tail(_\d+)?$|^tail$|^tail1$", b["name"], re.I):
            anim["bones"][b["name"]] = {
                "rotation": {
                    "0.00": [0, 0, 0],
                    f"{FLAP_LEN/2:.2f}": [0, TAIL_AMP, 0],
                    f"{FLAP_LEN:.2f}": [0, 0, 0],
                }
            }
            break
    return anim, used, roots


def fix_bp_entities(bp_dir, ids, dry):
    changed = []
    for pid in ids:
        path = os.path.join(bp_dir, "entities", f"{pid}.json")
        ent = load(path)
        comps = ent["minecraft:entity"]["components"]
        before = json.dumps(comps, sort_keys=True)

        if "minecraft:movement" in comps:
            comps["minecraft:movement"]["value"] = SPEED["movement"]
        if "minecraft:behavior.follow_owner" in comps:
            fo = comps["minecraft:behavior.follow_owner"]
            fo["speed_multiplier"] = SPEED["follow_multiplier"]
            fo["start_distance"] = max(fo.get("start_distance", 6), 8)
            fo["stop_distance"] = max(fo.get("stop_distance", 2.5), 3.5)
        if "minecraft:behavior.float_wander" in comps:
            fw = comps["minecraft:behavior.float_wander"]
            fw.update(SPEED["float_wander"])

        if json.dumps(comps, sort_keys=True) != before:
            changed.append(pid)
            if not dry:
                save(path, ent)
    return changed


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    pack = sys.argv[1].rstrip("/")
    dry = "--dry-run" in sys.argv

    bp_dir = os.path.join(pack, "bp")
    rp_dir = os.path.join(pack, "rp")
    ids = flyer_ids(bp_dir)
    print(f"飛行實體 {len(ids)} 個（含異色）")

    geos = collect_geometries(rp_dir)
    print(f"幾何體 {len(geos)} 個")

    # 以本體（非 _shiny）產生動畫，異色共用同一條
    base_ids = [i for i in ids if not i.endswith("_shiny")]
    anim_files = {}
    written = 0
    for pid in base_ids:
        ce_path = os.path.join(rp_dir, "entity", f"{pid}.entity.json")
        if not os.path.exists(ce_path):
            print(f"  {pid}: 缺 client entity，跳過")
            continue
        desc = load(ce_path)["minecraft:client_entity"]["description"]
        gid = desc.get("geometry", {}).get("default")
        geo = geos.get(gid)
        if not geo:
            print(f"  {pid}: geometry {gid} 找不到，跳過")
            continue
        anim, used, roots = build_fly(geo)
        if not anim:
            print(f"  {pid}: 沒有翅膀/手臂骨骼，跳過")
            continue

        anim_path = os.path.join(rp_dir, "animations", f"{pid}.animations.json")
        data = load(anim_path) if os.path.exists(anim_path) else {"format_version": "1.8.0", "animations": {}}
        key = f"animation.poke_{pid}.fly"
        old = data["animations"].get(key, {})
        data["animations"][key] = anim

        # 確保 client entity 有綁 fly
        if "fly" not in desc.get("animations", {}):
            desc.setdefault("animations", {})["fly"] = key
            ce = load(ce_path)
            ce["minecraft:client_entity"]["description"] = desc
            if not dry:
                save(ce_path, ce)
            print(f"  {pid}: client entity 補上 fly 綁定")
        animate = desc.get("scripts", {}).get("animate", [])
        flat = [a if isinstance(a, str) else k for a in animate for k in ([a] if isinstance(a, str) else a.keys())]
        if "fly" not in flat:
            ce = load(ce_path)
            ce["minecraft:client_entity"]["description"].setdefault("scripts", {})["animate"] = ["fly"] + animate
            if not dry:
                save(ce_path, ce)
            print(f"  {pid}: animate 清單補上 fly")

        if old != anim and not dry:
            save(anim_path, data)
            written += 1
        print(f"  {pid}: 翅膀骨 {len(roots)} 根 → {[u[0] for u in used][:6]}{' ...' if len(used) > 6 else ''} (共 {len(used)} 根)")

    bp_changed = fix_bp_entities(bp_dir, ids, dry)
    print(f"\nBP 速度調整：{len(bp_changed)} 個實體檔")
    print(f"RP 動畫重寫：{written} 個檔")
    if dry:
        print("（dry-run，未寫入）")


if __name__ == "__main__":
    main()
