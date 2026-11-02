#!/usr/bin/env python3
"""從 kirbycope/cobblemon-bedrock（MIT / CC 授權）匯入 12 隻寶可夢的模型與貼圖，
套進我們自己的 add-on（client entity 換成高精度模型，行為/招式仍是我們寫的）。

產出：
  rp/models/entity/cobblemon/<id>.geo.json
  rp/textures/entity/pokemon/<id>.png
  rp/entity/<id>.entity.json      （identifier = poke:<id>，指向上面兩個）
  rp/CREDITS.md  + rp/licenses/<id>-LICENSE
"""
import json
import os
import sys
import urllib.request

REPO = "kirbycope/cobblemon-bedrock"
BRANCH = "main"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"

# 我們的 id -> (圖鑑編號, 英文小寫檔名)
SPECIES = {
    "articuno": ("0144", "articuno"),
    "zapdos": ("0145", "zapdos"),
    "moltres": ("0146", "moltres"),
    "aerodactyl": ("0142", "aerodactyl"),
    "regirock": ("0377", "regirock"),
    "regice": ("0378", "regice"),
    "registeel": ("0379", "registeel"),
    "regieleki": ("0894", "regieleki"),
    "regidrago": ("0895", "regidrago"),
    "zarude": ("0893", "zarude"),
    "tyranitar": ("0248", "tyranitar"),
    "salamence": ("0373", "salamence"),
    "metagross": ("0376", "metagross"),
    "hydreigon": ("0635", "hydreigon"),
    "goodra": ("0706", "goodra"),
    "kommoo": ("0784", "kommoo"),
    "dragapult": ("0887", "dragapult"),
    "duraludon": ("0884", "duraludon"),
    "baxcalibur": ("0998", "baxcalibur"),
    "garganacl": ("0950", "garganacl"),
    "pikachu":    ("0025", "pikachu"),
    "eevee":      ("0133", "eevee"),
    "bulbasaur":  ("0001", "bulbasaur"),
    "charmander": ("0004", "charmander"),
    "squirtle":   ("0007", "squirtle"),
    "jigglypuff": ("0039", "jigglypuff"),
    "meowth":     ("0052", "meowth"),
    "gengar":     ("0094", "gengar"),
    "snorlax":    ("0143", "snorlax"),
    "dragonite":  ("0149", "dragonite"),
    "charizard":  ("0006", "charizard"),
    "mewtwo":     ("0150", "mewtwo"),
    "psyduck":      ("0054", "psyduck"),
    "gyarados":     ("0130", "gyarados"),
    "lapras":       ("0131", "lapras"),
    "machamp":      ("0068", "machamp"),
    "alakazam":     ("0065", "alakazam"),
    "onix":         ("0095", "onix"),
    "lucario":      ("0448", "lucario"),
    "gardevoir":    ("0282", "gardevoir"),
    "greninja":     ("0658", "greninja"),
    "mimikyu":      ("0778", "mimikyu"),
    "sylveon":      ("0700", "sylveon"),
    "garchomp":     ("0445", "garchomp"),
    # ---- 傳說（有開源模型的）----
    "lugia":        ("0249", "lugia"),
    "hooh":         ("0250", "hooh"),
    "rayquaza":     ("0384", "rayquaza"),
    "latias":       ("0380", "latias"),
    "latios":       ("0381", "latios"),
    "regigigas":    ("0486", "regigigas"),
    "mew":          ("0151", "mew"),
    "xerneas":      ("0716", "xerneas"),
    "eternatus":    ("0890", "eternatus"),
}

RP_PREFIX = "development_resource_packs/cobblemon/"


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-poke-import"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def get_json(url: str):
    return json.loads(http_get(url).decode("utf-8", "replace"))


def tree_paths():
    url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    t = get_json(url)
    return [x["path"] for x in t.get("tree", []) if x["type"] == "blob"]


def pick_geo(paths, num, name):
    """優先找 _male.geo.json，其次 default/其他"""
    base = f"{RP_PREFIX}models/entity/{num}_{name}/"
    cand = [p for p in paths if p.startswith(base) and p.endswith(".geo.json")]
    if not cand:
        return None
    for key in (f"{name}_male.geo.json", f"{name}.geo.json", f"{name}_female.geo.json"):
        for p in cand:
            if p.endswith("/" + key):
                return p
    return sorted(cand)[0]


