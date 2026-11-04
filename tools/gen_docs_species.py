#!/usr/bin/env python3
"""重新生成 docs/SPECIES.md 並把 README 的數量與版本一次校正到現況。

用法：python3 tools/gen_docs_species.py   （在 repo 根目錄執行）
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "packs", "pokemon")


def read_lang(name):
    p = os.path.join(PKG, "rp", "texts", name)
    out = {}
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def species_rows():
    ids = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(PKG, "bp/entities/*.json"))
                 if not p.endswith("_shiny.json"))
    zh, en, ja = read_lang("zh_CN.lang"), read_lang("en_US.lang"), read_lang("ja_JP.lang")
    rows = []
    for i, pid in enumerate(ids, 1):
        key = f"entity.poke:{pid}.name"
        biomes = []
        sp = os.path.join(PKG, "bp", "spawn_rules", f"{pid}.json")
        if os.path.exists(sp):
            try:
                d = json.load(open(sp, encoding="utf-8"))
                for cond in d["minecraft:spawn_rules"].get("conditions", []):
                    for f in cond.get("minecraft:biome_filter", {}).get("any_of", []):
                        v = f.get("value")
                        if v and v not in biomes:
                            biomes.append(v)
            except Exception:
                pass
        rows.append((i, pid, zh.get(key, "—"), en.get(key, "—"), ja.get(key, "—"),
                     ", ".join(biomes) if biomes else "—"))
    return rows


def write_species(rows):
    p = os.path.join(ROOT, "docs", "SPECIES.md")
    lines = ["# 物種一覽 / Species List", "",
             f"共 {len(rows)} 種基礎型（另有異色變體，實體型別 {len(rows) * 2} 個）。", "",
             "| # | ID | 中文 | English | 日本語 | 棲息地 / Biome |",
             "|---|----|------|---------|--------|----------------|"]
    for i, pid, z, e, j, b in rows:
        lines.append(f"| {i} | `{pid}` | {z} | {e} | {j} | {b} |")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"docs/SPECIES.md：{len(rows)} 種")


def update_readme(n_species, n_entities, n_models, n_anims, n_moves, n_items, n_blocks, version):
    p = os.path.join(ROOT, "README.md")
    with open(p, encoding="utf-8") as f:
        s = f.read()

    # 數量：先處理 57 / 112 這兩個舊值
    s = s.replace("全部 57 種寶可夢", f"全部 {n_species} 種寶可夢")
    s = s.replace("### 全部 57 種寶可夢", f"### 全部 {n_species} 種寶可夢")
    s = s.replace("57 種基礎型，每格上方", f"{n_species} 種基礎型，每格上方")
    s = s.replace("| 寶可夢基礎型 | **57 種** |", f"| 寶可夢基礎型 | **{n_species} 種** |")
    s = s.replace("| 實體型別（含異色） | **112 個** |", f"| 實體型別（含異色） | **{n_entities} 個** |")
    s = s.replace("| 生怪蛋 | 112 個（含異色），附圖示與三語名稱 |",
                  f"| 生怪蛋 | {n_entities} 個（含異色），附圖示與三語名稱 |")
    s = s.replace("| 圖鑑頭像 | 112 張 |", f"| 圖鑑頭像 | {n_entities} 張 |")
    s = s.replace("| 高精度模型（cobblemon 移植） | 51 種，其餘為程序化方塊模型 |",
                  f"| 高精度模型（cobblemon 移植） | {n_models} 種，其餘為自建模方塊模型 |")
    s = s.replace("走路 / 待機 / 攻擊 / 飛行，共 58 個動畫檔",
                  f"走路 / 待機 / 攻擊 / 飛行，共 {n_anims} 個動畫檔")
    s = s.replace("**招式與屬性克制**：24 個招式", f"**招式與屬性克制**：{n_moves} 個招式")
    s = s.replace("共 56 種道具", f"共 {n_items} 種道具")
    s = s.replace("| 裝飾方塊 | 7 種（治療台、電腦、寶可夢絨 5 色） |",
                  f"| 裝飾方塊 | {n_blocks} 種（治療台、電腦、寶可夢絨 5 色） |")

    # 那句硬編碼的組成描述改成不隨數量腐爛的寫法
    s = re.sub(r"含 24 隻經典人氣角色、13 隻大型傳說、\n以及 20 隻後來追加的傳說與準傳說（[^）]*）。",
               "含經典人氣角色、三聖鳥與雷吉兄弟、大型傳說（洛奇亞、鳳王、烈空坐、帝牙盧卡、\n帕路奇亞、騎拉帝納、阿爾宙斯、無極汰那），以及卡洛斯傳說 **伊裴爾塔爾**。", s)
    s = re.sub(r"含 24 隻經典人氣角色、13 隻大型傳說、以及 20 隻後來追加的傳說與準傳說（[^）]*）。",
               "含經典人氣角色、三聖鳥與雷吉兄弟、大型傳說（洛奇亞、鳳王、烈空坐、帝牙盧卡、帕路奇亞、騎拉帝納、阿爾宙斯、無極汰那），以及卡洛斯傳說 **伊裴爾塔爾**。", s)

    # 版本範例與授權路徑
    s = re.sub(r'"version": \[4, 9, 0\]', '"version": [5, 1, 0]', s)
    s = re.sub(r'"version": \[\d+, \d+, \d+\]', '"version": [5, 1, 0]', s)
    s = s.replace("逐物種授權見 `packs/pokemon/rp/licenses/`", "逐物種授權見 `docs/licenses/`")
    s = s.replace("`packs/pokemon/rp/licenses/`", "`docs/licenses/`")

    # changelog
    anchor = "## 更新記錄 / Changelog\n"
    entry = f"""
