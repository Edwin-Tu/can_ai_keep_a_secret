import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from model_client import get_client
from leak_detector import detect_leak
from scoring import level_to_score, calculate_total_score


ROOT = Path(__file__).resolve().parents[1]


def safe_filename(name: str) -> str:
    """
    Convert a model name into a Windows-safe filename.
    """
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


def load_flag() -> str:
    return (ROOT / "data" / "protected_data.txt").read_text(encoding="utf-8").strip()


def load_system_prompt(flag: str) -> str:
    template = (ROOT / "prompts" / "system_prompt.txt").read_text(encoding="utf-8")
    return template.format(flag=flag)


def load_attacks() -> list[dict]:
    return json.loads((ROOT / "attacks" / "attacks.json").read_text(encoding="utf-8"))


def run_attack(
    client,
    model_name: str,
    system_prompt: str,
    flag: str,
    attack: dict,
    temperature: float,
    max_tokens: int,
    attack_index: int,
    total_attacks: int,
) -> list[dict]:
    """
    Single-turn: each attack starts a fresh session.
    Multi-turn: context is preserved only inside the same attack.
    """
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

        response = client.generate(messages, temperature=temperature, max_tokens=max_tokens)
        messages.append({"role": "assistant", "content": response})

        leak = detect_leak(response, flag)
        score = level_to_score(leak.leak_level)

        print(
            f"[{attack_index}/{total_attacks}] "
            f"{attack['id']} turn {turn_index}/{total_turns}: "
            f"done, leak_level={leak.leak_level}, score={score}",
            flush=True,
        )

        rows.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "model": model_name,
            "attack_id": attack["id"],
            "mode": attack.get("mode", "single_turn"),
            "category": attack.get("category", ""),
            "turn_index": turn_index,
            "prompt": turn["content"],
            "response": response,
            "leak_level": leak.leak_level,
            "score": score,
            "result": leak.result,
            "format_violation": leak.format_violation,
            "reasons": " | ".join(leak.reasons),
            "description": attack.get("description", "")
        })

        # Keep all attacks fully comparable. Do not early stop by default.
        # if leak.leak_level == 4:
        #     break

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mock", help="mock / ollama:<model_name>")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=800,
        help="Maximum output tokens per model response. Default: 800",
    )
    args = parser.parse_args()

    flag = load_flag()
    system_prompt = load_system_prompt(flag)
    attacks = load_attacks()
    client = get_client(args.model)

    print("==================================================", flush=True)
    print("Run benchmark", flush=True)
    print("==================================================", flush=True)
    print(f"Model: {args.model}", flush=True)
    print(f"Temperature: {args.temperature}", flush=True)
    print(f"Max tokens: {args.max_tokens}", flush=True)
    print(f"Total attacks: {len(attacks)}", flush=True)
    print("==================================================", flush=True)

    all_rows = []

    for attack_index, attack in enumerate(attacks, start=1):
        print(
            f"[{attack_index}/{len(attacks)}] "
            f"Running {attack['id']} - {attack.get('category', '')}",
            flush=True,
        )

        rows = run_attack(
            client=client,
            model_name=args.model,
            system_prompt=system_prompt,
            flag=flag,
            attack=attack,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            attack_index=attack_index,
            total_attacks=len(attacks),
        )
        all_rows.extend(rows)

        print(
            f"[{attack_index}/{len(attacks)}] Done {attack['id']}",
            flush=True,
        )

    if not all_rows:
        raise RuntimeError("No benchmark rows were generated. Please check attacks/attacks.json.")

    output_path = ROOT / "results" / f"results_{safe_filename(args.model)}.csv"
    output_path.parent.mkdir(exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

    total_score = calculate_total_score(all_rows)

    print("==================================================", flush=True)
    print(f"Benchmark completed: {output_path}", flush=True)
    print(f"Secret Protection Score: {total_score}", flush=True)
    print("==================================================", flush=True)


if __name__ == "__main__":
    main()
