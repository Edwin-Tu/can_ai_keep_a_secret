from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
<<<<<<< HEAD
import re
=======
>>>>>>> python_automation
import socket
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from model_client import get_client
from leak_detector import detect_leak
from scoring import level_to_score, calculate_total_score


ROOT = Path(__file__).resolve().parents[1]
<<<<<<< HEAD
BENCHMARK_VERSION = "0.3.0"


def safe_filename(name: str) -> str:
    """Convert a model name into a Windows-safe filename."""
=======
BENCHMARK_VERSION = "0.4.0-python-automation"


def safe_filename(name: str) -> str:
>>>>>>> python_automation
    return (
        name.replace(":", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace("|", "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("?", "_")
        .replace("*", "_")
        .replace('"', "_")
    )


def get_provider(model_name: str) -> str:
    if model_name.startswith("ollama:"):
        return "ollama"
    if ":" in model_name:
        return model_name.split(":", 1)[0]
    return model_name


<<<<<<< HEAD
def get_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        value = result.stdout.strip()
        return value if result.returncode == 0 and value else "N/A"
    except Exception:
        return "N/A"


def run_command(command: list[str], timeout: int = 10) -> str:
    """Run a local command and return stdout/stderr, or N/A if unavailable."""
=======
def run_command(command: list[str], timeout: int = 10) -> str:
>>>>>>> python_automation
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return "N/A"

    output = (result.stdout or result.stderr or "").strip()
    return output if result.returncode == 0 and output else "N/A"


<<<<<<< HEAD
def get_ram_gb() -> str:
    """Return system RAM in GB without requiring third-party dependencies."""
    try:
        import psutil  # type: ignore

        return str(round(psutil.virtual_memory().total / (1024 ** 3), 2))
=======
def get_commit_hash() -> str:
    return run_command(["git", "rev-parse", "--short", "HEAD"])


def file_sha256_short(path: Path, length: int = 12) -> str:
    if not path.exists():
        return "N/A"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:length]


def get_ram_gb() -> str:
    try:
        import psutil  # type: ignore
        return str(round(psutil.virtual_memory().total / (1024**3), 2))
>>>>>>> python_automation
    except Exception:
        pass

    if sys.platform.startswith("win"):
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
<<<<<<< HEAD
            return str(round(status.ullTotalPhys / (1024 ** 3), 2))
=======
            return str(round(status.ullTotalPhys / (1024**3), 2))
>>>>>>> python_automation
        except Exception:
            return "N/A"

    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
<<<<<<< HEAD
        return str(round(pages * page_size / (1024 ** 3), 2))
=======
        return str(round(pages * page_size / (1024**3), 2))
>>>>>>> python_automation
    except Exception:
        return "N/A"


def get_ollama_model_name(model_name: str) -> str:
<<<<<<< HEAD
    if model_name.startswith("ollama:"):
        return model_name.split("ollama:", 1)[1]
    return model_name
=======
    return model_name.split("ollama:", 1)[1] if model_name.startswith("ollama:") else model_name
>>>>>>> python_automation


def get_ollama_version(provider: str) -> str:
    if provider != "ollama":
        return "N/A"
    return run_command(["ollama", "--version"])


def get_ollama_model_id(model_name: str, provider: str) -> str:
<<<<<<< HEAD
    """Best-effort extraction of the Ollama model ID/digest from `ollama list`."""
=======
>>>>>>> python_automation
    if provider != "ollama":
        return "N/A"

    local_model = get_ollama_model_name(model_name)
    output = run_command(["ollama", "list"])
<<<<<<< HEAD
=======

>>>>>>> python_automation
    if output == "N/A":
        return "N/A"

    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[0] == local_model:
            return parts[1]

    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and local_model in parts[0]:
            return parts[1]

    return "N/A"


<<<<<<< HEAD
def ns_to_seconds(value) -> str:
    try:
        if value in (None, ""):
            return ""
        return str(round(float(value) / 1_000_000_000, 3))
    except (TypeError, ValueError):
        return ""


def tokens_per_second(eval_count, eval_duration) -> str:
    try:
        count = float(eval_count)
        seconds = float(eval_duration) / 1_000_000_000
        if count <= 0 or seconds <= 0:
            return ""
        return str(round(count / seconds, 2))
    except (TypeError, ValueError, ZeroDivisionError):
        return ""


def file_sha256_short(path: Path, length: int = 12) -> str:
    if not path.exists():
        return "N/A"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:length]


=======
>>>>>>> python_automation
def load_flag() -> str:
    return (ROOT / "data" / "protected_data.txt").read_text(encoding="utf-8").strip()


def load_system_prompt(flag: str) -> str:
    template = (ROOT / "prompts" / "system_prompt.txt").read_text(encoding="utf-8")
    return template.format(flag=flag)


def load_attacks() -> list[dict]:
    return json.loads((ROOT / "attacks" / "attacks.json").read_text(encoding="utf-8"))


def normalize_max_tokens(value: Optional[int]) -> Optional[int]:
    if value is None or value <= 0:
        return None
    return value


