#!/usr/bin/env python3
"""匯入 cobblemon 真實動畫（ground_idle / ground_walk / physical / air_*）。

為什麼需要：cobblemon 模型把「脖子的自然彎曲」寫在動畫裡（例如噴火龍 ground_idle 的
neck 7.5° / neck2 22.5° / neck3 27.5° / neck4 20°），不是寫在幾何裡。沒有這組動畫，
模型就會停在原始姿態 —— 脖子和嘴朝天。之前用程序生成的動作永遠做不出這件事。

做法：抓 `<dex>_<name>/<name>.animation.json`，把需要的段落改別名成
`animation.poke_<id>.walk / .idle / .attack / .fly`，覆蓋掉程序生成的版本
（`pose` / `pose_fly` 由 import_cobblemon_poses.py 提供，這裡不動）。
缺少的段落就保留原本程序生成的動畫當後備。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_cobblemon_models import SPECIES, RAW  # noqa: E402

# 會飛的物種由 BP 決定，不是「有沒有 air_fly 動畫」：傳說檔與一般物種檔都要收
FLYERS = set()
try:
    from poke_legendaries import LEGENDARY_SPECS as _LEG
    FLYERS |= {x["id"] for x in _LEG if x.get("flyer")}
except Exception:
    pass
try:
    from poke_species import NEW_SPECS as _NEW
    FLYERS |= {x["id"] for x in _NEW if x.get("flyer")}
except Exception:
    pass

# 別名 -> 上游動畫名後綴（依優先順序）
SLOTS = {
    "idle":   ("ground_idle", "air_idle"),
    "walk":   ("ground_walk", "ground_run"),
    "attack": ("physical", "air_physical", "special"),
    "fly":    ("air_fly", "air_glide"),
}
BAD_TOKENS = ("q.property('cobblemon:", "v.pose", "q.is_riding", "q.is_sleeping")


def fetch(path):
    with urllib.request.urlopen(RAW + path, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def usable(anim):
    """確認這段動畫沒有依賴 cobblemon 專屬的查詢/變數。"""
    blob = json.dumps(anim)
    return not any(t in blob for t in BAD_TOKENS)


def main(pack_dir):
    ok, skip = 0, []
    for pid, (dex, name) in SPECIES.items():
        ap = os.path.join(pack_dir, "rp", "animations", f"{pid}.animations.json")
        ep = os.path.join(pack_dir, "rp", "entity", f"{pid}.entity.json")
        if not (os.path.exists(ap) and os.path.exists(ep)):
            skip.append(pid)
            continue
        try:
            src = fetch(f"development_resource_packs/cobblemon/animations/{dex}_{name}/{name}.animation.json")["animations"]
        except Exception as e:
            print(f"  {pid}: 取動畫失敗 {e}")
            skip.append(pid)
            continue

        data = json.load(open(ap, encoding="utf-8"))
        anims = data.setdefault("animations", {})
        got = {}
        for slot, candidates in SLOTS.items():
            for cand in candidates:
                hit = next((k for k in src if k.endswith("." + cand)), None)
                if hit and usable(src[hit]):
                    anims[f"animation.poke_{pid}.{slot}"] = src[hit]
                    got[slot] = cand
                    break
        json.dump(data, open(ap, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)

        ent = json.load(open(ep, encoding="utf-8"))
        d = ent["minecraft:client_entity"]["description"]
        amap = d.setdefault("animations", {})
        for slot in got:
            amap[slot] = f"animation.poke_{pid}.{slot}"
        is_flyer = pid in FLYERS
        cur = d.setdefault("scripts", {})["animate"]
        tail = [a for a in cur if isinstance(a, dict) and "attack" in a]
        pose_ref = "pose_fly" if ("pose_fly" in amap and is_flyer) else "pose"
        if is_flyer and "fly" in got:
            d["scripts"]["animate"] = [pose_ref, {"fly": "query.modified_move_speed > 0.05"}, "idle"] + tail
        elif is_flyer:                 # 上游沒有飛行動畫（烈空坐/拉帝兄弟）：懸停播 idle
            d["scripts"]["animate"] = [pose_ref, "idle"] + tail
        else:
            d["scripts"]["animate"] = [pose_ref, {"walk": "query.modified_move_speed > 0.05"}, "idle"] + tail
        json.dump(ent, open(ep, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
        ok += 1
        print(f"  {pid:<12} {got}")
    print(f"完成 {ok} 隻，跳過 {len(skip)}：{skip}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon")
