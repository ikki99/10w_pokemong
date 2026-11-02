#!/usr/bin/env python3
"""在既有的 pokemon pack 上追加：異色實體、大量道具、裝飾方塊。

素材來自 assets/cobblemon/（由 tools/fetch_cobblemon_assets.py 抓的開源貼圖）。

用法: python3 tools/gen_pokemon_extra.py <pack 根目錄> [assets 根目錄]
"""
import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_species_zh():
    """從 BP 實體檔動態取得 id → 中文名，之後加新寶可夢不用改這裡。"""
    out = {}
    for f in glob.glob(os.path.join(HERE, "packs/pokemon/bp/entities/*.json")):
        base = os.path.basename(f)[:-5]
        if base.endswith("_shiny"):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))["minecraft:entity"]
            name = d.get("description", {}).get("identifier", "")
            if not name.startswith("poke:"):
                continue
            # 中文名從 RP lang 撈，沒有就用 id
            out[base] = base
        except Exception:
            continue
    for lang in glob.glob(os.path.join(HERE, "packs/pokemon/rp/texts/zh_CN.lang")):
        for line in open(lang, encoding="utf-8"):
            k, _, v = line.strip().partition("=")
            if k.startswith("entity.poke:") and k.endswith(".name"):
                pid = k[len("entity.poke:"):-len(".name")]
                if pid in out:
                    out[pid] = v
    return out


SPECIES_ZH = _load_species_zh()

# ---------------------------------------------------------------- 道具表
# id: (中文, 英文, 堆疊, 分類, 說明)
BALLS = {
    "pokeball": ("精靈球", "Poké Ball", 16, 0.0),
    "greatball": ("高級球", "Great Ball", 16, 0.15),
    "ultraball": ("超級球", "Ultra Ball", 16, 0.30),
    "masterball": ("大師球", "Master Ball", 4, 1.0),
    "dive_ball": ("潛水球", "Dive Ball", 16, 0.20),
    "dusk_ball": ("黑暗球", "Dusk Ball", 16, 0.20),
    "timer_ball": ("計時球", "Timer Ball", 16, 0.18),
    "quick_ball": ("先機球", "Quick Ball", 16, 0.25),
    "repeat_ball": ("重複球", "Repeat Ball", 16, 0.15),
    "net_ball": ("捕蟲球", "Net Ball", 16, 0.15),
    "nest_ball": ("巢穴球", "Nest Ball", 16, 0.15),
    "luxury_ball": ("奢華球", "Luxury Ball", 16, 0.12),
    "heal_ball": ("治癒球", "Heal Ball", 16, 0.12),
    "friend_ball": ("友友球", "Friend Ball", 16, 0.12),
    "love_ball": ("甜蜜球", "Love Ball", 16, 0.15),
    "moon_ball": ("月亮球", "Moon Ball", 16, 0.15),
    "fast_ball": ("速度球", "Fast Ball", 16, 0.15),
    "heavy_ball": ("沉重球", "Heavy Ball", 16, 0.15),
    "level_ball": ("等級球", "Level Ball", 16, 0.15),
    "lure_ball": ("誘餌球", "Lure Ball", 16, 0.15),
    "premier_ball": ("紀念球", "Premier Ball", 16, 0.05),
    "safari_ball": ("狩獵球", "Safari Ball", 16, 0.20),
    "dream_ball": ("夢境球", "Dream Ball", 16, 0.25),
    "beast_ball": ("究極球", "Beast Ball", 8, 0.40),
}

STONES = {
    "fire_stone": "火之石", "water_stone": "水之石", "thunder_stone": "雷之石",
    "leaf_stone": "葉之石", "moon_stone": "月之石", "sun_stone": "日之石",
    "shiny_stone": "光之石", "dusk_stone": "暗之石", "dawn_stone": "覺醒之石",
    "ice_stone": "冰之石",
}

BERRIES = {
    "berry": ("樹果", "Berry", 6),
    "oran_berry": ("橘果", "Oran Berry", 10),
    "sitrus_berry": ("文柚果", "Sitrus Berry", 16),
    "lum_berry": ("木子果", "Lum Berry", 20),
    "leppa_berry": ("苧莓", "Leppa Berry", 8),
    "aguav_berry": ("哈密果", "Aguav Berry", 12),
    "rawst_berry": ("莓莓果", "Rawst Berry", 12),
}

MISC = {
    "moomoo_milk": ("哞哞鮮奶", "Moomoo Milk", 16, 20),
    "revival_herb": ("復活草", "Revival Herb", 8, 30),
    "shed_shell": ("脫殼", "Shed Shell", 16, 0),
    "pep_up_flower": ("活力花", "Pep-Up Flower", 16, 0),
}

BADGES = {
    "boulder_badge": "灰色徽章", "cascade_badge": "藍色徽章", "thunder_badge": "橙色徽章",
    "rainbow_badge": "彩虹徽章", "soul_badge": "粉紅徽章", "marsh_badge": "金色徽章",
    "volcano_badge": "深紅徽章", "rising_badge": "升龍徽章",
}