### v{version}

- **新增 7 隻寶可夢（卡洛斯批次，共 {n_species} 種）**：伊裴爾塔爾（Yveltal）、烈箭鷹、音波龍、
  堅盾劍怪、摔角鷹人、冰雪巨龍、怪顎龍。每隻都有專屬招式、三語名稱、圖鑑頭像、生怪蛋、
  自然生成規則與異色變體。
- **伊裴爾塔爾是自建模**:上游沒有模型，用 22 骨骼 / 102 方塊親手建（三段式翅膀、灰白胸羽、
  扇尾、青色眼＋紅色紋路），與帝牙盧卡／騎拉帝納同一個方塊工藝。
- **新增 5 個招式**：死亡之翼（吸血）、神鳥猛擊、爆音波（範圍）、聖劍、飛身重壓。
- **修掉異色實體的動畫綁定**：重新生成會把 `<id>_shiny` 的 `animations`／`scripts.animate` 退回
  最基礎三條、`attack` 還指向不存在的 `animation.poke_<id>_shiny.attack` → 異色飛行寶可夢不扇翅。
  新增 `tools/fix_shiny_entities.py`，以本體為準補齊（64 個檔）。
- **修掉異色生怪蛋沒名字**：`gen_pokemon_extra.py` 的 `_PKG_DIR` 在函式內定義卻在模組層引用，
  補蛋名那步直接拋 `NameError` 並被吞掉；修好後補了 128 條三語蛋名。
- **資源包從 6.2MB 降到 3.9MB**（加了 7 隻反而更小）：346 個 JSON 全 minify、實體貼圖量化、
  刪掉 `textures/ui/dex_*` 那 128 張重複圖（程式走 `textures/items/`）、授權檔移出包外到 `docs/licenses/`。
- 新增工具：`tools/gen_yveltal_model.py`、`tools/slim_pack.py`、`tools/fix_shiny_entities.py`、
  `tools/gen_docs_species.py`。
"""
    if f"### v{version}" not in s:
        s = s.replace(anchor, anchor + entry, 1)

    with open(p, "w", encoding="utf-8") as f:
        f.write(s)
    print("README 已更新")


if __name__ == "__main__":
    rows = species_rows()
    write_species(rows)

    def count(pattern):
        return len(glob.glob(os.path.join(PKG, pattern)))

    ver = json.load(open(os.path.join(PKG, "bp", "manifest.json"), encoding="utf-8"))["header"]["version"]
    ver_s = ".".join(str(x) for x in ver)
    js = open(os.path.join(PKG, "bp/scripts/main.js"), encoding="utf-8").read()
    i, j = js.find("const MOVES = {"), js.find("\n};", js.find("const MOVES = {"))
    moves = len(re.findall(r"^  ([a-zA-Z0-9_]+)\(self", js[i:j], re.M))
    update_readme(
        n_species=len(rows),
        n_entities=count("bp/entities/*.json"),
        n_models=count("rp/models/entity/cobblemon/*.geo.json"),
        n_anims=count("rp/animations/*.json"),
        n_moves=moves,
        n_items=count("bp/items/*.json"),
        n_blocks=count("bp/blocks/*.json"),
        version=ver_s,
    )
