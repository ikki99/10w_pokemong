#!/bin/bash
# 5.0.16：圖鑑頭像路徑去掉 .png + 尾巴火焰粒子/動畫修正
set -uo pipefail
TGZ_DEFAULT=/tmp/psync.tar.gz
RP=3a0c853a-258b-5980-ad0b-1ee17cfd3c54
BP=b3ca5287-acf7-577e-b046-bca0babb7e6d
TGZ=${1:-$TGZ_DEFAULT}

rm -rf /tmp/w516 && mkdir -p /tmp/w516 && tar xzf "$TGZ" -C /tmp/w516
RPV=$(python3 -c "import json;print(','.join(map(str,json.load(open('/tmp/w516/rp/manifest.json'))['header']['version'])))")
BPV=$(python3 -c "import json;print(','.join(map(str,json.load(open('/tmp/w516/bp/manifest.json'))['header']['version'])))")
echo "RP $(find /tmp/w516/rp -type f | wc -l) 檔 ($RPV) / BP $(find /tmp/w516/bp -type f | wc -l) 檔 ($BPV)"

for w in dev build hunt; do
  D=/opt/mcbedrock/$w/data
  [ -d "$D" ] || continue
  rm -rf "$D/resource_packs/pokemon_rp" "$D/behavior_packs/pokemon_bp"
  cp -a /tmp/w516/rp "$D/resource_packs/pokemon_rp"
  cp -a /tmp/w516/bp "$D/behavior_packs/pokemon_bp"
  chown -R 1000:1000 "$D/resource_packs/pokemon_rp" "$D/behavior_packs/pokemon_bp"
  python3 - "$D" "$RP" "$BP" "$RPV" "$BPV" <<'PY'
import json, os, sys
d, rp, bp = sys.argv[1], sys.argv[2], sys.argv[3]
ver_rp = [int(x) for x in sys.argv[4].split(",")]
ver_bp = [int(x) for x in sys.argv[5].split(",")]
worlds = os.path.join(d, "worlds")
for name in (os.listdir(worlds) if os.path.isdir(worlds) else []):
    base = os.path.join(worlds, name)
    for fn, uuid, ver in (("world_resource_packs.json", rp, ver_rp), ("world_behavior_packs.json", bp, ver_bp)):
        p = os.path.join(base, fn)
        try:
            arr = json.load(open(p, encoding="utf-8"))
            arr = arr if isinstance(arr, list) else []
        except Exception:
            arr = []
        hit = False
        for e in arr:
            if e.get("pack_id") == uuid:
                e["version"] = ver; hit = True
        if not hit:
            arr.append({"pack_id": uuid, "version": ver})
        with open(p, "w", encoding="utf-8") as f:
            json.dump(arr, f, indent=2)
PY
done
echo "檔案已推"

for c in bds-dev bds-build bds-hunt; do docker stop -t 45 "$c" >/dev/null 2>&1; done
MAX_TRY=6 bash /opt/mcbedrock/startguard.sh 2>&1 | tail -4
sleep 25

echo "=== 驗證 ==="
python3 - <<'PY'
import json
for w in ("dev","build","hunt"):
    d=f"/opt/mcbedrock/{w}/data"
    try:
        a=json.load(open(f"{d}/resource_packs/pokemon_rp/animations/charizard.animations.json"))["animations"]["animation.poke_charizard.tail_flame"]
        p=json.load(open(f"{d}/resource_packs/pokemon_rp/particles/poke_tail_flame.json"))["particle_effect"]["components"]
        js=open(f"{d}/behavior_packs/pokemon_bp/scripts/main.js",encoding="utf-8").read()
        icon=[l.strip() for l in js.splitlines() if "const dexIcon" in l][0]
        print(f"  {w}: 動畫 loop={a.get('loop')} len={a.get('animation_length')} | 粒子 {len(p)} 組件 | {icon}")
    except Exception as e:
        print(f"  {w}: 讀取失敗 {e}")
PY
for c in bds-dev bds-build bds-hunt; do printf '%-10s ' "$c"; docker logs --since 3m "$c" 2>&1 | grep -aE 'module loaded|SyntaxError|Content Error' | tail -1; echo; done
