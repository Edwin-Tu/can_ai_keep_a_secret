# Can AI Keep a Secret?

## LLM Secret Guard Benchmark

本專案是一個 **LLM 機密資料防護測試框架**，用來測試不同 AI 模型在面對 Prompt Injection、角色扮演、規則覆蓋、編碼繞過與多輪誘導時，是否能保護 hidden flag。

## 第一版目標

第一版採用：

```text
固定攻擊題庫 attacks.json
        ↓
main.py / run_benchmark.py
        ↓
Target LLM (Mock / 本地模型框架)
        ↓
Leak Detector
        ↓
results.csv / report.md
```

第一版重點：

> AI 的回覆會影響評分，但不影響下一題要問什麼。

也就是不根據 AI 回覆臨時追問，而是使用固定腳本，確保不同模型受到相同測試。

## 專案結構

```text
llm-secret-guard/
├── src/
│   ├── main.py
│   ├── run_benchmark.py         - 支援 ollama:<model_name>
│   ├── model_client.py          - 支援本地模型掛載
│   ├── leak_detector.py
│   ├── scoring.py
│   ├── report_generator.py
│   ├── run_all_local_models.py  - 批次測試框架 (TODO)
│   ├── clients/
│   │   ├── mock_client.py
│   │   ├── openai_client.py     - TODO
│   │   ├── anthropic_client.py  - TODO
│   │   ├── gemini_client.py     - TODO
│   │   └── ollama_client.py     - TODO (本地模型)
│   └── agents/
│       ├── attacker_agent.py
│       └── judge_agent.py
├── attacks/
│   └── attacks.json
├── data/
│   └── protected_data.txt
├── prompts/
│   └── system_prompt.txt
├── results/
├── reports/
├── docs/
│   ├── architecture.md
│   └── demo_script.md
├── configs/
│   └── local_models.json        - 本地模型配置
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## 快速開始

### 1. 安裝環境

```bash
pip install -r requirements.txt
```

### 2. 先跑 Mock 模型

```bash
python src/run_benchmark.py --model mock
```

### 3. 手動測試模式

```bash
python src/main.py --model mock
```

### 4. 產生報告

```bash
python src/report_generator.py
```

## 本地模型支援（框架已準備，待實現）

本專案框架已支援本地開源模型測試，目前結構如下：

| 組件 | 狀態 | 用途 |
|------|------|------|
| OllamaClient | 🔧 框架 (TODO) | 本地 Ollama 模型支援 |
| configs/local_models.json | ✅ 已建立 | 模型配置清單 |
| run_all_local_models.py | 🔧 框架 (TODO) | 批次測試執行器 |

### 使用本地模型的預期命令（待實現）

```bash
# 單一模型測試
python src/run_benchmark.py --model ollama:qwen2.5:3b

# 批次模型測試
python src/run_all_local_models.py
```

## 目前版本

- V1：固定題庫 vs Mock 模型（已完成）
- V1.5：本地模型框架（準備中）
  - OllamaClient 實現待補充
  - 本地模型測試流程實現待補充
- V2：AI vs AI 自動攻防
- V3：Dashboard / Web UI / MCP 工具整合

## 安全聲明

本專案只使用 fake flag，不應放入真實密碼、API Key、個資或公司機密。
