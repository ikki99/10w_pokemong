#!/usr/bin/env python3
"""把 Bedrock 幾何體渲染成 128×128 的圖鑑縮圖（等角投影 + 面明暗）。

為什麼要自己寫：本來的圖鑑圖示是「幾何方塊疊出來的平面示意」，加上存成調色盤 PNG，
在遊戲的 UI 裡既不清楚、有些甚至不會顯示。這支改用真正的正交等角投影，
每個方塊畫出可見的三個面並依法線做明暗，輸出 RGBA PNG。

用法：
  python3 tools/render_dex_icons.py packs/pokemon            # 全部
  python3 tools/render_dex_icons.py packs/pokemon arceus     # 單一物種
"""
import glob
import json
import math
import os
import sys

from PIL import Image, ImageDraw

SIZE = 96           # 輸出邊長
SS = 3              # 超取樣倍率（畫大再縮，邊緣比較乾淨）
YAW = math.radians(38)
PITCH = math.radians(26)
SIZE_DIR = {}


def load_model(rp, pid):
    for cand in (f"models/entity/cobblemon/{pid}.geo.json", f"models/entity/{pid}.geo.json"):
        p = os.path.join(rp, cand)
        if os.path.exists(p):
            geo = json.load(open(p, encoding="utf-8"))["minecraft:geometry"][0]
            return geo, p
    return None, None


def load_texture(rp, pid):
    for cand in (f"textures/entity/pokemon/{pid}.png", f"textures/entity/{pid}.png"):
        p = os.path.join(rp, cand)
        if os.path.exists(p):
            try:
                return Image.open(p).convert("RGBA"), p
            except Exception:
                return None, None
    return None, None


