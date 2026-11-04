#!/usr/bin/env python3
"""修尾巴火焰：
問題拆解
 1) 動畫 animation.poke_<id>.tail_flame 只有一個 0.0 關鍵影格，長度 0，
    播完立刻結束，綁在動畫上的粒子發射器下一秒就被移除 -> 看不到火焰。
 2) 粒子本身用 emitter_rate_steady + expiration_expression 0（永不過期），
    一旦動畫真的重複觸發，發射器會無限堆疊。
解法
 - 粒子改成「一次性爆發」：emitter_lifetime_once(0.05s) + rate_instant(3 顆)，
   每顆活 0.35 秒，不會殘留。
 - 動畫改成 loop:true + animation_length 0.12，等於每秒約 25 顆，
   發射器隨動畫短命，不會疊。
用法：python3 tools/fix_tail_flame.py packs/pokemon [--bump 5.0.16]
"""
import glob
import json
import os
import re
import sys

PARTICLE = {
    "format_version": "1.10.0",
    "particle_effect": {
        "description": {
            "identifier": "poke:tail_flame",
            "basic_render_parameters": {
                "material": "particles_alpha",
                "texture": "textures/particle/particles",
            },
        },
        "components": {
            "minecraft:emitter_local_space": {"position": True, "rotation": False, "velocity": False},
            "minecraft:emitter_rate_instant": {"num_particles": 3},
            "minecraft:emitter_lifetime_once": {"active_time": 0.05},
            "minecraft:emitter_shape_point": {"offset": [0, 0, 0], "direction": [0, 1, 0]},
            "minecraft:particle_lifetime_expression": {"max_lifetime": 0.35},
            "minecraft:particle_appearance_billboard": {
                "size": [0.22, 0.22],
                "facing_camera_mode": "lookat_xyz",
                "uv": {"texture_width": 128, "texture_height": 128, "uv": [0, 24], "uv_size": [8, 8]},
            },
            "minecraft:particle_appearance_tinting": {"color": [1.0, 0.82, 0.32, 1.0]},
            "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.55, 0]},
        },
    },
}


def fix_particle(rp):
    p = os.path.join(rp, "particles", "poke_tail_flame.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    old = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    json.dump(PARTICLE, open(p, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print("  粒子改寫：", len(old), "->", os.path.getsize(p), "bytes")


def fix_animations(rp):
    n = 0
    for f in glob.glob(os.path.join(rp, "animations", "*.animations.json")):
        doc = json.load(open(f, encoding="utf-8"))
        anims = doc.get("animations") or {}
        changed = False
        for key, val in list(anims.items()):
            if not key.endswith(".tail_flame"):
                continue
            pe = (val or {}).get("particle_effects") or {"0.0": {"effect": "tail_flame", "locator": "fire"}}
            anims[key] = {
                "loop": True,
                "animation_length": 0.12,
                "particle_effects": pe,
            }
            changed = True
        if changed:
            json.dump(doc, open(f, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
            n += 1
            print("  動畫已修：", os.path.basename(f))
    print("  共修", n, "個動畫檔")


def ensure_locator(rp):
    """確認每個有 tail_flame 動畫的實體，其幾何體真的有 fire locator。"""
    ids = set()
    for f in glob.glob(os.path.join(rp, "animations", "*.animations.json")):
        if any("tail_flame" in k for k in (json.load(open(f, encoding="utf-8")).get("animations") or {})):
            ids.add(os.path.basename(f).replace(".animations.json", ""))
    for pid in sorted(ids):
        ep = os.path.join(rp, "entity", f"{pid}.entity.json")
        if not os.path.exists(ep):
            continue
        ident = json.load(open(ep, encoding="utf-8"))["minecraft:client_entity"]["description"]["geometry"]["default"]
        found = None
        for g in glob.glob(os.path.join(rp, "models", "entity", "**", "*.geo.json"), recursive=True):
            try:
                geo = json.load(open(g, encoding="utf-8"))["minecraft:geometry"][0]
            except Exception:
                continue
            if geo.get("description", {}).get("identifier") != ident:
                continue
            has = any("fire" in (b.get("locators") or {}) for b in geo["bones"])
            found = (g, has)
            break
        print(f"  {pid}: geometry={ident} fire locator={'有' if found and found[1] else '沒有'}")


def bump(pack_dir, ver):
    v = [int(x) for x in ver.split(".")]
    for sub in ("bp", "rp"):
        p = os.path.join(pack_dir, sub, "manifest.json")
        d = json.load(open(p, encoding="utf-8"))
        d["header"]["version"] = v
        d["modules"] = [dict(m, version=v) for m in d["modules"]]
        json.dump(d, open(p, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    js = os.path.join(pack_dir, "bp", "scripts", "main.js")
    s = open(js, encoding="utf-8").read()
    s2 = re.sub(r'const VERSION = "[0-9.]+";', f'const VERSION = "{ver}";', s, count=1)
    if s2 != s:
        open(js, "w", encoding="utf-8").write(s2)
    print("  版本 ->", ver)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pack_dir = args[0] if args else "packs/pokemon"
    rp = os.path.join(pack_dir, "rp")
    print("[1] 粒子")
    fix_particle(rp)
    print("[2] 動畫")
    fix_animations(rp)
    print("[3] locator 檢查")
    ensure_locator(rp)
    ver = None
    for i, a in enumerate(sys.argv):
        if a == "--bump":
            ver = sys.argv[i + 1]
    if ver:
        print("[4] 版本")
        bump(pack_dir, ver)
