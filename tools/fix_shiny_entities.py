#!/usr/bin/env python3
"""修正異色（<id>_shiny）client entity 的動畫綁定。

背景：gen_pokemon.py 每跑一次就會重寫所有 RP client entity，異色那份只拿到最基礎的
walk/idle/attack，而且 attack 會被指到不存在的 `animation.poke_<id>_shiny.attack`
（gen_pokemon_extra / wire_attack 之後的樣貌）。結果：異色飛行寶可夢不扇翅、不擺姿勢。

做法：以本體（非 _shiny）為準，把 geometry / materials / render_controllers /
animations / scripts.animate 全部複製給異色，只保留異色自己的 textures 與 spawn_egg。

用法： python3 tools/fix_shiny_entities.py packs/pokemon/rp
"""
import glob
import json
import os
import sys


def main(rp):
    ent_dir = os.path.join(rp, "entity")
    fixed = 0
    for shiny_path in sorted(glob.glob(os.path.join(ent_dir, "*_shiny.entity.json"))):
        base_path = shiny_path.replace("_shiny.entity.json", ".entity.json")
        if not os.path.exists(base_path):
            print(f"  跳過 {os.path.basename(shiny_path)}：找不到本體")
            continue
        with open(base_path, encoding="utf-8") as f:
            base = json.load(f)["minecraft:client_entity"]["description"]
        with open(shiny_path, encoding="utf-8") as f:
            data = json.load(f)
        sh = data["minecraft:client_entity"]["description"]

        before = json.dumps(sh, sort_keys=True)

        for key in ("geometry", "materials", "render_controllers", "texture_assignments"):
            if key in base:
                sh[key] = json.loads(json.dumps(base[key]))

        # 動畫別名與播放清單直接照抄本體（動畫檔共用，異色不該有專屬檔）
        if "animations" in base:
            sh["animations"] = json.loads(json.dumps(base["animations"]))
        base_scripts = base.get("scripts", {})
        if "animate" in base_scripts:
            sh.setdefault("scripts", {})["animate"] = json.loads(json.dumps(base_scripts["animate"]))

        # 貼圖維持異色自己的
        tex = sh.get("textures", {}).get("default", "")
        if not tex.endswith("_shiny"):
            pid = os.path.basename(shiny_path).replace(".entity.json", "")
            sh["textures"] = {"default": f"textures/entity/pokemon/{pid}"}

        if json.dumps(sh, sort_keys=True) != before:
            data["minecraft:client_entity"]["description"] = sh
            with open(shiny_path, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
            fixed += 1
            print(f"  ✔ {os.path.basename(shiny_path)}")
    print(f"修正 {fixed} 個異色 client entity")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon/rp")