def get_client_metadata(client) -> dict:
    metadata = getattr(client, "last_metadata", {}) or {}
<<<<<<< HEAD
    eval_count = metadata.get("eval_count", "")
    eval_duration = metadata.get("eval_duration", "")
    total_duration = metadata.get("total_duration", "")
    load_duration = metadata.get("load_duration", "")
    prompt_eval_duration = metadata.get("prompt_eval_duration", "")

    return {
        "total_duration": total_duration,
        "total_duration_sec": metadata.get("total_duration_sec") or ns_to_seconds(total_duration),
        "load_duration": load_duration,
        "load_duration_sec": metadata.get("load_duration_sec") or ns_to_seconds(load_duration),
        "prompt_eval_count": metadata.get("prompt_eval_count", ""),
        "prompt_eval_duration": prompt_eval_duration,
        "prompt_eval_duration_sec": metadata.get("prompt_eval_duration_sec") or ns_to_seconds(prompt_eval_duration),
        "eval_count": eval_count,
        "eval_duration": eval_duration,
        "eval_duration_sec": metadata.get("eval_duration_sec") or ns_to_seconds(eval_duration),
        "tokens_per_second": metadata.get("tokens_per_second") or tokens_per_second(eval_count, eval_duration),
=======
    return {
        "total_duration": metadata.get("total_duration", ""),
        "total_duration_sec": metadata.get("total_duration_sec", ""),
        "load_duration": metadata.get("load_duration", ""),
        "load_duration_sec": metadata.get("load_duration_sec", ""),
        "prompt_eval_count": metadata.get("prompt_eval_count", ""),
        "prompt_eval_duration": metadata.get("prompt_eval_duration", ""),
        "prompt_eval_duration_sec": metadata.get("prompt_eval_duration_sec", ""),
        "eval_count": metadata.get("eval_count", ""),
        "eval_duration": metadata.get("eval_duration", ""),
        "eval_duration_sec": metadata.get("eval_duration_sec", ""),
        "tokens_per_second": metadata.get("tokens_per_second", ""),
>>>>>>> python_automation
    }


def run_attack(
    client,
    model_name: str,
    system_prompt: str,
    flag: str,
    attack: dict,
    temperature: float,
    max_tokens: Optional[int],
    run_metadata: dict,
    attack_index: int,
    total_attacks: int,
) -> list[dict]:
<<<<<<< HEAD
    """
    Single-turn: each attack starts a fresh session.
    Multi-turn: context is preserved only inside the same attack.

    max_tokens=None means no explicit output token limit is sent to the client.
    """
=======
>>>>>>> python_automation
    rows = []
    messages = [{"role": "system", "content": system_prompt}]
    turns = attack["turns"]
    total_turns = len(turns)

    for turn_index, turn in enumerate(turns, start=1):
        print(
            f"[{attack_index}/{total_attacks}] "
            f"{attack['id']} turn {turn_index}/{total_turns}: sending prompt...",
            flush=True,
        )

        messages.append(turn)

        if max_tokens is None:
            response = client.generate(messages, temperature=temperature)
        else:
            response = client.generate(messages, temperature=temperature, max_tokens=max_tokens)

        messages.append({"role": "assistant", "content": response})

        leak = detect_leak(response, flag)
        score = level_to_score(leak.leak_level)
        client_metadata = get_client_metadata(client)

        print(
            f"[{attack_index}/{total_attacks}] "
            f"{attack['id']} turn {turn_index}/{total_turns}: "
            f"done, leak_level={leak.leak_level}, score={score}",
            flush=True,
        )

        row = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "run_id": run_metadata["run_id"],
            "model": model_name,
            "provider": run_metadata["provider"],
            "temperature": temperature,
            "max_tokens": run_metadata["max_tokens_label"],
            "benchmark_version": run_metadata["benchmark_version"],
            "attack_set_version": run_metadata["attack_set_version"],
            "commit_hash": run_metadata["commit_hash"],
            "host_name": run_metadata["host_name"],
            "python_version": run_metadata["python_version"],
            "platform": run_metadata["platform"],
            "os_version": run_metadata["os_version"],
            "machine": run_metadata["machine"],
            "processor": run_metadata["processor"],
            "cpu_count": run_metadata["cpu_count"],
            "ram_gb": run_metadata["ram_gb"],
            "ollama_version": run_metadata["ollama_version"],
            "ollama_model_id": run_metadata["ollama_model_id"],
            "attack_id": attack["id"],
            "mode": attack.get("mode", "single_turn"),
            "category": attack.get("category", ""),
            "turn_index": turn_index,
            "prompt": turn["content"],
            "response": response,
            "response_chars": len(response),
            "leak_level": leak.leak_level,
            "score": score,
            "result": leak.result,
            "format_violation": leak.format_violation,
            "reasons": " | ".join(leak.reasons),
            "description": attack.get("description", ""),
        }
        row.update(client_metadata)
        rows.append(row)
<<<<<<< HEAD

        # Keep all attacks fully comparable. Do not early stop by default.
        # if leak.leak_level == 4:
        #     break
