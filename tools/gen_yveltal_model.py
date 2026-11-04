#!/usr/bin/env python3
"""伊裴爾塔爾（Yveltal）高精度方塊模型產生器。

獨立一支，避免動到 gen_detailed_models.py 既有內容：
  python3 tools/gen_yveltal_model.py packs/pokemon [--shiny]

產出
  rp/models/entity/yveltal.geo.json          （identifier geometry.poke_yveltal_detailed）
  rp/textures/entity/pokemon/yveltal.png
  rp/textures/entity/pokemon/yveltal_shiny.png（--shiny）
  rp/entity/yveltal[_shiny].entity.json      geometry / textures 指到上面兩個

骨骼命名刻意對齊 fix_models_anim 與 fix_flyers 的分類：
  body/torso、neck/neck2、head、ear_l/ear_r、wing_l/wing_l2/wing_l3（右側 wing_r…）、
  tail/tail2/tail3、leg0/leg0_low/leg0_foot（右 leg1）
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_detailed_models import Kit, W, H, CELL, PALETTES, make_texture  # noqa: E402

IDENT = "geometry.poke_yveltal_detailed"

# 破壞之繭：黑栗色軀幹、灰白胸羽、鮮紅紋路、青色眼
PALETTES["yveltal"] = [
    (0x2A1A22, "bod"), (0x150C12, "bodD"), (0xC02838, "red"), (0x7A1622, "redD"),
    (0xE84858, "redL"), (0xD8D2CE, "grey"), (0xA8A29E, "greyD"), (0x4A4A52, "beak"),
    (0x2E2E36, "beakD"), (0x5AC8E8, "eye"), (0x0E0A0E, "black"), (0xFFFFFF, "pure"),
    (0x43303A, "bodL"), (0x3A2830, "belly"), (0x241820, "wing"), (0x120C10, "wingD"),
]


def build_yveltal():
    k = Kit("yveltal")

    # ------------------------------------------------ 軀幹
    body = k.bone("body", pivot=(0, 30, 0))
    k.bx(body, -8, 24, -10, 16, 14, 18, "bod")            # 主軀幹
    k.bx(body, -6, 21, -8, 12, 4, 14, "belly")            # 腹部
    k.bx(body, -7, 34, -8, 14, 4, 14, "bodL")             # 背甲
    k.bx(body, -8.6, 28, -6, 1, 8, 10, "red")             # 左側紅紋
    k.bx(body, 7.6, 28, -6, 1, 8, 10, "red")              # 右側紅紋
    k.bx(body, -6, 20, 5, 12, 6, 9, "wing")               # 尾根覆羽
    # 灰白胸羽（三層，招牌的領口）
    k.bx(body, -9, 26, -13, 18, 9, 4, "grey")
    k.bx(body, -7, 22, -12, 14, 6, 3, "greyD")
    k.bx(body, -5, 19, -11, 10, 5, 3, "grey")
    k.bx(body, -2, 27, -14, 4, 7, 1.5, "redL")            # 胸口紅芯
    k.bx(body, -7, 33, -12, 14, 3, 3, "redD")             # 肩前紅帶

    # ------------------------------------------------ 肩胸
    torso = k.bone("torso", parent="body", pivot=(0, 34, -6))
    k.bx(torso, -10, 30, -12, 20, 10, 12, "bod")
    k.bx(torso, -11, 32, -8, 2, 7, 9, "redD")             # 左肩甲
    k.bx(torso, 9, 32, -8, 2, 7, 9, "redD")               # 右肩甲
    k.bx(torso, -6, 26, -11, 12, 5, 4, "grey")            # 領下絨羽
    k.bx(torso, -3, 28, -12.6, 6, 6, 1.4, "red")          # 胸前紅紋

    # ------------------------------------------------ 頸
    neck = k.bone("neck", parent="torso", pivot=(0, 35, -10))
    k.bx(neck, -5, 34, -16, 10, 8, 8, "bod")
    k.bx(neck, -5.4, 36, -12, 10.8, 3, 6, "redD")         # 頸環
    neck2 = k.bone("neck2", parent="neck", pivot=(0, 40, -14))
    k.bx(neck2, -4.5, 38, -20, 9, 7, 8, "bod")
    k.bx(neck2, -4, 41, -16, 8, 2.5, 6, "red")

    # ------------------------------------------------ 頭
    head = k.bone("head", parent="neck2", pivot=(0, 43, -15))
    k.bx(head, -5, 42, -26, 10, 8, 11, "bod")             # 顱
    k.bx(head, -5.4, 44, -24, 10.8, 6, 9, "redD")         # 面罩
    k.bx(head, -5.6, 48, -22, 11.2, 2, 8, "bodD")         # 眉脊
    k.bx(head, -5.8, 44, -22, 1, 5, 7, "bodL")            # 左頰
    k.bx(head, 4.8, 44, -22, 1, 5, 7, "bodL")             # 右頰
    k.bx(head, -2.4, 45, -33, 4.8, 3, 8, "beak")          # 上喙
    k.bx(head, -1.8, 43.4, -32, 3.6, 2.4, 6, "beakD")     # 下喙
    k.bx(head, -2.8, 47.4, -30, 5.6, 1.4, 4, "bodD")      # 喙上脊
    k.bx(head, -4.6, 46.4, -25.4, 2.6, 2.2, 1.6, "eye")   # 左眼
    k.bx(head, 2, 46.4, -25.4, 2.6, 2.2, 1.6, "eye")      # 右眼
    k.bx(head, -4, 46.8, -26.4, 1.4, 1.2, 1, "black")     # 左瞳
    k.bx(head, 2.6, 46.8, -26.4, 1.4, 1.2, 1, "black")    # 右瞳
    k.bx(head, -5, 45.6, -24.4, 4, 0.8, 1, "redL")        # 左眼紅暈
    k.bx(head, 1, 45.6, -24.4, 4, 0.8, 1, "redL")         # 右眼紅暈
    k.bx(head, -1.6, 49.6, -20, 3.2, 2, 7, "bodL")        # 頭頂脊

    # 後掠的角（左右各三節）
    horn_l = k.bone("ear_l", parent="head", pivot=(-4.6, 49, -20))
    k.bx(horn_l, -7.6, 49.4, -22, 3, 3, 8, "bodD", rot=[16, 0, 12], pivot=[-4.6, 49, -20])
    k.bx(horn_l, -10.6, 50.4, -16, 2.6, 2.6, 7, "bod", rot=[16, 0, 12], pivot=[-4.6, 49, -20])
    k.bx(horn_l, -13, 51.4, -10, 2, 2, 6, "redD", rot=[16, 0, 12], pivot=[-4.6, 49, -20])
    horn_r = k.bone("ear_r", parent="head", pivot=(4.6, 49, -20))
    k.bx(horn_r, 4.6, 49.4, -22, 3, 3, 8, "bodD", rot=[16, 0, -12], pivot=[4.6, 49, -20])
    k.bx(horn_r, 8, 50.4, -16, 2.6, 2.6, 7, "bod", rot=[16, 0, -12], pivot=[4.6, 49, -20])
    k.bx(horn_r, 11, 51.4, -10, 2, 2, 6, "redD", rot=[16, 0, -12], pivot=[4.6, 49, -20])

    # ------------------------------------------------ 翅膀（三段，展開）
    for sx, side, tag in ((-1, "l", "wing_l"), (1, "r", "wing_r")):
        root = k.bone(tag, parent="torso", pivot=(sx * 9, 34, -6))
        # 上臂
        k.bx(root, min(sx * 9, sx * 30), 31, -9, 21, 6, 9, "wing")
        k.bx(root, min(sx * 11, sx * 29), 32, -9.6, 18, 2.4, 10, "redD")     # 前緣紅線
        k.bx(root, min(sx * 11, sx * 16), 29, -9, 5, 6, 9, "bod")            # 肩覆羽
        k.bx(root, min(sx * 13, sx * 22), 28.4, -8.4, 9, 3, 8, "greyD")      # 翼下灰羽

        mid = k.bone(tag + "2", parent=tag, pivot=(sx * 30, 34, -6))
        k.bx(mid, min(sx * 30, sx * 48), 32, -8, 18, 5, 8, "wing")
        k.bx(mid, min(sx * 32, sx * 47), 32.6, -8.6, 15, 2, 8.8, "red")      # 中段紅紋
        k.bx(mid, min(sx * 31, sx * 45), 28, -8, 14, 4, 7, "wingD")          # 次級飛羽
        k.bx(mid, min(sx * 33, sx * 43), 24.4, -7, 10, 4, 6, "wing")         # 三級飛羽

        tip = k.bone(tag + "3", parent=tag + "2", pivot=(sx * 48, 34, -6))
        # 初級飛羽四根（張開的手指狀），越外側越斜
        for i in range(4):
            x0 = sx * (58 + i * 2.5)
            k.bx(tip, min(x0, x0 + sx * 16), 33 - i * 1.2, -6 - i * 0.6, 16, 3, 5,
                 "wing" if i % 2 == 0 else "wingD",
                 rot=[0, 0, -sx * (6 + i * 5)], pivot=[sx * 48, 34, -6])
            k.bx(tip, min(x0 + sx * 12, x0 + sx * 22), 31 - i * 1.2, -5.6 - i * 0.6, 6, 2, 4.4,
                 "red", rot=[0, 0, -sx * (6 + i * 5)], pivot=[sx * 48, 34, -6])
        k.bx(tip, min(sx * 48, sx * 60), 32, -7, 12, 4, 7, "bodD")           # 翼端骨架

    # ------------------------------------------------ 尾（扇形）
    t1 = k.bone("tail", parent="body", pivot=(0, 26, 8))
    k.bx(t1, -5, 22, 8, 10, 8, 10, "bod")
    k.bx(t1, -1, 24, 10, 2, 6, 9, "red")
    t2 = k.bone("tail2", parent="tail", pivot=(0, 22, 16))
    k.bx(t2, -4, 18, 16, 8, 7, 10, "bod")
    k.bx(t2, -3, 16, 18, 6, 3, 9, "redD")
    t3 = k.bone("tail3", parent="tail2", pivot=(0, 18, 24))
    k.bx(t3, -3, 14, 26, 6, 5, 12, "wing")                                   # 中央尾羽
    for a, col in ((18, "wingD"), (-18, "wingD"), (36, "wing"), (-36, "wing")):
        k.bx(t3, -2.4, 14.4, 28, 4.8, 4, 12, col, rot=[0, a, 0], pivot=[0, 18, 24])
    for a in (18, -18, 36, -36):
        k.bx(t3, -1.6, 13.6, 36, 3.2, 3, 5, "redL", rot=[0, a, 0], pivot=[0, 18, 24])

    # ------------------------------------------------ 收起的腿
    for sx, tag in ((-1, "leg0"), (1, "leg1")):
        up = k.bone(tag, parent="body", pivot=(sx * 6, 22, 0))
        k.bx(up, sx * 6 - 3.4, 16, -2, 6.8, 7, 7, "bod")
        k.bx(up, sx * 6 - 3.8, 19, -2.4, 7.6, 2, 7.8, "redD")
        low = k.bone(tag + "_low", parent=tag, pivot=(sx * 6, 16, 0))
        k.bx(low, sx * 6 - 2.8, 11, -1.5, 5.6, 6, 6, "bodD")
        foot = k.bone(tag + "_foot", parent=tag + "_low", pivot=(sx * 6, 11, 0))
        k.bx(foot, sx * 6 - 3.2, 7.6, -4, 6.4, 3.6, 9, "bod")
        for c in (-2, 0, 2):
            k.bx(foot, sx * 6 + c - 0.9, 7, -6, 1.8, 2, 3, "grey")
    return k


def apply(pack_dir, shiny=False):
    rp = os.path.join(pack_dir, "rp")
    k = build_yveltal()
    tex_dir = os.path.join(rp, "textures", "entity", "pokemon")
    os.makedirs(tex_dir, exist_ok=True)

    if shiny:
        make_texture("yveltal", os.path.join(tex_dir, "yveltal_shiny.png"), True)
        print("異色貼圖完成")
        return

    geo_path = os.path.join(rp, "models", "entity", "yveltal.geo.json")
    os.makedirs(os.path.dirname(geo_path), exist_ok=True)
    with open(geo_path, "w", encoding="utf-8") as f:
        json.dump(k.geo(IDENT), f, separators=(",", ":"), ensure_ascii=False)
    make_texture("yveltal", os.path.join(tex_dir, "yveltal.png"))

    cubes = sum(len(b["cubes"]) for b in k.bones)
    print(f"yveltal      骨骼 {len(k.bones):>3}  方塊 {cubes:>3}")

    for target in ("yveltal", "yveltal_shiny"):
        ep = os.path.join(rp, "entity", f"{target}.entity.json")
        if not os.path.exists(ep):
            continue
        with open(ep, encoding="utf-8") as f:
            d = json.load(f)
        desc = d["minecraft:client_entity"]["description"]
        desc["geometry"] = {"default": IDENT}
        desc["textures"] = {"default": f"textures/entity/pokemon/{target}"}
        with open(ep, "w", encoding="utf-8") as f:
            json.dump(d, f, separators=(",", ":"), ensure_ascii=False)
        print(f"  {target}.entity.json → {IDENT}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply(args[0] if args else "packs/pokemon", shiny="--shiny" in sys.argv)
