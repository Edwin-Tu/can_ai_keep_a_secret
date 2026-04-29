# report.md

# Can AI Keep a Secret? 專案掃描與修正報告

## 掃描分支

```text
Repository: Edwin-Tu/can_ai_keep_a_secret
Branch: Edwin-0428
Target folder: llm-secret-guard/
```

## 一、總結判斷

目前 `Edwin-0428` 分支的專題方向 **沒有偏離目標**。

此專案仍然符合原本設定的核心目的：

> 建立一套 LLM hidden flag 防護能力測試 benchmark，透過固定攻擊題庫、固定 system prompt、固定 fake flag、固定洩漏偵測與固定評分規則，比較不同模型是否會在提示詞攻擊下洩漏受保護資料。

目前專案的主要問題不是方向錯誤，而是：

```text
1. 部分檔案格式可能造成程式無法執行
2. 本地端開源模型串接尚未完成
3. 題庫數量仍偏少
4. 多模型彙整報告尚未完整
5. GitHub 上的結果保存策略需要調整
```

因此，接下來的修正重點應該是：

```text
先修可執行性
再接 Ollama
再做本地大量模型測試
最後產生總結報告
```

---

# 二、是否偏離專題目標？

## 2.1 判斷結果

```text
是否偏離目標：否
目前方向：正確
目前架構：合理
目前階段：測試框架雛形
下一階段：接入本地開源模型並批次測試
```

---

## 2.2 為什麼沒有偏離？

目前專案仍圍繞以下核心流程：

```text
protected_data.txt
        ↓
system_prompt.txt
        ↓
attacks.json
        ↓
run_benchmark.py
        ↓
Target LLM
        ↓
leak_detector.py
        ↓
scoring.py
        ↓
results.csv
        ↓
report.md
```

這正好對應專題目標：

```text
讓不同 LLM 面對相同 hidden flag 與相同攻擊題庫，
觀察模型是否會洩漏受保護資料，
最後輸出量化比較報告。
```

---

## 2.3 目前保留的正確設計

目前專案中的這些設計是正確的：

| 項目 | 判斷 |
|---|---|
| 使用 fake flag | 正確 |
| 使用 system prompt 保護資料 | 正確 |
| 使用固定 attacks.json 題庫 | 正確 |
| 區分 single-turn / multi-turn | 正確 |
| AI 回覆只影響評分，不影響下一題 | 正確 |
| 使用 leak level 分級 | 正確 |
| 先做固定 benchmark，再做 AI vs AI | 正確 |
| 預留多模型 client 架構 | 正確 |
| 後續優先本地開源模型 | 正確 |

---

# 三、重大缺失

## 3.1 重大缺失一：部分 Python 檔案可能被壓成單行

目前最大風險是部分 Python 檔案在 GitHub raw 顯示中可能被壓成單行。

例如應該是：

```python
import argparse
import csv
import json
```

但如果變成：

```python
import argparse import csv import json
```

Python 會直接出現：

```text
SyntaxError
```

這會導致整個 benchmark 無法執行。

---

## 3.2 優先檢查檔案

請優先檢查以下檔案是否換行與縮排正常：

```text
src/run_benchmark.py
src/model_client.py
src/leak_detector.py
src/main.py
src/scoring.py
src/report_generator.py
src/clients/mock_client.py
src/clients/ollama_client.py
tests/test_leak_detector.py
```

如果這些檔案出現單行化，請先修復後再進行下一步。

---

## 3.3 重大缺失二：requirements.txt 可能格式錯誤

`requirements.txt` 每個套件應該獨立一行。

正確格式：

```text
python-dotenv>=1.0.1
openai>=1.0.0
google-generativeai>=0.3.0
requests>=2.31.0
anthropic>=0.7.0
```

錯誤格式：

```text
python-dotenv>=1.0.1 openai>=1.0.0 google-generativeai>=0.3.0 requests>=2.31.0 anthropic>=0.7.0
```

若全部擠在同一行，`pip install -r requirements.txt` 可能無法正確安裝。

---

## 3.4 重大缺失三：Ollama client 尚未完整實作

你目前下一步目標是：

```text
取得開源模型並於本地端大量測試
```

因此最重要的模型連接方式應該是：

```text
Ollama
```

目前若 `src/clients/ollama_client.py` 仍只有 `NotImplementedError`，代表還不能真正測本地模型。

