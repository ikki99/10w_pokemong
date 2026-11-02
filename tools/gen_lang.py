#!/usr/bin/env python3
"""產生完整的 en_US / ja_JP 語言檔（以 zh_CN 的 key 為準，一個都不漏）。

zh_CN 有 287 條（112 實體 + 112 生怪蛋 + 56 道具 + 7 方塊），
但 en_US 只有 169 條（缺全部道具/方塊、缺異色實體名），ja_JP 完全沒有。
這支腳本以 zh_CN 的 key 清單為基準，逐一產生英文與日文名稱。
"""
import os
import re
import sys

# ---------------- 寶可夢：日文名 ----------------
JA_SPECIES = {
    "pikachu": "ピカチュウ", "eevee": "イーブイ", "bulbasaur": "フシギダネ", "charmander": "ヒトカゲ",
    "squirtle": "ゼニガメ", "jigglypuff": "プリン", "meowth": "ニャース", "gengar": "ゲンガー",
    "snorlax": "カビゴン", "dragonite": "カイリュー", "charizard": "リザードン", "mewtwo": "ミュウツー",
    "psyduck": "コダック", "gyarados": "ギャラドス", "lapras": "ラプラス", "machamp": "カイリキー",
    "alakazam": "フーディン", "onix": "イワーク", "lucario": "ルカリオ", "gardevoir": "サーナイト",
    "greninja": "ゲッコウガ", "mimikyu": "ミミッキュ", "sylveon": "ニンフィア", "garchomp": "ガブリアス",
    "lugia": "ルギア", "hooh": "ホウオウ", "rayquaza": "レックウザ", "latias": "ラティアス",
    "latios": "ラティオス", "regigigas": "レジギガス", "mew": "ミュウ", "xerneas": "ゼルネアス",
    "eternatus": "ムゲンダイナ", "dialga": "ディアルガ", "palkia": "パルキア", "giratina": "ギラティナ",
    "arceus": "アルセウス", "articuno": "フリーザー", "zapdos": "サンダー", "moltres": "ファイヤー",
    "aerodactyl": "プテラ", "regirock": "レジロック", "regice": "レジアイス", "registeel": "レジスチル",
    "regieleki": "レジエレキ", "regidrago": "レジドラゴ", "zarude": "ザルード", "tyranitar": "バンギラス",
    "salamence": "ボーマンダ", "metagross": "メタグロス", "hydreigon": "サザンドラ", "goodra": "ヌメルゴン",
    "kommoo": "ジャラランガ", "dragapult": "ドラパルト", "duraludon": "ジュラルドン",
    "baxcalibur": "セグレイブ", "garganacl": "キョジオーン",
}

# ---------------- 寶可夢：英文名（補齊，含上游常用寫法） ----------------
EN_SPECIES = {
    "pikachu": "Pikachu", "eevee": "Eevee", "bulbasaur": "Bulbasaur", "charmander": "Charmander",
    "squirtle": "Squirtle", "jigglypuff": "Jigglypuff", "meowth": "Meowth", "gengar": "Gengar",
    "snorlax": "Snorlax", "dragonite": "Dragonite", "charizard": "Charizard", "mewtwo": "Mewtwo",
    "psyduck": "Psyduck", "gyarados": "Gyarados", "lapras": "Lapras", "machamp": "Machamp",
    "alakazam": "Alakazam", "onix": "Onix", "lucario": "Lucario", "gardevoir": "Gardevoir",
    "greninja": "Greninja", "mimikyu": "Mimikyu", "sylveon": "Sylveon", "garchomp": "Garchomp",
    "lugia": "Lugia", "hooh": "Ho-Oh", "rayquaza": "Rayquaza", "latias": "Latias", "latios": "Latios",
    "regigigas": "Regigigas", "mew": "Mew", "xerneas": "Xerneas", "eternatus": "Eternatus",
    "dialga": "Dialga", "palkia": "Palkia", "giratina": "Giratina", "arceus": "Arceus",
    "articuno": "Articuno", "zapdos": "Zapdos", "moltres": "Moltres", "aerodactyl": "Aerodactyl",
    "regirock": "Regirock", "regice": "Regice", "registeel": "Registeel", "regieleki": "Regieleki",
    "regidrago": "Regidrago", "zarude": "Zarude", "tyranitar": "Tyranitar", "salamence": "Salamence",
    "metagross": "Metagross", "hydreigon": "Hydreigon", "goodra": "Goodra", "kommoo": "Kommo-o",
    "dragapult": "Dragapult", "duraludon": "Duraludon", "baxcalibur": "Baxcalibur", "garganacl": "Garganacl",
}

