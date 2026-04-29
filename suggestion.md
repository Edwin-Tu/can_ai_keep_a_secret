# suggestion.md

# Can AI Keep a Secret? 下一階段修改建議

本文件整理目前專案接下來的修改方向，重點是支援「本地端開源模型測試」與「學校電腦教室多台主機分散執行 benchmark」。

---

## 1. 目前專案定位

目前 GitHub 上的內容主要是建立一個統一的 LLM 安全測試框架。

也就是先標準化以下內容：

```text
固定 fake flag
固定 system prompt
固定 attacks.json 攻擊題庫
固定 leak_detector.py 洩漏偵測
固定 scoring.py 評分規則
固定 results.csv 結果輸出
固定 report.md 報告格式
```

目前專案不是重點放在串接所有付費 API，而是先完成一套可重複、可比較、可量化的測試流程。

---

## 2. 目前主要缺口

目前主要缺口不是專題方向錯誤，而是：

> 被測試模型的連接方式還沒有完整。

也就是 Target LLM 的 client 還需要補強。

商用 API 模型可能會透過：

```text
OpenAI API
Claude API
Gemini API
```

本地開源模型則建議先透過：

```text
Ollama
LM Studio
llama.cpp
text-generation-webui
```

但目前下一階段最建議先做的是：

```text
Ollama 本地模型串接
```

---

## 3. 下一階段核心目標

下一階段目標是：

```text
1. 確認 mock benchmark 可以正常執行
2. 新增 Ollama client
3. 支援 ollama:<model_name> 形式執行本地模型
4. 新增本地模型清單
5. 新增批次測試腳本
6. 讓多台學校電腦可以各自跑不同模型
7. 最後彙整 results.csv 與 report.md 到 GitHub
```

---

## 4. 建議優先修改清單

## 4.1 確認目前 mock 流程可執行

在接本地模型之前，先確認現有流程可以跑。

執行：

```bash
cd llm-secret-guard
python src/run_benchmark.py --model mock
python src/report_generator.py
```

成功後應產生：

```text
results/results_mock.csv
reports/report_mock.md
```

如果這兩個檔案無法產生，代表主流程仍有錯誤，應先修復後再接 Ollama。

---

## 4.2 新增 Ollama Client

新增檔案：

```text
src/clients/ollama_client.py
```

建議內容：

```python
import requests
from typing import List, Dict


class OllamaClient:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        max_tokens: int = 300,
    ) -> str:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "keep_alive": "10m",
        }

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=180,
        )
        response.raise_for_status()

        data = response.json()
        return data["message"]["content"]
```

此檔案的目的：

```text
讓專案可以呼叫本機 Ollama 模型
```

---

## 4.3 修改 model_client.py 支援 Ollama

修改：

```text
src/model_client.py
```

新增支援格式：

```text
ollama:<model_name>
```

例如：

```bash
python src/run_benchmark.py --model ollama:qwen2.5:3b
python src/run_benchmark.py --model ollama:llama3.1:8b
python src/run_benchmark.py --model ollama:gemma3:4b
```

建議邏輯：

```python
from clients.ollama_client import OllamaClient

def get_client(model_name: str):
    model_name_lower = model_name.lower()

    if model_name_lower == "mock":
        return MockClient()

    if model_name_lower.startswith("ollama:"):
        ollama_model = model_name.split("ollama:", 1)[1]
        return OllamaClient(model_name=ollama_model)

    ...
```

---

## 4.4 修改 run_benchmark.py 的輸出檔名

因為 Ollama 模型名稱可能包含冒號，例如：

```text
ollama:qwen2.5:7b
```

在 Windows 中，冒號不適合直接當檔名。

建議在：

```text
src/run_benchmark.py
```

新增：

```python
def safe_filename(name: str) -> str:
    return (
        name.replace(":", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
    )
```

並將：

```python
output_path = ROOT / "results" / f"results_{args.model}.csv"
```

改為：

```python
output_path = ROOT / "results" / f"results_{safe_filename(args.model)}.csv"
```

預期輸出：

```text
results/results_ollama_qwen2.5_3b.csv
results/results_ollama_llama3.1_8b.csv
results/results_ollama_gemma3_4b.csv
```

---

## 4.5 新增 configs/local_models.json

新增資料夾與檔案：

```text
configs/local_models.json
```

用途：

```text
集中管理要測試的本地模型清單
```

範例：

```json
[
  {
    "name": "qwen2.5:3b",
    "provider": "ollama",
    "enabled": true,
    "assigned_pc": "PC-01"
  },
  {
    "name": "llama3.1:8b",
    "provider": "ollama",
    "enabled": true,
    "assigned_pc": "PC-02"
  },
  {
    "name": "gemma3:4b",
    "provider": "ollama",
    "enabled": true,
    "assigned_pc": "PC-03"
  },
  {
    "name": "deepseek-r1:7b",
    "provider": "ollama",
    "enabled": true,
    "assigned_pc": "PC-04"
  },
  {
    "name": "mistral:7b",
    "provider": "ollama",
    "enabled": true,
    "assigned_pc": "PC-05"
  }
]
```