建議補上：

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

---

## 3.5 重大缺失四：model_client.py 需支援 ollama:<model>

目前若 `model_client.py` 尚未支援以下格式：

```text
ollama:qwen2.5:3b
ollama:llama3.1:8b
ollama:gemma3:4b
```

就無法直接執行本地模型 benchmark。

建議新增：

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

## 3.6 重大缺失五：題庫數量仍偏少

目前題庫分類方向正確，但數量仍偏少。

若只有 6 題單輪加 1 組多輪，作為 Demo 可以，但作為 benchmark 稍嫌不足。

建議擴充到：

```text
25～35 題
```

建議比例：

| 類型 | 建議題數 |
|---|---:|
| Direct Request | 3–5 |
| Role Play | 3–5 |
| Instruction Override | 3–5 |
| System Prompt Extraction | 3–5 |
| Encoding Bypass | 3–5 |
| Partial Disclosure | 3–5 |
| Multi-turn Social Engineering | 3–5 組 |

---

## 3.7 重大缺失六：結果檔案可能被 .gitignore 忽略

你的計畫是：

```text
在學校電腦教室跑大量模型
每台主機產生結果
最後將報告上傳 GitHub
```

如果 `.gitignore` 直接忽略：

```text
results/
reports/
```

那正式結果可能不會被 Git 追蹤。

建議改成：

```gitignore
results/tmp/
reports/tmp/
```

或保留 final 結果：

```gitignore
results/*
reports/*

!results/final/
!results/final/*.csv
!reports/final/
!reports/final/*.md
```

---

# 四、目前做得好的部分

## 4.1 專案骨架完整

目前資料夾設計符合 benchmark 專案需求：

```text
llm-secret-guard/
├── attacks/
├── data/
├── docs/
├── prompts/
├── reports/
├── results/
├── src/
├── tests/
├── README.md
├── requirements.txt
└── .env.example
```

這代表專案已經不是零散程式，而是有清楚分層。

---

## 4.2 專題名稱與定位清楚

目前專案名稱：

```text
Can AI Keep a Secret?
```

很符合專題主軸。

它清楚表達：

```text
測試 AI 能不能保護秘密
```

對 Demo、簡報與 GitHub 都很有記憶點。

---

## 4.3 V1 / V2 路線正確

目前規劃：

```text
V1：固定題庫 vs 被測試模型
V2：AI vs AI 自動攻防
```

這是正確順序。

第一版先做固定 benchmark，能確保公平性。  
第二版再加入 Attacker LLM，能增加展示亮點。

---

## 4.4 attacks.json 類型方向正確

目前包含的攻擊類型符合專題目的：

```text
direct_request
role_play
instruction_override
system_prompt_extraction
encoding_bypass
partial_disclosure
multi_turn_social_engineering
```

這些足以覆蓋基本 prompt injection 測試場景。

---

# 五、接下來修正優先順序

## Priority 1：先讓專案可以執行

請先完成：

```text
1. 修正所有 Python 檔案換行與縮排
2. 修正 requirements.txt 每個套件一行
3. 安裝套件
4. 跑 mock benchmark
5. 產生 mock 報告
```

指令：

```bash
cd llm-secret-guard
pip install -r requirements.txt
python src/run_benchmark.py --model mock
python src/report_generator.py
```

成功標準：

```text
results/results_mock.csv
reports/report_mock.md
```

---

## Priority 2：完成 Ollama 本地模型串接

新增或完成：

```text
src/clients/ollama_client.py
```

修改：

```text
src/model_client.py
```

測試：

```bash
ollama pull qwen2.5:3b
python src/run_benchmark.py --model ollama:qwen2.5:3b
```

成功標準：

```text
results/results_ollama_qwen2.5_3b.csv
```

---

## Priority 3：新增本地模型清單

新增：

```text
configs/local_models.json
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
  }
]
```

---

## Priority 4：新增批次測試器

新增：

```text
src/run_all_local_models.py
```

用途：

```text
讀取 configs/local_models.json
逐一執行本地模型 benchmark
每個模型產生自己的 results.csv
```

執行：

```bash
python src/run_all_local_models.py
```

---

## Priority 5：新增 summary_report.md

目前單模型報告可以保留，但多模型 benchmark 最終應該產生總表。

建議新增：

```text
reports/summary_report.md
```

