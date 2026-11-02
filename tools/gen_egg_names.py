#!/usr/bin/env python3
"""補齊所有生怪蛋的名稱（含異色）。

生怪蛋的名稱不是寫在 BP，而是要靠資材包 lang 的
`item.spawn_egg.entity.poke:<id>.name`；少寫就顯示原始 key 或空白。
異色實體（<id>_shiny）是後加的，原本沒寫 lang，所以蛋沒名字。
這裡依實際存在的實體檔補齊，異色取名為「<基礎名>（異色）生怪蛋」。
"""
import glob
import os
import re
import sys

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(pack_dir):
    ents = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(pack_dir, "bp", "entities", "*.json"))}
    lang_paths = [os.path.join(pack_dir, "rp", "texts", "zh_CN.lang"),
                  os.path.join(pack_dir, "bp", "texts", "zh_CN.lang")]
    SPECIAL_EN = {"hooh": "Ho-Oh", "mewtwo": "Mewtwo", "porygon": "Porygon"}

    def en_name(base):
        if base in SPECIAL_EN:
            return SPECIAL_EN[base]
        return " ".join(w.capitalize() for w in base.split("_"))
    zh = open(lang_paths[0], encoding="utf-8").read()
    base_names = dict(re.findall(r"item\.spawn_egg\.entity\.poke:([a-z_]+)\.name=(.+)", zh))
    added_total = 0
    for path in lang_paths:
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        have = set(re.findall(r"item\.spawn_egg\.entity\.poke:([a-z_]+)\.name", text))
        add = []
        for pid in sorted(ents - have):
            if pid.endswith("_shiny"):
                base = pid[:-6]
                label = base_names.get(base, base)
                label = re.sub(r"\s*生怪蛋\s*$", "", label)
                add.append(f"item.spawn_egg.entity.poke:{pid}.name={label}（異色） 生怪蛋")
            else:
                add.append(f"item.spawn_egg.entity.poke:{pid}.name={pid} 生怪蛋")
        if add:
            if text and not text.endswith("\n"):
                text += "\n"
            open(path, "w", encoding="utf-8").write(text + "\n".join(add) + "\n")
            added_total += len(add)
            print(f"  {os.path.relpath(path, pack_dir)}: 補 {len(add)} 條")
    # 英文 lang（en_US）：不補的話英文客戶端整批蛋都是原始 key
    for path in (os.path.join(pack_dir, "rp", "texts", "en_US.lang"),
                 os.path.join(pack_dir, "bp", "texts", "en_US.lang")):
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        have = set(re.findall(r"item\.spawn_egg\.entity\.poke:([a-z_]+)\.name", text))
        add = []
        for pid in sorted(ents - have):
            if pid.endswith("_shiny"):
                add.append(f"item.spawn_egg.entity.poke:{pid}.name=Shiny {en_name(pid[:-6])} Egg")
            else:
                add.append(f"item.spawn_egg.entity.poke:{pid}.name={en_name(pid)} Egg")
        if add:
            if text and not text.endswith("\n"):
                text += "\n"
            open(path, "w", encoding="utf-8").write(text + "\n".join(add) + "\n")
            print(f"  {os.path.relpath(path, pack_dir)}: 補 {len(add)} 條（英文）")
    print(f"合計補 {added_total} 條")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(PKG, "packs", "pokemon"))
