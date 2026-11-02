#!/usr/bin/env python3
"""第三批：大型傳說寶可夢。

分兩種來源：
  * **有開源模型的**（lugia / hooh / rayquaza / latias / latios / regigigas / mew / xerneas / eternatus）
    —— 由 tools/import_cobblemon_models.py 從 cobblemon-bedrock 匯入高精度模型與貼圖，
       這裡的 body/head/legs 只用來算碰撞箱。
  * **沒有開源模型的**（dialga / palkia / giratina / arceus）
    —— Cobblemon 本身還沒做這四隻，kirbycope 的 Bedrock 移植也沒有，
       所以先用程序生成的大型方塊模型（之後有素材再換掉）。

scale 是整體放大倍率（1.0 = 一般寶可夢大小），傳說級別 1.8～2.8。
"""


def pal(body, accent, belly=None, limb=None, ear=None, tail=None):
    return dict(body=body, accent=accent, belly=belly or body, limb=limb or body,
                ear=ear or body, tail=tail or body)


def face(eye="#1A1A1A", hl="#FFFFFF", cheek=None, mouth="#5A3B20"):
    return dict(eye=eye, eye_hl=hl, cheek=cheek or "#FFFFFF", mouth=mouth)


LEGENDARY_SPECS = [
    # ---------------- 有 cobblemon 模型 ----------------
    dict(id="lugia", flyer=True, zh="洛奇亞", en="Lugia", hp=106, speed=0.42, damage=8,
         body=(14, 12, 20), head=(12, 11, 14), legs=(4, 5, 5), ears=((1, 3, 2), (1, 3, 2)),
         tail="long", stance="quad",
         pal=pal("#D8E4F0", "#5A7AA8", belly="#F2F6FA"),
         face=face(eye="#2A3A6A", mouth="#3A4A6A"),
         hostile=False, family=["poke", "lugia", "psychic"], scale=2.0),

    dict(id="hooh", flyer=True, zh="鳳王", en="Ho-Oh", hp=106, speed=0.40, damage=8,
         body=(13, 13, 19), head=(11, 10, 12), legs=(3, 6, 4), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="biped",
         pal=pal("#E8B03C", "#3AA05A", belly="#F5E0A0"),
         face=face(eye="#8A2A2A", mouth="#8A5A18"),
         hostile=False, family=["poke", "hooh", "fire"], scale=2.1),

    dict(id="rayquaza", flyer=True, zh="烈空坐", en="Rayquaza", hp=105, speed=0.46, damage=9,
         body=(10, 10, 34), head=(11, 9, 12), legs=(3, 4, 4), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#3F9A5A", "#1F5A3A", belly="#8AD8A0"),
         face=face(eye="#E8D040", mouth="#1F3A28"),
         hostile=False, family=["poke", "rayquaza", "dragon"], scale=2.6),

    dict(id="latias", flyer=True, zh="拉帝亞斯", en="Latias", hp=80, speed=0.55, damage=6,
         body=(9, 8, 15), head=(10, 8, 10), legs=(3, 4, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#E86A6A", "#F0E4E4", belly="#F5DCDC"),
         face=face(eye="#8A2A2A", mouth="#8A4A4A"),
         hostile=False, family=["poke", "latias", "dragon"], scale=1.6),

    dict(id="latios", flyer=True, zh="拉帝歐斯", en="Latios", hp=80, speed=0.55, damage=7,
         body=(9, 8, 15), head=(10, 8, 10), legs=(3, 4, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#4A8AD8", "#E8E8F0", belly="#C8DCF0"),
         face=face(eye="#B03030", mouth="#2A4A6A"),
         hostile=False, family=["poke", "latios", "dragon"], scale=1.6),

    dict(id="regigigas", zh="雷吉奇卡斯", en="Regigigas", hp=110, speed=0.25, damage=10,
         body=(18, 16, 16), head=(12, 10, 12), legs=(7, 8, 8), ears=((1, 2, 1), (1, 2, 1)),
         tail="stub", stance="biped",
         pal=pal("#E8E4D0", "#3A3A2A", belly="#F5F2E0"),
         face=face(eye="#E8A020", mouth="#3A3A2A"),
         hostile=False, family=["poke", "regigigas", "normal"], scale=2.4),

    dict(id="mew", flyer=True, zh="夢幻", en="Mew", hp=100, speed=0.46, damage=6,
         body=(6, 6, 8), head=(8, 7, 7), legs=(2, 3, 3), ears=((2, 4, 1), (2, 4, 1)),
         tail="long", stance="biped",
         pal=pal("#F2C0D8", "#F8E0EC", belly="#F8E8F0"),
         face=face(eye="#4A6AA8", mouth="#C87A9A"),
         hostile=False, family=["poke", "mew", "psychic"], scale=0.9),

    dict(id="xerneas", zh="哲爾尼亞斯", en="Xerneas", hp=126, speed=0.41, damage=8,
         body=(12, 13, 20), head=(11, 10, 14), legs=(3, 9, 4), ears=((2, 4, 1), (2, 4, 1)),
         tail="stub", stance="quad",
         pal=pal("#3A5A8A", "#60C8E8", belly="#2A3A5A"),
         face=face(eye="#60C8E8", mouth="#1F3A5A"),
         hostile=False, family=["poke", "xerneas", "fairy"], scale=2.2),

    dict(id="eternatus", flyer=True, zh="無極汰那", en="Eternatus", hp=140, speed=0.36, damage=10,
         body=(10, 12, 32), head=(9, 8, 10), legs=(3, 5, 4), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#6A3A8A", "#E83A6A", belly="#3A2A4A"),
         face=face(eye="#E83A6A", mouth="#2A1A3A"),
         hostile=True, family=["poke", "eternatus", "poison"], scale=2.8),

    # ---------------- 沒有開源模型：程序生成的大型版本 ----------------
    dict(id="dialga", zh="帝牙盧卡", en="Dialga", hp=100, speed=0.35, damage=10,
         body=(16, 15, 24), head=(15, 13, 16), legs=(5, 10, 6), ears=((2, 4, 2), (2, 4, 2)),
         tail="long", stance="quad",
         pal=pal("#4A6FA5", "#C8D8F0", belly="#9FB6D8"),
         face=face(eye="#E03C3C", mouth="#2A3A5A"),
         hostile=False, family=["poke", "dialga", "steel"], scale=2.6),

    dict(id="palkia", flyer=True, zh="帕路奇亞", en="Palkia", hp=90, speed=0.37, damage=10,
         body=(15, 16, 22), head=(14, 12, 14), legs=(5, 12, 6), ears=((2, 3, 2), (2, 3, 2)),
         tail="long", stance="biped",
         pal=pal("#D89AC8", "#F0E0F0", belly="#F5ECF5"),
         face=face(eye="#8A2A6A", mouth="#8A5A7A"),
         hostile=False, family=["poke", "palkia", "water"], scale=2.6),

    dict(id="giratina", flyer=True, zh="騎拉帝納", en="Giratina", hp=150, speed=0.33, damage=11,
         body=(18, 16, 26), head=(16, 12, 18), legs=(6, 8, 6), ears=((2, 4, 2), (2, 4, 2)),
         tail="long", stance="quad",
         pal=pal("#6A5A7A", "#C8B84A", belly="#8A7A9A"),
         face=face(eye="#E83A3A", mouth="#3A2A4A"),
         hostile=True, family=["poke", "giratina", "ghost"], scale=2.8),

    dict(id="arceus", flyer=True, zh="阿爾宙斯", en="Arceus", hp=120, speed=0.38, damage=12,
         body=(17, 16, 24), head=(15, 13, 16), legs=(5, 10, 6), ears=((2, 3, 2), (2, 3, 2)),
         tail="long", stance="quad",
         pal=pal("#E8E4D8", "#C8A840", belly="#F5F2E8"),
         face=face(eye="#3A8A5A", mouth="#8A7A4A"),
         hostile=False, family=["poke", "arceus", "normal"], scale=2.6),
]

# id: (population_control, brightness, biomes, weight, herd)
LEGENDARY_SPAWN_PROFILES = {
    "lugia":     ("monster", (0, 7),   ["deep_ocean", "ocean", "frozen_ocean"], 1, (1, 1)),
    "hooh":      ("animal",  (10, 15), ["mountains", "stony_peaks", "savanna"], 1, (1, 1)),
    "rayquaza":  ("monster", (10, 15), ["stony_peaks", "frozen_peaks", "mountains"], 1, (1, 1)),
    "latias":    ("animal",  (7, 15),  ["forest", "birch_forest", "jungle"], 1, (1, 1)),
    "latios":    ("animal",  (7, 15),  ["forest", "birch_forest", "jungle"], 1, (1, 1)),
    "regigigas": ("monster", (0, 7),   ["frozen_peaks", "ice_spikes", "snowy_taiga"], 1, (1, 1)),
    "mew":       ("animal",  (0, 15),  ["jungle", "cherry_grove", "flower_forest"], 1, (1, 1)),
    "xerneas":   ("animal",  (7, 15),  ["flower_forest", "meadow", "cherry_grove"], 1, (1, 1)),
    "eternatus": ("monster", (0, 7),   ["deep_dark", "roofed", "swamp"], 1, (1, 1)),
    "dialga":    ("monster", (0, 10),  ["stony_peaks", "mountains", "deep_dark"], 1, (1, 1)),
    "palkia":    ("monster", (0, 10),  ["deep_ocean", "ocean", "river"], 1, (1, 1)),
    "giratina":  ("monster", (0, 7),   ["deep_dark", "roofed", "swamp"], 1, (1, 1)),
    "arceus":    ("animal",  (10, 15), ["stony_peaks", "frozen_peaks", "meadow"], 1, (1, 1)),
}
