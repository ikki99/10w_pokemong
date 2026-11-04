#!/usr/bin/env python3
"""一次性把卡洛斯批次（7 隻，含伊裴爾塔爾）寫進各資料表。

只改資料檔，不生成 pack。改完再跑生成管線。
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


# ---------------------------------------------------------------- 1. poke_species.py
SPECS_SNIPPET = '''
    # ---------------- 卡洛斯（Kalos）批次 ----------------
    dict(id="talonflame", zh="烈箭鷹", en="Talonflame", hp=78, speed=0.40, damage=6,
         body=(10, 11, 12), head=(9, 8, 9), legs=(2, 7, 3), ears=((1, 3, 1), (1, 3, 1)),
         tail="long", stance="biped", wings=True,
         pal=pal("#E8503A", "#3A3A42", belly="#F2C24A"),
         face=face(eye="#E8C24A", mouth="#5A5A64"),
         hostile=False, family=["poke", "talonflame", "fire", "flying"], scale=1.15),

    dict(id="noivern", zh="音波龍", en="Noivern", hp=85, speed=0.44, damage=6,
         body=(10, 10, 13), head=(10, 9, 10), legs=(2, 6, 3), ears=((4, 6, 2), (4, 6, 2)),
         tail="long", stance="biped", wings=True, flyer=True,
         pal=pal("#6A5A8A", "#3A2F52", belly="#9A8AC0"),
         face=face(eye="#E8C24A", mouth="#2A2A3A"),
         hostile=False, family=["poke", "noivern", "flying", "dragon"], scale=1.2),

    dict(id="aegislash", zh="堅盾劍怪", en="Aegislash", hp=60, speed=0.30, damage=7,
         body=(9, 12, 6), head=(9, 9, 6), legs=(2, 5, 2), ears=((1, 2, 1), (1, 2, 1)),
         tail="stub", stance="biped",
         pal=pal("#B0A890", "#6A5A8A", belly="#D8D0B8"),
         face=face(eye="#5AC8E8", mouth="#4A4A44"),
         hostile=False, family=["poke", "aegislash", "steel", "ghost"], scale=1.1),

    dict(id="hawlucha", zh="摔角鷹人", en="Hawlucha", hp=78, speed=0.42, damage=6,
         body=(9, 10, 10), head=(9, 8, 8), legs=(2, 7, 3), ears=((1, 3, 1), (1, 3, 1)),
         tail="stub", stance="biped", wings=True,
         pal=pal("#3AA85A", "#E8503A", belly="#F2EED8"),
         face=face(eye="#E8C24A", mouth="#2A3A2A"),
         hostile=False, family=["poke", "hawlucha", "fighting", "flying"], scale=1.05),

    dict(id="aurorus", zh="冰雪巨龍", en="Aurorus", hp=123, speed=0.22, damage=5,
         body=(12, 14, 15), head=(9, 8, 10), legs=(4, 8, 4), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#A8D8E8", "#3A6AA8", belly="#E8F4FA"),
         face=face(eye="#3A5AA8", mouth="#5A7A9A"),
         hostile=False, family=["poke", "aurorus", "rock", "ice"], scale=1.35),

    dict(id="tyrantrum", zh="怪顎龍", en="Tyrantrum", hp=82, speed=0.28, damage=8,
         body=(12, 13, 16), head=(12, 10, 13), legs=(4, 7, 5), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#B04A32", "#5A2A22", belly="#E8D8B0"),
         face=face(eye="#E8C24A", mouth="#3A1A14"),
         hostile=True, family=["poke", "tyrantrum", "rock", "dragon"], scale=1.3),
'''

SPAWN_SNIPPET = '''
    "talonflame": ("animal",  (7, 15), ["mountains", "savanna", "stony_peaks"], 4, (1, 2)),
    "noivern":    ("monster", (0, 7),  ["roofed", "dripstone_caves", "dark_forest"], 3, (1, 1)),
    "aegislash":  ("monster", (0, 7),  ["roofed", "deep_dark", "dark_forest"], 2, (1, 1)),
    "hawlucha":   ("animal",  (7, 15), ["savanna", "jungle", "mesa"], 5, (1, 2)),
    "aurorus":    ("animal",  (0, 7),  ["frozen_peaks", "snowy_taiga", "ice_spikes"], 3, (1, 1)),
    "tyrantrum":  ("monster", (0, 10), ["mesa", "badlands", "desert"], 2, (1, 1)),
'''


def patch_species():
    p = os.path.join(ROOT, "tools", "poke_species.py")
    s = read(p)
    if "talonflame" in s:
        print("poke_species.py 已有卡洛斯批次，跳過")
        return
    nl = "\r\n" if "\r\n" in s else "\n"
    body = SPECS_SNIPPET.replace("\n", nl)
    spawn = SPAWN_SNIPPET.replace("\n", nl)
    # 插在 NEW_SPECS 的結尾 ] 之前
    i = s.find("NEW_SPECS = [")
    j = s.find(nl + "]", i)
    s = s[:j] + nl + body.rstrip(nl) + s[j:]
    # 插在 NEW_SPAWN_PROFILES 的結尾 } 之前
    i = s.find("NEW_SPAWN_PROFILES = {")
    j = s.find(nl + "}", i)
    s = s[:j] + nl + spawn.rstrip(nl) + s[j:]
    write(p, s)
    print("poke_species.py 已加 6 隻")


# ---------------------------------------------------------------- 2. poke_legendaries.py
LEGEND_SNIPPET = '''
    dict(id="yveltal", flyer=True, zh="伊裴爾塔爾", en="Yveltal", hp=126, speed=0.40, damage=9,
         body=(16, 14, 22), head=(12, 10, 14), legs=(4, 6, 5), ears=((2, 4, 2), (2, 4, 2)),
         tail="long", stance="quad",
         pal=pal("#2A1A22", "#C02838", belly="#43303A"),
         face=face(eye="#5AC8E8", mouth="#141014"),
         hostile=False, family=["poke", "yveltal", "dark", "flying"], scale=2.3),
'''

LEGEND_SPAWN_SNIPPET = '''
    "yveltal":   ("monster", (10, 15), ["stony_peaks", "mountains", "frozen_peaks"], 1, (1, 1)),
'''


def patch_legendaries():
    p = os.path.join(ROOT, "tools", "poke_legendaries.py")
    s = read(p)
    if "yveltal" in s:
        print("poke_legendaries.py 已有 yveltal，跳過")
        return
    nl = "\r\n" if "\r\n" in s else "\n"
    i = s.find("LEGENDARY_SPECS = [")
    j = s.find(nl + "]", i)
    s = s[:j] + nl + LEGEND_SNIPPET.replace("\n", nl).rstrip(nl) + s[j:]
    i = s.find("LEGENDARY_SPAWN_PROFILES = {")
    j = s.find(nl + "}", i)
    s = s[:j] + nl + LEGEND_SPAWN_SNIPPET.replace("\n", nl).rstrip(nl) + s[j:]
    write(p, s)
    print("poke_legendaries.py 已加 yveltal")


# ---------------------------------------------------------------- 3. 匯入對照表
KALOS_DEX = {
    "talonflame": ("0663", "talonflame"),
    "noivern": ("0715", "noivern"),
    "aegislash": ("0681", "aegislash"),
    "hawlucha": ("0701", "hawlucha"),
    "aurorus": ("0699", "aurorus"),
    "tyrantrum": ("0697", "tyrantrum"),
}


def patch_import_maps():
    for fn in ("import_cobblemon_models.py", "fetch_cobblemon_assets.py"):
        p = os.path.join(ROOT, "tools", fn)
        s = read(p)
        if "talonflame" in s:
            print(f"{fn} 已有卡洛斯條目，跳過")
            continue
        nl = "\r\n" if "\r\n" in s else "\n"
        lines = []
        for pid, (dex, name) in KALOS_DEX.items():
            lines.append(f'    "{pid}":{" " * max(1, 14 - len(pid))}("{dex}", "{name}"),')
        i = s.find("SPECIES = {")
        j = s.find(nl + "}", i)
        s = s[:j] + nl + nl.join(lines) + s[j:]
        write(p, s)
        print(f"{fn} 已加 6 隻")


# ---------------------------------------------------------------- 4. lang
JA_NEW = {
    "yveltal": "イベルタル", "talonflame": "ファイアロー", "noivern": "オンバーン",
    "aegislash": "ギルガルド", "hawlucha": "ルチャブル", "aurorus": "アマルルガ",
    "tyrantrum": "ガチゴラス",
}
EN_NEW = {
    "yveltal": "Yveltal", "talonflame": "Talonflame", "noivern": "Noivern",
    "aegislash": "Aegislash", "hawlucha": "Hawlucha", "aurorus": "Aurorus",
    "tyrantrum": "Tyrantrum",
}


def patch_lang():
    p = os.path.join(ROOT, "tools", "gen_lang.py")
    s = read(p)
    if "yveltal" in s:
        print("gen_lang.py 已有新名字，跳過")
        return
    nl = "\r\n" if "\r\n" in s else "\n"
    for marker, table in (("JA_SPECIES = {", JA_NEW), ("EN_SPECIES = {", EN_NEW)):
        i = s.find(marker)
        j = s.find(nl + "}", i)
        add = "".join(f'    "{k}": "{v}",' + nl for k, v in table.items())
        s = s[:j] + nl + add.rstrip(nl) + s[j:]
    write(p, s)
    print("gen_lang.py 已加 7 隻 ja/en 名")


# ---------------------------------------------------------------- 5. poke_main.js
JS_TYPES = {
    "poke:yveltal": "dark", "poke:talonflame": "fire", "poke:noivern": "dragon",
    "poke:aegislash": "steel", "poke:hawlucha": "fighting", "poke:aurorus": "ice",
    "poke:tyrantrum": "rock",
}
JS_NAMES = {
    "poke:yveltal": "伊裴爾塔爾", "poke:talonflame": "烈箭鷹", "poke:noivern": "音波龍",
    "poke:aegislash": "堅盾劍怪", "poke:hawlucha": "摔角鷹人", "poke:aurorus": "冰雪巨龍",
    "poke:tyrantrum": "怪顎龍",
}
JS_ABILITY = {
    "poke:yveltal": "oblivionwing", "poke:talonflame": "bravebird", "poke:noivern": "boomburst",
    "poke:aegislash": "sacredsword", "poke:hawlucha": "flyingpress", "poke:aurorus": "icebeam",
    "poke:tyrantrum": "rockthrow",
}

NEW_MOVES = '''
  oblivionwing(self, t) {
    fx(t.dimension, t.location, "minecraft:soul_particle", "mob.wither.shoot", 1.5);
    hit(self, t, 7, "dark");
    try { self.addEffect("regeneration", 80, { amplifier: 1 }); } catch (e) {}
    try { t.addEffect("weakness", 100, { amplifier: 1 }); } catch (e) {}
    return "伊裴爾塔爾：死亡之翼！";
  },
  bravebird(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.enderdragon.flap", 1.3);
    hit(self, t, 7, "flying");
    knock(self, t, 2.2, 0.6);
    return "烈箭鷹：神鳥猛擊！";
  },
  boomburst(self, t) {
    const dim = t.dimension;
    fx(dim, t.location, "minecraft:knockback_roar_particle", "mob.warden.roar", 2.2);
    hit(self, t, 5, "normal");
    let extras = [];
    try {
      extras = dim.getEntities({ location: t.location, maxDistance: 6, families: ["monster"] });
    } catch (e) { extras = []; }
    for (const e of extras) {
      if (e.id === self.id || e.id === t.id) continue;
      try { hit(self, e, 3, "normal"); } catch (err) {}
    }
    return "音波龍：爆音波！";
  },
  sacredsword(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.irongolem.throw", 1.2);
    hit(self, t, 6, "steel");
    try { t.addEffect("slowness", 60, { amplifier: 1 }); } catch (e) {}
    return "堅盾劍怪：聖劍！";
  },
  flyingpress(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.player.attack.strong", 1.4);
    hit(self, t, 6, "fighting");
    knock(self, t, 1.8, 0.8);
    return "摔角鷹人：飛身重壓！";
  },
'''


def patch_js():
    p = os.path.join(ROOT, "tools", "poke_main.js")
    s = read(p)
    if "poke:yveltal" in s:
        print("poke_main.js 已有新物種，跳過")
        return
    nl = "\r\n" if "\r\n" in s else "\n"

    def add_entries(s, marker, table):
        i = s.find(marker)
        assert i > 0, marker
        j = s.find(nl + "};", i)
        add = "".join(f'  "{k}": "{v}",' + nl for k, v in table.items())
        return s[:j] + nl + add.rstrip(nl) + s[j:]

    s = add_entries(s, "const POKE_TYPE = {", JS_TYPES)
    s = add_entries(s, "const NAME_ZH = {", JS_NAMES)
    s = add_entries(s, "const ABILITY = {", JS_ABILITY)
    # 招式加在 MOVES 結尾（最後一個 move 之後）
    i = s.find("const MOVES = {")
    j = s.find(nl + "};", i)
    s = s[:j] + nl + NEW_MOVES.replace("\n", nl).rstrip(nl) + s[j:]
    write(p, s)
    print("poke_main.js 已加 7 隻 + 5 個招式")


if __name__ == "__main__":
    patch_species()
    patch_legendaries()
    patch_import_maps()
    patch_lang()
    patch_js()