# ---------------- 道具 ----------------
EN_ITEMS = {
    "pokeball": "Poke Ball", "greatball": "Great Ball", "ultraball": "Ultra Ball", "masterball": "Master Ball",
    "potion": "Potion", "rarecandy": "Rare Candy", "berry": "Berry", "pokedex": "Pokedex",
    "dive_ball": "Dive Ball", "dusk_ball": "Dusk Ball", "timer_ball": "Timer Ball", "quick_ball": "Quick Ball",
    "repeat_ball": "Repeat Ball", "net_ball": "Net Ball", "nest_ball": "Nest Ball", "luxury_ball": "Luxury Ball",
    "heal_ball": "Heal Ball", "friend_ball": "Friend Ball", "love_ball": "Love Ball", "moon_ball": "Moon Ball",
    "fast_ball": "Fast Ball", "heavy_ball": "Heavy Ball", "level_ball": "Level Ball", "lure_ball": "Lure Ball",
    "premier_ball": "Premier Ball", "safari_ball": "Safari Ball", "dream_ball": "Dream Ball",
    "beast_ball": "Beast Ball",
    "fire_stone": "Fire Stone", "water_stone": "Water Stone", "thunder_stone": "Thunder Stone",
    "leaf_stone": "Leaf Stone", "moon_stone": "Moon Stone", "sun_stone": "Sun Stone",
    "shiny_stone": "Shiny Stone", "dusk_stone": "Dusk Stone", "dawn_stone": "Dawn Stone", "ice_stone": "Ice Stone",
    "oran_berry": "Oran Berry", "sitrus_berry": "Sitrus Berry", "lum_berry": "Lum Berry",
    "leppa_berry": "Leppa Berry", "aguav_berry": "Aguav Berry", "rawst_berry": "Rawst Berry",
    "moomoo_milk": "Moomoo Milk", "revival_herb": "Revival Herb", "shed_shell": "Shed Shell",
    "pep_up_flower": "Pep-Up Flower",
    "boulder_badge": "Boulder Badge", "cascade_badge": "Cascade Badge", "thunder_badge": "Thunder Badge",
    "rainbow_badge": "Rainbow Badge", "soul_badge": "Soul Badge", "marsh_badge": "Marsh Badge",
    "volcano_badge": "Volcano Badge", "rising_badge": "Rising Badge",
}
JA_ITEMS = {
    "pokeball": "モンスターボール", "greatball": "スーパーボール", "ultraball": "ハイパーボール",
    "masterball": "マスターボール", "potion": "キズぐすり", "rarecandy": "ふしぎなアメ", "berry": "きのみ",
    "pokedex": "ポケモン図鑑",
    "dive_ball": "ダイブボール", "dusk_ball": "ダークボール", "timer_ball": "タイマーボール",
    "quick_ball": "クイックボール", "repeat_ball": "リピートボール", "net_ball": "ネットボール",
    "nest_ball": "ネストボール", "luxury_ball": "ゴージャスボール", "heal_ball": "ヒールボール",
    "friend_ball": "フレンドボール", "love_ball": "ラブラブボール", "moon_ball": "ムーンボール",
    "fast_ball": "スピードボール", "heavy_ball": "ヘビーボール", "level_ball": "レベルボール",
    "lure_ball": "ルアーボール", "premier_ball": "プレミアボール", "safari_ball": "サファリボール",
    "dream_ball": "ドリームボール", "beast_ball": "ビーストボール",
    "fire_stone": "ほのおのいし", "water_stone": "みずのいし", "thunder_stone": "かみなりのいし",
    "leaf_stone": "リーフのいし", "moon_stone": "つきのいし", "sun_stone": "たいようのいし",
    "shiny_stone": "ひかりのいし", "dusk_stone": "やみのいし", "dawn_stone": "めざめのいし",
    "ice_stone": "こおりのいし",
    "oran_berry": "オレンのみ", "sitrus_berry": "オボンのみ", "lum_berry": "ラムのみ",
    "leppa_berry": "ヒメリのみ", "aguav_berry": "ウイのみ", "rawst_berry": "チーゴのみ",
    "moomoo_milk": "モーモーミルク", "revival_herb": "ふっかつそう", "shed_shell": "ぬけがら",
    "pep_up_flower": "やるきのはな",
    "boulder_badge": "グレーバッジ", "cascade_badge": "ブルーバッジ", "thunder_badge": "オレンジバッジ",
    "rainbow_badge": "レインボーバッジ", "soul_badge": "ピンクバッジ", "marsh_badge": "ゴールドバッジ",
    "volcano_badge": "クリムゾンバッジ", "rising_badge": "ライジングバッジ",
}
EN_TILES = {"healing_machine": "Pokemon Healing Machine", "pc": "Pokemon PC",
            "pokewool_red": "Pokewool (Red)", "pokewool_green": "Pokewool (Green)",
            "pokewool_pink": "Pokewool (Pink)", "pokewool_black": "Pokewool (Black)",
            "pokewool_white": "Pokewool (White)"}
