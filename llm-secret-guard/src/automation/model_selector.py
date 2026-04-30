from __future__ import annotations

from automation.benchmark_runner import run_single_benchmark, run_batch_benchmark
from automation.ollama_tools import get_installed_models
from automation.report_runner import generate_reports


def _normalize_model(model: str) -> str:
    if model == "mock" or model.startswith("ollama:"):
        return model
    return f"ollama:{model}"


def interactive_select_and_run(
    temperature: float = 0,
    max_tokens: int | None = None,
    report_mode: str = "public",
) -> int:
    print("=" * 72)
    print("LLM Secret Guard interactive model selector")
    print("=" * 72)
    print("1. Single model")
    print("2. Batch models from configs/local_models.json")
    print("3. Mock model only")
    choice = input("Select mode [1/2/3]: ").strip() or "1"

    if choice == "2":
        return run_batch_benchmark(
            temperature=temperature,
            max_tokens=max_tokens,
            report_mode=report_mode,
            skip_report=False,
        )

    if choice == "3":
        code = run_single_benchmark("mock", temperature=temperature, max_tokens=max_tokens)
        if code == 0:
            return generate_reports(report_mode)
        return code

    models = get_installed_models()
    if models:
        print("\nInstalled Ollama models:")
        for index, name in enumerate(models, start=1):
            print(f"{index}. {name}")
        raw = input("Choose model number or type model name: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(models):
            model = models[int(raw) - 1]
        else:
            model = raw
    else:
        model = input("Type model name, for example llama3.2:1b or mock: ").strip()

    if not model:
        print("[FAIL] No model selected.")
        return 1

    model_arg = _normalize_model(model)
    code = run_single_benchmark(model_arg, temperature=temperature, max_tokens=max_tokens)
    if code == 0:
        return generate_reports(report_mode)
    return code
