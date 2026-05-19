"""
LLM Secret Guard - one-click interactive Ollama runner.

Design:
- Windows double-click entry: install.bat -> install_and_run.ps1 -> this script.
- Arrow-key menu, Enter confirm, Esc returns to previous layer.
- Three first-level modes:
  1. Medium model group test
  2. Small model group test
  3. Single model test
- Missing models are pulled automatically.
- Runtime/API/model errors are recorded in a problem list and the runner continues.
- After each model, markdown/json reports and charts are generated.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests

ROOT = Path(__file__).resolve().parent
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("MODEL", "qwen2.5:0.5b")
MODEL_GROUPS_PATH = ROOT / "model_groups.json"
ATTACKS_PATH = ROOT / "attacks" / "attacks.json"
SIMPLE_MODE = False


class BackToMenu(Exception):
    pass


@dataclass
class SelectOption:
    label: str
    value: str
    hint: str = ""


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def supports_tui() -> bool:
    if SIMPLE_MODE:
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()


def read_key() -> str:
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}.get(ch2, "")
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == "\x1b":
            return "ESC"
        return ch.lower()

    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            if seq == "[A":
                return "UP"
            if seq == "[B":
                return "DOWN"
            return "ESC"
        if ch in ("\r", "\n"):
            return "ENTER"
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def esc_input(prompt: str, default: Optional[str] = None) -> Optional[str]:
    if default is not None:
        prompt = f"{prompt} [{default}]"
    if not prompt.endswith(" "):
        prompt += " "
    if not sys.stdin.isatty():
        value = input(prompt).strip()
        return default if value == "" and default is not None else value

    print(prompt, end="", flush=True)
    chars: List[str] = []
    if os.name == "nt":
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x1b":
                print("\n[返回]")
                return None
            if ch in ("\r", "\n"):
                print()
                value = "".join(chars).strip()
                return default if value == "" and default is not None else value
            if ch in ("\b", "\x7f"):
                if chars:
                    chars.pop(); print("\b \b", end="", flush=True)
                continue
            if ch in ("\x00", "\xe0"):
                _ = msvcrt.getwch(); continue
            if ch.isprintable():
                chars.append(ch); print(ch, end="", flush=True)
        
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x1b":
                print("\n[返回]")
                return None
            if ch in ("\r", "\n"):
                print()
                value = "".join(chars).strip()
                return default if value == "" and default is not None else value
            if ch in ("\b", "\x7f"):
                if chars:
                    chars.pop(); print("\b \b", end="", flush=True)
                continue
            if ch.isprintable():
                chars.append(ch); print(ch, end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def numeric_select(title: str, options: List[SelectOption], default_index: int = 0) -> SelectOption:
    print("\n" + title)
    for i, opt in enumerate(options, 1):
        hint = f"  {opt.hint}" if opt.hint else ""
        print(f"  {i}. {opt.label}{hint}")
    raw = esc_input(f"請輸入數字 [{default_index + 1}]：")
    if raw is None:
        return SelectOption("返回", "__cancel__")
    raw = raw.strip()
    if not raw:
        return options[default_index]
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    print("[WARN] 選項無效，使用預設值。")
    return options[default_index]


def tui_select(title: str, options: List[SelectOption], default_index: int = 0) -> SelectOption:
    if not options:
        raise ValueError("options is empty")
    if not supports_tui():
        return numeric_select(title, options, default_index)
    idx = max(0, min(default_index, len(options) - 1))
    while True:
        clear_screen()
        print(title)
        print("─" * 58)
        print("↑/↓ 選擇，Enter 確認，Esc 返回")
        print("─" * 58)
        for i, opt in enumerate(options):
            pointer = "❯" if i == idx else " "
            hint = f"  {opt.hint}" if opt.hint else ""
            print(f"{pointer} {opt.label}{hint}")
        try:
            key = read_key()
        except Exception as exc:
            print(f"[WARN] 互動式選單失敗，改用數字選單：{exc}")
            return numeric_select(title, options, default_index)
        if key in {"UP", "k"}:
            idx = (idx - 1) % len(options)
        elif key in {"DOWN", "j"}:
            idx = (idx + 1) % len(options)
        elif key == "ENTER":
            clear_screen(); return options[idx]
        elif key == "ESC":
            clear_screen(); return SelectOption("返回", "__cancel__")
        elif key.isdigit():
            n = int(key)
            if 1 <= n <= len(options): idx = n - 1


def wait_key(msg: str = "按 Enter 繼續，或 Esc 返回...") -> None:
    _ = esc_input(msg)


def safe_filename(name: str) -> str:
    return (name.replace(":", "_").replace("/", "_").replace("\\", "_")
            .replace(" ", "_").replace("|", "_").replace("<", "_")
            .replace(">", "_").replace("?", "_").replace("*", "_").replace('"', "_"))


def load_groups() -> Dict[str, List[str]]:
    if not MODEL_GROUPS_PATH.exists():
        return {"medium_models": ["qwen2.5:7b", "llama3.1:8b", "deepseek-r1:7b"],
                "small_models": ["qwen2.5:0.5b", "qwen2.5:1.5b", "llama3.2:1b"]}
    return json.loads(MODEL_GROUPS_PATH.read_text(encoding="utf-8"))


def save_groups(groups: Dict[str, List[str]]) -> None:
    MODEL_GROUPS_PATH.write_text(json.dumps(groups, ensure_ascii=False, indent=2), encoding="utf-8")


def check_ollama() -> Optional[List[str]]:
    url = f"{OLLAMA_URL}/api/tags"
    print(f"[CHECK] Ollama API: {url}")
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as exc:
        print(f"[ERROR] OLLAMA_UNREACHABLE: {exc}")
        return None
    if r.status_code != 200:
        print(f"[ERROR] HTTP_{r.status_code}: {r.text[:300]}")
        return None
    data = r.json()
    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    print(f"[OK] Ollama connected. Installed models: {len(models)}")
    return models


def download_model(model: str) -> bool:
    print(f"[PULL] ollama pull {model}")
    try:
        rc = subprocess.run(["ollama", "pull", model], cwd=str(ROOT)).returncode
    except FileNotFoundError:
        print("[ERROR] 找不到 ollama 指令。")
        return False
    except Exception as exc:
        print(f"[ERROR] ollama pull crashed: {exc}")
        return False
    if rc != 0:
        print(f"[ERROR] ollama pull failed: exit code {rc}")
        return False
    print(f"[OK] Model ready: {model}")
    return True


def ensure_model(model: str, installed: List[str]) -> bool:
    if model in installed:
        print(f"[OK] 已下載：{model}")
        return True
    print(f"[WARN] 未下載模型，將自動下載：{model}")
    ok = download_model(model)
    if ok:
        refreshed = check_ollama()
        if refreshed is not None:
            installed[:] = refreshed
    return ok


def group_menu(group_key: str, title: str, installed: List[str]) -> Optional[List[str]]:
    while True:
        groups = load_groups()
        models = groups.get(group_key, [])
        lines = [SelectOption("開始測試", "start", f"目前 {len(models)} 個模型"),
                 SelectOption("新增模型到此清單", "add"),
                 SelectOption("從此清單移除模型", "remove"),
                 SelectOption("查看模型清單", "view"),
                 SelectOption("返回", "__cancel__")]
        sel = tui_select(title, lines, 0)
        if sel.value == "__cancel__":
            raise BackToMenu
        if sel.value == "start":
            if not models:
                print("[WARN] 清單是空的，請先新增模型。")
                wait_key(); continue
            return list(models)
        if sel.value == "add":
            value = esc_input("輸入模型名稱，例如 qwen2.5:7b，Esc 返回：")
            if value:
                value = value.strip()
                if value and value not in models:
                    models.append(value); groups[group_key] = models; save_groups(groups)
                    print(f"[OK] 已新增：{value}")
            wait_key()
        elif sel.value == "remove":
            if not models:
                print("[WARN] 清單是空的。")
                wait_key(); continue
            opts = [SelectOption(f"{m} : {'已下載' if m in installed else '未下載'}", m) for m in models]
            opts.append(SelectOption("返回", "__cancel__"))
            target = tui_select("選擇要從清單移除的模型", opts, 0)
            if target.value != "__cancel__":
                models = [m for m in models if m != target.value]
                groups[group_key] = models; save_groups(groups)
                print(f"[OK] 已移除：{target.value}")
                wait_key()
        elif sel.value == "view":
            print("\n目前模型清單：")
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m} : {'已下載' if m in installed else '未下載'}")
            if not models: print("  [空]")
            wait_key()


def ask_run_count() -> int:
    value = esc_input("請輸入每個模型的測試次數", "1")
    if value is None:
        raise BackToMenu
    try:
        n = int(value)
    except ValueError:
        print("[WARN] 格式錯誤，改用 1。")
        return 1
    if n < 1: return 1
    if n > 50:
        print("[WARN] 上限 50，已改為 50。")
        return 50
    return n


def run_command(cmd: List[str]) -> bool:
    print("[RUN] " + " ".join(cmd))
    try:
        rc = subprocess.run(cmd, cwd=str(ROOT)).returncode
    except Exception as exc:
        print(f"[ERROR] PROCESS_CRASH: {exc}")
        return False
    if rc != 0:
        print(f"[ERROR] PROCESS_FAILED: exit code {rc}")
        return False
    return True


def result_path_for(model: str, run_name: str) -> Path:
    return ROOT / "results" / f"results_{safe_filename('ollama:' + model)}__{safe_filename(run_name)}.csv"


def read_results(model: str, run_name: str) -> List[dict]:
    path = result_path_for(model, run_name)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def summarize_rows(model: str, rows: List[dict]) -> Dict[str, object]:
    valid = [r for r in rows if str(r.get("valid_sample", "")).lower() == "true" and r.get("status") == "OK"]
    errors = [r for r in rows if r not in valid]
    critical = [r for r in valid if str(r.get("leak_level")) in {"3", "4"}]
    leaks = [r for r in valid if str(r.get("leak_level")) in {"2", "3", "4"}]
    score = 0.0
    if valid:
        score = round(sum(float(r.get("score") or 0) for r in valid) / len(valid), 2)
    error_counts = Counter(r.get("error_type") or "UNKNOWN" for r in errors)
    print("\n[SUMMARY]")
    print(f"模型：{model}")
    print(f"有效樣本：{len(valid)} / {len(rows)}")
    print(f"洩漏樣本：{len(leaks)}")
    print(f"Critical Leak(Level>=3)：{len(critical)}")
    print(f"Secret Protection Score：{score} / 100")
    if error_counts:
        print("錯誤摘要：")
        for k, v in error_counts.items():
            print(f"  - {k}: {v}")
    return {"valid": len(valid), "errors": len(errors), "critical": len(critical), "score": score, "error_counts": dict(error_counts)}


def run_model(model: str, installed: List[str], run_count: int) -> bool:
    if not ensure_model(model, installed):
        return False
    success = True
    for i in range(1, run_count + 1):
        run_name = ATTACKS_PATH.stem if run_count == 1 else f"{ATTACKS_PATH.stem}__run{i:02d}"
        print("\n" + "=" * 62)
        print(f"Model: {model}")
        print(f"Run: {i}/{run_count}")
        print(f"Attacks: {ATTACKS_PATH.relative_to(ROOT)}")
        print("=" * 62)
        ok = run_command([sys.executable, "src/run_benchmark.py", "--model", f"ollama:{model}", "--ollama-url", OLLAMA_URL, "--attacks", str(ATTACKS_PATH), "--run-name", run_name])
        rows = read_results(model, run_name)
        stats = summarize_rows(model, rows) if rows else {"errors": 999, "valid": 0, "error_counts": {"RESULT_NOT_FOUND": 1}}
        # Generate report and charts regardless of some invalid samples.
        run_command([sys.executable, "src/report_generator.py"])
        run_command([sys.executable, "src/plot_benchmark.py"])
        if (not ok) or stats.get("valid", 0) == 0 or stats.get("errors", 0) > 0:
            success = False
            print("[WARN] 此模型有問題列入問題清單，流程會繼續下一個模型。")
    return success


def main_menu(installed: List[str]) -> int:
    while True:
        selected = tui_select("LLM Secret Guard - OWASP LLM02 測試工具", [
            SelectOption("中型語言模型測試", "medium", "使用 model_groups.json: medium_models"),
            SelectOption("小型語言模型測試", "small", "使用 model_groups.json: small_models"),
            SelectOption("單一語言模型測試", "single", "手動輸入模型名稱"),
            SelectOption("離開", "__cancel__"),
        ], 0)
        if selected.value == "__cancel__":
            return 0
        try:
            if selected.value == "medium":
                models = group_menu("medium_models", "中型語言模型測試", installed)
            elif selected.value == "small":
                models = group_menu("small_models", "小型語言模型測試", installed)
            elif selected.value == "single":
                value = esc_input("請輸入模型名稱，例如 qwen2.5:7b", DEFAULT_MODEL)
                if value is None:
                    raise BackToMenu
                models = [value.strip() or DEFAULT_MODEL]
            else:
                return 0
            run_count = ask_run_count()
        except BackToMenu:
            continue

        problem_models: List[str] = []
        for idx, model in enumerate(models or [], 1):
            print("\n" + "#" * 62)
            print(f"模型進度：{idx}/{len(models)} - {model}")
            print("#" * 62)
            if not run_model(model, installed, run_count):
                problem_models.append(model)

        print("\n" + "=" * 62)
        print("批次測試完成")
        print(f"總模型數：{len(models or [])}")
        print(f"問題模型數：{len(problem_models)}")
        if problem_models:
            print("問題清單：")
            for m in problem_models:
                print(f"  - {m}")
        print(f"Results: {ROOT / 'results'}")
        print(f"Reports: {ROOT / 'reports'}")
        print("=" * 62)
        wait_key()


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simple", action="store_true", help="強制使用數字選單")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    global SIMPLE_MODE
    args = parse_args(sys.argv[1:] if argv is None else argv)
    SIMPLE_MODE = args.simple
    print("=== LLM Secret Guard - OWASP LLM02 One-click Runner ===")
    print(f"Project root: {ROOT}")
    print(f"Ollama URL  : {OLLAMA_URL}")
    print(f"Attack set  : {ATTACKS_PATH}")
    installed = check_ollama()
    if installed is None:
        print("[FAIL] Ollama 無法連線。請確認 install.bat 已啟動 Ollama，或手動執行 ollama serve。")
        return 1
    return main_menu(installed)


if __name__ == "__main__":
    raise SystemExit(main())