def pick_texture(paths, num, name):
    base = f"{RP_PREFIX}textures/entity/{num}_{name}/"
    cand = [p for p in paths if p.startswith(base) and p.endswith(".png")]
    if not cand:
        return None
    for key in (f"{name}.png", f"{name}_male.png"):
        for p in cand:
            if p.endswith("/" + key):
                return p
    # 排除 shiny / emissive
    plain = [p for p in cand if "shiny" not in p and "emissive" not in p and "cap" not in p]
    return sorted(plain or cand)[0]


def pick_shiny(paths, num, name):
    """找異色貼圖（<name>_shiny.png），沒有就回 None。"""
    base = f"{RP_PREFIX}textures/entity/{num}_{name}/"
    cand = [p for p in paths if p.startswith(base) and p.endswith("_shiny.png")]
    if not cand:
        return None
    for key in (f"{name}_shiny.png", f"{name.replace('_', '')}_shiny.png"):
        for p in cand:
            if p.endswith("/" + key):
                return p
    return sorted(cand)[0]


def main():
    out_root = sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon"
    rp = os.path.join(out_root, "rp")
    geo_dir = os.path.join(rp, "models", "entity", "cobblemon")
    tex_dir = os.path.join(rp, "textures", "entity", "pokemon")
    ent_dir = os.path.join(rp, "entity")
    lic_dir = os.path.join(rp, "licenses")
    for d in (geo_dir, tex_dir, ent_dir, lic_dir):
        os.makedirs(d, exist_ok=True)

    print("抓取檔案清單…")
    paths = tree_paths()
    print("  共", len(paths), "個檔案")

    credits = ["# 模型與貼圖來源 / Credits", "",
               "本 add-on 的寶可夢模型（geometry）與貼圖來自開源專案：", "",
               f"- 來源 repo: https://github.com/{REPO}",
               "- 上游: Cobblemon（Minecraft 寶可夢模組）之 Bedrock 移植",
               "- 授權: 見 `licenses/` 目錄下每個模型附帶的 LICENSE 檔（Creative Commons）",
               "- 我方修改: 僅調整 client entity 綁定（identifier 改為 poke:*）、"
               "加入自己的行為/招式/生成規則；模型與貼圖未修改。", ""]

    ok = 0
    for pid, (num, name) in SPECIES.items():
        geo_path = pick_geo(paths, num, name)
        tex_path = pick_texture(paths, num, name)
        if not geo_path or not tex_path:
            print(f"  ✘ {pid}: 找不到 geo={geo_path} tex={tex_path}")
            continue

        gdata = http_get(RAW + geo_path).decode("utf-8", "replace")
        geo = json.loads(gdata)
        geo_id = geo["minecraft:geometry"][0]["description"]["identifier"]
        with open(os.path.join(geo_dir, f"{pid}.geo.json"), "w", encoding="utf-8") as f:
            f.write(gdata)

        with open(os.path.join(tex_dir, f"{pid}.png"), "wb") as f:
            f.write(http_get(RAW + tex_path))

        shiny_path = pick_shiny(paths, num, name)
        if shiny_path:
            with open(os.path.join(tex_dir, f"{pid}_shiny.png"), "wb") as f:
                f.write(http_get(RAW + shiny_path))
        else:
            print(f"     (沒有異色貼圖: {pid})")

        # 授權檔（模型目錄裡附帶的那份）
        lic_src = geo_path.rsplit("/", 1)[0] + "/license"
        if lic_src in paths:
            with open(os.path.join(lic_dir, f"{pid}-LICENSE"), "wb") as f:
                f.write(http_get(RAW + lic_src))
            credits.append(f"- {pid}: `{geo_path.split('/')[-1]}` + `{tex_path.split('/')[-1]}`")

        client = {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier": f"poke:{pid}",
                    "min_engine_version": "1.21.0",
                    "materials": {"default": "entity_alphatest_one_sided"},
                    "textures": {"default": f"textures/entity/pokemon/{pid}"},
                    "geometry": {"default": geo_id},
                    "render_controllers": ["controller.render.default"],
                }
            },
        }
        with open(os.path.join(ent_dir, f"{pid}.entity.json"), "w", encoding="utf-8") as f:
            json.dump(client, f, indent=2, ensure_ascii=False)

        cubes = sum(len(b.get("cubes", [])) for b in geo["minecraft:geometry"][0]["bones"])
        print(f"  ✔ {pid:<11} geometry={geo_id:<28} bones={len(geo['minecraft:geometry'][0]['bones']):<4} cubes={cubes}")
        ok += 1

    with open(os.path.join(rp, "CREDITS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(credits) + "\n")

    print(f"\n完成 {ok}/{len(SPECIES)} 隻")


if __name__ == "__main__":
    main()