JA_TILES = {"healing_machine": "ポケモン回復マシン", "pc": "ポケモンPC",
            "pokewool_red": "ポケモンウール（赤）", "pokewool_green": "ポケモンウール（緑）",
            "pokewool_pink": "ポケモンウール（桃）", "pokewool_black": "ポケモンウール（黒）",
            "pokewool_white": "ポケモンウール（白）"}


def translate(key, lang):
    """把一條 zh_CN 的 key 翻成 en / ja。"""
    m = re.match(r"item\.spawn_egg\.entity\.poke:([a-z_]+)\.name$", key)
    if m:
        pid = m.group(1)
        shiny = pid.endswith("_shiny")
        base = pid[:-6] if shiny else pid
        if lang == "en":
            name = EN_SPECIES.get(base, base.title())
            return f"Shiny {name} Egg" if shiny else f"{name} Egg"
        name = JA_SPECIES.get(base, base)
        return f"色違い{name}のタマゴ" if shiny else f"{name}のタマゴ"

    m = re.match(r"entity\.poke:([a-z_]+)\.name$", key)
    if m:
        pid = m.group(1)
        shiny = pid.endswith("_shiny")
        base = pid[:-6] if shiny else pid
        if lang == "en":
            name = EN_SPECIES.get(base, base.title())
            return f"Shiny {name}" if shiny else name
        name = JA_SPECIES.get(base, base)
        return f"色違い{name}" if shiny else name

    m = re.match(r"item\.poke:([a-z_0-9]+)$", key)
    if m:
        table = EN_ITEMS if lang == "en" else JA_ITEMS
        return table.get(m.group(1), m.group(1).replace("_", " ").title())

    m = re.match(r"tile\.poke:([a-z_0-9]+)\.name$", key)
    if m:
        table = EN_TILES if lang == "en" else JA_TILES
        return table.get(m.group(1), m.group(1).replace("_", " ").title())
    return None


def build(zh_text, lang):
    out, missing = [], []
    for line in zh_text.splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key = line.split("=", 1)[0]
        val = translate(key, lang)
        if val is None:
            missing.append(key)
            continue
        out.append(f"{key}={val}")
    return out, missing


def main(pack_dir):
    total = 0
    for pack in ("rp", "bp"):
        src = os.path.join(pack_dir, pack, "texts", "zh_CN.lang")
        if not os.path.exists(src):
            continue
        zh = open(src, encoding="utf-8").read()
        for lang, fname in (("en", "en_US.lang"), ("ja", "ja_JP.lang")):
            lines, missing = build(zh, lang)
            dst = os.path.join(pack_dir, pack, "texts", fname)
            open(dst, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            print(f"  {pack}/{fname}: {len(lines)} 條" + (f" | 未翻譯 {len(missing)}: {missing[:5]}" if missing else ""))
            total += len(lines)
    print(f"合計 {total} 條")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon")
