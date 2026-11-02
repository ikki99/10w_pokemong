#!/usr/bin/env python3
"""依「模型實際骨骼」產生 walk / idle 動畫，並修正 client entity 的 geometry 對應。

兩個致命坑（都踩過）：
  1. 舊動畫用 leg_left / torso 這種想像中的骨骼名，實際模型叫 leg0..leg3 / body，
     名稱對不上 → 動畫對任何骨骼都不生效 → 看起來永遠靜止、手永遠伸著。
  2. client entity 寫 geometry.<id>_male，但模型檔 identifier 是 geometry.poke_<id>
     → 對不上，只能吃 fallback 模型。

規則：
  * 腿 / 臂 / 翅：只動「鏈條最上層」那根（子骨骼會跟著父骨骼走），避免幅度疊加。
  * 尾巴 / 耳朵：整條鏈都動，越末端幅度越小（甩尾才自然）。
  * 身體：上下呼吸 + 輕微左右擺；頭：小幅點頭。

用法：python3 fix_models_anim.py <rp_dir>
"""
import glob
import json
import math
import os
import re
import sys


def load_geo(path):
    g = json.load(open(path, encoding="utf-8"))
    if "minecraft:geometry" in g:
        g = g["minecraft:geometry"][0]
    return g


def parents_of(geo):
    """cobblemon 的 geo 用 `parent` 欄位（不是 children 陣列）——只讀 children 會讓整棵樹斷掉，
    腿/蛇身的「鏈條最上層」判斷就全錯。兩種寫法都吃。"""
    parent = {}
    for b in geo["bones"]:
        name = b["name"]
        parent.setdefault(name, None)
        if b.get("parent"):
            parent[name] = b["parent"]
        for c in b.get("children", []) or []:
            if isinstance(c, str):
                parent[c] = name
            elif isinstance(c, dict):
                parent[c["name"]] = name
    return parent


def depth_of(name, parent):
    d, cur, guard = 0, parent.get(name), 0
    while cur and guard < 40:
        d += 1
        cur = parent.get(cur)
        guard += 1
    return d


def side_of(name, idx):
    low = name.lower()
    if "left" in low or re.search(r"_l\d*$", low) or low.endswith("_l"):
        return 1
    if "right" in low or re.search(r"_r\d*$", low) or low.endswith("_r"):
        return -1
    return 1 if idx % 2 == 0 else -1


def classify(bones, with_cubes, parent):
    groups = {"legs": [], "arms": [], "wings": [], "tails": [], "ears": [], "bodies": [], "heads": [],
              "spines": [], "necks": [], "others": []}
    # 可以動畫的骨骼：自己有方塊，或有子孫帶方塊（例如 segment1 自己沒方塊但 boulder1 有）
    movable = set(with_cubes)
    # 祖先帶方塊 → 可以動
    for name in bones:
        cur, guard = parent.get(name), 0
        while cur and guard < 40:
            if cur in with_cubes:
                movable.add(name)
                break
            cur = parent.get(cur)
            guard += 1
    # 子孫帶方塊 → 也可以動（蛇身的 segment 自己沒方塊，方塊長在 boulder 上）
    kids = {}
    for child, par in parent.items():
        if par:
            kids.setdefault(par, []).append(child)
    def has_cube_desc(n, seen=None):
        seen = seen or set()
        if n in seen:
            return False
        seen.add(n)
        for c in kids.get(n, []):
            if c in with_cubes or has_cube_desc(c, seen):
                return True
        return False
    for name in bones:
        if name not in movable and has_cube_desc(name):
            movable.add(name)

    for name in bones:
        low = name.lower()
        if low.startswith("locator"):
            continue          # locator 是掛點，不要去動它
        if re.search(r"(^|_)(segment|vertebra|spine)\d*($|_)", low):
            groups["spines"].append(name)
        elif re.search(r"(^|_)neck\d*($|_)", low):
            groups["necks"].append(name)
        elif re.search(r"(^|_)(leg|foot|feet|paw|thigh|shin|toe)\d*($|_)", low):
            groups["legs"].append(name)
        elif re.search(r"(^|_)(arm|hand|claw|flipper)\d*($|_)", low):
            groups["arms"].append(name)
        elif re.search(r"(^|_)(wing|wings|fin|sail|feather|flap|blade)\d*($|_)", low):
            groups["wings"].append(name)
        elif re.search(r"(^|_)tail\d*($|_)", low):
            groups["tails"].append(name)
        elif re.search(r"(^|_)ear\d*($|_)", low):
            groups["ears"].append(name)
        elif re.search(r"(^|_)(body|torso|chest|belly|waist)\d*($|_)", low):
            groups["bodies"].append(name)
        elif re.search(r"(^|_)(head)\d*($|_)", low):
            groups["heads"].append(name)
        elif name in with_cubes:
            groups["others"].append(name)
    out = {}
    for k, lst in groups.items():
        lst = [b for b in lst if b in movable]
        if k in ("legs", "arms", "wings"):
            tops = []
            for b in lst:
                anc = parent.get(b)
                is_child = False
                guard = 0
                while anc and guard < 40:
                    if anc in lst:
                        is_child = True
                        break
                    anc = parent.get(anc)
                    guard += 1
                if not is_child:
                    tops.append(b)
            out[k] = tops or lst
        else:
            out[k] = sorted(lst, key=lambda n: depth_of(n, parent))
    return out