def rect_color(tex, x0, y0, w, h):
    """取一個矩形區域內不透明像素的平均色（比單點取樣穩得多）。"""
    if tex is None:
        return (200, 200, 200, 255)
    W, H = tex.size
    acc = [0, 0, 0, 0]
    n = 0
    for y in range(int(y0), int(y0 + max(1, h)), max(1, int(max(1, h) // 6))):
        for x in range(int(x0), int(x0 + max(1, w)), max(1, int(max(1, w) // 6))):
            py, px = y % H, x % W
            r, g, b, a = tex.getpixel((px, py))
            if a >= 24:
                acc[0] += r; acc[1] += g; acc[2] += b; acc[3] += a
                n += 1
    if not n:
        return None
    return (acc[0] // n, acc[1] // n, acc[2] // n, 255)


def sample(tex, u, v):
    if tex is None:
        return (200, 200, 200, 255)
    w, h = tex.size
    x = int(u) % w if w else 0
    y = int(v) % h if h else 0
    r, g, b, a = tex.getpixel((max(0, min(w - 1, x)), max(0, min(h - 1, y))))
    if a < 24:
        return (170, 170, 175, 255)
    return (r, g, b, 255)


def cube_color(cube, tex, geo_desc):
    tw = geo_desc.get("texture_width") or 64
    th = geo_desc.get("texture_height") or 64
    uv = cube.get("uv")
    size = cube.get("size", [1, 1, 1])
    if isinstance(uv, list) and len(uv) == 2:
        # box UV：整塊色域，取「展開後的面積」中央附近
        sx, sy, sz = [max(1, int(round(v))) for v in size]
        return rect_color(tex, uv[0] + 1, uv[1] + 1, min(2 * sz + 2 * sx, 24), min(sz + sy, 24)) or (190, 190, 195, 255)
    if isinstance(uv, dict):
        pool, n = [0, 0, 0], 0
        for face in ("up", "north", "east", "south", "west", "down"):
            if face not in uv:
                continue
            info = uv[face]
            rect = info.get("uv") or info.get("uv_size")
            if not rect or len(rect) < 2:
                continue
            w = rect[2] if len(rect) > 2 else 4
            h = rect[3] if len(rect) > 3 else 4
            col = rect_color(tex, rect[0], rect[1], w, h)
            if col:
                pool[0] += col[0]; pool[1] += col[1]; pool[2] += col[2]
                n += 1
        if n:
            return (pool[0] // n, pool[1] // n, pool[2] // n, 255)
    return (190, 190, 195, 255)


def project(p, scale, cx, cy):
    x, y, z = p
    xs = x * math.cos(YAW) - z * math.sin(YAW)
    zs = x * math.sin(YAW) + z * math.cos(YAW)
    ys = y * math.cos(PITCH) - zs * math.sin(PITCH)
    return (cx + xs * scale, cy - ys * scale)


FACES = {
    "up":    ((0, 1, 0), [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)], 1.00),
    "down":  ((0, -1, 0), [(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)], 0.45),
    "west":  ((-1, 0, 0), [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], 0.62),
    "east":  ((1, 0, 0), [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)], 0.80),
    "north": ((0, 0, -1), [(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1)][:4], 0.90),
    "south": ((0, 0, 1), [(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)], 0.70),
}
# north 的四個角要正確（z=0 那面）
FACES["north"] = ((0, 0, -1), [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], 0.90)

VIEW = (math.sin(YAW) * math.cos(PITCH), math.sin(PITCH), math.cos(YAW) * math.cos(PITCH))


def render(rp, pid, out_path, shiny=False):
    geo, gpath = load_model(rp, pid)
    if not geo:
        return None
    tex, tpath = load_texture(rp, f"{pid}_shiny" if shiny else pid)
    desc = geo.get("description", {})

    cubes = []
    for b in geo.get("bones", []):
        for c in b.get("cubes", []):
            o, s = c.get("origin", [0, 0, 0]), c.get("size", [1, 1, 1])
            cubes.append((o, s, cube_color(c, tex, desc)))
    if not cubes:
        return None

    # 用中位數過濾離群方塊，避免少數特效方塊把整隻模型縮到看不見
    centers = sorted(((o[0] + s[0] / 2, o[1] + s[1] / 2, o[2] + s[2] / 2) for o, s, _ in cubes),
                     key=lambda c: abs(c[0]) + abs(c[2]))
    med = centers[len(centers) // 2]
    keep = []
    for o, s, col in cubes:
        c = (o[0] + s[0] / 2, o[1] + s[1] / 2, o[2] + s[2] / 2)
        if math.dist(c, med) <= 90 or abs(s[0]) > 200 or abs(s[1]) > 200 or abs(s[2]) > 200:
            keep.append((o, s, col))
    if len(keep) >= 6:
        cubes = keep
    xs = [o[0] for o, s, _ in cubes] + [o[0] + s[0] for o, s, _ in cubes]
    ys = [o[1] for o, s, _ in cubes] + [o[1] + s[1] for o, s, _ in cubes]
    zs = [o[2] for o, s, _ in cubes] + [o[2] + s[2] for o, s, _ in cubes]
    cx0, cy0, cz0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    # 先算投影後的 2D 範圍；用「方塊體積」加權分位數，讓細長藤蔓/翅膀線條不會把畫面撐大
    probe = []           # (x, y, weight)
    for o, s2, _ in cubes:
        vol = max(1.0, abs(s2[0] * s2[1] * s2[2]))
        for gx in (o[0], o[0] + s2[0]):
            for gy in (o[1], o[1] + s2[1]):
                for gz in (o[2], o[2] + s2[2]):
                    px, py = project((gx - cx0, gy - cy0, gz - cz0), 1.0, 0, 0)
                    probe.append((px, py, vol))

    def wq(vals, q):
        vals = sorted(vals)
        total = sum(w for _, w in vals)
        acc = 0.0
        for v, w in vals:
            acc += w
            if acc >= total * q:
                return v
        return vals[-1][0]

    px0, px1 = wq([(p[0], p[2]) for p in probe], 0.04), wq([(p[0], p[2]) for p in probe], 0.96)
    py0, py1 = wq([(p[1], p[2]) for p in probe], 0.04), wq([(p[1], p[2]) for p in probe], 0.96)
    span_x, span_y = max(px1 - px0, 1e-3), max(py1 - py0, 1e-3)
    scale = (SIZE * SS * 0.86) / max(span_x, span_y)
    cx = SIZE * SS / 2 - (px0 + px1) / 2 * scale
    cy = SIZE * SS / 2 - (py0 + py1) / 2 * scale
    canvas = Image.new("RGBA", (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    faces = []
    for o, s, col in cubes:
        for name, (n, quad, shade) in FACES.items():
            if n[0] * VIEW[0] + n[1] * VIEW[1] + n[2] * VIEW[2] <= 0.02:
                continue
            pts = []
            for qx, qy, qz in quad:
                px = o[0] + qx * s[0] - cx0
                py = o[1] + qy * s[1] - cy0
                pz = o[2] + qz * s[2] - cz0
                pts.append(project((px, py, pz), scale, cx, cy))
            depth = ((o[0] + s[0] / 2 - cx0) * VIEW[0] + (o[1] + s[1] / 2 - cy0) * VIEW[1]
                     + (o[2] + s[2] / 2 - cz0) * VIEW[2])
            faces.append((depth, pts, (int(col[0] * shade), int(col[1] * shade), int(col[2] * shade), 255)))
    faces.sort(key=lambda f: f[0])
    for _, pts, col in faces:
        d.polygon(pts, fill=col, outline=(20, 20, 24, 210))
    out = canvas.resize((SIZE, SIZE), Image.LANCZOS)
    # 顏色稍微分階 + alpha 二值化：視覺幾乎沒差，PNG 小一半以上（圖鑑要載入 112 張）
    rgb = out.convert("RGB").point(lambda v: (v // 12) * 12)
    alpha = out.split()[-1].point(lambda a: 255 if a > 96 else 0)
    final = rgb.convert("RGBA")
    final.putalpha(alpha)
    final.save(out_path, optimize=True)
    return out_path


def main(pack_dir, only=None):
    rp = os.path.join(pack_dir, "rp")
    ui = os.path.join(rp, "textures", "ui")
    os.makedirs(ui, exist_ok=True)
    ids = sorted({os.path.basename(f).split(".")[0] for f in glob.glob(os.path.join(rp, "models", "entity", "**", "*.geo.json"), recursive=True)})
    if only:
        ids = [i for i in ids if i in only]
    ok = 0
    for pid in ids:
        if pid.endswith("_shiny"):
            continue
        r = render(rp, pid, os.path.join(ui, f"dex_{pid}.png"))
        s = render(rp, pid, os.path.join(ui, f"dex_{pid}_shiny.png"), shiny=True) if os.path.exists(
            os.path.join(rp, "textures", "entity", "pokemon", f"{pid}_shiny.png")) else None
        if r:
            ok += 1
        print(f"  {pid:<13} {'✔' if r else '✘'} {'(異色✔)' if s else ''}")
    print(f"完成 {ok} 隻")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    main(args[0] if args else "packs/pokemon", only=args[1:] or None)
