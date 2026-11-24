# LangGraph workflow

This diagram shows the compiled graph in `starter/agent/graph.py`. Blue nodes call the model; every other node is plain Python. The node table, check rules and decide order are in [architecture_note.md](architecture_note.md).

```mermaid
flowchart TD
    S([START]) --> P["parse_input<br/>regex for CLM- / EML- IDs<br/>model extraction only for free text"]
    P -->|claim ID found| L["lookup<br/>claim, batch, SKU, stockist,<br/>sales rows, credited claims"]
    P -->|no single claim| E
    L -->|claim not in register| X([END · NOT_FOUND])
    L --> D[dispatch_checks]
    D --> C1["check_window §5.2"]
    D --> C2["check_quantity §5.5"]
    D --> C3["check_duplicate §5.6"]
    D --> C4["check_invoice_ref §5.4"]
    D --> C5["check_batch_expiry"]
    D --> C6["check_value §5.7"]
    C1 & C2 & C3 & C4 & C5 & C6 --> DEC["decide<br/>REJECT · NEEDS_PERSON · RECOMMEND_CREDIT"]
    DEC --> E["explain<br/>model writes 3–5 sentences;<br/>code guard + fallback"]
    E --> Z([END])

    classDef llm fill:#e8f1ff,stroke:#3973c6,color:#172b4d
    class P,E llm
```