ARM_REST_DEG = 58.0   # 手臂從「平伸」往下收的角度（依 pivot 的 x 決定左右方向）


try:
    from poke_legendaries import LEGENDARY_SPECS as _LEG

    FLYERS = {x["id"] for x in _LEG if x.get("flyer")}
except Exception:                       # 沒有那份資料就當作沒有飛行物種
    FLYERS = set()


def R(vals):
    return {f"{t:.2f}": v for t, v in vals}


def compute_arm_rest(geo):
    """把「往兩側平伸」的手臂收下來。

    做法：看每條手臂骨鏈的「根部 pivot → 末端 pivot」方向向量，
    算出目前與水平的夾角，再轉到「往下斜一點」的目標角度。
      * +x 側：目標約 -70°（往下、略往外）
      * -x 側：目標約 -110°（對稱）
    末端用最深子孫的 pivot；沒有子孫就退而用方塊最外緣。
    回傳 {bone_name: z_degrees}
    """
    by_name = {b["name"]: b for b in geo["bones"]}
    kids = {}
    for b in geo["bones"]:
        par = b.get("parent")
        if par:
            kids.setdefault(par, []).append(b["name"])

    def tip_of(name):
        cur, guard, last = name, 0, None
        while cur and guard < 40:
            nxt = kids.get(cur) or []
            if not nxt:
                return cur
            # 選 pivot 最遠的子節點，沿鏈走
            cur = nxt[0]
            last = cur
            guard += 1
        return last or name

    out = {}
    for b in geo["bones"]:
        name = b["name"]
        if not re.search(r"(^|_)(arm|hand|claw)\d*($|_)", name.lower()):
            continue
        if not (b.get("cubes") or kids.get(name)):
            continue
        pivot = b.get("pivot") or [0, 0, 0]
        tip = by_name.get(tip_of(name), {})
        tp = tip.get("pivot") or [0, 0, 0]
        dx, dy = tp[0] - pivot[0], tp[1] - pivot[1]
        if abs(dx) < 0.3 and abs(dy) < 0.3:
            # 末端跟根部重疊 → 用方塊最外緣
            cubes = b.get("cubes") or []
            if cubes:
                c = max(cubes, key=lambda c: abs((c.get("origin") or [0])[0] - pivot[0]))
                o, sz = c.get("origin", [0, 0, 0]), c.get("size", [1, 1, 1])
                dx = (o[0] + sz[0] / 2) - pivot[0]
                dy = (o[1] + sz[1] / 2) - pivot[1]
        if abs(dx) < 0.2:
            continue                      # 已經接近垂直，不用收
        cur_deg = math.degrees(math.atan2(dy, dx))
        target = -70.0 if dx > 0 else -110.0
        delta = target - cur_deg
        while delta > 180:
            delta -= 360
        while delta < -180:
            delta += 360
        delta = max(-100.0, min(100.0, delta))
        if abs(delta) < 4:
            delta = 0.0
        # 實測發現這些模型的骨骼 z 軸方向跟推導相反（照推導寫會把手舉起來），
        # 所以統一取負號。換模型來源時要重新確認這一行。
        out[name] = round(-delta, 1)
    return out



