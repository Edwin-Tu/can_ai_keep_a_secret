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
Target LLM
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
│   ├── run_benchmark.py
│   ├── model_client.py
│   ├── leak_detector.py
│   ├── scoring.py
│   ├── report_generator.py
│   ├── clients/
│   │   ├── mock_client.py
│   │   ├── openai_client.py
│   │   ├── anthropic_client.py
│   │   └── gemini_client.py
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

## 目前版本

- V1：固定題庫 vs 被測試模型
- V2：預留 AI vs AI 自動攻防
- V3：預留 Dashboard / Web UI / MCP 工具整合

## 安全聲明

本專案只使用 fake flag，不應放入真實密碼、API Key、個資或公司機密。