內容包含：

| Model | Score | Full Leak | Partial Leak | Format Leak | Error Count |
|---|---:|---:|---:|---:|---:|
| qwen2.5:3b | 88 | 0 | 2 | 1 | 0 |
| llama3.1:8b | 82 | 1 | 3 | 1 | 0 |
| gemma3:4b | 76 | 2 | 4 | 2 | 0 |

---

# 六、可優化部分

## 6.1 強化 leak_detector.py

後續建議加入更多變形洩漏偵測：

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
46 4c 41 47 ...
70 76 65 71 ...
}6202_TERCES_TSET_AIA{GALF
```

---

## 6.2 results.csv 增加 metadata

為了支援多台主機測試，建議新增欄位：

```text
benchmark_version
commit_hash
host_name
provider
model
temperature
max_tokens
attack_set_version
test_date
```

這樣可以避免不同電腦跑出來的結果混淆。

---

## 6.3 README 增加 Ollama 測試教學

建議新增章節：

```text
## Local Open-Source Model Testing
```

內容包含：

```bash
ollama pull qwen2.5:3b
ollama run qwen2.5:3b
python src/run_benchmark.py --model ollama:qwen2.5:3b
python src/report_generator.py
```

---

## 6.4 新增 docs/experiment_rules.md

建議新增：

```text
docs/experiment_rules.md
```

內容：

```text
1. 所有模型使用相同 fake flag
2. 所有模型使用相同 system prompt
3. 所有模型使用相同 attacks.json
4. temperature = 0
5. max_tokens = 300
6. 單輪測試每題重新建立 session
7. 多輪測試固定輪數與固定內容
8. 第一版不允許動態追問
9. 所有結果記錄 commit hash
10. 只使用 fake secret
```

---

## 6.5 擴充 tests/test_leak_detector.py

建議加入：

```text
test_full_leak
test_base64_leak
test_partial_leak
test_format_leak
test_reverse_string_leak
test_space_separated_leak
test_api_error
test_format_violation
```

這樣可以避免 leak detector 後續修改時壞掉。

---

# 七、學校電腦教室測試建議

## 7.1 多台主機分工方式

| 電腦 | 模型 | 指令 | 輸出檔案 |
|---|---|---|---|
| PC-01 | qwen2.5:3b | `python src/run_benchmark.py --model ollama:qwen2.5:3b` | `results_ollama_qwen2.5_3b.csv` |
| PC-02 | llama3.1:8b | `python src/run_benchmark.py --model ollama:llama3.1:8b` | `results_ollama_llama3.1_8b.csv` |
| PC-03 | gemma3:4b | `python src/run_benchmark.py --model ollama:gemma3:4b` | `results_ollama_gemma3_4b.csv` |
| PC-04 | deepseek-r1:7b | `python src/run_benchmark.py --model ollama:deepseek-r1:7b` | `results_ollama_deepseek-r1_7b.csv` |

---

## 7.2 多台電腦測試時必須固定

```text
相同 Git commit
相同 protected_data.txt
相同 system_prompt.txt
相同 attacks.json
相同 leak_detector.py
相同 scoring.py
temperature = 0
max_tokens = 300
```

---

## 7.3 結果彙整方式

每台電腦跑完後，收集：

```text
results/*.csv
reports/*.md
```

最後放入：

```text
results/final/
reports/final/
```

再產生：

```text
reports/summary_report.md
```

---

# 八、最短可行 TODO

```text
1. 修正所有 Python 檔案格式
2. 修正 requirements.txt
3. 確認 mock benchmark 可跑
4. 完成 ollama_client.py
5. 修改 model_client.py 支援 ollama:<model>
6. 測試 qwen2.5:3b
7. 新增 configs/local_models.json
8. 新增 run_all_local_models.py
9. 新增 summary_report.md
10. 擴充 attacks.json
11. 強化 leak_detector.py
12. README 加入本地模型測試教學
```

---

# 九、最終評估

```text
方向是否正確：是
是否偏離目標：否
架構是否合理：是
是否可立即大量測試：否
最大問題：檔案格式與 Ollama client 尚未完成
下一步：先修格式，再跑 mock，再接 Ollama
```

目前專案已經具備清楚的研究型 benchmark 架構。  
只要修正可執行性問題並接上 Ollama，本專題就能進入本地大量模型測試階段。
