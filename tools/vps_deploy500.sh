#!/bin/bash
# 5.0.0：六隻簡陋模型重製（阿爾宙斯/帝牙盧卡/帕路奇亞/騎拉帝納/戟脊龍/鹽石巨靈）+ 圖鑑縮圖全部重畫
set -uo pipefail
VER=5.0.0
RP=3a0c853a-258b-5980-ad0b-1ee17cfd3c54
BP=b3ca5287-acf7-577e-b046-bca0babb7e6d

rm -rf /tmp/w500 && mkdir -p /tmp/w500 && tar xzf /tmp/p500.tar.gz -C /tmp/w500
echo "RP 檔 $(find /tmp/w500/rp -type f | wc -l) / BP 檔 $(find /tmp/w500/bp -type f | wc -l)"

for w in dev build hunt; do
  D=/opt/mcbedrock/$w/data
  [ -d "$D" ] || continue
  rm -rf "$D/resource_packs/pokemon_rp" "$D/behavior_packs/pokemon_bp"
  cp -a /tmp/w500/rp "$D/resource_packs/pokemon_rp"
  cp -a /tmp/w500/bp "$D/behavior_packs/pokemon_bp"
  chown -R 1000:1000 "$D/resource_packs/pokemon_rp" "$D/behavior_packs/pokemon_bp"
  python3 - "$D" "$RP" "$BP" "$VER" <<'PY'
import json, os, sys
d, rp, bp = sys.argv[1], sys.argv[2], sys.argv[3]
ver = [int(x) for x in sys.argv[4].split(".")]
worlds = os.path.join(d, "worlds")
for name in (os.listdir(worlds) if os.path.isdir(worlds) else []):
    base = os.path.join(worlds, name)
    for fn, uuid in (("world_resource_packs.json", rp), ("world_behavior_packs.json", bp)):
        p = os.path.join(base, fn)
        try:
            arr = json.load(open(p, encoding="utf-8")); arr = arr if isinstance(arr, list) else []
        except Exception:
            arr = []
        hit = False
        for e in arr:
            if e.get("pack_id") == uuid:
                e["version"] = ver; hit = True
        if not hit:
            arr.append({"pack_id": uuid, "version": ver})
        json.dump(arr, open(p, "w", encoding="utf-8"), indent=2)
PY
done
echo "檔案已推"

for c in bds-dev bds-build bds-hunt; do docker stop -t 45 "$c" >/dev/null 2>&1; done
MAX_TRY=6 bash /opt/mcbedrock/startguard.sh 2>&1 | tail -6
sleep 24

echo "=== 驗證 ==="
python3 - <<'PY'
import json, glob, os
d = "/opt/mcbedrock/dev/data"
for pid in ("arceus", "dialga", "palkia", "giratina", "baxcalibur", "garganacl"):
    gp = f"{d}/resource_packs/pokemon_rp/models/entity/{pid}.geo.json"
    g = json.load(open(gp))["minecraft:geometry"][0]
    cubes = sum(len(b.get("cubes") or []) for b in g["bones"])
    e = json.load(open(f"{d}/resource_packs/pokemon_rp/entity/{pid}.entity.json"))["minecraft:client_entity"]["description"]
    a = json.load(open(f"{d}/resource_packs/pokemon_rp/animations/{pid}.animations.json"))["animations"]
    icon = f"{d}/resource_packs/pokemon_rp/textures/ui/dex_{pid}.png"
    print(f"  {pid:<12} 骨骼{len(g['bones']):>3} 方塊{cubes:>3} | geo={e['geometry']['default']:<32} | 動畫{sorted(k.split('.')[-1] for k in a)} | 縮圖{os.path.getsize(icon)//1024}KB")
icons = glob.glob(f"{d}/resource_packs/pokemon_rp/textures/ui/dex_*.png")
print("圖鑑縮圖:", len(icons), "| 版本:", json.load(open(f"{d}/resource_packs/pokemon_rp/manifest.json"))["header"]["version"])
PY
for c in bds-dev bds-build bds-hunt; do printf '%-10s ' "$c"; docker logs --since 4m "$c" 2>&1 | grep -aE 'module loaded|Import \[|Content Error' | tail -1; echo; done
echo "=== 召喚測試 ==="
for p in dialga palkia giratina baxcalibur garganacl arceus; do docker exec bds-build send-command "summon poke:$p 0 -58 12" >/dev/null 2>&1; sleep 1; done
sleep 4
docker logs --since 2m bds-build 2>&1 | grep -acE 'Object successfully summoned'
docker logs --since 2m bds-build 2>&1 | grep -aiE 'content error|invalid|not found' | tail -3
for p in dialga palkia giratina baxcalibur garganacl arceus; do docker exec bds-build send-command "kill @e[type=poke:$p]" >/dev/null 2>&1; done
du -sh /opt/mcbedrock/dev/data/resource_packs/pokemon_rp
for p in 19136 19140 19139; do echo -n "  外部 $p: "; timeout 6 curl -s "http://YOUR_SERVER_IP:$p/v1/join" | head -c 24; echo; done
