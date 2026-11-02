#!/usr/bin/env python3
"""生成「寶可夢城市 + 傳送廣場」的指令清單（給 BDS console 執行）。

用法：python3 gen_world_plaza.py > /tmp/plaza_cmds.txt
座標固定在超平坦世界：地面方塊 y=-61、站立高度 y=-60。
"""
SB = "minecraft:stone_bricks"
PAPER = "minecraft:quartz_block"
DARK = "minecraft:blackstone"
GLOW = "minecraft:sea_lantern"
WOOD = "minecraft:oak_fence"

out = []
def f(x1, y1, z1, x2, y2, z2, block, mode="replace"):
    out.append(f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block} {mode}")
def s(x, y, z, block):
    out.append(f"setblock {x} {y} {z} {block}")

# ---------------------------------------------------------------- 廣場
out.append("tickingarea add -32 -64 -32 32 0 512 plaza")
f(-20, -61, -20, 20, -61, 20, SB)
f(-16, -61, -16, 16, -61, 16, "minecraft:polished_andesite")
f(-9, -61, -9, 9, -61, 9, "minecraft:polished_diorite")
# 中央噴泉（中心方塊是 lodestone＝腳本的啟用標記）
f(-3, -61, -3, 3, -61, 3, PAPER)
f(-2, -61, -2, 2, -61, 2, "minecraft:lodestone")
f(-3, -60, -3, 3, -60, 3, PAPER)
f(-2, -60, -2, 2, -60, 2, "minecraft:water")
# 四座傳送台（3x3 海晶燈）
f(-1, -61, -16, 1, -61, -14, GLOW)   # 北：寶可夢城市
f(14, -61, -1, 16, -61, 1, GLOW)     # 東：動物園（施工中）
f(-16, -61, -1, -14, -61, 1, GLOW)   # 西：海底世界（施工中）
f(-1, -61, 14, 1, -61, 16, GLOW)     # 南：建築練習場
# 四座拱門
for (ax, az) in ((-2, -18), (2, -18), (-2, 18), (2, 18), (-18, -2), (-18, 2), (18, -2), (18, 2)):
    f(ax, -61, az, ax, -58, az, DARK)
f(-2, -57, -18, 2, -57, -18, DARK)
f(-2, -57, 18, 2, -57, 18, DARK)
f(-18, -57, -2, -18, -57, 2, DARK)
f(18, -57, -2, 18, -57, 2, DARK)
# 四角路燈
for (lx, lz) in ((-18, -18), (18, -18), (-18, 18), (18, 18)):
    s(lx, -60, lz, WOOD)
    s(lx, -59, lz, GLOW)