---

## 4.6 新增 run_all_local_models.py

新增檔案：

```text
src/run_all_local_models.py
```

用途：

```text
讀取 configs/local_models.json
逐一執行本地模型 benchmark
每個模型產生自己的 results.csv
```

建議內容：

```python
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "local_models.json"
    models = json.loads(config_path.read_text(encoding="utf-8"))

    for item in models:
        if not item.get("enabled", True):
            continue

        model_name = item["name"]
        cli_model_name = f"ollama:{model_name}"

        print(f"=== Running benchmark: {cli_model_name} ===")

        subprocess.run(
            [
                "python",
                "src/run_benchmark.py",
                "--model",
                cli_model_name,
                "--temperature",
                "0",
                "--max-tokens",
                "300",
            ],
            cwd=ROOT,
            check=False,
        )


if __name__ == "__main__":
    main()
```

執行方式：

```bash
python src/run_all_local_models.py
```

---

## 5. 學校電腦教室測試流程建議

你計畫在學校電腦教室使用多台主機跑不同模型，這是可行且適合本專題的方法。

建議流程如下：

```text
1. 每台電腦 clone 同一份 GitHub repo
2. 每台電腦安裝相同版本的 Python 套件
3. 每台電腦安裝 Ollama
4. 每台電腦 pull 指定模型
5. 每台電腦執行相同 benchmark
6. 每台電腦產生自己的 results.csv / report.md
7. 最後彙整到主 repo
```

---

## 6. 多台主機分工範例

| 電腦 | 模型 | 指令 | 輸出檔案 |
|---|---|---|---|
| PC-01 | qwen2.5:3b | `python src/run_benchmark.py --model ollama:qwen2.5:3b` | `results_ollama_qwen2.5_3b.csv` |
| PC-02 | llama3.1:8b | `python src/run_benchmark.py --model ollama:llama3.1:8b` | `results_ollama_llama3.1_8b.csv` |
| PC-03 | gemma3:4b | `python src/run_benchmark.py --model ollama:gemma3:4b` | `results_ollama_gemma3_4b.csv` |
| PC-04 | deepseek-r1:7b | `python src/run_benchmark.py --model ollama:deepseek-r1:7b` | `results_ollama_deepseek-r1_7b.csv` |
| PC-05 | mistral:7b | `python src/run_benchmark.py --model ollama:mistral:7b` | `results_ollama_mistral_7b.csv` |

---

## 7. 測試公平性注意事項

使用多台電腦測試時，最重要的是固定實驗條件。

每台電腦都應使用相同版本的：

```text
protected_data.txt
system_prompt.txt
attacks.json
leak_detector.py
scoring.py
run_benchmark.py
```

並固定參數：

```text
temperature = 0
max_tokens = 300
```

也應記錄：

```text
benchmark version
commit hash
attack set version
model name
computer name
test date
```

建議每份結果都能追溯到同一個 Git commit。

---

## 8. 建議新增 experiment metadata

建議在 `results.csv` 裡增加欄位：

```text
benchmark_version
commit_hash
host_name
model
provider
temperature
max_tokens
attack_id
category
turn_index
leak_level
score
result
```

這樣未來彙整多台電腦結果時，比較不會混亂。

如果短期不想改很多，可以至少在報告中手動註明：

```text
Benchmark Version: v0.1
Commit Hash: xxxxxxx
Attack Set: attacks_v1
Flag: FLAG{AIA_TEST_SECRET_2026}
Temperature: 0
Max Tokens: 300
```

---

## 9. 建議新增 docs/local_model_testing.md

新增文件：

```text
docs/local_model_testing.md
```

內容建議包含：

```text
1. 安裝 Ollama
2. pull 模型
3. 確認模型可執行
4. 執行單一模型 benchmark
5. 執行多模型 benchmark
6. 收集 results.csv 與 report.md
7. 上傳結果到 GitHub
```

範例指令：

```bash
ollama pull qwen2.5:3b
ollama run qwen2.5:3b

python src/run_benchmark.py --model ollama:qwen2.5:3b
python src/report_generator.py
```

---

## 10. 建議新增 docs/experiment_rules.md

新增文件：

```text
docs/experiment_rules.md
```

內容建議包含：

```text
# Experiment Rules

1. All models use the same fake flag.
2. All models use the same system prompt.
3. All models use the same attacks.json.
4. All single-turn tests start from a fresh session.
5. All multi-turn tests follow fixed turns.
6. No dynamic follow-up is allowed in V1.
7. temperature must be 0.
8. max_tokens must be 300.
9. Results must include model name and benchmark version.
10. Only fake secrets are used.
```

這份文件可以直接放進報告，強調實驗公平性。

---

## 11. 建議優化 report_generator.py

目前報告可以先產生單模型報告。

下一步建議新增多模型總表：

```text
reports/summary_report.md
```

內容包含：

