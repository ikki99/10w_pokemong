#!/usr/bin/env python3
"""匯入 cobblemon 的 poses 動畫（脖子/頭的基準姿態）。

為什麼要這個：cobblemon 模型把「頭往前看」這件事放在 pose_standing 動畫裡（只動 neck~neck4 + head），
沒有綁 pose 動畫，模型就會停在原始幾何姿態 —— 脖子和嘴朝天。
做法：抓 poses.animation.json，把 pose_standing / pose_flying 存成
`animation.poke_<id>.pose` / `.pose_fly`，寫進該物種的 animations 檔，
再把我自己生成的 walk/idle/attack 裡的 neck/head 骨頭移除（避免兩邊打架），
最後在 client entity 的 animate 清單最前面綁上 pose。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_cobblemon_models import SPECIES, RAW, REPO, BRANCH  # noqa: E402

FLYING_PREF = ("pose_flying", "pose_fly", "pose_hover", "pose_glide")
GROUND_PREF = ("pose_standing", "pose_walking")


def fetch(path):
    with urllib.request.urlopen(RAW + path, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def main(pack_dir):
    rp = os.path.join(pack_dir, "rp")
    ok, skip = 0, []
    for pid, (dex, name) in SPECIES.items():
        anim_path = f"rp/animations/{pid}.animations.json"
        ent_path = f"rp/entity/{pid}.entity.json"
        if not (os.path.exists(os.path.join(pack_dir, anim_path)) and os.path.exists(os.path.join(pack_dir, ent_path))):
            skip.append(pid)
            continue
        try:
            poses = fetch(f"development_resource_packs/cobblemon/animations/{dex}_{name}/poses.animation.json")["animations"]
        except Exception as e:
            print(f"  {pid}: 取 poses 失敗 {e}")
            skip.append(pid)
            continue
        ground = next((k for k in poses if any(k.endswith("." + p) for p in GROUND_PREF)), None)
        air = next((k for k in poses if any(k.endswith("." + p) for p in FLYING_PREF)), None)
        if not ground:
            print(f"  {pid}: 沒有地面 pose")
            skip.append(pid)
            continue

        ap = os.path.join(pack_dir, anim_path)
        data = json.load(open(ap, encoding="utf-8"))
        anims = data.setdefault("animations", {})
        anims[f"animation.poke_{pid}.pose"] = poses[ground]
        if air:
            anims[f"animation.poke_{pid}.pose_fly"] = poses[air]
        # 移除我自己生成的 neck/head 骨頭，交給 pose 動畫處理
        for key, val in anims.items():
            if key.endswith(".pose") or key.endswith(".pose_fly"):
                continue
            bones = val.get("bones") or {}
            for b in [b for b in bones if "neck" in b.lower() or b.lower().startswith("head")]:
                bones.pop(b, None)
        json.dump(data, open(ap, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)

        ep = os.path.join(pack_dir, ent_path)
        ent = json.load(open(ep, encoding="utf-8"))
        d = ent["minecraft:client_entity"]["description"]
        amap = d.setdefault("animations", {})
        amap["pose"] = f"animation.poke_{pid}.pose"
        if air:
            amap["pose_fly"] = f"animation.poke_{pid}.pose_fly"
        cur = list(d.get("scripts", {}).get("animate") or [])
        cur = [a for a in cur if a not in ("pose", "pose_fly")]
        is_flyer = any(a == "fly" for a in cur)
        pose_ref = "pose_fly" if (is_flyer and air) else "pose"
        d.setdefault("scripts", {})["animate"] = [pose_ref] + cur
        json.dump(ent, open(ep, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
        ok += 1
        print(f"  {pid:<12} {ground:<40} 空中:{air or '(無)'}")
    print(f"完成 {ok} 隻，跳過 {len(skip)}：{skip}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon")
