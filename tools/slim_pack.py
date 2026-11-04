#!/usr/bin/env python3
"""資源包瘦身：JSON 全 minify + 實體貼圖量化。

用法： python3 tools/slim_pack.py packs/pokemon
只動 rp/ 與 bp/ 內的 .json 與指定目錄的 PNG，不動模型結構。
"""
import glob
import json
import os
import sys

from PIL import Image


def minify_jsons(root):
    saved = 0
    n = 0
    for p in glob.glob(os.path.join(root, "**", "*.json"), recursive=True):
        try:
            with open(p, encoding="utf-8") as f:
                raw = f.read()
            if ", " not in raw and '": ' not in raw:
                continue
            before = os.path.getsize(p)
            data = json.loads(raw)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
            after = os.path.getsize(p)
            if after < before:
                saved += before - after
                n += 1
        except Exception as e:
            print(f"  跳過 {os.path.basename(p)}: {e}")
    print(f"JSON minify：{n} 檔，省 {saved/1024:.0f} KB")


def quantize_pngs(root, min_bytes=20000):
    saved = 0
    n = 0
    for p in sorted(glob.glob(os.path.join(root, "**", "*.png"), recursive=True)):
        before = os.path.getsize(p)
        if before < min_bytes:
            continue
        try:
            img = Image.open(p).convert("RGBA")
        except Exception as e:
            print(f"  跳過 {os.path.basename(p)}: {e}")
            continue
        alpha = img.getchannel("A")
        lo, hi = alpha.getextrema()
        # alpha 全不透明 → 直接轉 RGB；有透明 → 二值化後轉調色盤
        if lo == 255:
            out = img.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT)
        else:
            a = alpha.point(lambda v: 255 if v > 128 else 0)
            tmp = img.copy()
            tmp.putalpha(a)
            out = tmp.quantize(colors=255, method=Image.FASTOCTREE)
        tmp_path = p + ".tmp.png"
        out.save(tmp_path, optimize=True)
        after = os.path.getsize(tmp_path)
        if after < before * 0.97:
            os.replace(tmp_path, p)
            saved += before - after
            n += 1
        else:
            os.remove(tmp_path)
    print(f"PNG 量化：{n} 張，省 {saved/1024:.0f} KB")


def main(pack):
    for sub in ("rp", "bp"):
        root = os.path.join(pack, sub)
        if not os.path.isdir(root):
            continue
        print(f"--- {sub}")
        minify_jsons(root)
        if sub == "rp":
            quantize_pngs(os.path.join(root, "textures", "entity"))
            quantize_pngs(os.path.join(root, "textures", "items"), min_bytes=8000)
    total = sum(os.path.getsize(os.path.join(dp, f))
                for sub in ("rp", "bp")
                for dp, _dn, fn in os.walk(os.path.join(pack, sub)) for f in fn)
    print(f"合計 {total/1024/1024:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon")
