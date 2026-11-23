# LangGraph workflow

This diagram reflects the current implementation in `starter/agent/graph.py`. The diamond explains the conditional routing in `route()`; it is not a separate LangGraph node.

```mermaid
flowchart TD
    User([User question]) --> Wrapper["run_question(question)<br/>Create HumanMessage<br/>Initialize trips = 0"]
    Wrapper --> Start([START])
    Start --> Model["MODEL NODE · call_model()<br/>LLM call: trips += 1<br/>get_llm() + bind available tools<br/>Send system prompt and message history<br/>System: use tools for facts; never invent values<br/>Forecast wording must say shipment baseline, method, and source period"]

    Model --> Route{"Does the model request a tool<br/>and are trips &lt; 4?"}
    Route -->|Yes| Tools["TOOLS NODE · run_tools()<br/>Dispatch each requested tool call<br/>Serialize results as JSON ToolMessages"]
    Tools -->|Append tool results to message history| Model
    Route -->|No tool call, or trips = 4| End([END])
    End --> Collect["run_question() collects the final answer,<br/>structured evidence, and model-call count"]

    subgraph ModelConfiguration["Model configuration · agent/llm.py"]
        Provider["ChatOpenAI client using OpenRouter<br/>Default model: openai/gpt-4o-mini<br/>MODEL env var can override default<br/>OPENROUTER_API_KEY read from environment"]
    end
    Model -.->|uses model config| Provider

    classDef llm fill:#e8f1ff,stroke:#3973c6,color:#172b4d
    classDef tool fill:#edf8f1,stroke:#39845a,color:#173c25
    classDef decision fill:#fff4d6,stroke:#c68a00,color:#503900
    class Model llm
    class Tools tool
    class Route decision
```

## Tools called by the tools node

These are registered Python tool functions in `starter/agent/tools.py`. They are dispatched inside the single LangGraph `tools` node; they are not separate nodes in the compiled graph.

```mermaid
flowchart LR
    ToolCall["Model tool call"] --> Dispatch{"Tool name"}
    Dispatch --> Batch["lookup_batch(batch_no)<br/>Batch and SKU details<br/>batch_master.csv + sku_master.csv"]
    Dispatch --> Shelf["find_short_shelf_life_shipments(limit)<br/>Invoice lines below 60% policy threshold<br/>primary_sales.csv + batch_master.csv"]
    Dispatch --> Stock["find_cfa_stock_imbalances(limit)<br/>Zero-stock vs positive batch stock by SKU<br/>cnf_stock_snapshot.csv"]
    Dispatch --> Forecast["forecast_primary_shipments(cfa, sku, horizon, limit)<br/>Same month last year baseline with source rows<br/>primary_sales.csv"]
    Batch --> Evidence["Python dict result → JSON ToolMessage"]
    Shelf --> Evidence
    Stock --> Evidence
    Forecast --> Evidence
    Evidence --> ModelAgain["Next model call reads tool result"]
```

## Call behavior

- The model can answer after its first call, or request one or more registered tools.
- A tool result returns to the model as a `ToolMessage`; the model may answer or request another tool.
- `MAX_TRIPS = 4` counts **model calls**, not tool calls. If the fourth model call still asks for tools, the graph ends without running another tools-node pass.
- A simple question that needs one tool normally uses two model calls: one to choose/call the tool and one to form the answer. Actual calls vary by question.
- The graph does not enforce user approval or perform write-back. Tools read the supplied CSV data and return evidence.
- The forecast tool is a deterministic primary-shipment baseline. It does not forecast downstream demand or promise an accuracy level for a specific CFA/SKU.

## Files behind this graph

- [Graph and routing](../starter/agent/graph.py)
- [Model/provider configuration](../starter/agent/llm.py)
- [Tool implementations](../starter/agent/tools.py)