=======
>>>>>>> python_automation

    return rows


<<<<<<< HEAD
def main():
=======
def main() -> None:
>>>>>>> python_automation
    parser = argparse.ArgumentParser(description="Run LLM Secret Guard benchmark")
    parser.add_argument("--model", default="mock", help="mock / ollama:<model_name>")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
<<<<<<< HEAD
        help=(
            "Optional maximum output tokens per model response. "
            "If omitted or <= 0, no explicit output token limit is sent to the model client."
        ),
=======
        help="Optional per-response token limit. Omit or <=0 for unlimited/model default.",
>>>>>>> python_automation
    )
    args = parser.parse_args()
    args.max_tokens = normalize_max_tokens(args.max_tokens)

    flag = load_flag()
    system_prompt = load_system_prompt(flag)
    attacks = load_attacks()
    client = get_client(args.model)

    max_tokens_label = str(args.max_tokens) if args.max_tokens is not None else "unlimited / model default"
    provider = get_provider(args.model)
<<<<<<< HEAD
=======

>>>>>>> python_automation
    run_metadata = {
        "run_id": uuid.uuid4().hex[:12],
        "provider": provider,
        "max_tokens_label": max_tokens_label,
        "benchmark_version": BENCHMARK_VERSION,
        "attack_set_version": file_sha256_short(ROOT / "attacks" / "attacks.json"),
        "commit_hash": get_commit_hash(),
        "host_name": socket.gethostname(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "os_version": platform.platform(),
        "machine": platform.machine() or "N/A",
        "processor": platform.processor() or "N/A",
        "cpu_count": os.cpu_count() or "N/A",
        "ram_gb": get_ram_gb(),
        "ollama_version": get_ollama_version(provider),
        "ollama_model_id": get_ollama_model_id(args.model, provider),
    }

<<<<<<< HEAD
    print("==================================================", flush=True)
    print("Run benchmark", flush=True)
    print("==================================================", flush=True)
    print(f"Run ID: {run_metadata['run_id']}", flush=True)
    print(f"Model: {args.model}", flush=True)
    print(f"Provider: {run_metadata['provider']}", flush=True)
    print(f"Temperature: {args.temperature}", flush=True)
    print(f"Max tokens: {max_tokens_label}", flush=True)
    print(f"Benchmark version: {BENCHMARK_VERSION}", flush=True)
    print(f"Attack set version: {run_metadata['attack_set_version']}", flush=True)
    print(f"Ollama version: {run_metadata['ollama_version']}", flush=True)
    print(f"Ollama model ID: {run_metadata['ollama_model_id']}", flush=True)
    print(f"Host: {run_metadata['host_name']}", flush=True)
    print(f"Total attacks: {len(attacks)}", flush=True)
    print("==================================================", flush=True)
=======
    print("=" * 72, flush=True)
    print("Run benchmark", flush=True)
    print("=" * 72, flush=True)
    print(f"Run ID: {run_metadata['run_id']}", flush=True)
    print(f"Model: {args.model}", flush=True)
    print(f"Provider: {provider}", flush=True)
    print(f"Temperature: {args.temperature}", flush=True)
    print(f"Max tokens: {max_tokens_label}", flush=True)
    print(f"Total attacks: {len(attacks)}", flush=True)
    print("=" * 72, flush=True)
>>>>>>> python_automation

    all_rows = []

    for attack_index, attack in enumerate(attacks, start=1):
        print(
            f"[{attack_index}/{len(attacks)}] "
            f"Running {attack['id']} - {attack.get('category', '')}",
            flush=True,
        )
<<<<<<< HEAD

=======
>>>>>>> python_automation
        rows = run_attack(
            client=client,
            model_name=args.model,
            system_prompt=system_prompt,
            flag=flag,
            attack=attack,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            run_metadata=run_metadata,
            attack_index=attack_index,
            total_attacks=len(attacks),
        )
        all_rows.extend(rows)
        print(f"[{attack_index}/{len(attacks)}] Done {attack['id']}", flush=True)

    if not all_rows:
        raise RuntimeError("No benchmark rows were generated. Please check attacks/attacks.json.")

        print(f"[{attack_index}/{len(attacks)}] Done {attack['id']}", flush=True)

    if not all_rows:
        raise RuntimeError("No benchmark rows were generated. Please check attacks/attacks.json.")

    output_path = ROOT / "results" / f"results_{safe_filename(args.model)}.csv"
    output_path.parent.mkdir(exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

    total_score = calculate_total_score(all_rows)

<<<<<<< HEAD
    print("==================================================", flush=True)
    print(f"Benchmark completed: {output_path}", flush=True)
    print(f"Secret Protection Score: {total_score}", flush=True)
    print("==================================================", flush=True)
=======
    print("=" * 72, flush=True)
    print(f"Benchmark completed: {output_path}", flush=True)
    print(f"Secret Protection Score: {total_score}", flush=True)
    print("=" * 72, flush=True)
>>>>>>> python_automation


if __name__ == "__main__":
    main()
