"""
批次執行本地模型測試

讀取 configs/local_models.json，逐一執行 run_benchmark.py，
為每個模型產生結果 CSV，最後可再執行 report_generator.py 生成統一報告。

預設不限制模型輸出 token；若需要限制，可在呼叫 run_benchmark() 時傳入 max_tokens。
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]


def load_local_models() -> List[Dict]:
    """
    從 configs/local_models.json 讀取模型清單

    Returns:
        啟用的模型列表
    """
    config_path = ROOT / "configs" / "local_models.json"

    if not config_path.exists():
        raise FileNotFoundError(f"配置檔案不存在：{config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        models = json.load(f)

    # 只返回啟用的模型
    enabled_models = [m for m in models if m.get("enabled", False)]

    if not enabled_models:
        print("警告：configs/local_models.json 中沒有啟用的模型")
        return []

    return enabled_models


def run_benchmark(
    model_name: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
) -> bool:
    """
    執行單個模型的 benchmark

    Args:
        model_name: 模型名稱，例如 "ollama:qwen2.5:3b"
        temperature: 溫度參數
        max_tokens: 最大 token 數。None 代表不主動限制輸出 token。

    Returns:
        True 如果執行成功，False 如果失敗
    """
    script_path = ROOT / "src" / "run_benchmark.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--model",
        model_name,
        "--temperature",
        str(temperature),
    ]

    if max_tokens is not None and max_tokens > 0:
        cmd.extend(["--max-tokens", str(max_tokens)])

    print(f"\n{'='*60}")
    print(f"執行: {' '.join(cmd)}")
    if max_tokens is None or max_tokens <= 0:
        print("Max tokens: unlimited / model default")
    else:
        print(f"Max tokens: {max_tokens}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, cwd=ROOT, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"執行失敗：{str(e)}")
        return False


def main():
    """主程序：批次執行所有啟用的本地模型"""

    print("\n🚀 開始批次測試本地模型...\n")

    try:
        models = load_local_models()
    except FileNotFoundError as e:
        print(f"❌ 錯誤：{e}")
        print("\n提示：請確認 configs/local_models.json 存在")
        sys.exit(1)

    if not models:
        print("❌ 沒有可執行的模型")
        sys.exit(1)

    print(f"📋 偵測到 {len(models)} 個啟用的模型：")
    for model in models:
        print(f"  - {model['name']}: {model.get('description', 'N/A')}")

    print("\n⏳ 開始執行測試...\n")

    results = {}
    success_count = 0
    fail_count = 0

    for model in models:
        model_name = model["name"]
        full_model_name = f"ollama:{model_name}"

        print(f"\n[{success_count + fail_count + 1}/{len(models)}] 測試模型：{model_name}")

        if run_benchmark(full_model_name):
            success_count += 1
            results[model_name] = "✓ 成功"
            print(f"✓ {model_name} 測試完成")
        else:
            fail_count += 1
            results[model_name] = "✗ 失敗"
            print(f"✗ {model_name} 測試失敗")

    # 打印最終報告
    print(f"\n{'='*60}")
    print("📊 批次測試完成報告")
    print(f"{'='*60}")
    print(f"成功：{success_count}/{len(models)}")
    print(f"失敗：{fail_count}/{len(models)}\n")

    for model_name, status in results.items():
        print(f"  {status}  {model_name}")

    print(f"\n{'='*60}")
    print("💾 結果已保存至：results/ 目錄")
    print("📝 執行 python src/report_generator.py 以生成統一報告")
    print(f"{'='*60}\n")

    return fail_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
