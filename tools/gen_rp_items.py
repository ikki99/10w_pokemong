#!/usr/bin/env python3
"""補齊自訂物品的「客戶端定義」（rp/items/*.json）。

症狀：物品欄裡一堆黑色球、沒名字。原因不是貼圖也不是 lang，
而是 **RP 完全沒有 items/ 目錄** —— 客戶端沒有物品註冊資訊，
所以既畫不出圖示、也顯示不出名稱（名稱 key 其實 lang 裡都有）。

BP 的 56 個物品每個都要在 RP 有一份對應定義，icon 名用 `poke_<短名>`，
這個名字必須存在於 rp/textures/item_texture.json 的清單裡。
"""
import glob
import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon"
BP, RP = os.path.join(ROOT, "bp"), os.path.join(ROOT, "rp")

texture_map = json.load(open(os.path.join(RP, "textures/item_texture.json"), encoding="utf-8"))["texture_data"]
lang = {}
for f in glob.glob(os.path.join(RP, "texts/*.lang")):
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            lang.setdefault(k, v)

CATEGORY = {
    "ball": "equipment",
    "potion": "equipment",
    "candy": "items",
}


def category_of(short):
    if short.endswith("ball"):
        return "equipment"
    if "badge" in short:
        return "items"
    return "items"


os.makedirs(os.path.join(RP, "items"), exist_ok=True)
made, missing_icon, missing_name = 0, [], []
for p in sorted(glob.glob(os.path.join(BP, "items/*.json"))):
    bp = json.load(open(p, encoding="utf-8"))["minecraft:item"]
    ident = bp["description"]["identifier"]
    short = ident.split(":")[-1]
    icon_comp = bp.get("components", {}).get("minecraft:icon")
    icon = None
    if isinstance(icon_comp, dict):
        icon = (icon_comp.get("textures") or {}).get("default") or icon_comp.get("texture")
    elif isinstance(icon_comp, str):
        icon = icon_comp
    icon = icon or f"poke_{short}"
    if icon not in texture_map:
        missing_icon.append((ident, icon))
        texture_map[icon] = {"textures": f"textures/items/{short}"}
    if f"item.{ident}" not in lang:
        missing_name.append(ident)

    rp = {
        "format_version": "1.21.10",
        "minecraft:item": {
            "description": {
                "identifier": ident,
                "menu_category": {"category": category_of(short)},
            },
            "components": {
                "minecraft:icon": {"textures": {"default": icon}},
            },
        },
    }
    json.dump(rp, open(os.path.join(RP, "items", f"{short}.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    made += 1

# 補齊 item_texture.json（把缺的 icon 名補上）
json.dump({"resource_pack_name": "pokemon", "texture_name": "atlas.items", "texture_data": texture_map},
          open(os.path.join(RP, "textures/item_texture.json"), "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)

print(f"產生 RP 物品定義：{made} 個")
print(f"補進 item_texture.json 的 icon：{len(missing_icon)}")
print(f"lang 缺名稱的物品：{len(missing_name)} {missing_name[:5]}")
print("RP items 目錄檔案數：", len(os.listdir(os.path.join(RP, "items"))))
