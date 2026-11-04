#!/usr/bin/env python3
"""修兩個 bug：
1) 圖鑑頭像不顯示：main.js 傳的路徑帶了 .png，script UI 的 iconPath 不能有副檔名。
2) 尾巴火焰不顯示：動畫在 locator "fire" 發粒子，但幾何體裡根本沒有這個 locator。

用法：python3 tools/fix_dex_and_flame.py packs/pokemon [--bump 5.0.15]
"""
import glob
import json
import os
import re
import sys


def fix_dex_icon_path(pack_dir):
    main_js = os.path.join(pack_dir, "bp", "scripts", "main.js")
    src = open(main_js, encoding="utf-8").read()
    before = src
    # textures/items/dex_<id>.png  ->  textures/items/dex_<id>
    src = re.sub(r'`textures/items/dex_\$\{id\}\.png`', '`textures/items/dex_${id}`', src)
    src = src.replace("textures/items/dex_${id}.png", "textures/items/dex_${id}")
    if src == before:
        print("  圖鑑路徑：沒有需要修的字串（檢查一下下面這行）")
    else:
        open(main_js, "w", encoding="utf-8").write(src)
        print("  圖鑑路徑已修：去掉 .png")
    for line in src.splitlines():
        if "dexIcon" in line or "const dexIcon" in line:
            print("   ", line.strip())
    return src


def find_geo(rp, pid):
    for p in (f"models/entity/cobblemon/{pid}.geo.json", f"models/entity/{pid}.geo.json"):
        full = os.path.join(rp, p)
        if os.path.exists(full):
            return full
    return None


def add_flame_locator(rp, pid):
    geo_path = find_geo(rp, pid)
    if not geo_path:
        return f"{pid}: 找不到模型"
    doc = json.load(open(geo_path, encoding="utf-8"))
    geo = doc["minecraft:geometry"][0]
    bones = geo["bones"]

    # 已經有 fire locator 就跳過
    for b in bones:
        if b.get("locators") and "fire" in b["locators"]:
            return f"{pid}: 已有 fire locator（{b['name']}）"

    # 優先找名字像尾尖的占位骨，其次找最深的 tail* 骨
    def depth(name):
        d, cur = 0, name
        by_name = {x["name"]: x for x in bones}
        while by_name.get(cur, {}).get("parent"):
            cur = by_name[cur]["parent"]
            d += 1
        return d

    cand = [b for b in bones if "tail_tip" in b["name"] or b["name"].endswith("tail_tip")]
    if not cand:
        tails = [b for b in bones if b["name"].startswith("tail")]
        if tails:
            cand = [max(tails, key=lambda b: (depth(b["name"]), (b.get("pivot") or [0, 0, 0])[2]))]
    if not cand:
        return f"{pid}: 沒有尾巴骨骼，略過"

    target = cand[0]
    target.setdefault("locators", {})["fire"] = [0, 0, 0]
    json.dump(doc, open(geo_path, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    return f"{pid}: 在 {target['name']} 加上 fire locator（pivot {(target.get('pivot'))}）"


def bump(pack_dir, ver):
    v = [int(x) for x in ver.split(".")]
    for sub in ("bp", "rp"):
        p = os.path.join(pack_dir, sub, "manifest.json")
        d = json.load(open(p, encoding="utf-8"))
        d["header"]["version"] = v
        d["modules"] = [dict(m, version=v) for m in d["modules"]]
        json.dump(d, open(p, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    js = os.path.join(pack_dir, "bp", "scripts", "main.js")
    s = open(js, encoding="utf-8").read()
    s2 = re.sub(r'const VERSION = "[0-9.]+";', f'const VERSION = "{ver}";', s, count=1)
    if s2 != s:
        open(js, "w", encoding="utf-8").write(s2)
    print(f"  版本 -> {ver}")


def main(pack_dir, ver=None):
    rp = os.path.join(pack_dir, "rp")
    print("[1] 圖鑑頭像路徑")
    fix_dex_icon_path(pack_dir)

    print("[2] 尾巴火焰 locator")
    ids = set()
    for f in glob.glob(os.path.join(rp, "animations", "*.animations.json")):
        d = json.load(open(f, encoding="utf-8")).get("animations", {})
        if any("tail_flame" in k for k in d):
            ids.add(os.path.basename(f).replace(".animations.json", ""))
    for pid in sorted(ids):
        print("   ", add_flame_locator(rp, pid))

    if ver:
        print("[3] 版本")
        bump(pack_dir, ver)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ver = None
    for i, a in enumerate(sys.argv):
        if a == "--bump":
            ver = sys.argv[i + 1]
    main(args[0] if args else "packs/pokemon", ver)
