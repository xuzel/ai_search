```mermaidpython -m src.web.app
flowchart TD
    User["👤 用户查询"]

    User -->|输入| WebUI["🌐 Web UI / CLI"]

    WebUI -->|查询| Router["🎯 智能路由器<br/>HybridRouter"]

    Router -->|快速识别| KR["⚡ 关键词路由<br/>~10ms"]
    KR -->|置信度判断| Conf{置信度<br/>≥0.7?}

    Conf -->|是| Decision["✅ 路由决策"]
    Conf -->|否| LR["🧠 LLM路由<br/>精确分类"]
    LR --> Decision

    Decision -->|RESEARCH| RA["🔍 研究Agent<br/>搜索+综合"]
    Decision -->|CODE| CA["💻 代码Agent<br/>生成+执行"]
    Decision -->|RAG| RAG["📖 RAG Agent<br/>文档问答"]
    Decision -->|CHAT| CHA["💬 对话Agent<br/>直接回复"]
    Decision -->|领域工具| Tools["🛠️ 领域工具<br/>天气/金融/路线"]

    RA -->|结果| Agg["📊 结果聚合"]
    CA -->|结果| Agg
    RAG -->|结果| Agg
    CHA -->|结果| Agg
    Tools -->|结果| Agg

    Agg -->|保存| DB["💾 SQLite数据库<br/>对话历史"]

    DB -->|返回| Output["📤 流式输出<br/>SSE/HTML"]

    Output -->|响应| User

    style User fill:#EBF5FB,stroke:#D5DBDB,color:#1B2631,stroke-width:3px
    style WebUI fill:#AEB6BF,stroke:#85929E,color:#1B2631,stroke-width:2px
    style Router fill:#1B2631,stroke:#0F1419,color:#FFFFFF,stroke-width:3px
    style KR fill:#5D6D7E,stroke:#34495E,color:#FFFFFF,stroke-width:2px
    style LR fill:#5D6D7E,stroke:#34495E,color:#FFFFFF,stroke-width:2px
    style Conf fill:#5D6D7E,stroke:#34495E,color:#FFFFFF,stroke-width:2px
    style Decision fill:#D5DBDB,stroke:#AEB6BF,color:#1B2631,stroke-width:2px
    style RA fill:#2C3E50,stroke:#1B2631,color:#FFFFFF,stroke-width:2px
    style CA fill:#2C3E50,stroke:#1B2631,color:#FFFFFF,stroke-width:2px
    style RAG fill:#2C3E50,stroke:#1B2631,color:#FFFFFF,stroke-width:2px
    style CHA fill:#2C3E50,stroke:#1B2631,color:#FFFFFF,stroke-width:2px
    style Tools fill:#34495E,stroke:#2C3E50,color:#FFFFFF,stroke-width:2px
    style Agg fill:#D5DBDB,stroke:#AEB6BF,color:#1B2631,stroke-width:2px
    style DB fill:#1B2631,stroke:#0F1419,color:#FFFFFF,stroke-width:3px
    style Output fill:#EBF5FB,stroke:#D5DBDB,color:#1B2631,stroke-width:2px
```