def make_attack(g, arm_rest=None):
    """近戰攻擊動作（一次性 0.55 秒）：蓄力 → 揮擊 → 收回。

    手臂在垂下（arm_rest 的 z 角）基礎上只加 x 軸前後擺：
    負的 x 是往前揮（跟原版殭屍 attack_bare_hand 的 -90 同向）。
    沒有手臂的物種（伊布、妙蛙種子）改成整條身體衝撞 + 四腿蹬地。
    """
    arm_rest = arm_rest or {}
    bones = {}
    PUNCH = -85.0
    for i, b in enumerate(g["arms"]):
        z = arm_rest.get(b, 0.0)
        s = side_of(b, i)
        bones[b] = {"rotation": R([
            (0.00, [0, 0, z]),
            (0.15, [35 * s, 0, z]),      # 蓄力：往後拉
            (0.30, [PUNCH, 0, z]),       # 揮出去
            (0.42, [-55, 0, z]),
            (0.55, [0, 0, z]),
        ])}
    for b in g["bodies"][:2]:
        bones.setdefault(b, {"rotation": R([
            (0.00, [0, 0, 0]), (0.15, [-6, 0, 0]), (0.30, [14, 0, 0]),
            (0.42, [7, 0, 0]), (0.55, [0, 0, 0]),
        ])})
    for b in g["heads"][:2]:
        bones.setdefault(b, {"rotation": R([
            (0.00, [0, 0, 0]), (0.30, [12, 0, 0]), (0.55, [0, 0, 0]),
        ])})
    for b in g["tails"][:2]:
        bones.setdefault(b, {"rotation": R([
            (0.00, [0, 0, 0]), (0.30, [-12, 0, 0]), (0.55, [0, 0, 0]),
        ])})
    if not g["arms"]:
        # 沒有手臂 → 衝撞：身體前後、四腿蹬地
        for b in g["bodies"][:2]:
            bones[b] = {"rotation": R([
                (0.00, [0, 0, 0]), (0.12, [-9, 0, 0]), (0.26, [20, 0, 0]),
                (0.40, [8, 0, 0]), (0.55, [0, 0, 0]),
            ])}
        for b in g["legs"][:4]:
            bones.setdefault(b, {"rotation": R([
                (0.00, [0, 0, 0]), (0.12, [-28, 0, 0]), (0.26, [38, 0, 0]),
                (0.55, [0, 0, 0]),
            ])})
    return {"animation_length": 0.55, "bones": bones}


def make_fly(g, arm_rest=None):
    """飛行/懸停動畫（循環）。翅膀拍動、身體上下浮、尾巴拖尾擺動、腿收起。"""
    arm_rest = arm_rest or {}
    bones = {}
    period = 1.1
    for i, b in enumerate(g["wings"][:4]):
        s2 = side_of(b, i)
        bones[b] = {"rotation": R([
            (0.00, [0, 0, 0]),
            (0.28, [0, 0, 26 * s2]),
            (0.55, [0, 0, 0]),
            (0.83, [0, 0, -18 * s2]),
            (1.10, [0, 0, 0]),
        ])}
    for i, b in enumerate(g["arms"][:2]):
        z = arm_rest.get(b, 0.0)
        s2 = side_of(b, i)
        bones.setdefault(b, {"rotation": R([
            (0.00, [0, 0, z]),
            (0.55, [-10 * s2, 0, z + 8 * s2]),
            (1.10, [0, 0, z]),
        ])})
    for b in g["bodies"][:2]:
        bones.setdefault(b, {
            "position": R([(0.00, [0, 0, 0]), (0.55, [0, 1.6, 0]), (1.10, [0, 0, 0])]),
            "rotation": R([(0.00, [0, 0, 0]), (0.55, [2.5, 0, 0]), (1.10, [0, 0, 0])]),
        })
    for i, b in enumerate(g["tails"][:4]):
        amp = max(4.0, 14.0 - i * 3)
        bones.setdefault(b, {"rotation": R([
            (0.00, [0, 0, 0]), (0.55, [0, amp, 0]), (1.10, [0, 0, 0]),
        ])})
    for b in g["legs"][:4]:
        bones.setdefault(b, {"rotation": R([(0.00, [-28, 0, 0]), (1.10, [-28, 0, 0])])})
    return {"animation_length": round(period, 2), "loop": True, "bones": bones}


