# InsurAgentRAG

一个可运行的多 Agent 保险策略推荐系统 Demo：
- 规划（Planner）：统筹流程
- 策略（Strategy）：生成结构化策略草案（LLM/启发式）
- 执行（Execution）：细化分阶段购买与动作
- 风控（Risk）：预算、缺口与高风险段提示
- 复核（Review）：完整性检查与续保/理赔提醒

## 目录结构
```
src/
  agents/
    base_agent.py
    planner.py
    strategy.py
    executor.py
    risk.py
    reviewer.py
  models/
    schemas.py
  tools/
    llm.py
    retriever.py
    evaluator.py
  pipeline.py
  main.py
```

## 运行
- Python 3.10+
- 可选：设置 `OPENAI_API_KEY` 使用真实 LLM；否则使用启发式回退

```bash
python -m src.main | cat
```

## 输入与输出
- 输入：`UserRequest`（投保人/财务/目标/已有保单/检索提示）
- 输出：`StrategyRecommendation`（险种、保额、期限、缴费、受益人；分阶段购买；组合说明；续保与理赔提示；风险提示）

## 说明
- 该 Demo 以结构化启发式为主，便于快速落地；可逐步替换为微调 LLM 与向量检索。

## 真实多 Agent + RAG（LangGraph + 本地Qwen + LoRA + FastAPI）

### 依赖
- transformers, peft, accelerate, torch
- sentence-transformers, faiss-cpu
- langgraph, fastapi, uvicorn
- sqlalchemy

### 本地模型与LoRA
- 基座模型目录（Windows）：`D:\LLM\Qwen3-4B`
- LoRA 目录（Windows）：`D:\PycharmProjects\LoveYiNuo\RAG\model-sft\output\v4-20250805-171721\checkpoint-500`
- 可通过环境变量覆盖：`LOCAL_QWEN_DIR` 与 `LORA_ADAPTER_DIR`

### 启动 API
```bash
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

### 调用
```bash
curl -X POST http://localhost:8000/strategy/generate \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 1}'
```

- 后端仅接收 `user_id`，通过数据库查询组装 `UserRequest`。
- LangGraph 管线在 `src/graph/pipeline_graph.py`，节点：plan -> rag -> strategy -> risk -> review。
- 真实 Prompt 存放于 `src/agents/prompts.py`。

### RAG 索引
- 首次运行会基于 `src/knowledge/` 目录构建 FAISS 索引，或通过环境变量 `KNOWLEDGE_DIR` 指向你的知识库目录。

### 注意
- 本地大模型推理依赖显存；如资源不足，可调整 `MAX_NEW_TOKENS`、`GEN_TEMPERATURE` 环境变量，或切换更小模型。

### 数据库准备
- 默认 `sqlite:///./insur_agent.db`，可通过 `DATABASE_URL` 覆盖（例：Postgres）。
- 初始化并插入样例：
```sql
-- 你可以用任何方式插入，这里仅演示表结构
-- users(id, age, gender, occupation, health_status, family_structure, smoker, city, annual_income, liabilities, assets, monthly_budget_for_insurance, goals)
-- policies(id, user_id, company, product, coverage_type, sum_assured, term_years, premium_annual)
```

### 环境变量
- `LOCAL_QWEN_DIR`：本地 Qwen 模型目录（默认 `D:\LLM\Qwen3-4B`）
- `LORA_ADAPTER_DIR`：LoRA 目录（默认为你提供的路径）
- `KNOWLEDGE_DIR`：知识库目录（默认 `src/knowledge`）
- `FAISS_INDEX_PATH`：向量索引文件路径（默认 `src/rag_index.faiss`）
- `RAG_TOP_K`：检索数量（默认 4）
- `MAX_NEW_TOKENS`、`GEN_TEMPERATURE`：生成控制
- `DATABASE_URL`：数据库连接串
