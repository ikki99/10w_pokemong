#!/usr/bin/env python3
"""生成圖鑑用的寶可夢頭像圖示（給 server-ui 表單按鈕用）

輸出：<rp>/textures/ui/dex_<id>.png  64x64 透明背景 + 細圓框
      異色另外輸出 dex_<id>_shiny.png（若貼圖存在）

用法： python3 gen_dex_icons.py <rp_dir>
"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_egg_portraits import collect_cubes, head_anchor, load_geometry, render, select_head_cubes  # noqa: E402

SIZE = 64
INNER = 56


def species_ids(rp):
    """從 rp/entity 抓出所有 poke 實體 id（去掉 _shiny）"""
    out = []
    edir = os.path.join(rp, "entity")
    for fn in sorted(os.listdir(edir)):
        if not fn.endswith(".entity.json"):
            continue
        ident = fn[: -len(".entity.json")]
        if ident and ident != "poke_catch_fx":
            out.append(ident)
    return out


def head_icon(rp, pid, size=INNER):
    geo_path = os.path.join(rp, "models", "entity", f"{pid}.geo.json")
    tex_path = os.path.join(rp, "textures", "entity", "pokemon", f"{pid}.png")
    if not (os.path.exists(geo_path) and os.path.exists(tex_path)):
        return None
    geo = load_geometry(geo_path)
    cubes, _how = select_head_cubes(geo)
    if not cubes:
        return None
    img = render(cubes, Image.open(tex_path).convert("RGBA"), out_size=size)
    return img


def frame(icon, size=SIZE, inner=INNER):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    pad = (size - inner) // 2
    # 深色半透明底 + 金色描邊，看起來像圖鑑格子
    d.rounded_rectangle([1, 1, size - 2, size - 2], radius=10, fill=(24, 26, 34, 235), outline=(196, 160, 74, 255), width=2)
    if icon is not None:
        big = icon.convert("RGBA").resize((inner, inner), Image.NEAREST)
        canvas.alpha_composite(big, (pad, pad))
    return canvas


def main(rp):
    out_dir = os.path.join(rp, "textures", "ui")
    os.makedirs(out_dir, exist_ok=True)
    ids = species_ids(rp)
    if not ids:
        print("找不到任何 poke 實體")
        return 1
    made = 0
    missing = []
    for pid in ids:
        base = pid.replace("_shiny", "")
        icon = head_icon(rp, pid)
        if icon is None:
            missing.append(pid)
            continue
        frame(icon).save(os.path.join(out_dir, f"dex_{pid}.png"))
        made += 1
        # 異色圖示：用異色貼圖但同一個頭部方塊
        if not pid.endswith("_shiny"):
            shiny_tex = os.path.join(rp, "textures", "entity", "pokemon", f"{pid}_shiny.png")
            if os.path.exists(shiny_tex):
                geo = load_geometry(os.path.join(rp, "models", "entity", f"{pid}.geo.json"))
                cubes, _ = select_head_cubes(geo)
                if cubes:
                    img = render(cubes, Image.open(shiny_tex).convert("RGBA"), out_size=INNER)
                    if img:
                        frame(img).save(os.path.join(out_dir, f"dex_{pid}_shiny.png"))
    print(f"圖鑑圖示：{made} 張 -> {out_dir}")
    if missing:
        print(f"略過（缺模型或貼圖）：{missing}")
    # 統計
    files = [f for f in os.listdir(out_dir) if f.startswith("dex_")]
    print(f"目錄內共 {len(files)} 張 dex 圖示")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/poke_new/rp"))