BLOCKS = {
    "healing_machine": ("寶可夢治療台", "pokemon_healing_machine", 1.5, 8, 10),
    "pc": ("寶可夢電腦", "pokemon_pc", 1.2, 6, 0),
    "display_case": ("展示櫃", "pokemon_display_case", 1.0, 4, 0),
    "pokewool_red": ("寶可夢絨紅", "pokewool_red", 0.6, 3, 0),
    "pokewool_blue": ("寶可夢絨藍", "pokewool_blue", 0.6, 3, 0),
    "pokewool_green": ("寶可夢絨綠", "pokewool_green", 0.6, 3, 0),
    "pokewool_pink": ("寶可夢絨粉", "pokewool_pink", 0.6, 3, 0),
    "pokewool_black": ("寶可夢絨黑", "pokewool_black", 0.6, 3, 0),
    "pokewool_white": ("寶可夢絨白", "pokewool_white", 0.6, 3, 0),
}


def item_json(iid, zh, stack, category="items"):
    return {
        "format_version": "1.21.0",
        "minecraft:item": {
            "description": {"identifier": f"poke:{iid}", "menu_category": {"category": category}},
            "components": {
                "minecraft:icon": {"textures": {"default": f"poke_{iid}"}},
                "minecraft:max_stack_size": stack,
                "minecraft:display_name": {"value": zh},
            },
        },
    }


def block_json(bid, zh, seconds, resistance, light):
    return {
        "format_version": "1.21.0",
        "minecraft:block": {
            "description": {"identifier": f"poke:{bid}", "menu_category": {"category": "construction"}},
            "components": {
                "minecraft:material_instances": {"*": {"texture": f"poke_{bid}", "render_method": "opaque"}},
                "minecraft:geometry": "minecraft:geometry.full_block",
                "minecraft:destructible_by_mining": {"seconds_to_destroy": seconds},
                "minecraft:destructible_by_explosion": {"explosion_resistance": resistance},
                "minecraft:light_emission": light,
                "minecraft:map_color": "#C84A4A",
            },
        },
    }


