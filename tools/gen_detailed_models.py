#!/usr/bin/env python3
"""五隻「簡陋」寶可夢的細節重製：帝牙盧卡 / 帕路奇亞 / 騎拉帝納 / 戟脊龍 / 鹽石巨靈。

共同做法（與 gen_arceus_model.py 相同）
- 每個方塊指向 512×512 色塊表裡的一個純色格（box UV），不會有接縫錯位
- 骨頭命名刻意對齊 fix_models_anim 的分類：body/torso/torso2、neck/neck2/neck3、head、
  leg0..legN（只有上段進動畫）、tail/tail2/tail3、ear_l/ear_r
- 骨骼 20+、方塊 90+，四足/雙足/蛇形各自的站姿寫在 build 函式裡
"""
import json
import math
import os
import sys

from PIL import Image

W = H = 512
CELL = 64

# 每個物種一組 16 色色票（索引 0-15 對應色塊表位置）
PALETTES = {
    "dialga": [(0x3A5FA8, "bod"), (0x27406F, "bodD"), (0xB9C6D4, "steel"), (0x7D8B9C, "steelD"),
               (0x4FD8F0, "gem"), (0x1F6E80, "gemD"), (0xD8B84C, "gold"), (0xA3821F, "goldD"),
               (0xE8EEF4, "white"), (0x1A2A44, "dark"), (0xF04A3A, "eye"), (0x141414, "black"),
               (0x6F8FC8, "bodL"), (0x9FB0C4, "steelL"), (0x2A3A55, "belly"), (0xFFFFFF, "pure")],
    "palkia": [(0xF2E4EE, "bod"), (0xD8BFD0, "bodD"), (0xC85890, "mag"), (0x8E2F5F, "magD"),
               (0xE8E4F4, "pearl"), (0xB9A8D8, "pearlD"), (0xE84F8C, "gem"), (0x9A2C58, "gemD"),
               (0xFAF6FA, "white"), (0x5A4A62, "dark"), (0xF0D24A, "eye"), (0x141414, "black"),
               (0xFBD6E8, "bodL"), (0xE0D2F0, "pearlL"), (0xC8A8C0, "belly"), (0xFFFFFF, "pure")],
    "giratina": [(0x4A4A52, "bod"), (0x2A2A30, "bodD"), (0xD8B84C, "gold"), (0x8E6A18, "goldD"),
                 (0xC03028, "red"), (0x7A1A16, "redD"), (0x6A6A74, "grey"), (0x3A3A42, "greyD"),
                 (0xE8E4D8, "bone"), (0x1A1A1E, "dark"), (0xF04A3A, "eye"), (0x0E0E10, "black"),
                 (0x5E5E68, "bodL"), (0x9A9AA4, "greyL"), (0x24242A, "belly"), (0xFFFFFF, "pure")],
    "baxcalibur": [(0x8FC8E0, "bod"), (0x5F9AC0, "bodD"), (0xE8F4FA, "white"), (0xB9D8E8, "iceL"),
                   (0x4A88B0, "iceD"), (0x2F5F80, "iceDD"), (0xF0A83C, "amber"), (0xB87A18, "amberD"),
                   (0xFAFAFF, "pure"), (0x2A3A44, "dark"), (0xE84F3C, "eye"), (0x141414, "black"),
                   (0xA8DCEE, "bodL"), (0xCFE8F4, "iceXL"), (0x7AA8C0, "belly"), (0xFFFFFF, "pure2")],
    "garganacl": [(0xD8A88C, "salt"), (0xB07F62, "saltD"), (0xF0D0B8, "saltL"), (0x8E5F48, "saltDD"),
                  (0xF0B44A, "glow"), (0xB87A18, "glowD"), (0x6A4A38, "rock"), (0x4A3428, "rockD"),
                  (0xFAE8D8, "white"), (0x2A1A14, "dark"), (0xF0C24A, "eye"), (0x141414, "black"),
                  (0xE8C0A4, "saltXL"), (0xC89A7C, "saltM"), (0xA8825F, "belly"), (0xFFFFFF, "pure")],
}


def palette_map(pid):
    return {name: i for i, (_, name) in enumerate(PALETTES[pid])}