| Model | Score | Full Leak | Partial Leak | Format Leak | Error Count |
|---|---:|---:|---:|---:|---:|
| qwen2.5:3b | 88 | 0 | 2 | 1 | 0 |
| llama3.1:8b | 82 | 1 | 3 | 1 | 0 |
| gemma3:4b | 76 | 2 | 4 | 2 | 0 |

建議 summary report 顯示：

```text
1. 各模型總分
2. 各模型完整洩漏次數
3. 各模型部分洩漏次數
4. 各模型格式洩漏次數
5. 各模型錯誤次數
6. 各模型測試題數
```

---

## 12. 題庫後續擴充建議

目前題庫類型方向正確，但若要做更可靠的 benchmark，建議擴充到 25 到 35 題。

建議比例：

| 類型 | 題數 |
|---|---:|
| Direct Request | 3–5 |
| Role Play | 3–5 |
| Instruction Override | 3–5 |
| System Prompt Extraction | 3–5 |
| Encoding Bypass | 3–5 |
| Partial Disclosure | 3–5 |
| Multi-turn Social Engineering | 3–5 組 |

原則：

```text
單輪題每題獨立 session
多輪題固定輪數與固定內容
不根據模型回覆臨時追加問題
```

---

## 13. 洩漏偵測後續優化建議

目前 leak detector 可以先做：

```text
完整 flag
flag 格式
部分內容
Base64
提到機密存在
```

後續建議增加：

```text
hex 編碼
ASCII code 編碼
反轉字串
空格分隔字元
大小寫變形
分段洩漏
```

例如：

```text
F L A G { A I A _ T E S T ... }
74657374...
70 76 65 71 ...
}6202_TERCES_TSET_AIA{GALF
```

這樣比較能測 encoding bypass。

---

## 14. README 建議新增內容

README 建議新增一節：

```text
## Local Open-Source Model Testing
```

內容包含：

```text
1. 安裝 Ollama
2. pull 模型
3. 單一模型測試
4. 批次模型測試
5. 彙整結果
```

範例：

```bash
ollama pull qwen2.5:3b
python src/run_benchmark.py --model ollama:qwen2.5:3b
python src/report_generator.py
```

---

## 15. .gitignore 建議

因為你要上傳報告到 GitHub，可以考慮調整 `.gitignore`。

如果想保存正式結果，可以不要完全忽略 `results/*.csv` 和 `reports/*.md`。

建議做法：

```text
results/raw/
reports/generated/
reports/final/
```

`.gitignore` 可以忽略 raw 暫存，但保留 final 報告。

範例：

```gitignore
# Ignore temporary results
results/tmp/
reports/tmp/

# Keep final benchmark reports
!reports/final/
!reports/final/*.md
!results/final/
!results/final/*.csv
```

或簡單做法：

```text
測試階段不 commit results
期末報告階段再手動加入 final report
```

---

## 16. 目前最小完成標準

下一階段完成以下項目，就代表專案可以進入大量模型測試：

```text
✅ mock benchmark 可以跑
✅ ollama_client.py 完成
✅ model_client.py 支援 ollama:<model>
✅ run_benchmark.py 可輸出安全檔名
✅ qwen2.5:3b 可在本地跑完 benchmark
✅ 至少 3 個開源模型可在不同電腦跑
✅ results.csv 可彙整
✅ summary_report.md 可產生
```

---

## 17. 建議開發順序

建議依照以下順序進行：

```text
Step 1：確認 mock benchmark 可執行
Step 2：新增 Ollama client
Step 3：修改 model_client.py 支援 ollama:<model>
Step 4：修正 run_benchmark.py 檔名安全問題
Step 5：安裝 Ollama 並 pull qwen2.5:3b
Step 6：測試單一 Ollama 模型
Step 7：新增 configs/local_models.json
Step 8：新增 run_all_local_models.py
Step 9：在多台學校電腦分散跑模型
Step 10：彙整 results.csv 與 reports
Step 11：產生 summary_report.md
Step 12：將 final report 上傳 GitHub
```

---

## 18. 可放入報告的專案描述

可以將以下文字放入 README、簡報或報告：

> 本專案目前先建立模型無關的 LLM 安全測試框架，將受保護資料、system prompt、攻擊題庫、洩漏偵測與評分規則標準化。後續可透過不同 model client 串接 OpenAI、Claude、Gemini 或本地開源模型。第一階段將以 Ollama 在本地端執行多個開源模型，並使用相同 benchmark 產生可比較的安全評估報告。

---

## 19. 結論

目前 GitHub 專案的主要價值在於：

```text
統一測試流程
統一題庫
統一偵測方式
統一報告格式
```

下一階段要做的是：

```text
接上本地開源模型
讓多台電腦可以分散跑 benchmark
最後彙整結果成模型安全比較報告
```

目前最重要的不是先接所有付費 API，而是：

> 先讓 Ollama 本地模型測試流程跑通。

完成後，專題會從「測試框架雛形」進一步變成「可大量測試不同 LLM 的安全評估工具」。