def main(pack, assets):
    bp = os.path.join(pack, "bp")
    rp = os.path.join(pack, "rp")
    for d in (os.path.join(bp, "items"), os.path.join(bp, "blocks"),
              os.path.join(bp, "entities"), os.path.join(rp, "entity"),
              os.path.join(rp, "textures", "items"), os.path.join(rp, "textures", "blocks"),
              os.path.join(rp, "textures", "entity", "pokemon"),
              os.path.join(bp, "texts"), os.path.join(rp, "texts")):
        os.makedirs(d, exist_ok=True)

    item_tex_path = os.path.join(rp, "textures", "item_texture.json")
    item_tex = json.load(open(item_tex_path, encoding="utf-8")) if os.path.exists(item_tex_path) else {
        "resource_pack_name": "pokemon", "texture_name": "atlas.items", "texture_data": {}}
    lang_bp = os.path.join(bp, "texts", "zh_CN.lang")
    lang_rp = os.path.join(rp, "texts", "zh_CN.lang")
    bp_lines = open(lang_bp, encoding="utf-8").read().split("\n") if os.path.exists(lang_bp) else []
    rp_lines = open(lang_rp, encoding="utf-8").read().split("\n") if os.path.exists(lang_rp) else []
    bp_lines = [l for l in bp_lines if l.strip()]
    rp_lines = [l for l in rp_lines if l.strip()]

    _PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    added_items = added_blocks = added_shiny = 0

    # ---------------- 異色實體
    for pid, zh in SPECIES_ZH.items():
        shiny_png = os.path.join(assets, "entity", "shiny", f"{pid}_shiny.png")
        # 新批次的異色貼圖來自 cobblemon 上游，直接放在資材包裡，這裡退回去找它
        if not os.path.exists(shiny_png):
            cand = os.path.join(rp, "textures", "entity", "pokemon", f"{pid}_shiny.png")
            if os.path.exists(cand):
                shiny_png = cand
        base_bp = os.path.join(bp, "entities", f"{pid}.json")
        base_rp = os.path.join(rp, "entity", f"{pid}.entity.json")
        if not (os.path.exists(shiny_png) and os.path.exists(base_bp) and os.path.exists(base_rp)):
            print(f"  ⚠ {pid} 缺少 shiny 或基礎檔，跳過")
            continue

        dst_png = os.path.join(rp, "textures", "entity", "pokemon", f"{pid}_shiny.png")
        if os.path.abspath(shiny_png) != os.path.abspath(dst_png):    # 回退時來源就是目的地，別複製
            shutil.copy(shiny_png, dst_png)

        d = json.load(open(base_bp, encoding="utf-8"))
        d["minecraft:entity"]["description"]["identifier"] = f"poke:{pid}_shiny"
        # 異色獨立成一個實體型別，避免依賴 render controller / variant
        json.dump(d, open(os.path.join(bp, "entities", f"{pid}_shiny.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)

        c = json.load(open(base_rp, encoding="utf-8"))
        desc = c["minecraft:client_entity"]["description"]
        desc["identifier"] = f"poke:{pid}_shiny"
        desc["textures"]["default"] = f"textures/entity/pokemon/{pid}_shiny"
        desc.pop("spawn_egg", None)
        json.dump(c, open(os.path.join(rp, "entity", f"{pid}_shiny.entity.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)

        bp_lines.append(f"entity.poke:{pid}_shiny.name={zh}（異色）")
        rp_lines.append(f"entity.poke:{pid}_shiny.name={zh}（異色）")
        added_shiny += 1

    # ---------------- 道具
    def add_item(iid, zh, stack):
        nonlocal added_items
        tex_src = os.path.join(assets, "items", f"{iid}.png")
        if not os.path.exists(tex_src):
            print(f"  ⚠ {iid} 沒有貼圖，略過")
            return
        shutil.copy(tex_src, os.path.join(rp, "textures", "items", f"{iid}.png"))
        item_tex["texture_data"][f"poke_{iid}"] = {"textures": f"textures/items/{iid}"}
        json.dump(item_json(iid, zh, stack), open(os.path.join(bp, "items", f"{iid}.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        bp_lines.append(f"item.poke:{iid}={zh}")
        rp_lines.append(f"item.poke:{iid}={zh}")
        added_items += 1

    for iid, (zh, en, stack, bonus) in BALLS.items():
        if iid in ("pokeball", "greatball", "ultraball", "masterball"):
            continue                     # 已存在，保留原圖示
        add_item(iid, zh, stack)
    for iid, zh in STONES.items():
        add_item(iid, zh, 16)
    for iid, (zh, en, heal) in BERRIES.items():
        if iid == "berry":
            continue
        add_item(iid, zh, 16)
    for iid, (zh, en, stack, heal) in MISC.items():
        add_item(iid, zh, stack)
    for iid, zh in BADGES.items():
        add_item(iid, zh, 1)

    # ---------------- 方塊
    terrain_path = os.path.join(rp, "textures", "terrain_texture.json")
    terrain = json.load(open(terrain_path, encoding="utf-8")) if os.path.exists(terrain_path) else {
        "resource_pack_name": "pokemon", "texture_name": "atlas.terrain", "padding": 8,
        "num_mip_levels": 4, "texture_data": {}}

    for bid, (zh, texkey, seconds, resistance, light) in BLOCKS.items():
        src = os.path.join(assets, "blocks", f"{bid}.png")
        if not os.path.exists(src):
            print(f"  ⚠ 方塊 {bid} 缺貼圖，略過")
            continue
        shutil.copy(src, os.path.join(rp, "textures", "blocks", f"{bid}.png"))
        terrain["texture_data"][f"poke_{bid}"] = {"textures": f"textures/blocks/{bid}"}
        json.dump(block_json(bid, zh, seconds, resistance, light),
                  open(os.path.join(bp, "blocks", f"{bid}.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        bp_lines.append(f"tile.poke:{bid}.name={zh}")
        rp_lines.append(f"tile.poke:{bid}.name={zh}")
        added_blocks += 1

    json.dump(item_tex, open(item_tex_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(terrain, open(terrain_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(lang_bp, "w", encoding="utf-8").write("\n".join(dict.fromkeys(bp_lines)) + "\n")
    open(lang_rp, "w", encoding="utf-8").write("\n".join(dict.fromkeys(rp_lines)) + "\n")

    # ---------------- CREDITS
    credits = os.path.join(rp, "CREDITS.md")
    text = open(credits, encoding="utf-8").read() if os.path.exists(credits) else "# 素材來源\n"
    if "生怪蛋圖示" not in text:
        text += """
## 追加素材（v4.0.0）

- 異色（shiny）模型貼圖、道具圖示、裝飾方塊貼圖：取自 `kirbycope/cobblemon-bedrock`（repo 授權 MIT，每個物種另有 CC 授權檔，見 `licenses/`）。
- 未使用對方的行為包／腳本／動畫控制器，只取貼圖。
- 各物種授權檔：`licenses/<id>-LICENSE`
"""
        open(credits, "w", encoding="utf-8").write(text)

    print(f"追加完成：異色 {added_shiny} 隻、道具 {added_items} 種、方塊 {added_blocks} 種")


if __name__ == "__main__":
    pack = sys.argv[1] if len(sys.argv) > 1 else "/tmp/poke_new"
    assets = sys.argv[2] if len(sys.argv) > 2 else "assets/cobblemon"
    main(pack, assets)

# 異色實體是新加的，生怪蛋名稱要另外補進 lang（不然蛋會沒名字）
try:
    import gen_egg_names
    gen_egg_names.main(_PKG_DIR)
except Exception as _e:      # 補名字失敗不該讓整條管線掛掉
    print(f"  ⚠ 補蛋名失敗：{_e}")