def make_walk(g, arm_rest=None):
    bones = {}
    for i, b in enumerate(g["legs"]):
        s = side_of(b, i)
        bones[b] = {"rotation": R([(0.0, [26 * s, 0, 0]), (0.25, [0, 0, 0]),
                                   (0.5, [-26 * s, 0, 0]), (0.75, [0, 0, 0]),
                                   (1.0, [26 * s, 0, 0])])}
    for i, b in enumerate(g["arms"]):
        s = side_of(b, i)
        z = (arm_rest or {}).get(b, 0.0)
        bones[b] = {"rotation": R([(0.0, [-20 * s, 0, z]), (0.5, [20 * s, 0, z]), (1.0, [-20 * s, 0, z])])}
    for i, b in enumerate(g["wings"]):
        s = side_of(b, i)
        bones[b] = {"rotation": R([(0.0, [0, 0, 24 * s]), (0.5, [0, 0, -20 * s]), (1.0, [0, 0, 24 * s])])}
    for i, b in enumerate(g["tails"]):
        amp = max(4, 16 - i * 5)
        bones[b] = {"rotation": R([(0.0, [0, amp, 0]), (0.5, [0, -amp, 0]), (1.0, [0, amp, 0])])}
    for i, b in enumerate(g["ears"]):
        s = side_of(b, i)
        bones[b] = {"rotation": R([(0.0, [-10, 0, 8 * s]), (0.5, [8, 0, -4 * s]), (1.0, [-10, 0, 8 * s])])}
    for i, b in enumerate(g["spines"]):
        amp = max(4, 14 - i)          # 越往末端越大，蛇身才有波浪感
        bones[b] = {"rotation": R([(0.0, [0, 0, amp]), (0.5, [0, 0, -amp]), (1.0, [0, 0, amp])])}
    for b in g["necks"]:
        # 脖子：只做 1.5° 的前後點頭，繞 Z 會變成「脖子往上撐」的怪姿勢
        bones.setdefault(b, {"rotation": R([(0.0, [1.5, 0, 0]), (0.5, [-1.5, 0, 0]), (1.0, [1.5, 0, 0])])})
    for b in g["bodies"]:
        bones[b] = {"position": R([(0.0, [0, 0, 0]), (0.25, [0, 0.8, 0]), (0.5, [0, 0, 0]),
                                   (0.75, [0, 0.8, 0]), (1.0, [0, 0, 0])]),
                    "rotation": R([(0.0, [0, 0, 2]), (0.5, [0, 0, -2]), (1.0, [0, 0, 2])])}
    for b in g["heads"]:
        bones[b] = {"rotation": R([(0.0, [3, 0, 0]), (0.5, [-3, 0, 0]), (1.0, [3, 0, 0])])}
    return {"loop": True, "animation_length": 1.0, "bones": bones}


