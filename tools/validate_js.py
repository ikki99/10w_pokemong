#!/usr/bin/env python3
"""部署前檢查 Bedrock 腳本：語法、重複宣告、未定義的函式呼叫。

BDS 對「重複宣告」只會在載入時吐 SyntaxError 並且整個模組不載入，
而 `node --check` 對某些形式的區塊作用域重複宣告不會報錯，所以自己再掃一遍。
用法: python3 validate_js.py <file.js>
"""
import re
import subprocess
import sys

BUILTINS = {
    # JS 內建
    "console", "Math", "JSON", "Object", "Array", "Map", "Set", "WeakMap", "Number", "String",
    "Boolean", "Promise", "Error", "Symbol", "Date", "parseInt", "parseFloat", "isNaN",
    "setTimeout", "clearTimeout", "structuredClone", "BigInt", "RegExp",
    # 關鍵字 / 語法
    "if", "for", "while", "switch", "catch", "return", "function", "typeof", "new", "await",
    "require", "import", "super", "constructor", "else", "do", "throw", "delete", "void",
    # Bedrock Script API 的注入符號
    "ItemStack", "ActionFormData", "ActionFormResponse", "ModalFormData", "MessageFormData",
    "world", "system", "BlockPermutation", "BlockVolume", "Vector", "Dimension", "Player",
    "Entity", "Block", "Container", "ScoreboardObjective", "EquipmentSlot", "GameMode",
    "ItemComponentTypes", "EntityComponentTypes", "BlockComponentTypes", "TicksPerSecond",
}


def strip_literals(text):
    """去掉字串/模板字串/註解，避免把文字內容當成程式碼掃描。"""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    text = re.sub(r"'(?:\\.|[^'\\])*'", "''", text)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    text = re.sub(r"`(?:\\.|[^`\\])*`", "``", text, flags=re.S)
    return text


def main(path):
    src = open(path, encoding="utf-8").read()
    code = strip_literals(src)
    ok = True

    r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
    if r.returncode != 0:
        print("✘ 語法錯誤：")
        print(r.stderr.strip()[:1200])
        ok = False
    else:
        print("✔ 語法檢查通過")

    # 收集宣告（只看縮排 0 的頂層宣告 + 任何縮排的 function）
    top_decls = {}
    all_decls = {}
    for i, line in enumerate(src.split("\n"), 1):
        m2 = re.match(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=|^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", line)
        if m2:
            nm = m2.group(1) or m2.group(2)
            all_decls.setdefault(nm, []).append(i)
        m = re.match(r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", line)
        if m:
            top_decls.setdefault(m.group(1), []).append(i)
        m = re.match(r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", line)
        if m:
            top_decls.setdefault(m.group(1), []).append(i)

    dups = {k: v for k, v in top_decls.items() if len(v) > 1}
    if dups:
        print("✘ 頂層重複宣告（BDS 會整包載入失敗）：")
        for k, v in dups.items():
            print(f"   {k}: 行 {v}")
        ok = False
    else:
        print("✔ 沒有重複宣告")

    # 未定義的呼叫：這個檢查抓過「函式根本沒被插進去、呼叫端卻已接上」的無聲 bug，
    # 所以直接算致命錯誤。物件字面值裡的方法名也算已定義。
    defined = set(all_decls) | set(top_decls)
    defined |= set(re.findall(r"^\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", code, re.M))
    called = set(re.findall(r"(?<![.\w$])([A-Za-z_$][\w$]*)\s*\(", code))
    unknown = sorted(c for c in called if c not in defined and c not in BUILTINS)
    if unknown:
        print(f"✘ 呼叫了不存在的函式（執行時會丟 ReferenceError 並被 try/catch 吞掉）：{unknown}")
        ok = False
    else:
        print("✔ 所有呼叫都有對應定義")

    print("")

    # 頂層 const/let 的「先用後宣告」（TDZ）：
    # BDS 只會吐 `ReferenceError: X is not initialized` 並讓整個模組載入失敗，
    # node --check 完全抓不到 —— 這個檢查就是為了擋這類災難。
    lines = src.split("\n")
    tdz = []
    consts = {m.group(1): i for i, line in enumerate(lines, 1)
              for m in [re.match(r"^(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=", line)] if m}
    code_lines = strip_literals(src).split("\n")
    for name, decl_line in consts.items():
        for lineno in range(1, decl_line):
            line = code_lines[lineno - 1]
            # 只看「頂層立即執行」的語句：縮排 0 且不是宣告本身。
            # 函式體內的使用是延後執行的，不算 TDZ 問題（否則全是誤報）。
            if not line or line[0] in " \t":
                continue
            if re.match(r"^(?:export\s+)?(?:const|let|var|function|class)\s+" + re.escape(name) + r"\b", line):
                continue
            if re.match(r"^(?:async\s+)?function\b", line):
                continue
            if re.search(r"(?<![.\w$])" + re.escape(name) + r"(?![\w$])", line):
                tdz.append((name, lineno, decl_line))
                break
    if tdz:
        print("✘ 先用後宣告（載入時 ReferenceError: X is not initialized）：")
        for name, used, decl in tdz:
            print(f"   {name}: 在行 {used} 使用，但行 {decl} 才宣告")
        ok = False
    else:
        print("✔ 沒有先用後宣告")

    print("\n結果:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "tools/poke_main.js"))
