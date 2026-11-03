#!/usr/bin/env python3
"""生成圖鑑用的寶可夢頭像圖示（給 server-ui 表單按鈕用）

輸出：<rp>/textures/ui/dex_<id>.png  96x96 RGBA 圖鑑立繪
      異色另外輸出 dex_<id>_shiny.png（若貼圖存在）

用法： python3 gen_dex_icons.py <rp_dir>
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_egg_portraits import bone_tree, collect_cubes, entity_geometries, load_geometry, render  # noqa: E402

SIZE = 96
INNER = 84


def frame(icon, size=SIZE, inner=INNER):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    pad = (size - inner) // 2
    # 深色半透明底 + 金色描邊，看起來像圖鑑格子
    d.rounded_rectangle([1, 1, size - 2, size - 2], radius=10, fill=(24, 26, 34, 235), outline=(196, 160, 74, 255), width=2)
    if icon is not None:
        big = icon.convert("RGBA").resize((inner, inner), Image.Resampling.LANCZOS)
        canvas.alpha_composite(big, (pad, pad))
    return canvas


def main(rp):
    out_dir = os.path.join(rp, "textures", "ui")
    os.makedirs(out_dir, exist_ok=True)
    geometries = entity_geometries(rp)
    # Some shiny textures have no separate client-entity file, but the dex UI
    # can still request their icon when the shiny is recorded. Reuse the base
    # species geometry for every available shiny texture.
    for pid, geo_path in list(geometries.items()):
        if pid.endswith("_shiny"):
            continue
        shiny_id = f"{pid}_shiny"
        shiny_tex = os.path.join(rp, "textures", "entity", "pokemon", f"{shiny_id}.png")
        if os.path.exists(shiny_tex):
            geometries.setdefault(shiny_id, geo_path)
    if not geometries:
        print("找不到任何 poke 實體模型")
        return 1
    made = 0
    missing = []
    for pid, geo_path in sorted(geometries.items()):
        tex_path = os.path.join(rp, "textures", "entity", "pokemon", f"{pid}.png")
        if not os.path.exists(tex_path):
            missing.append(pid)
            continue
        geo = load_geometry(geo_path)
        _, children, roots = bone_tree(geo)
        cubes = []
        for root in roots:
            collect_cubes(root, children, cubes)
        if not cubes:
            missing.append(pid)
            continue
        icon = render(cubes, Image.open(tex_path).convert("RGBA"), out_size=INNER, margin=3, geo=geo)
        if icon is None:
            missing.append(pid)
            continue
        frame(icon).save(os.path.join(out_dir, f"dex_{pid}.png"))
        made += 1
    print(f"圖鑑全身立繪：{made} 張 -> {out_dir}")
    if missing:
        print(f"略過（缺模型或貼圖）：{missing}")
    # 統計
    files = [f for f in os.listdir(out_dir) if f.startswith("dex_")]
    print(f"目錄內共 {len(files)} 張 dex 圖示")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/poke_new/rp"))
