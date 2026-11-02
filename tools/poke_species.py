#!/usr/bin/env python3
"""第二批 12 隻寶可夢的 SPECS 與生怪設定。

只放「資料」：模型/貼圖由 tools/import_cobblemon_models.py 從 cobblemon-bedrock 匯入，
這裡的 body/head/legs 只用來算碰撞箱（及在沒有匯入模型時的後備程序模型）。
"""

# 共用調色盤小工具
def pal(body, accent, belly=None, limb=None, ear=None, tail=None):
    return dict(
        body=body, accent=accent,
        belly=belly or body, limb=limb or body,
        ear=ear or body, tail=tail or body,
    )


def face(eye="#1A1A1A", hl="#FFFFFF", cheek=None, mouth="#5A3B20"):
    return dict(eye=eye, eye_hl=hl, cheek=cheek or "#FFFFFF", mouth=mouth)


NEW_SPECS = [
    # ---------------- 水
    dict(id="psyduck", zh="可達鴨", en="Psyduck", hp=50, speed=0.28,
         body=(7, 7, 9), head=(9, 8, 8), legs=(2, 3, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="stub", stance="biped",
         pal=pal("#F5D67B", "#6B4E2E", belly="#F7E3A8"),
         face=face(mouth="#C86A2A"),
         hostile=False, family=["poke", "psyduck", "water"], scale=1.0),

    dict(id="gyarados", zh="暴鯉龍", en="Gyarados", hp=95, speed=0.28, damage=6,
         body=(10, 22, 14), head=(11, 10, 12), legs=(3, 2, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#2F6FD0", "#E8E4C9", belly="#F2EED0"),
         face=face(eye="#D83A2A", mouth="#7A1F1F"),
         hostile=True, family=["poke", "gyarados", "water", "dragon"], scale=1.15),

    dict(id="lapras", zh="拉普拉斯", en="Lapras", hp=130, speed=0.22, damage=4,
         body=(12, 14, 14), head=(10, 9, 10), legs=(3, 4, 4), ears=((1, 2, 1), (1, 2, 1)),
         tail="stub", stance="quad", shell=True,
         pal=pal("#6BA8D8", "#F2E8C9", belly="#F7F0D8"),
         face=face(mouth="#5A4A2A"),
         hostile=False, family=["poke", "lapras", "water"], scale=1.1),

    dict(id="greninja", zh="甲賀忍蛙", en="Greninja", hp=72, speed=0.42, damage=5,
         body=(9, 10, 10), head=(9, 8, 8), legs=(2, 7, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="stub", stance="biped",
         pal=pal("#3A7BD8", "#E8D8A0", belly="#F2E8C9"),
         face=face(eye="#E8E4D0", cheek="#E8A020", mouth="#2A2A3A"),
         hostile=False, family=["poke", "greninja", "water", "dark"], scale=1.0),

    # ---------------- 格鬥 / 岩石 / 超能
    dict(id="machamp", zh="怪力", en="Machamp", hp=90, speed=0.30, damage=7,
         body=(11, 10, 10), head=(9, 8, 8), legs=(3, 8, 4), ears=((1, 2, 1), (1, 2, 1)),
         tail="stub", stance="biped",
         pal=pal("#8A8AA0", "#E8E4D0", belly="#B0B0C0"),
         face=face(mouth="#3A3A4A"),
         hostile=False, family=["poke", "machamp", "fighting"], scale=1.1),

    dict(id="alakazam", zh="胡地", en="Alakazam", hp=55, speed=0.32, damage=5,
         body=(8, 9, 9), head=(9, 8, 8), legs=(2, 8, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="biped",
         pal=pal("#E8C24A", "#8A4A2A", belly="#F2D882"),
         face=face(mouth="#5A3B20"),
         hostile=False, family=["poke", "alakazam", "psychic"], scale=1.0),

    dict(id="onix", zh="大岩蛇", en="Onix", hp=35, speed=0.26, damage=5,
         body=(10, 24, 10), head=(10, 9, 10), legs=(3, 2, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad",
         pal=pal("#8A8A8E", "#5A5A5E", belly="#A8A8AC"),
         face=face(eye="#E8E4D0", mouth="#3A3A3E"),
         hostile=False, family=["poke", "onix", "rock", "ground"], scale=1.15),

    dict(id="lucario", zh="路卡利歐", en="Lucario", hp=70, speed=0.38, damage=6,
         body=(9, 10, 9), head=(8, 8, 8), legs=(2, 8, 3), ears=((2, 4, 1), (2, 4, 1)),
         tail="stub", stance="biped",
         pal=pal("#3A6BD8", "#E8E4D0", belly="#F2EED8"),
         face=face(eye="#D83A2A", mouth="#2A2A3A"),
         hostile=False, family=["poke", "lucario", "fighting", "steel"], scale=1.05),

    dict(id="gardevoir", zh="沙奈朵", en="Gardevoir", hp=68, speed=0.32, damage=5,
         body=(8, 10, 8), head=(8, 9, 8), legs=(2, 8, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="stub", stance="biped",
         pal=pal("#E0E8E8", "#3BA88A", belly="#F7FBFB"),
         face=face(eye="#C83A5A", cheek="#C83A5A", mouth="#5A3B20"),
         hostile=False, family=["poke", "gardevoir", "psychic", "fairy"], scale=1.1),

    # ---------------- 幽靈 / 妖精 / 龍
    dict(id="mimikyu", zh="謎擬Q", en="Mimikyu", hp=55, speed=0.33, damage=4,
         body=(7, 7, 8), head=(10, 9, 9), legs=(2, 2, 3), ears=((2, 4, 1), (2, 4, 1)),
         tail="stub", stance="biped",
         pal=pal("#C8B888", "#6B5A3A", belly="#D8C898"),
         face=face(eye="#1A1A1A", cheek="#E86A8A", mouth="#3A3A2A"),
         hostile=False, family=["poke", "mimikyu", "ghost", "fairy"], scale=0.95),

    dict(id="sylveon", zh="仙子伊布", en="Sylveon", hp=95, speed=0.32, damage=4,
         body=(7, 7, 9), head=(8, 8, 8), legs=(2, 3, 3), ears=((2, 6, 2), (2, 6, 2)),
         tail="bushy", stance="quad",
         pal=pal("#F2C8D8", "#F2E8D8", belly="#F7E8EE", ear="#F2C8D8"),
         face=face(eye="#3A5AA8", cheek="#E88AA8", mouth="#8A5A6A"),
         hostile=False, family=["poke", "sylveon", "fairy"], scale=1.0),

    dict(id="garchomp", zh="烈咬陸鯊", en="Garchomp", hp=108, speed=0.36, damage=7,
         body=(11, 12, 14), head=(10, 9, 11), legs=(3, 7, 4), ears=((1, 2, 1), (1, 2, 1)),
         tail="long", stance="quad", wings=True,
         pal=pal("#3A5A8A", "#E8D8A0", belly="#C8D0D8"),
         face=face(eye="#E8C24A", mouth="#2A2A3A"),
         hostile=True, family=["poke", "garchomp", "dragon", "ground"], scale=1.15),
]

# id: (population_control, brightness, biomes, weight, herd)
NEW_SPAWN_PROFILES = {
    "psyduck":   ("animal", (5, 15), ["river", "swamp", "beach"], 10, (1, 3)),
    "gyarados":  ("animal", (0, 15), ["ocean", "deep_ocean", "river"], 4, (1, 1)),
    "lapras":    ("animal", (0, 15), ["frozen_ocean", "deep_frozen_ocean", "ocean"], 3, (1, 2)),
    "greninja":  ("animal", (0, 10), ["swamp", "jungle", "mangrove_swamp"], 5, (1, 2)),
    "machamp":   ("animal", (7, 15), ["mountains", "stone_shore", "savanna"], 5, (1, 2)),
    "alakazam":  ("animal", (0, 7), ["desert", "mesa", "badlands"], 4, (1, 1)),
    "onix":      ("animal", (0, 15), ["mountains", "stone_shore", "dripstone_caves"], 6, (1, 2)),
    "lucario":   ("animal", (5, 15), ["snowy_plains", "taiga", "mountains"], 4, (1, 2)),
    "gardevoir": ("animal", (0, 7), ["flower_forest", "forest", "birch_forest"], 3, (1, 1)),
    "mimikyu":   ("animal", (0, 7), ["roofed_forest", "dark_forest", "swamp"], 3, (1, 1)),
    "sylveon":   ("animal", (7, 15), ["flower_forest", "meadow", "sunflower_plains"], 5, (1, 2)),
    "garchomp":  ("animal", (0, 7), ["desert", "mesa", "savanna"], 2, (1, 1)),
}