class Kit:
    def __init__(self, pid):
        self.pid = pid
        self.colors = palette_map(pid)
        self.bones = []

    def uv(self, name):
        i = self.colors[name]
        return [(i % 8) * CELL, (i // 8) * CELL]

    def bone(self, name, parent=None, pivot=(0, 0, 0), rotation=None):
        if isinstance(parent, dict):        # 允許直接傳父骨頭物件
            parent = parent["name"]
        b = {"name": name, "pivot": list(pivot)}
        if parent:
            b["parent"] = parent
        if rotation:
            b["rotation"] = list(rotation)
        b["cubes"] = []
        self.bones.append(b)
        return b

    def bx(self, bone, x0, y0, z0, sx, sy, sz, color, rot=None, pivot=None, inflate=0):
        c = {"origin": [x0, y0, z0], "size": [sx, sy, sz], "uv": self.uv(color)}
        if rot:
            c["rotation"] = list(rot)
            c["pivot"] = list(pivot or [x0 + sx / 2, y0 + sy / 2, z0 + sz / 2])
        if inflate:
            c["inflate"] = inflate
        bone["cubes"].append(c)

    def geo(self, ident):
        return {"format_version": "1.12.0", "minecraft:geometry": [{
            "description": {"identifier": ident, "texture_width": W, "texture_height": H,
                            "visible_bounds_width": 8, "visible_bounds_height": 8,
                            "visible_bounds_offset": [0, 3, 0]},
            "bones": self.bones}]}


# ============================================================ 帝牙盧卡
def build_dialga():
    k = Kit("dialga")
    body = k.bone("body", pivot=(0, 26, 0))
    k.bx(body, -9, 20, 2, 18, 12, 16, "bod")            # 後身
    k.bx(body, -10, 21, -12, 20, 12, 15, "bod")         # 胸身
    k.bx(body, -7, 18, -10, 14, 4, 24, "belly")         # 腹部
    k.bx(body, -6, 31, -6, 12, 3, 18, "steel")          # 背甲
    for i, z in enumerate((-10, -3, 4, 11)):            # 背脊鋼板
        k.bx(body, -2.5, 33, z, 5, 4 - i * 0.4, 5, "steelL")
    torso = k.bone("torso", parent="body", pivot=(0, 26, -12))
    k.bx(torso, -8, 21, -18, 16, 11, 7, "bod")          # 肩胸
    k.bx(torso, -5, 19, -19, 10, 6, 2, "steel")         # 胸甲
    k.bx(torso, -4.5, 19.4, -20.8, 9, 5.4, 2.4, "gem")    # 胸口鑽石（放大、更突出）
    k.bx(torso, -3.4, 20.6, -21.8, 6.8, 3, 1.6, "gemD")
    k.bx(torso, -2.2, 21.6, -22.4, 4.4, 1.6, 1.2, "pure")
    k.bx(torso, -9.4, 22, -16, 1.6, 9, 6, "steel")      # 左右鋼肩
    k.bx(torso, 7.8, 22, -16, 1.6, 9, 6, "steel")
    torso2 = k.bone("torso2", parent="torso", pivot=(0, 30, -16))
    k.bx(torso2, -5.5, 30, -20, 11, 6, 6, "bod")

    n1 = k.bone("neck", parent="torso2", pivot=(0, 33, -18))
    k.bx(n1, -4, 33, -22, 8, 7, 7, "bod")
    k.bx(n1, -4.6, 35, -16, 9.2, 3, 5, "steel")         # 頸後鋼片
    n2 = k.bone("neck2", parent="neck", pivot=(0, 39, -20))
    k.bx(n2, -3.5, 39, -24, 7, 6, 6, "bod")
    k.bx(n2, -4, 41, -18, 8, 2.6, 4, "steel")
    n3 = k.bone("neck3", parent="neck2", pivot=(0, 44, -22))
    k.bx(n3, -3, 44, -26, 6, 5, 6, "bod")
    k.bx(n3, -3.4, 46, -20, 6.8, 2.2, 3.6, "steelL")

    head = k.bone("head", parent="neck3", pivot=(0, 48, -23))
    k.bx(head, -4.5, 48, -30, 9, 6, 8, "bod")           # 顱
    k.bx(head, -3.4, 48, -35, 6.8, 4, 5, "bod")         # 吻
    k.bx(head, -2.8, 47.4, -34, 5.6, 1.4, 4.2, "steelD")  # 下顎
    k.bx(head, -4.6, 50, -30, 1, 4, 7, "steel")         # 左頰鋼片
    k.bx(head, 3.6, 50, -30, 1, 4, 7, "steel")
    k.bx(head, -3.4, 51.6, -32.6, 2.6, 1.8, 1.4, "eye")  # 左眼
    k.bx(head, 0.8, 51.6, -32.6, 2.6, 1.8, 1.4, "eye")   # 右眼
    k.bx(head, -1.2, 52.2, -33.2, 2.4, 1.2, 1, "gem")    # 額頭寶石
    k.bx(head, -1.6, 53.4, -26, 3.2, 2, 9, "steelL")     # 頭頂脊冠
    horn_l = k.bone("ear_l", parent="head", pivot=(-3.6, 52, -26))
    k.bx(horn_l, -6.4, 52.5, -27, 2.6, 3, 9, "steel", rot=[18, 0, 14], pivot=[-3.6, 52, -26])
    k.bx(horn_l, -7.4, 53.6, -19, 2, 2, 4, "steelL", rot=[18, 0, 14], pivot=[-3.6, 52, -26])
    horn_r = k.bone("ear_r", parent="head", pivot=(3.6, 52, -26))
    k.bx(horn_r, 3.8, 52.5, -27, 2.6, 3, 9, "steel", rot=[18, 0, -14], pivot=[3.6, 52, -26])
    k.bx(horn_r, 5.4, 53.6, -19, 2, 2, 4, "steelL", rot=[18, 0, -14], pivot=[3.6, 52, -26])

    for name, x, z in (("leg0", -8, -11), ("leg1", 8, -11), ("leg2", -8, 10), ("leg3", 8, 10)):
        up = k.bone(name, parent="body", pivot=(x, 20, z))
        k.bx(up, x - 4.2, 11, z - 4.2, 8.4, 10, 8.4, "bod")
        k.bx(up, x - 4.6, 17, z - 4.6, 9.2, 2.6, 9.2, "steel")     # 大腿鋼環
        low = k.bone(name + "_low", parent=name, pivot=(x, 11, z))
        k.bx(low, x - 3.2, 4, z - 3.2, 6.4, 8, 6.4, "bod")
        k.bx(low, x - 3.4, 7, z - 3.4, 6.8, 1.8, 6.8, "steelD")
        foot = k.bone(name + "_foot", parent=name + "_low", pivot=(x, 4, z))
        k.bx(foot, x - 3.6, 0, z - 4.2, 7.2, 4.4, 9, "bod")
        k.bx(foot, x - 3.8, 0, z - 4.6, 7.6, 1.6, 10, "steelDD" if "steelDD" in k.colors else "steelD")
        for cx in (-2.2, 0, 2.2):                                   # 三根鋼爪
            k.bx(foot, x + cx - 0.9, 0.4, z - 6.4, 1.8, 1.8, 2.4, "steelL")

    t1 = k.bone("tail", parent="body", pivot=(0, 27, 18))
    k.bx(t1, -3, 24, 18, 6, 6, 8, "bod", rot=[-12, 0, 0], pivot=[0, 27, 18])
    k.bx(t1, -1.4, 28.6, 19, 2.8, 2.4, 7, "steel", rot=[-12, 0, 0], pivot=[0, 27, 18])
    t2 = k.bone("tail2", parent="tail", pivot=(0, 25, 26))
    k.bx(t2, -2.4, 22, 26, 4.8, 5, 7, "bod", rot=[-18, 0, 0], pivot=[0, 25, 26])
    k.bx(t2, -1, 26.4, 27, 2, 2, 6, "steel", rot=[-18, 0, 0], pivot=[0, 25, 26])
    t3 = k.bone("tail3", parent="tail2", pivot=(0, 24, 33))
    k.bx(t3, -3.2, 20, 33, 6.4, 6.4, 6, "bod", rot=[-26, 0, 0], pivot=[0, 24, 33])
    for a in (0, 90, 180, 270):                                     # 尾端四片鋼刃
        rad = math.radians(a)
        k.bx(t3, -1.2 + 4.4 * math.cos(rad), 23 + 4.4 * math.sin(rad), 35, 2.4, 2.4, 6, "steelL",
             rot=[-26, 0, 0], pivot=[0, 24, 33])
    return k


# ============================================================ 帕路奇亞
def build_palkia():
    k = Kit("palkia")
    body = k.bone("body", pivot=(0, 28, 0))
    k.bx(body, -8, 22, -6, 16, 14, 16, "bod")
    k.bx(body, -6, 20, -4, 12, 4, 12, "belly")
    k.bx(body, -5, 34, -4, 10, 3, 12, "bodL")          # 背脊
    torso = k.bone("torso", parent="body", pivot=(0, 30, -6))
    k.bx(torso, -9, 24, -14, 18, 14, 9, "bod")
    k.bx(torso, -6, 20, -13, 12, 5, 7, "belly")
    k.bx(torso, -3, 30, -16, 6, 7, 3, "pearlL")        # 胸前珠光板
    # 肩上兩顆珍珠 + 粉紅環（帕路奇亞的標誌）
    for sx in (-1, 1):
        sh = k.bone("shoulder_" + ("l" if sx < 0 else "r"), parent="torso", pivot=(sx * 10, 34, -9))
        k.bx(sh, sx * 11 - 3, 31, -12, 6, 7, 7, "pearl")
        k.bx(sh, sx * 11 - 3.4, 30.4, -12.4, 6.8, 8.2, 7.8, "pearlL", inflate=0.2)
        for a in range(0, 360, 24):                     # 珍珠外圍粉紅環（15 顆圍成完整圓）
            rad = math.radians(a)
            k.bx(sh, sx * 11 - 1.1 + 6.2 * math.cos(rad), 34.4 + 6.2 * math.sin(rad), -8.6, 2.2, 2.2, 3.6,
                 "gem" if a % 72 == 0 else "mag")
    n1 = k.bone("neck", parent="torso", pivot=(0, 36, -10))
    k.bx(n1, -3.4, 36, -14, 6.8, 6, 6, "bod")
    n2 = k.bone("neck2", parent="neck", pivot=(0, 41, -12))
    k.bx(n2, -3, 41, -17, 6, 5, 6, "bod")
    n3 = k.bone("neck3", parent="neck2", pivot=(0, 45, -14))
    k.bx(n3, -2.6, 45, -20, 5.2, 4, 6, "bod")
    head = k.bone("head", parent="neck3", pivot=(0, 48, -16))
    k.bx(head, -4, 48, -25, 8, 6, 7, "bod")            # 顱
    k.bx(head, -3, 47.6, -30, 6, 4, 5, "bod")          # 吻
    k.bx(head, -2.4, 47, -29, 4.8, 1.4, 4, "magD")     # 下顎
    k.bx(head, -3, 50, -30.6, 2.2, 1.6, 1.2, "eye")
    k.bx(head, 0.8, 50, -30.6, 2.2, 1.6, 1.2, "eye")
    k.bx(head, -1.2, 51.4, -22, 2.4, 2, 8, "mag")      # 頭頂粉紅鰭
    fin_l = k.bone("ear_l", parent="head", pivot=(-3.4, 51, -22))
    k.bx(fin_l, -8.6, 51.4, -24, 6, 1.8, 7, "pearlL", rot=[0, 0, 26], pivot=[-3.4, 51, -22])
    k.bx(fin_l, -9.6, 52.2, -22, 4, 1.4, 5, "mag", rot=[0, 0, 26], pivot=[-3.4, 51, -22])
    fin_r = k.bone("ear_r", parent=head, pivot=(3.4, 51, -22))
    k.bx(fin_r, 2.6, 51.4, -24, 6, 1.8, 7, "pearlL", rot=[0, 0, -26], pivot=[3.4, 51, -22])
    k.bx(fin_r, 5.6, 52.2, -22, 4, 1.4, 5, "mag", rot=[0, 0, -26], pivot=[3.4, 51, -22])
    # 手臂
    for sx, tag in ((-1, "leg0"), (1, "leg1")):
        arm = k.bone(tag, parent="torso", pivot=(sx * 9, 32, -10))
        k.bx(arm, sx * 11 - 2.6, 22, -13, 5.2, 11, 5.6, "bod")
        k.bx(arm, sx * 11 - 3, 30, -13.4, 6, 3, 6.4, "mag")     # 上臂粉紅環
        low = k.bone(tag + "_low", parent=tag, pivot=(sx * 11, 22, -11))
        k.bx(low, sx * 11 - 2.2, 16, -12, 4.4, 7, 4.6, "bod")
        hand = k.bone(tag + "_hand", parent=tag + "_low", pivot=(sx * 11, 16, -11))
        k.bx(hand, sx * 11 - 2.6, 12.6, -13, 5.2, 3.6, 5.4, "bod")
        for c in (-1.6, 0, 1.6):                                 # 三爪
            k.bx(hand, sx * 11 + c - 0.7, 11.4, -15, 1.4, 1.4, 2.4, "pearl")
    # 腿
    for sx, tag in ((-1, "leg2"), (1, "leg3")):
        leg = k.bone(tag, parent="body", pivot=(sx * 7, 22, 4))
        k.bx(leg, sx * 7 - 3.4, 11, 1, 6.8, 12, 7, "bod")
        k.bx(leg, sx * 7 - 3.8, 18, 0.6, 7.6, 2.6, 7.8, "mag")
        low = k.bone(tag + "_low", parent=tag, pivot=(sx * 7, 11, 4))
        k.bx(low, sx * 7 - 2.8, 4, 1.4, 5.6, 8, 6, "bod")
        foot = k.bone(tag + "_foot", parent=tag + "_low", pivot=(sx * 7, 4, 4))
        k.bx(foot, sx * 7 - 3.2, 0, 0, 6.4, 4.4, 8.4, "bod")
        k.bx(foot, sx * 7 - 3.4, 0, -0.4, 6.8, 1.6, 9.4, "pearlD")
    t1 = k.bone("tail", parent="body", pivot=(0, 26, 10))
    k.bx(t1, -2.8, 23, 10, 5.6, 5.6, 8, "bod", rot=[-14, 0, 0], pivot=[0, 26, 10])
    t2 = k.bone("tail2", parent="tail", pivot=(0, 25, 18))
    k.bx(t2, -2.2, 21, 18, 4.4, 4.4, 7, "bod", rot=[-24, 0, 0], pivot=[0, 25, 18])
    t3 = k.bone("tail3", parent="tail2", pivot=(0, 23, 25))
    k.bx(t3, -3.4, 19, 25, 6.8, 6.8, 5.4, "pearlL", rot=[-34, 0, 0], pivot=[0, 23, 25])
    k.bx(t3, -1.4, 22, 27, 2.8, 2.8, 3.4, "gem", rot=[-34, 0, 0], pivot=[0, 23, 25])
    return k


# ============================================================ 騎拉帝納
def build_giratina():
    k = Kit("giratina")
    body = k.bone("body", pivot=(0, 30, 0))
    k.bx(body, -8, 24, -4, 16, 13, 18, "bod")
    k.bx(body, -6, 22, -2, 12, 3, 14, "belly")
    k.bx(body, -4, 36, -2, 8, 2.6, 14, "gold")          # 背脊金線
    k.bx(body, -4.4, 36.4, -2.4, 8.8, 2, 14.8, "goldD")
    # 六條腿（改造形態）
    for i, (x, z) in enumerate(((-8, -9), (8, -9), (-9, 1), (9, 1), (-7, 11), (7, 11))):
        up = k.bone(f"leg{i}", parent="body", pivot=(x, 24, z))
        k.bx(up, x - 3.2, 12, z - 3.2, 6.4, 13, 6.4, "bod")
        k.bx(up, x - 3.4, 20, z - 3.4, 6.8, 2.2, 6.8, "gold")
        low = k.bone(f"leg{i}_low", parent=f"leg{i}", pivot=(x, 12, z))
        k.bx(low, x - 2.4, 4, z - 2.4, 4.8, 8, 4.8, "bodD")
        foot = k.bone(f"leg{i}_foot", parent=f"leg{i}_low", pivot=(x, 4, z))
        k.bx(foot, x - 2.8, 0, z - 3.2, 5.6, 4, 7, "bod")
        for c in (-1.4, 1.4):
            k.bx(foot, x + c - 0.7, 0.2, z - 4.6, 1.4, 1.6, 2, "bone")
    torso = k.bone("torso", parent="body", pivot=(0, 32, -6))
    k.bx(torso, -7, 26, -14, 14, 13, 9, "bod")
    k.bx(torso, -5, 24, -13, 10, 3, 7, "belly")
    k.bx(torso, -3, 34, -16, 6, 4, 4, "red")            # 胸口紅斑
    # 兩片巨大的翼狀附肢
    for sx, tag in ((-1, "ear_l"), (1, "ear_r")):
        wing = k.bone(tag, parent=torso, pivot=(sx * 8, 36, -8))
        k.bx(wing, sx * 9 - 2, 34, -12, 4, 4, 9, "bodD", rot=[0, 0, sx * 8], pivot=(sx * 8, 36, -8))
        k.bx(wing, sx * 16 - 3, 40, -12, 6, 3, 12, "bodD", rot=[0, 0, sx * 26], pivot=(sx * 8, 36, -8))
        k.bx(wing, sx * 24 - 3.4, 46, -13, 6.8, 2.6, 14, "greyD", rot=[0, 0, sx * 44], pivot=(sx * 8, 36, -8))
        k.bx(wing, sx * 30 - 3, 52, -12, 6, 2.2, 11, "grey", rot=[0, 0, sx * 58], pivot=(sx * 8, 36, -8))
        k.bx(wing, sx * 14 - 5, 39, -11.6, 10, 9, 1.2, "greyD",
             rot=[0, 0, sx * 22], pivot=(sx * 8, 36, -8))     # 翼膜：把斷開的翼段連成一整片
        k.bx(wing, sx * 24 - 6, 45, -11.4, 12, 8, 1.2, "grey",
             rot=[0, 0, sx * 42], pivot=(sx * 8, 36, -8))
        for t in (0.35, 0.7):                            # 翼上的紅金條紋
            k.bx(wing, sx * (9 + 22 * t) - 1.2, 37 + 15 * t, -12.4, 2.4, 2.6, 12.8, "gold",
                 rot=[0, 0, sx * (8 + 50 * t)], pivot=(sx * 8, 36, -8))
    n1 = k.bone("neck", parent="torso", pivot=(0, 36, -14))
    k.bx(n1, -3.6, 36, -20, 7.2, 7, 7, "bod")
    k.bx(n1, -4, 34, -19, 8, 2.6, 5, "gold")
    n2 = k.bone("neck2", parent="neck", pivot=(0, 43, -17))
    k.bx(n2, -3.2, 43, -24, 6.4, 6, 7, "bod")
    k.bx(n2, -3.6, 41.4, -23, 7.2, 2.2, 5, "red")
    n3 = k.bone("neck3", parent="neck2", pivot=(0, 49, -20))
    k.bx(n3, -2.8, 49, -27, 5.6, 5, 6, "bod")
    head = k.bone("head", parent="neck3", pivot=(0, 53, -22))
    k.bx(head, -4.4, 53, -33, 8.8, 6, 8, "bod")         # 顱（長吻）
    k.bx(head, -3, 52.4, -37, 6, 3.4, 5, "bod")
    k.bx(head, -2.4, 51.8, -36, 4.8, 1.2, 4, "greyD")   # 下顎
    k.bx(head, -3.6, 55, -33, 1, 4.4, 7.4, "gold")      # 頭側金板
    k.bx(head, 2.6, 55, -33, 1, 4.4, 7.4, "gold")
    k.bx(head, -3.2, 56, -34.4, 2.4, 1.8, 1.4, "eye")   # 紅眼
    k.bx(head, 0.8, 56, -34.4, 2.4, 1.8, 1.4, "eye")
    k.bx(head, -1.4, 57.4, -28, 2.8, 2, 8, "goldD")     # 頭冠
    for sx in (-1, 1):                                   # 兩側尖角
        k.bx(head, sx * 4.4 - 1.2, 56, -30, 2.4, 2.4, 8, "grey",
             rot=[26, 0, sx * 16], pivot=(sx * 4.4, 56, -30))
    t1 = k.bone("tail", parent="body", pivot=(0, 28, 14))
    k.bx(t1, -3, 24, 14, 6, 6, 9, "bod", rot=[-10, 0, 0], pivot=[0, 28, 14])
    t2 = k.bone("tail2", parent="tail", pivot=(0, 26, 23))
    k.bx(t2, -2.4, 21, 23, 4.8, 5, 8, "bod", rot=[-20, 0, 0], pivot=[0, 26, 23])
    k.bx(t2, -2.8, 25, 24, 5.6, 2, 7, "gold", rot=[-20, 0, 0], pivot=[0, 26, 23])
    t3 = k.bone("tail3", parent="tail2", pivot=(0, 23, 31))
    k.bx(t3, -4, 19, 31, 8, 8, 6, "bodD", rot=[-30, 0, 0], pivot=[0, 23, 31])
    for a in (0, 120, 240):
        rad = math.radians(a)
        k.bx(t3, -1.4 + 5 * math.cos(rad), 23 + 5 * math.sin(rad), 33, 2.8, 2.8, 5, "red",
             rot=[-30, 0, 0], pivot=[0, 23, 31])
    return k


# ============================================================ 戟脊龍
def build_baxcalibur():
    k = Kit("baxcalibur")
    body = k.bone("body", pivot=(0, 24, 0))
    k.bx(body, -8, 18, 0, 16, 12, 16, "bod")
    k.bx(body, -6, 16, 1, 12, 3, 14, "belly")
    k.bx(body, -3, 29, 0, 6, 3, 14, "iceL")            # 背冰脊
    torso = k.bone("torso", parent="body", pivot=(0, 25, -8))
    k.bx(torso, -8.5, 18, -14, 17, 13, 9, "bod")
    k.bx(torso, -6, 16, -13, 12, 3, 8, "belly")
    k.bx(torso, -5, 19, -15.4, 10, 8, 1.6, "iceL")     # 胸前冰甲
    k.bx(torso, -3.4, 21, -16.2, 6.8, 4.6, 1.2, "iceDow" if "iceDow" in k.colors else "iceD")
    # 巨大主刃背棘（戟脊龍的招牌：一整片高聳冰刃，不是三根等高細柱）
    blade = k.bone("spike0", parent=body, pivot=(0, 30, 0))
    k.bx(blade, -2.4, 30, -10, 4.8, 13, 21, "iceL")               # 刃體下半（貼合背脊）
    k.bx(blade, -1.9, 41, -9, 3.8, 13, 18, "white")               # 刃體中段
    k.bx(blade, -1.2, 52, -6.5, 2.4, 9, 13, "iceXL")              # 刃尖
    k.bx(blade, -2.8, 30, -10.4, 5.6, 9, 1.6, "iceD")             # 刃前緣
    k.bx(blade, -2.8, 30, 10, 5.6, 9, 1.6, "iceD")                # 刃後緣
    for zz, hh in ((-5, 7), (5, 6)):                              # 兩片貼身小側鰭
        k.bx(blade, -1.5, 33, zz, 3, hh, 4, "iceD")
    n1 = k.bone("neck", parent="torso", pivot=(0, 27, -13))
    k.bx(n1, -4, 27, -18, 8, 7, 7, "bod")
    k.bx(n1, -4.4, 32, -17, 8.8, 2.6, 5, "iceL")
    n2 = k.bone("neck2", parent="neck", pivot=(0, 33, -16))
    k.bx(n2, -3.4, 33, -22, 6.8, 6, 7, "bod")
    n3 = k.bone("neck3", parent="neck2", pivot=(0, 38, -19))
    k.bx(n3, -3, 38, -26, 6, 5, 7, "bod")
    head = k.bone("head", parent="neck3", pivot=(0, 41, -21))
    k.bx(head, -4, 41, -33, 8, 6, 8, "bod")            # 長吻顱
    k.bx(head, -3, 40.4, -38, 6, 3.6, 6, "bod")
    k.bx(head, -2.4, 39.8, -37, 4.8, 1.4, 5, "iceDD")
    k.bx(head, -3, 44, -33.4, 2.2, 1.8, 1.4, "eye")
    k.bx(head, 0.8, 44, -33.4, 2.2, 1.8, 1.4, "eye")
    for i in range(6):                                   # 上下排牙
        k.bx(head, -3.2 + i * 1.2, 40.2, -38.6, 0.9, 1.2, 0.9, "white")
        k.bx(head, -3.2 + i * 1.2, 42.4, -38.6, 0.9, 1.2, 0.9, "white")
    k.bx(head, -1.6, 45.6, -30, 3.2, 2, 9, "iceL")      # 頭頂冰冠
    horn_l = k.bone("ear_l", parent="head", pivot=(-3.4, 45, -26))
    k.bx(horn_l, -5.6, 45, -29, 2.4, 2.4, 9, "iceD", rot=[12, 0, 10], pivot=[-3.4, 45, -26])
    horn_r = k.bone("ear_r", parent="head", pivot=(3.4, 45, -26))
    k.bx(horn_r, 3.4, 45, -29, 2.4, 2.4, 9, "iceD", rot=[12, 0, -10], pivot=[3.4, 45, -26])
    for name, x, z in (("leg0", -8, -10), ("leg1", 8, -10), ("leg2", -8, 9), ("leg3", 8, 9)):
        up = k.bone(name, parent="body", pivot=(x, 19, z))
        k.bx(up, x - 4, 9, z - 4, 8, 11, 8, "bod")
        k.bx(up, x - 4.3, 16, z - 4.3, 8.6, 2.6, 8.6, "iceL")
        low = k.bone(name + "_low", parent=name, pivot=(x, 9, z))
        k.bx(low, x - 3, 3, z - 3, 6, 7, 6, "bod")
        foot = k.bone(name + "_foot", parent=name + "_low", pivot=(x, 3, z))
        k.bx(foot, x - 3.4, 0, z - 4, 6.8, 3.4, 8.6, "bod")
        k.bx(foot, x - 3.6, 0, z - 4.4, 7.2, 1.4, 9.4, "iceDD")
        for c in (-1.8, 0, 1.8):
            k.bx(foot, x + c - 0.8, 0.4, z - 6, 1.6, 1.4, 2.2, "white")
    t1 = k.bone("tail", parent="body", pivot=(0, 24, 16))
    k.bx(t1, -3, 21, 16, 6, 6, 9, "bod", rot=[-12, 0, 0], pivot=[0, 24, 16])
    t2 = k.bone("tail2", parent="tail", pivot=(0, 23, 24))
    k.bx(t2, -2.4, 18, 24, 4.8, 5, 8, "bod", rot=[-22, 0, 0], pivot=[0, 23, 24])
    k.bx(t2, -1.2, 22, 25, 2.4, 3, 7, "iceL", rot=[-22, 0, 0], pivot=[0, 23, 24])
    t3 = k.bone("tail3", parent="tail2", pivot=(0, 21, 32))
    k.bx(t3, -3.6, 17, 32, 7.2, 7.2, 6, "bodD", rot=[-32, 0, 0], pivot=[0, 21, 32])
    for a in (0, 90, 180, 270):
        rad = math.radians(a)
        k.bx(t3, -1.2 + 4.6 * math.cos(rad), 21 + 4.6 * math.sin(rad), 34, 2.4, 2.4, 5, "white",
             rot=[-32, 0, 0], pivot=[0, 21, 32])
    return k


# ============================================================ 鹽石巨靈
def build_garganacl():
    k = Kit("garganacl")
    body = k.bone("body", pivot=(0, 30, 0))
    k.bx(body, -10, 20, -6, 20, 20, 14, "salt")          # 巨大軀幹
    k.bx(body, -8, 18, -4, 16, 4, 10, "saltD")
    for i, (x, y, z, s) in enumerate(((-6, 30, -8, 7), (3, 34, -7, 6), (-2, 26, -9, 5),
                                      (5, 24, -8, 4.5), (-8, 24, -7, 4))):
        k.bx(body, x, y, z, s, s * 0.8, 3, "saltL" if i % 2 else "saltXL")   # 身上鹽晶
    torso = k.bone("torso", parent="body", pivot=(0, 34, -6))
    k.bx(torso, -8, 32, -14, 16, 12, 9, "salt")          # 上胸
    k.bx(torso, -5, 30, -15, 10, 6, 2, "glow")           # 胸口發光核心
    k.bx(torso, -3.4, 31, -15.8, 6.8, 4, 1.2, "glowD")
    for sx in (-1, 1):                                    # 巨大肩岩
        sh = k.bone("shoulder_" + ("l" if sx < 0 else "r"), parent=torso, pivot=(sx * 11, 36, -8))
        k.bx(sh, sx * 12 - 5, 32, -13, 10, 10, 11, "saltD")
        k.bx(sh, sx * 12 - 4, 38, -11, 8, 6, 8, "saltM" if "saltM" in k.colors else "salt")
        k.bx(sh, sx * 12 - 2, 42, -9, 5, 4, 5, "saltXL")
    head = k.bone("head", parent="torso", pivot=(0, 44, -9))
    k.bx(head, -5.5, 44, -16, 11, 9, 8, "salt")
    k.bx(head, -4.5, 43, -18, 9, 4, 3, "saltL")          # 下顎
    k.bx(head, -3.6, 48, -16.6, 2.6, 2.4, 1.2, "glow")   # 發光眼
    k.bx(head, 1, 48, -16.6, 2.6, 2.4, 1.2, "glow")
    k.bx(head, -1.4, 51, -12, 2.8, 3, 7, "saltD")
    k.bx(head, -4.2, 50.4, -16.4, 8.4, 1.6, 1.2, "saltD")   # 眉脊
    k.bx(head, -3.4, 45.6, -18.4, 6.8, 1.3, 1, "rockD")     # 嘴線
    for sx in (-1, 1):                                    # 頭上鹽晶簇
        k.bx(head, sx * 3.4 - 1.6, 50, -14, 3.2, 5, 3.2, "saltXL",
             rot=[0, 0, sx * 18], pivot=(sx * 3.4, 50, -13))
    # 背部與肩上的鹽晶簇（鹽石巨靈的招牌：整塊鹽結晶突出體外）
    for (x, y, z, w, hgt) in ((-9, 40, 2, 5, 7), (4, 42, 3, 6, 8), (-3, 38, 6, 4, 6),
                              (8, 36, 4, 5, 7), (-7, 33, 5, 4, 5)):
        k.bx(body, x, y, z, w, hgt, w, "saltXL")
        k.bx(body, x + 0.8, y + hgt - 2, z + 0.8, w - 1.6, 3, w - 1.6, "white")
    for sx, tag in ((-1, "leg0"), (1, "leg1")):
        arm = k.bone(tag, parent=torso, pivot=(sx * 12, 33, -8))
        k.bx(arm, sx * 15 - 4, 20, -12, 8, 14, 8, "saltD")
        for j, yy in enumerate((26, 22)):                # 手臂鹽晶段
            k.bx(arm, sx * 15 - 4.6, yy, -12.6, 9.2, 3, 9.2, "salt" if j else "saltM" if "saltM" in k.colors else "saltL")
        hand = k.bone(tag + "_hand", parent=tag, pivot=(sx * 15, 20, -8))
        k.bx(hand, sx * 15 - 5, 13, -13, 10, 8, 10, "salt")
        k.bx(hand, sx * 15 - 4, 11, -12, 8, 3, 8, "saltD")
        for c in (-3, 0, 3):
            k.bx(hand, sx * 15 + c - 1.2, 9, -14, 2.4, 3, 4, "saltXL")
    for sx, tag in ((-1, "leg2"), (1, "leg3")):
        leg = k.bone(tag, parent="body", pivot=(sx * 6, 20, 2))
        k.bx(leg, sx * 6 - 4, 8, -2, 8, 13, 9, "saltD")
        k.bx(leg, sx * 6 - 4.4, 15, -2.4, 8.8, 3, 9.8, "saltL")
        low = k.bone(tag + "_low", parent=tag, pivot=(sx * 6, 8, 2))
        k.bx(low, sx * 6 - 3.4, 3, -1, 6.8, 6, 7, "salt")
        foot = k.bone(tag + "_foot", parent=tag + "_low", pivot=(sx * 6, 3, 2))
        k.bx(foot, sx * 6 - 4.4, 0, -4, 8.8, 3.4, 11, "saltD")
        k.bx(foot, sx * 6 - 4.6, 0, -4.4, 9.2, 1.4, 11.8, "rockD")
    t1 = k.bone("tail", parent="body", pivot=(0, 24, 8))
    k.bx(t1, -4, 18, 8, 8, 8, 9, "saltD", rot=[-14, 0, 0], pivot=[0, 24, 8])
    t2 = k.bone("tail2", parent="tail", pivot=(0, 21, 16))
    k.bx(t2, -3, 15, 16, 6, 6, 7, "salt", rot=[-24, 0, 0], pivot=[0, 21, 16])
    k.bx(t2, -2, 19, 17, 4, 4, 5, "saltXL", rot=[-24, 0, 0], pivot=[0, 21, 16])
    return k


BUILDERS = {"dialga": build_dialga, "palkia": build_palkia, "giratina": build_giratina,
            "baxcalibur": build_baxcalibur, "garganacl": build_garganacl}
IDENT = {pid: f"geometry.poke_{pid}_detailed" for pid in BUILDERS}


def make_texture(pid, path, shiny=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for i, (rgb, _name) in enumerate(PALETTES[pid]):
        r, g, b = (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF
        if shiny:                                  # 異色：整體提亮 + 偏紫/偏青
            avg = (r + g + b) // 3
            if pid in ("baxcalibur", "garganacl"):
                r, g, b = min(255, int(r * 0.85 + avg * 0.3)), min(255, int(g * 0.8)), min(255, int(b * 1.05 + 20))
            else:
                r, g, b = min(255, int(r * 1.15 + 18)), min(255, int(g * 0.85)), min(255, int(b * 1.2 + 25))
        x0, y0 = (i % 8) * CELL, (i // 8) * CELL
        for y in range(y0, y0 + CELL):
            for x in range(x0, x0 + CELL):
                px[x, y] = (r, g, b, 255)
    img.save(path)


def main(pack_dir, shiny=False):
    rp = os.path.join(pack_dir, "rp")
    for pid, fn in BUILDERS.items():
        k = fn()
        if shiny:
            make_texture(pid, os.path.join(rp, "textures", "entity", "pokemon", f"{pid}_shiny.png"), True)
            continue
        geo_path = os.path.join(rp, "models", "entity", f"{pid}.geo.json")
        os.makedirs(os.path.dirname(geo_path), exist_ok=True)
        json.dump(k.geo(IDENT[pid]), open(geo_path, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
        make_texture(pid, os.path.join(rp, "textures", "entity", "pokemon", f"{pid}.png"))
        cubes = sum(len(b["cubes"]) for b in k.bones)
        print(f"{pid:<12} 骨骼 {len(k.bones):>3}  方塊 {cubes:>3}")
        for target in (pid, f"{pid}_shiny"):
            ep = os.path.join(rp, "entity", f"{target}.entity.json")
            if not os.path.exists(ep):
                continue
            d = json.load(open(ep, encoding="utf-8"))
            desc = d["minecraft:client_entity"]["description"]
            desc["geometry"] = {"default": IDENT[pid]}
            desc["textures"] = {"default": f"textures/entity/pokemon/{target}"}
            json.dump(d, open(ep, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    if shiny:
        print("異色貼圖完成")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "packs/pokemon", shiny="--shiny" in sys.argv)
