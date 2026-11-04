#!/usr/bin/env python3
"""從 cobblemon 的 3D 模型渲染「頭像」，做成生怪蛋的圖示。

比手畫臉可靠得多：直接把模型裡 head 骨骼（含子孫骨骼）的方塊，
用等角投影 + 貼圖取樣畫出來，一眼就能看出是哪隻寶可夢。

用法: python3 tools/gen_egg_portraits.py <rp_dir> [--preview out.png]
輸出: <rp_dir>/textures/items/portrait_<id>.png（32x32 RGBA，透明底）
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

# ---------------------------------------------------------------- 幾何

COS30 = 0.8660254
SIN30 = 0.5

# 等角投影：+x 往右下、+z 往左下、+y 往上
def project(p):
    x, y, z = p
    sx = (x - z) * COS30
    sy = (x + z) * SIN30 - y
    return np.array([sx, sy])


def view_depth(p):
    """越大越靠近相機（相機在 +x/+y/+z 方向）。"""
    x, y, z = p
    return x + y + z


FACE_NORMALS = {
    "up": (0, 1, 0),
    "down": (0, -1, 0),
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
    "south": (0, 0, 1),
    "north": (0, 0, -1),
}
# 只畫面向相機的三個方向
VISIBLE = ("up", "east", "south")
SHADE = {"up": 1.0, "east": 0.76, "south": 0.60, "down": 0.45, "west": 0.45, "north": 0.45}


def face_quad(origin, size, face):
    """回傳該面的 4 個 3D 角點，順序對應 (u0,v0) (u1,v0) (u1,v1) (u0,v1)。"""
    ox, oy, oz = origin
    w, h, d = size
    x0, x1 = ox, ox + w
    y0, y1 = oy, oy + h
    z0, z1 = oz, oz + d
    if face == "up":
        return [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)]
    if face == "down":
        return [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)]
    if face == "east":       # +x
        return [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)]
    if face == "west":       # -x
        return [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)]
    if face == "south":      # +z
        return [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)]
    if face == "north":      # -z
        return [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)]
    raise ValueError(face)


def box_uv_rects(uv, size):
    """Bedrock 盒式 UV 版面 → 每個面的 (u, v, w, h)。"""
    u, v = uv
    w, h, d = size
    return {
        "up": (u + d, v, w, d),
        "down": (u + d + w, v, w, d),
        "east": (u, v + d, d, h),
        "north": (u + d, v + d, w, h),
        "west": (u + d + w, v + d, d, h),
        "south": (u + d + w + d, v + d, w, h),
    }


def per_face_uv(cube):
    """支援 uv 為 dict 的模型（逐面指定）。"""
    out = {}
    for face, spec in cube["uv"].items():
        u, v = spec["uv"]
        w, h = spec.get("uv_size", spec.get("uvSize", [1, 1]))
        out[face] = (u, v, w, h)
    return out


# ---------------------------------------------------------------- 骨骼樹

def bone_tree(geo):
    bones = geo.get("bones", [])
    by_name = {b.get("name"): b for b in bones}
    children = {}
    roots = []
    for b in bones:
        parent = b.get("parent")
        if parent and parent in by_name:
            children.setdefault(parent, []).append(b)
        else:
            roots.append(b)
    return by_name, children, roots


def collect_cubes(bone, children, out, depth=0):
    for cube in bone.get("cubes", []):
        out.append((bone, cube))
    for kid in children.get(bone.get("name"), []):
        collect_cubes(kid, children, out, depth + 1)


def head_anchor(geo):
    """找頭部中心：優先 head 骨骼，其次 locator_head / locator_face，最後用模型上半部。"""
    by_name, children, roots = bone_tree(geo)
    for want in ("head", "locator_head", "locator_face", "locator_item_face"):
        b = by_name.get(want)
        if b and b.get("pivot"):
            return world_point(geo, b, b["pivot"]), want
    for name, b in by_name.items():
        if name and "head" in name.lower() and b.get("pivot"):
            return world_point(geo, b, b["pivot"]), name
    cubes = [(b, c) for b in geo.get("bones", []) for c in b.get("cubes", [])]
    if not cubes:
        return [0, 0, 0], "none"
    centers = [cube_world_center(geo, b, c) for b, c in cubes]
    xs = [p[0] for p in centers]
    zs = [p[2] for p in centers]
    ys = [p[1] for p in centers]
    return [(min(xs) + max(xs)) / 2, max(ys) - 3, (min(zs) + max(zs)) / 2], "bbox-top"


def rotate_point(point, pivot, rotation):
    p = np.asarray(point, dtype=float) - np.asarray(pivot, dtype=float)
    # Bedrock applies Euler rotations X, then Y, then Z (degrees).
    for axis, angle in enumerate(rotation):
        a = np.radians(float(angle)); c, s = np.cos(a), np.sin(a)
        if axis == 0: m = np.array([[1,0,0],[0,c,-s],[0,s,c]])
        elif axis == 1: m = np.array([[c,0,s],[0,1,0],[-s,0,c]])
        else: m = np.array([[c,-s,0],[s,c,0],[0,0,1]])
        p = m @ p
    return p + np.asarray(pivot, dtype=float)


def bone_chain(geo, bone):
    by_name = {b.get("name"): b for b in geo.get("bones", [])}
    chain, cur, seen = [], bone, set()
    while cur and cur.get("name") not in seen:
        seen.add(cur.get("name")); chain.append(cur)
        cur = by_name.get(cur.get("parent"))
    return chain


def world_point(geo, bone, point, cube_rotation=None, cube_pivot=None):
    p = np.asarray(point, dtype=float)
    if cube_rotation:
        p = rotate_point(p, cube_pivot or (np.asarray(point) + 0.0), cube_rotation)
    for b in bone_chain(geo, bone):
        pivot = b.get("pivot", [0, 0, 0])
        p = rotate_point(p, pivot, b.get("rotation", [0, 0, 0]))
    return p.tolist()


def cube_world_center(geo, bone, cube):
    origin, size = cube["origin"], cube["size"]
    center = [origin[i] + size[i] / 2 for i in range(3)]
    return world_point(geo, bone, center, cube.get("rotation"), cube.get("pivot", center))


def select_head_cubes(geo, radius=12.0):
    """以頭部中心為球心取半徑內的方塊 —— 不依賴骨骼命名，
    眼睛/耳朵/嘴巴/吻部只要在頭附近就一定會被帶進來（Gengar 這種沒有 head 骨骼的模型也能處理）。"""
    anchor, how = head_anchor(geo)
    allc = [(b, c) for b in geo.get("bones", []) for c in b.get("cubes", [])]
    picked = []
    r = radius
    while r <= radius * 2.4:
        picked = []
        for b, c in allc:
            ctr = cube_world_center(geo, b, c)
            d = sum((ctr[i] - anchor[i]) ** 2 for i in range(3)) ** 0.5
            if d <= r:
                picked.append((b, c))
        if len(picked) >= 6:
            break
        r += radius * 0.5
    return picked, f"{how}@r{int(r)}"


# ---------------------------------------------------------------- 渲染

def render(cubes, tex, out_size=32, margin=1, geo=None):
    """把方塊群的頭部畫成 out_size 見方 RGBA。"""
    tex = np.asarray(tex.convert("RGBA"), dtype=np.uint8)
    th, tw = tex.shape[:2]

    tris = []          # (depth, face, quad3d, u0,v0,u1,v1)
    for bone, cube in cubes:
        # Bedrock cube origins are model-space coordinates. Apply cube rotation
        # and the bone/ancestor rotations around their declared pivots.
        origin = cube["origin"]
        size = cube["size"]
        raw_center = [origin[i] + size[i] / 2 for i in range(3)]
        cube_pivot = cube.get("pivot", raw_center)
        inflate = cube.get("inflate", 0)
        if inflate:
            origin = [origin[i] - inflate for i in range(3)]
            size = [size[i] + inflate * 2 for i in range(3)]
        uv = cube.get("uv")
        if not uv:
            continue
        rects = per_face_uv(cube) if isinstance(uv, dict) else box_uv_rects(uv, size)
        for face in FACE_NORMALS:
            rect = rects.get(face)
            if not rect:
                continue
            n = np.asarray(FACE_NORMALS[face], dtype=float)
            center = np.asarray(origin, dtype=float) + np.asarray(size, dtype=float) / 2
            normal_tip = center + n
            if geo:
                normal_tip = np.asarray(world_point(geo, bone, normal_tip, cube.get("rotation"), cube_pivot))
                center = np.asarray(world_point(geo, bone, center, cube.get("rotation"), cube_pivot))
            if np.dot(normal_tip - center, np.asarray([1, 1, 1])) <= 0.02:
                continue
            u, v, fw, fh = rect
            if fw <= 0 or fh <= 0:
                continue
            quad = face_quad(origin, size, face)
            if geo:
                quad = [world_point(geo, bone, q, cube.get("rotation"), cube_pivot) for q in quad]
            depth = sum(view_depth(p) for p in quad) / 4
            tris.append((depth, face, quad, u, v, u + fw, v + fh))

    tris.sort(key=lambda t: t[0])          # 遠的先畫

    # 先算整體投影範圍
    pts = [project(p) for _, _, quad, *_ in tris for p in quad]
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    span = max(maxx - minx, maxy - miny)
    k = (out_size - margin * 2) / max(span, 1e-6)

    canvas = np.zeros((out_size, out_size, 4), dtype=np.uint8)

    def to_px(p2):
        sx = (p2[0] - (minx + maxx) / 2) * k + out_size / 2
        sy = (p2[1] - (miny + maxy) / 2) * k + out_size / 2
        return np.array([sx, sy])

    for depth, face, quad, u0, v0, u1, v1 in tris:
        p = [to_px(project(q)) for q in quad]
        P00, P10, P11, P01 = p[0], p[1], p[2], p[3]
        ax = P10 - P00
        ay = P01 - P00
        det = ax[0] * ay[1] - ax[1] * ay[0]
        if abs(det) < 1e-9:
            continue

        xs_min = int(np.floor(min(P00[0], P10[0], P11[0], P01[0])))
        xs_max = int(np.ceil(max(P00[0], P10[0], P11[0], P01[0])))
        ys_min = int(np.floor(min(P00[1], P10[1], P11[1], P01[1])))
        ys_max = int(np.ceil(max(P00[1], P10[1], P11[1], P01[1])))
        xs_min, xs_max = max(0, xs_min), min(out_size - 1, xs_max)
        ys_min, ys_max = max(0, ys_min), min(out_size - 1, ys_max)
        if xs_min > xs_max or ys_min > ys_max:
            continue

        gx, gy = np.meshgrid(np.arange(xs_min, xs_max + 1) + 0.5,
                             np.arange(ys_min, ys_max + 1) + 0.5)
        dx = gx - P00[0]
        dy = gy - P00[1]
        a = (dx * ay[1] - dy * ay[0]) / det
        b = (ax[0] * dy - ax[1] * dx) / det
        inside = (a >= -0.02) & (a <= 1.02) & (b >= -0.02) & (b <= 1.02)
        if not inside.any():
            continue

        tu = (u0 + np.clip(a, 0, 1) * (u1 - u0)).astype(np.int32)
        tv = (v0 + np.clip(b, 0, 1) * (v1 - v0)).astype(np.int32)
        tu = np.clip(tu, 0, tw - 1)
        tv = np.clip(tv, 0, th - 1)
        col = tex[tv, tu].astype(np.float32)
        col[..., :3] *= SHADE[face]
        col = np.clip(col, 0, 255).astype(np.uint8)
        col[..., 3] = np.where(col[..., 3] > 24, 255, 0)

        region = canvas[ys_min:ys_max + 1, xs_min:xs_max + 1]
        m = inside & (col[..., 3] > 0)
        region[m] = col[m]
        canvas[ys_min:ys_max + 1, xs_min:xs_max + 1] = region

    return Image.fromarray(canvas, "RGBA")


def load_geometry(path):
    d = json.load(open(path, encoding="utf-8"))
    if "minecraft:geometry" in d:
        return d["minecraft:geometry"][0]
    return d


def entity_geometries(rp_dir):
    """Resolve geometry identifiers from client entities, including aliases."""
    model_root = os.path.join(rp_dir, "models", "entity")
    geo_files = {}
    for path in glob.glob(os.path.join(model_root, "**", "*.geo.json"), recursive=True):
        geo_files[os.path.basename(path).replace(".geo.json", "")] = path
    found = {}
    for entity_path in glob.glob(os.path.join(rp_dir, "entity", "*.entity.json")):
        pid = os.path.basename(entity_path).replace(".entity.json", "")
        try:
            d = json.load(open(entity_path, encoding="utf-8"))
            desc = d["minecraft:client_entity"]["description"]
            geo_id = desc.get("geometry", {}).get("default", "").replace("geometry.", "")
            candidates = [geo_id, geo_id.removeprefix("poke_")]
            if geo_id.endswith("_detailed"):
                candidates.append(geo_id.removeprefix("poke_").removesuffix("_detailed"))
            if geo_id.endswith("_male"):
                candidates.append(geo_id.removesuffix("_male"))
            candidates.extend({"ho_oh": "hooh", "kommo-o": "kommoo"}.get(x, x) for x in tuple(candidates))
            candidates.append(pid.removesuffix("_shiny"))
            path = next((geo_files[x] for x in candidates if x in geo_files), None)
            if path:
                found[pid] = path
        except (OSError, ValueError, KeyError):
            continue
    return found


def main(rp_dir, preview_path=None):
    tex_dir = os.path.join(rp_dir, "textures", "entity", "pokemon")
    out_dir = os.path.join(rp_dir, "textures", "items")
    os.makedirs(out_dir, exist_ok=True)

    tiles = []
    for pid, geo_path in sorted(entity_geometries(rp_dir).items()):
        if pid.endswith("_shiny"):
            continue
        tex_path = os.path.join(tex_dir, f"{pid}.png")
        if not os.path.exists(tex_path):
            print(f"  {pid}: 沒有貼圖，跳過")
            continue
        geo = load_geometry(geo_path)
        cubes, how = select_head_cubes(geo)
        if not cubes:
            # A full-body fallback still provides a species-specific egg crest.
            cubes = collect_cubes(geo.get("bones", [])[0], bone_tree(geo)[1], []) if geo.get("bones") else []
            how = "full-model"
        if not cubes:
            print(f"  {pid}: 找不到方塊")
            continue
        img = render(cubes, Image.open(tex_path), out_size=64, geo=geo)
        if img is not None:
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
        if img is None:
            print(f"  {pid}: 渲染失敗")
            continue
        img.save(os.path.join(out_dir, f"portrait_{pid}.png"))
        shiny_tex = os.path.join(tex_dir, f"{pid}_shiny.png")
        if os.path.exists(shiny_tex):
            shiny_img = render(cubes, Image.open(shiny_tex), out_size=64, geo=geo)
            if shiny_img is not None:
                shiny_img.save(os.path.join(out_dir, f"portrait_{pid}_shiny.png"))
        print(f"  {pid:12s} 方塊={len(cubes):3d} 來源={how}")
        tiles.append((pid, img))

    if preview_path and tiles:
        cols = 8
        cell = 96
        rows = (len(tiles) + cols - 1) // cols
        prev = Image.new("RGBA", (cols * cell, rows * cell), (30, 30, 38, 255))
        for i, (pid, img) in enumerate(tiles):
            big = img.resize((cell - 16, cell - 16), Image.NEAREST)
            prev.alpha_composite(big, ((i % cols) * cell + 8, (i // cols) * cell + 8))
        prev.save(preview_path)
        print(f"預覽: {preview_path}  ({len(tiles)} 隻)")


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else "/tmp/poke_new/rp"
    preview = None
    if "--preview" in sys.argv:
        preview = sys.argv[sys.argv.index("--preview") + 1]
    main(rp, preview)
