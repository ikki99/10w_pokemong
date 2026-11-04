#!/usr/bin/env python3
"""把公眾號文章 Markdown 轉成一份可以直接貼進微信編輯器（含圖）的 HTML。

用法：python3 tools/gen_article_html.py promo/公众号文章-宝可梦模组.md promo/公众号文章-含图.html
圖片從 promo/wechat/*.jpg 讀進來做 base64 內嵌，單檔可直接開、直接全選複製。
"""
import base64
import html as H
import os
import sys

FIGS = [
    ("hero", None, "57 種寶可夢，112 個實體。Switch、手機、Windows 進的是同一個世界"),
    ("square", "最后这几只的方块数", "重製後的模型，每一隻都是遊戲裡實際載入的方塊模型"),
    ("features", "112 张图全部重画。", "圖鑑、精靈球、生怪蛋、道具，都在同一個介面裡"),
    ("eggwall", "三份都是 287 条。", "112 顆生怪蛋，每顆有自己的圖示和名字"),
    ("shiny", "念一整天。", "左邊是普通，右邊是異色，機率六十四分之一"),
]

CSS = """
  body { margin:0; background:#f4f4f5; }
  .hint { max-width:677px; margin:0 auto; background:#fffbe8; border-left:4px solid #e8c55c;
          padding:10px 14px; font:14px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif; color:#7a6320; }
  .wrap { max-width:677px; margin:0 auto; background:#fff; padding:28px 20px 60px; }
  h1 { font:700 24px/1.5 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif; color:#1a1a1a; margin:24px 0 18px; }
  h2 { font:700 19px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif; color:#1a1a1a;
       margin:34px 0 14px; padding-left:10px; border-left:4px solid #d8b84c; }
  p  { font:17px/1.95 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif; color:#3a3a3a;
       margin:0 0 20px; letter-spacing:.4px; }
  figure { margin:30px 0 36px; }
  figure img { width:100%; display:block; border-radius:4px; }
  figcaption { font:13px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
               color:#9a9a9a; text-align:center; margin-top:10px; letter-spacing:.3px; }
  .repo a { color:#a3821f; }
  @media (max-width:520px){ p{font-size:16px} .wrap{padding:20px 16px 48px} }
"""


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def figure(img_dir, name, caption):
    p = os.path.join(img_dir, f"{name}.jpg")
    if not os.path.exists(p):
        return ""
    return (f'<figure><img src="{data_uri(p)}" alt="{H.escape(caption)}">'
            f'<figcaption>{H.escape(caption)}</figcaption></figure>')


def build(md_path, out_path):
    src = open(md_path, encoding="utf-8").read()
    body = src.split("---\n\n仓库地址")[0].rstrip()
    img_dir = os.path.join(os.path.dirname(md_path), "wechat")
    placed = set()
    parts = []

    # 頭圖先放
    parts.append(figure(img_dir, "hero", FIGS[0][2]))
    placed.add("hero")

    title = None
    for blk in body.split("\n\n"):
        t = blk.strip()
        if not t:
            continue
        if t.startswith("# "):
            title = t[2:].strip()
            parts.append(f"<h1>{H.escape(title)}</h1>")
            continue
        if t.startswith("## "):
            parts.append(f"<h2>{H.escape(t[3:].strip())}</h2>")
            continue
        parts.append("<p>" + H.escape(t).replace("\n", "<br>") + "</p>")
        for name, anchor, cap in FIGS:
            if name in placed or not anchor:
                continue
            if anchor in t:
                parts.append(figure(img_dir, name, cap))
                placed.add(name)
    parts.append('<p class="repo">倉庫地址 '
                 '<a href="https://github.com/ikki99/10w_pokemong">github.com/ikki99/10w_pokemong</a></p>')

    doc = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{H.escape(title or '文章')}</title>
<style>{CSS}</style></head><body>
<div class="hint">用法：瀏覽器打開這個檔案 → 全選（Ctrl/Cmd+A）→ 複製 → 貼進公眾號編輯器。圖片會一起進去，微信自動上傳。</div>
<div class="wrap">
{chr(10).join(p for p in parts if p)}
</div></body></html>"""
    open(out_path, "w", encoding="utf-8").write(doc)
    missing = [n for n, _, _ in FIGS if n not in placed]
    print(f"{out_path}  {os.path.getsize(out_path)/1048576:.2f} MB  圖片 {len(placed)} 張  未插入 {missing or '無'}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "promo/公众号文章-宝可梦模组.md",
          sys.argv[2] if len(sys.argv) > 2 else "promo/公众号文章-含图.html")