# ---------------------------------------------------------------- 寶可夢城市
CX = 400
f(CX - 16, -61, -16, CX + 16, -61, 16, "minecraft:grass_block")  # 中央草坪（先鋪，否則會蓋掉路口）
f(CX - 4, -61, -32, CX + 4, -61, 32, SB)        # 南北主路
f(CX - 30, -61, -4, CX + 30, -61, 4, SB)        # 東西大路
# 寶可夢中心（北側）
f(CX - 8, -61, 10, CX + 8, -61, 20, PAPER)              # 地板
f(CX - 8, -60, 10, CX + 8, -60, 10, PAPER)              # 南牆
f(CX - 8, -60, 20, CX + 8, -60, 20, PAPER)              # 北牆
f(CX - 8, -60, 10, CX - 8, -60, 20, PAPER)              # 西牆
f(CX + 8, -60, 10, CX + 8, -60, 20, PAPER)              # 東牆
f(CX - 8, -59, 10, CX + 8, -59, 10, PAPER)
f(CX - 8, -59, 20, CX + 8, -59, 20, PAPER)
f(CX - 8, -59, 10, CX - 8, -59, 20, PAPER)
f(CX + 8, -59, 10, CX + 8, -59, 20, PAPER)
f(CX - 8, -58, 10, CX + 8, -58, 10, "minecraft:light_blue_stained_glass")
f(CX - 8, -58, 20, CX + 8, -58, 20, PAPER)
f(CX - 8, -58, 10, CX - 8, -58, 20, PAPER)
f(CX + 8, -58, 10, CX + 8, -58, 20, PAPER)
f(CX - 9, -57, 9, CX + 9, -57, 21, "minecraft:red_concrete")     # 屋頂
f(CX - 1, -60, 10, CX + 1, -58, 10, "minecraft:air")            # 大門
s(CX - 4, -60, 16, "poke:healing_machine")
s(CX + 4, -60, 16, "poke:pc")
s(CX, -58, 18, GLOW)
s(CX, -56, 15, "minecraft:red_concrete")                        # 屋頂招牌
# 商店（南側）
f(CX - 6, -61, -20, CX + 6, -61, -10, "minecraft:polished_granite")
f(CX - 6, -60, -20, CX + 6, -60, -20, "minecraft:white_terracotta")
f(CX - 6, -60, -10, CX + 6, -60, -10, "minecraft:white_terracotta")
f(CX - 6, -60, -20, CX - 6, -60, -10, "minecraft:white_terracotta")
f(CX + 6, -60, -20, CX + 6, -60, -10, "minecraft:white_terracotta")
f(CX - 6, -59, -20, CX + 6, -59, -20, "minecraft:white_terracotta")
f(CX - 6, -59, -10, CX + 6, -59, -10, "minecraft:white_terracotta")
f(CX - 6, -59, -20, CX - 6, -59, -10, "minecraft:white_terracotta")
f(CX + 6, -59, -20, CX + 6, -59, -10, "minecraft:white_terracotta")
f(CX - 7, -58, -21, CX + 7, -58, -9, "minecraft:blue_concrete")
f(CX - 1, -60, -10, CX + 1, -58, -10, "minecraft:air")
s(CX + 4, -60, -16, "minecraft:barrel")
s(CX + 2, -60, -16, "minecraft:chest")
# 兩排住宅
HOUSES = [
    (-24, 8, "minecraft:orange_concrete"), (-24, -16, "minecraft:lime_concrete"),
    (24, 8, "minecraft:yellow_concrete"), (24, -16, "minecraft:magenta_concrete"),
    (-14, -24, "minecraft:cyan_concrete"), (14, -24, "minecraft:purple_concrete"),
]
for (hx, hz, roof) in HOUSES:
    f(CX + hx - 3, -61, hz - 3, CX + hx + 3, -61, hz + 3, "minecraft:oak_planks")
    f(CX + hx - 3, -60, hz - 3, CX + hx + 3, -60, hz + 3, "minecraft:oak_planks")
    f(CX + hx - 3, -59, hz - 3, CX + hx + 3, -59, hz - 3, PAPER)
    f(CX + hx - 3, -59, hz + 3, CX + hx + 3, -59, hz + 3, PAPER)
    f(CX + hx - 3, -59, hz - 3, CX + hx - 3, -59, hz + 3, PAPER)
    f(CX + hx + 3, -59, hz - 3, CX + hx + 3, -59, hz + 3, PAPER)
    f(CX + hx - 4, -58, hz - 4, CX + hx + 4, -58, hz + 4, roof)
    s(CX + hx, -60, hz + 3, "minecraft:air")
# 路燈與樹籬
z = -30
while z <= 30:
    for lx in (CX - 6, CX + 6):
        s(lx, -60, z, WOOD)
        s(lx, -59, z, GLOW)
    z += 10
f(CX - 31, -61, -5, CX - 31, -61, 5, "minecraft:oak_leaves")
f(CX + 31, -61, -5, CX + 31, -61, 5, "minecraft:oak_leaves")
# 回程傳送台
f(CX - 1, -61, -29, CX + 1, -61, -27, GLOW)
for (ax, az) in ((CX - 2, -30), (CX + 2, -30)):
    f(ax, -61, az, ax, -58, az, DARK)
f(CX - 2, -57, -30, CX + 2, -57, -30, DARK)

# ---------------------------------------------------------------- 建築練習場
f(-30, -61, 370, 30, -61, 430, "minecraft:smooth_stone")
f(-32, -61, 368, 32, -61, 368, "minecraft:chiseled_stone_bricks")
f(-32, -61, 432, 32, -61, 432, "minecraft:chiseled_stone_bricks")
f(-32, -61, 368, -32, -61, 432, "minecraft:chiseled_stone_bricks")
f(32, -61, 368, 32, -61, 432, "minecraft:chiseled_stone_bricks")
f(-1, -61, 371, 1, -61, 373, GLOW)      # 回廣場的台
f(-30, -60, 400, -30, -58, 400, DARK)
f(30, -60, 400, 30, -58, 400, DARK)

print("\n".join(out))
