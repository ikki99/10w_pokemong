#!/usr/bin/env python3
"""把「攻擊動作」接起來：BP 實體屬性 + 腳本觸發 + RP 實體動畫綁定。

問題：夥伴的攻擊是**腳本 applyDamage** 打出來的（不是原版 melee 行為），
所以客戶端的 `query.is_delayed_attacking` 永遠是 false → 攻擊動畫不會播。

做法：
  1. BP 實體加 `minecraft:properties.poke_attack`（bool，client_sync=true）
  2. 腳本打人的時候 setProperty(true)，0.6 秒後設回 false
  3. RP 實體 description.scripts.animate 加 `{"attack": "query.property('poke_attack')"}`
"""
import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon"
BP = os.path.join(ROOT, "bp")
RP = os.path.join(ROOT, "rp")

PROP = "poke:attack"   # 實體屬性名必須帶命名空間，否則 BDS 直接拒收


def patch_bp():
    n = 0
    for fn in sorted(os.listdir(os.path.join(BP, "entities"))):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(BP, "entities", fn)
        d = json.load(open(p, encoding="utf-8"))
        ent = d["minecraft:entity"]
        desc = ent.setdefault("description", {})
        props = desc.setdefault("properties", {})
        props.pop("poke_attack", None)      # 舊的非法名字要清掉
        if PROP not in props:
            props[PROP] = {"type": "bool", "default": False, "client_sync": True}
            n += 1
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"BP 實體屬性：{n} 個檔案加入 {PROP}")


def patch_rp():
    n = 0
    for fn in sorted(os.listdir(os.path.join(RP, "entity"))):
        if not fn.endswith(".entity.json") or fn.startswith("poke_catch_fx"):
            continue
        p = os.path.join(RP, "entity", fn)
        d = json.load(open(p, encoding="utf-8"))
        desc = d["minecraft:client_entity"]["description"]
        anims = desc.setdefault("animations", {})
        base = fn.replace(".entity.json", "")
        anims["attack"] = f"animation.poke_{base}.attack"
        scripts = desc.setdefault("scripts", {})
        animate = scripts.setdefault("animate", [])
        cond = f"query.property('{PROP}')"
        # 移除舊的，避免重跑疊加
        animate[:] = [a for a in animate if not (isinstance(a, dict) and "attack" in a)]
        animate.append({"attack": cond})
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        n += 1
    print(f"RP 實體動畫綁定：{n} 個檔案")


def patch_js():
    p = os.path.join(BP, "scripts", "main.js")
    s = open(p, encoding="utf-8").read()
    if "poke_attack" in s:
        print("main.js 已接過，跳過")
        return
    anchor = '''  try {
    target.applyDamage(5, { cause: "entityAttack", damagingEntity: follower });'''
    repl = '''  // 讓客戶端播攻擊動作：屬性是 client_sync，RP 的 animate 條件讀它
  try {
    follower.setProperty("poke_attack", true);
    system.runTimeout(() => {
      try { follower.setProperty("poke_attack", false); } catch (e) {}
    }, 12);
  } catch (e) {}

  try {
    target.applyDamage(5, { cause: "entityAttack", damagingEntity: follower });'''
    if anchor not in s:
        print("!! 找不到 followerAttack 的錨點，main.js 沒改")
        return
    s = s.replace(anchor, repl, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("main.js：followerAttack 已加 attack 屬性觸發")


if __name__ == "__main__":
    patch_bp()
    patch_rp()
    patch_js()