def make_idle(g, arm_rest=None):
    bones = {}
    for b in g["bodies"]:
        bones[b] = {"position": R([(0.0, [0, 0, 0]), (1.2, [0, 0.7, 0]), (2.4, [0, 0, 0])])}
    for b in g["heads"]:
        bones[b] = {"rotation": R([(0.0, [0, 0, 0]), (0.8, [4, 8, 0]), (1.6, [0, -6, 0]), (2.4, [0, 0, 0])])}
    for i, b in enumerate(g["tails"]):
        amp = max(3, 12 - i * 4)
        bones[b] = {"rotation": R([(0.0, [0, amp, 0]), (1.2, [0, -amp, 0]), (2.4, [0, amp, 0])])}
    for i, b in enumerate(g["ears"]):
        s = side_of(b, i)
        bones[b] = {"rotation": R([(0.0, [0, 0, 0]), (0.6, [-12, 0, 5 * s]), (1.2, [0, 0, 0]), (2.4, [0, 0, 0])])}
    for i, b in enumerate(g["wings"]):
        s = side_of(b, i)
        bones[b] = {"rotation": R([(0.0, [0, 0, 4 * s]), (1.2, [0, 0, -4 * s]), (2.4, [0, 0, 4 * s])])}
    for i, b in enumerate(g["arms"]):
        s = side_of(b, i)
        z = (arm_rest or {}).get(b, 0.0)
        bones[b] = {"rotation": R([(0.0, [0, 0, z]), (1.2, [3 * s, 0, z + 1.5 * s]), (2.4, [0, 0, z])])}
    for i, b in enumerate(g["spines"]):
        amp = max(2, 7 - i // 3)
        bones[b] = {"rotation": R([(0.0, [0, 0, amp]), (1.2, [0, 0, -amp]), (2.4, [0, 0, amp])])}
    for b in g["necks"]:
        bones.setdefault(b, {"rotation": R([(0.0, [1, 0, 0]), (1.2, [-1, 0, 0]), (2.4, [1, 0, 0])])})
    return {"loop": True, "animation_length": 2.4, "bones": bones}


def find_geo(rp, pid):
    for cand in (os.path.join(rp, "models", "entity", "cobblemon", f"{pid}.geo.json"),
                 os.path.join(rp, "models", "entity", f"{pid}.geo.json")):
        if os.path.exists(cand):
            return cand
    hits = glob.glob(os.path.join(rp, "models", "entity", "**", f"{pid}.geo.json"), recursive=True)
    return hits[0] if hits else None


def main(rp):
    ent_dir = os.path.join(rp, "entity")
    anim_dir = os.path.join(rp, "animations")
    os.makedirs(anim_dir, exist_ok=True)

    ids = sorted(os.path.basename(p).replace(".entity.json", "")
                 for p in glob.glob(os.path.join(ent_dir, "*.entity.json"))
                 if not os.path.basename(p).startswith("poke_catch_fx")
                 and not os.path.basename(p).endswith("_shiny.entity.json"))
    print(f"物種 {len(ids)} 個")
    ok = 0
    for pid in ids:
        gpath = find_geo(rp, pid)
        if not gpath:
            print(f"  {pid:12s} ✘ 找不到模型")
            continue
        geo = load_geo(gpath)
        ident = geo.get("description", {}).get("identifier")
        bones = [b["name"] for b in geo["bones"]]
        with_cubes = {b["name"] for b in geo["bones"] if b.get("cubes")}
        parent = parents_of(geo)
        g = classify(bones, with_cubes, parent)
        arm_rest = compute_arm_rest(geo)

        anim = {"format_version": "1.8.0", "animations": {
            f"animation.poke_{pid}.walk": make_walk(g, arm_rest),
            f"animation.poke_{pid}.idle": make_idle(g, arm_rest),
            f"animation.poke_{pid}.attack": make_attack(g, arm_rest),
            **({f"animation.poke_{pid}.fly": make_fly(g, arm_rest)} if pid in FLYERS else {}),
        }}
        json.dump(anim, open(os.path.join(anim_dir, f"{pid}.animations.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)

        ep = os.path.join(ent_dir, f"{pid}.entity.json")
        ce = json.load(open(ep, encoding="utf-8"))
        d = ce["minecraft:client_entity"]["description"]
        if ident:
            d["geometry"] = {"default": ident}
        if pid in FLYERS:
            d["animations"] = {"fly": f"animation.poke_{pid}.fly", "idle": f"animation.poke_{pid}.idle"}
            d["scripts"] = {"animate": ["fly"]}
        else:
            d["animations"] = {"walk": f"animation.poke_{pid}.walk", "idle": f"animation.poke_{pid}.idle"}
            d["scripts"] = {"animate": [{"walk": "query.modified_move_speed"}, "idle"]}
        json.dump(ce, open(ep, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

        used = sum(len(v) for k, v in g.items() if k != "others")
        folded = sum(1 for v in arm_rest.values() if v != 0)
        print(f"  {pid:12s} {ident:28s} 骨骼{len(bones):4d} 動畫{used:3d} "
              f"(腿{len(g['legs'])} 臂{len(g['arms'])} 翅{len(g['wings'])} 尾{len(g['tails'])} "
              f"耳{len(g['ears'])} 身{len(g['bodies'])} 頭{len(g['heads'])} 鏈{len(g['spines'])} 頸{len(g['necks'])} 收臂{folded})")
        ok += 1
    print(f"\n完成 {ok}/{len(ids)}")
    return 0 if ok == len(ids) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon/rp"))
