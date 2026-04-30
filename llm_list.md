# LLM 可測試模型清單

本清單依照模型參數量與本地測試負擔，分為小型、中型、大型 LLM。  
適用於 Ollama 本地模型測試與 LLM Secret Guard benchmark。

---

## 分類標準

| 分類 | 參數量範圍 | 適合用途 |
|---|---:|---|
| 小型 LLM | 約 0.5B～4B | 快速測試、流程驗證、低記憶體環境 |
| 中型 LLM | 約 7B～14B | 正式比較、一般桌機/筆電主力測試 |
| 大型 LLM | 約 24B 以上 | 高能力模型比較，需要較高 RAM / VRAM |

---

# 小型 LLM

這一組適合先跑 benchmark，速度快，也比較不吃記憶體。

| 模型系列 | 可測版本 | 指令範例 |
|---|---|---|
| Llama 3.2 | `llama3.2:1b`, `llama3.2:3b` | `ollama pull llama3.2:1b` |
| Qwen2.5 | `qwen2.5:0.5b`, `qwen2.5:1.5b`, `qwen2.5:3b` | `ollama pull qwen2.5:3b` |
| Qwen2.5-Coder | `qwen2.5-coder:0.5b`, `qwen2.5-coder:1.5b`, `qwen2.5-coder:3b` | `ollama pull qwen2.5-coder:3b` |
| Gemma 3 | `gemma3:270m`, `gemma3:1b`, `gemma3:4b` | `ollama pull gemma3:4b` |
| Phi-4 Mini | `phi4-mini:3.8b` | `ollama pull phi4-mini:3.8b` |

## 小型 LLM 備註

- Qwen2.5 系列尺寸涵蓋 `0.5B` 到 `72B`。
- Qwen2.5-Coder 系列包含 `0.5B`、`1.5B`、`3B`、`7B`、`14B`、`32B`。
- Gemma 3 系列包含 `270M`、`1B`、`4B`、`12B`、`27B`。
- Phi-4 Mini 約為 `3.8B`。

---

# 中型 LLM

這一組是正式做模型比較時最推薦的主力。

| 模型系列 | 可測版本 | 指令範例 |
|---|---|---|
| Qwen2.5 | `qwen2.5:7b`, `qwen2.5:14b` | `ollama pull qwen2.5:7b` |
| Qwen2.5-Coder | `qwen2.5-coder:7b`, `qwen2.5-coder:14b` | `ollama pull qwen2.5-coder:7b` |
| Llama 3.1 | `llama3.1:8b` | `ollama pull llama3.1:8b` |
| Mistral | `mistral:7b` | `ollama pull mistral:7b` |
| Gemma 3 | `gemma3:12b` | `ollama pull gemma3:12b` |
| Phi-4 | `phi4:14b` | `ollama pull phi4:14b` |
| Phi-4 Reasoning | `phi4-reasoning:14b` | `ollama pull phi4-reasoning:14b` |
| DeepSeek-R1 Distill | `deepseek-r1:7b`, `deepseek-r1:8b`, `deepseek-r1:14b` | `ollama pull deepseek-r1:8b` |

## 中型 LLM 備註

- Llama 3.1 有 `8B`、`70B`、`405B`。
- Mistral 常用版本為 `7B`。
- Phi-4 為 `14B`。
- Phi-4 Reasoning 為 `14B`。
- DeepSeek-R1 在 Ollama tags 中列出 `1.5B`、`7B`、`8B`、`14B`、`32B`、`70B`、`671B`。

---

# 大型 LLM

這一組適合有較高 RAM / VRAM 時測試。一般筆電不一定跑得順。

| 模型系列 | 可測版本 | 指令範例 |
|---|---|---|
| Qwen2.5 | `qwen2.5:32b`, `qwen2.5:72b` | `ollama pull qwen2.5:32b` |
| Qwen2.5-Coder | `qwen2.5-coder:32b` | `ollama pull qwen2.5-coder:32b` |
| Gemma 3 | `gemma3:27b` | `ollama pull gemma3:27b` |
| DeepSeek-R1 | `deepseek-r1:32b`, `deepseek-r1:70b`, `deepseek-r1:671b` | `ollama pull deepseek-r1:32b` |
| Mistral Small | `mistral-small:22b`, `mistral-small:24b` | `ollama pull mistral-small` |
| Mistral Small 3.2 | `mistral-small3.2:24b` | `ollama pull mistral-small3.2` |
| Mixtral | `mixtral:8x7b`, `mixtral:8x22b` | `ollama pull mixtral:8x7b` |
| Mistral Large | `mistral-large:123b` | `ollama pull mistral-large` |

## 大型 LLM 備註

- Mistral Small 3 是 `24B`。
- Mistral Small 3.2 是 `24B`。
- Mixtral 是 MoE 架構，常見版本包含 `8x7B` 與 `8x22B`。
- Mistral Large 2 約為 `123B`。
- DeepSeek-R1 大型版本包含 `32B`、`70B`、`671B`。

---

# 建議第一輪測試模型

若要先完成一輪可展示的 benchmark，建議優先測：

| 分類 | 模型 |
|---|---|
| 小型 | `llama3.2:1b` |
| 小型 | `qwen2.5:3b` |
| 小型 | `qwen2.5-coder:3b` |
| 小型 | `gemma3:4b` |
| 中型 | `llama3.1:8b` |
| 中型 | `qwen2.5:7b` |
| 中型 | `deepseek-r1:8b` |
| 中型 | `phi4:14b` |

---

# Ollama 下載指令整理

## 小型模型

```bash
ollama pull llama3.2:1b V
ollama pull llama3.2:3b V
ollama pull qwen2.5:0.5b
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:3b
ollama pull qwen2.5-coder:0.5b V
ollama pull qwen2.5-coder:1.5b V
ollama pull qwen2.5-coder:3b V
ollama pull gemma3:270m
ollama pull gemma3:1b V
ollama pull gemma3:4b
ollama pull phi4-mini:3.8b
```

## 中型模型

```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull gemma3:12b
ollama pull phi4:14b
ollama pull phi4-reasoning:14b
ollama pull deepseek-r1:7b
ollama pull deepseek-r1:8b
ollama pull deepseek-r1:14b
```

## 大型模型

```bash
ollama pull qwen2.5:32b
ollama pull qwen2.5:72b
ollama pull qwen2.5-coder:32b
ollama pull gemma3:27b
ollama pull deepseek-r1:32b
ollama pull deepseek-r1:70b
ollama pull deepseek-r1:671b
ollama pull mistral-small
ollama pull mistral-small3.2
ollama pull mixtral:8x7b
ollama pull mixtral:8x22b
ollama pull mistral-large
```

---

# 測試指令範例

單一模型測試：

```bash
python src/run_benchmark.py --model ollama:llama3.2:1b
python src/report_generator.py
```

若使用互動式自動化腳本：

```bash
python3 check.py
```

或在 Windows：

```powershell
python check.py
```
