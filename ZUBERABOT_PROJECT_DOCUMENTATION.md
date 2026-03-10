# 🤖 Zubera Bot — Technical Project Documentation

> **AI-Powered Financial Advisory & Personal Finance Assistant**


## 1. Project Overview & Objective

### Problem Statement

Individual investors lack access to affordable, personalized financial guidance. Professional advisors charge high fees, and generic financial tools don't account for personal risk profiles, investment goals, or spending patterns.

### Solution

Zubera Bot is an **AI-powered financial advisor** accessible 24/7 via WhatsApp that:

- Understands each user's financial context and risk appetite
- Remembers preferences and conversation history across sessions
- Provides **live mutual fund data** (NAV, returns, fund details) from Indian markets
- Tracks expenses with category-wise budgeting
- Delivers **goal-based investment recommendations** (retirement, wealth, emergency, child education, short-term)
- Manages support tickets with priority and lifecycle tracking
- Maintains a **RAG knowledge base** for financial document search

### Core Objective

> Build an autonomous, multi-provider AI agent that delivers personalized financial advisory services through natural conversation, backed by real-time market data, persistent user profiles, and a vector-powered knowledge base.

---

## 2. System Architecture

### High-Level Architecture Flow

> 📐 **Visual Diagram:** Open [`ZUBERABOT_ARCHITECTURE_DIAGRAM.html`](./ZUBERABOT_ARCHITECTURE_DIAGRAM.html) in a browser for a full-color professional architecture diagram.

```mermaid
flowchart TD
    subgraph USERS["👥 Users"]
        U["📱 WhatsApp Users<br/>Investors & Finance Seekers"]
    end

    subgraph CHANNEL["📡 Channel & Auth"]
        WA["💬 WhatsApp Web<br/>End-to-end encrypted"]
        QR["🔐 QR Authentication"]
        BR["🌉 Node.js Bridge<br/>Baileys + WebSocket<br/>ws://localhost:3001"]
        CH["📨 WhatsApp Channel<br/>Python handler → MessageBus"]
    end

    subgraph AGENT["🧠 Agent Core"]
        AL["⚙️ Agent Loop<br/>Max 20 iterations"]
        CB["📋 Context Builder<br/>System prompt + Memory + Skills"]
        SM["💾 Session Manager<br/>DB-backed sessions"]
        UM["🧠 User Memory<br/>Per-user isolation"]
        subgraph TOOLS["🔧 Tool Registry - 10+ Tools"]
            T1["📈 Finance Tool"]
            T2["💰 Expense Tracker"]
            T3["🎫 Ticket Manager"]
            T4["📚 RAG Knowledge"]
            T5["🔍 Web Search"]
            T6["🌐 Web Fetch"]
        end
    end

    subgraph LLM["🤖 AI / LLM Providers"]
        GW["🔀 LiteLLM Gateway"]
        P1["⚡ Groq - llama-3.3-70b"]
        P2["🟠 OpenRouter - Multi-model"]
        P3["🦙 vLLM - Self-hosted"]
        FS["🛡️ Financial Safety Layer"]
    end

    subgraph DATA["🗄️ Data Layer"]
        PG["🐘 PostgreSQL 15<br/>8 Tables: Users, Sessions,<br/>Tickets, Expenses, Preferences"]
        CR["📊 ChromaDB<br/>Vector Store - all-MiniLM-L6-v2"]
        WS["📁 User Workspaces<br/>Per-user file storage"]
    end

    subgraph APIS["🌐 External APIs"]
        A1["📈 yFinance API<br/>Stocks + NSE/BSE"]
        A2["🏦 MFAPI India<br/>Mutual Fund NAV & Returns"]
        A3["🔍 Brave Search<br/>Web Search API"]
    end

    U -->|"WhatsApp Protocol"| WA
    WA --> BR
    QR -.->|"First-time"| BR
    BR -->|"WebSocket JSON"| CH
    CH -->|"MessageBus"| AL
    AL --> CB
    AL --> SM
    CB --> UM
    AL --> TOOLS
    AL -->|"Chat request"| GW
    GW --> P1
    GW --> P2
    GW --> P3
    GW --> FS
    SM --> PG
    T4 --> CR
    AL --> WS
    T1 --> A1
    T1 --> A2
    T5 --> A3
    AL -->|"Response"| CH
    CH -->|"OutboundMessage"| BR
    BR -->|"Reply"| U

    style USERS fill:#f0fff4,stroke:#48bb78,stroke-width:2px
    style CHANNEL fill:#ebf8ff,stroke:#4299e1,stroke-width:2px
    style AGENT fill:#faf5ff,stroke:#9f7aea,stroke-width:2px
    style LLM fill:#fff5f7,stroke:#ed64a6,stroke-width:2px
    style DATA fill:#e6fffa,stroke:#38b2ac,stroke-width:2px
    style APIS fill:#fffaf0,stroke:#ed8936,stroke-width:2px
    style TOOLS fill:#fffaf0,stroke:#ed8936,stroke-width:1px
```

### Component Breakdown

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **WhatsApp Bridge** | Node.js + `@whiskeysockets/baileys` | Receives/sends WhatsApp messages via WebSocket |
| **WhatsApp Channel** | Python `WhatsAppChannel` class | Parses bridge messages, extracts sender ID, publishes to bus |
| **Message Bus** | `asyncio.Queue` | Decoupled `InboundMessage` / `OutboundMessage` routing |
| **Agent Loop** | Python asyncio (`AgentLoop`) | Core message processing, LLM orchestration, tool execution |
| **Context Builder** | `UserContextBuilder` | Assembles system prompt + memory + skills + history |
| **Session Manager** | SQLAlchemy + PostgreSQL | Multi-user session isolation with DB-backed history |
| **LiteLLM Provider** | `LiteLLMProvider` via LiteLLM library | Unified interface to 7+ LLM providers |
| **Tool Registry** | 10+ async Python tools | Finance, expense, ticket, RAG, web, file, shell, spawn |
| **User Memory** | `UserMemoryStore` + filesystem | Long-term memory (`MEMORY.md`) + daily notes per user |
| **PostgreSQL** | PostgreSQL 15 + SQLAlchemy 2.0 | 8 tables: users, verifications, preferences, conversations, recommendations, sessions, workspaces, tickets |
| **ChromaDB** | ChromaDB + SentenceTransformers | Vector knowledge base for RAG with `all-MiniLM-L6-v2` embeddings |

### Key Source Files

| File | Path | Purpose |
|------|------|---------|
| `loop.py` | `zuberabot/agent/loop.py` | Agent loop – core processing engine |
| `context.py` | `zuberabot/agent/context.py` | System prompt builder with identity, memory, skills |
| `user_context.py` | `zuberabot/agent/user_context.py` | User-isolated context builder for multi-user |
| `user_memory.py` | `zuberabot/agent/user_memory.py` | Per-user memory system (long-term + daily) |
| `models.py` | `zuberabot/database/models.py` | SQLAlchemy ORM models (8 tables) |
| `postgres.py` | `zuberabot/database/postgres.py` | Database manager with CRUD operations |
| `litellm_provider.py` | `zuberabot/providers/litellm_provider.py` | Multi-provider LLM gateway |
| `ollama.py` | `zuberabot/providers/ollama.py` | Ollama local inference + Financial safety layer |
| `whatsapp.py` | `zuberabot/channels/whatsapp.py` | WhatsApp channel via bridge WebSocket |
| `schema.py` | `zuberabot/config/schema.py` | Pydantic configuration schema |
| `finance.py` | `zuberabot/agent/tools/finance.py` | Financial tools (stocks, MF, recommendations) |
| `expense.py` | `zuberabot/agent/tools/expense.py` | Expense tracking tool |
| `ticket.py` | `zuberabot/agent/tools/ticket.py` | Support ticket management |
| `rag.py` | `zuberabot/agent/tools/rag.py` | RAG knowledge base (ChromaDB) |
| `web.py` | `zuberabot/agent/tools/web.py` | Web search + URL fetch tools |

---

## 3. Application Workflow

### End-to-End Message Processing Pipeline

```
User sends message on WhatsApp
        │
        ▼
Step 1: BRIDGE RECEPTION
        Node.js bridge (Baileys) receives the WhatsApp message
        and forwards it as JSON over WebSocket to Python backend
        │
        ▼
Step 2: CHANNEL HANDLER
        WhatsAppChannel parses the JSON message
        Extracts: sender phone number, content, message ID, timestamp
        Creates InboundMessage and publishes to MessageBus
        │
        ▼
Step 3: SESSION CREATION
        SessionManager retrieves existing ChatSession from PostgreSQL
        OR creates a new one (keyed by "whatsapp:<phone_number>")
        Loads conversation history (up to 50 messages)
        │
        ▼
Step 4: CONTEXT ASSEMBLY
        UserContextBuilder constructs the full LLM prompt:
        ├── System Identity ("You are Zubera Bot, a financial advisor...")
        ├── User Memory (long-term MEMORY.md + today's daily notes)
        ├── Loaded Skills (always-on + available skill summaries)
        └── Conversation History (last 50 messages from DB session)
        │
        ▼
Step 5: LLM CALL
        Assembled messages + tool definitions sent to configured LLM:
        Provider: LiteLLMProvider → Gemini / Groq / OpenRouter / Ollama
        Max tokens: 8192 | Temperature: 0.7 | Timeout: 120s
        │
        ▼
Step 6: TOOL EXECUTION LOOP (up to 20 iterations)
        ┌──────────────────────────────────────────────┐
        │ IF LLM returns tool_calls:                   │
        │   Execute each tool async (finance, expense, │
        │   ticket, RAG, web search, etc.)             │
        │   Append tool results to messages             │
        │   Re-call LLM with updated context           │
        │   REPEAT until LLM returns text OR 20 iters  │
        └──────────────────────────────────────────────┘
        │
        ▼
Step 7: RESPONSE DELIVERY
        Final text response published as OutboundMessage on MessageBus
        Routed through WhatsApp channel → bridge → user's WhatsApp
        │
        ▼
Step 8: PERSISTENCE
        User message + bot response saved to:
        ├── sessions table (JSON messages array for LLM context)
        └── conversations table (message + response + timestamp)
```

### Tool Execution Detail

When the LLM decides to use a tool, the flow is:

1. LLM returns `tool_calls` array with tool name + arguments
2. `AgentLoop` looks up the tool in the registry
3. Tool's `execute()` method is called with parsed arguments
4. Tool result (string) is added to messages as `role: "tool"`
5. Updated messages sent back to LLM for next iteration
6. Loop continues until LLM returns a final text response or max 20 iterations reached

---

## 4. LLM Providers & AI Models

### Supported LLM Providers

Zubera Bot supports **7 LLM providers** through a unified `LiteLLMProvider` abstraction, enabling seamless switching between cloud and local models.

| # | Provider | Model(s) | Use Case | Type | API Key Env Var |
|---|----------|----------|----------|------|-----------------|
| 1 | **Google Gemini** | `gemini/gemini-2.0-flash` | Primary cloud inference | ☁️ Cloud | `GEMINI_API_KEY` |
| 2 | **Groq** | `groq/llama-3.3-70b` | Ultra-fast inference | ☁️ Cloud | `GROQ_API_KEY` |
| 3 | **OpenRouter** | Multiple (Claude, GPT, Llama, etc.) | Multi-model gateway / fallback | ☁️ Cloud | `OPENROUTER_API_KEY` |
| 4 | **Ollama** | `mistral:7b-instruct-q4_K_M` | Privacy-focused local inference | 🏠 Local | — |
| 5 | **Anthropic** | `anthropic/claude-sonnet-4-5` | High-quality reasoning | ☁️ Cloud | `ANTHROPIC_API_KEY` |
| 6 | **OpenAI** | GPT-4, GPT-3.5 | General purpose | ☁️ Cloud | `OPENAI_API_KEY` |
| 7 | **vLLM** | Custom hosted models | Self-hosted production inference | 🏠 Self-Hosted | `OPENAI_API_KEY` (compat) |

### Provider Selection Logic (`LiteLLMProvider.__init__`)

```
Model prefix → Provider routing:
  "ollama/"     → Ollama (local, OLLAMA_API_BASE)
  "groq/"       → Groq (GROQ_API_KEY)
  "openrouter/" → OpenRouter (OPENROUTER_API_KEY)
  "gemini/"     → Google Gemini (GEMINI_API_KEY)
  "anthropic/"  → Anthropic (ANTHROPIC_API_KEY)
  "openai/gpt"  → OpenAI (OPENAI_API_KEY)
  Custom base   → vLLM (hosted_vllm/ prefix)
```

### Financial Safety Layer

The `FinancialOllamaProvider` (extends `OllamaProvider`) adds financial-specific safeguards:

- **Calculation verification** — validates numerical computations in responses
- **Disclaimer injection** — automatically adds investment disclaimers
- **Fact-checking prompts** — enriches system prompt with financial accuracy guidelines
- **Conservative defaults** — emergency fund always directed to debt instruments regardless of risk profile

### Embedding Model (RAG)

| Model | Library | Dimension | Purpose |
|-------|---------|-----------|---------|
| `all-MiniLM-L6-v2` | SentenceTransformers | 384 | Document embeddings for ChromaDB vector search |

---

## 5. APIs & External Services

### 5.1 yFinance API

| Field | Details |
|-------|---------|
| **Library** | `yfinance` (Python) |
| **Authentication** | None required (public data) |
| **Data Provided** | Stock prices (global + NSE/BSE), fund info (NAV, category, YTD return), market news per ticker, historical price data |
| **Used By** | `finance_tool` → actions: `get_stock_price`, `get_fund_info`, `market_news`, `compare_funds` |

### 5.2 MFAPI (mfapi.in) — Indian Mutual Fund API

| Field | Details |
|-------|---------|
| **Client** | `MFAPIClient` (async httpx) |
| **Authentication** | None required (public API) |
| **Endpoints** | Fund search by name, fund details by scheme code, latest NAV, historical NAV data |
| **Calculations** | 1-year return, 3-year return (computed from historical NAV) |
| **Used By** | `finance_tool` → actions: `search_funds`, `get_fund_nav`, `recommend_funds`, `get_fund_recommendation` |

### 5.3 Brave Search API

| Field | Details |
|-------|---------|
| **Client** | `httpx` async HTTP |
| **Authentication** | `BRAVE_API_KEY` (header: `X-Subscription-Token`) |
| **Endpoint** | `https://api.search.brave.com/res/v1/web/search` |
| **Returns** | Titles, URLs, and description snippets (max 10 results) |
| **Used By** | `web_search` tool |

### 5.4 WhatsApp Web (Baileys Bridge)

| Field | Details |
|-------|---------|
| **Library** | `@whiskeysockets/baileys` (Node.js) |
| **Protocol** | Reverse-engineered WhatsApp Web protocol |
| **Authentication** | QR code scan on first connection |
| **Communication** | WebSocket (`ws://localhost:3001`) between Node.js bridge and Python |
| **Features** | Send/receive text messages, voice message detection, group support, connection status, auto-reconnect |

---

## 6. Agent Tools & Capabilities

### Tool Registry

| # | Tool Name | File | Description |
|---|-----------|------|------------|
| 1 | `finance_tool` | `tools/finance.py` | Stock prices, fund info, MF recommendations, NAV, comparison |
| 2 | `expense_tracker` | `tools/expense.py` | Add expenses, get expenses, monthly summary by category |
| 3 | `ticket_manager` | `tools/ticket.py` | Create, get, update, list support tickets with priority |
| 4 | `rag_knowledge` | `tools/rag.py` | ChromaDB knowledge store with multi-context isolation |
| 5 | `web_search` | `tools/web.py` | Brave Search API — titles, URLs, snippets |
| 6 | `web_fetch` | `tools/web.py` | Fetch URL content, HTML → markdown/text extraction |
| 7 | `message` | `tools/message.py` | Send messages to specific chat channels |
| 8 | `file tools` | `tools/filesystem.py` | Read, write, list, search files in user workspace |
| 9 | `shell` | `tools/shell.py` | Execute system commands |
| 10 | `spawn` | `tools/spawn.py` | Delegate tasks to sub-agents |

### Finance Tool — Detailed Actions

| Action | Required Params | Description |
|--------|----------------|-------------|
| `get_stock_price` | `symbol` | Live stock price via yFinance (e.g., AAPL, TATAMOTORS.NS) |
| `get_fund_info` | `symbol` | Fund NAV, category, YTD return via yFinance |
| `market_news` | `symbol` | Latest 3 news articles for a ticker |
| `search_funds` | `query` | Search Indian MFs by name/keyword via MFAPI |
| `get_fund_nav` | `scheme_code` | Detailed MF: NAV, fund house, category, 1Y/3Y returns |
| `recommend_funds` | `risk_profile`, `investment_amount` | Risk-profiled MF recommendations with live NAV data |
| `get_fund_recommendation` | `risk_profile`, `investment_amount`, `investment_goal` | Interactive 3-step questionnaire for personalized goal-based advice |
| `compare_funds` | `symbols[]` (2-3) | Side-by-side fund comparison (returns, category, expense ratio) |

### Expense Tracker — Actions

| Action | Params | Description |
|--------|--------|-------------|
| `add_expense` | `user_id`, `amount`, `category`, `description` | Log expense (categories: food, transport, bills, entertainment, shopping, healthcare, other) |
| `get_expenses` | `user_id`, `month?`, `category?` | Query expenses with optional filters |
| `monthly_summary` | `user_id`, `month?` | Category-wise breakdown with totals (INR) |

### RAG Knowledge — Actions

| Action | Params | Description |
|--------|--------|-------------|
| `add` | `content` or `file_path`, `context`, `category` | Store text/PDF in ChromaDB with metadata |
| `search` | `query`, `context` | Semantic search across stored knowledge (top 3 results) |
| `switch_context` | `context` | Switch active context (e.g., "banking", "personal") |
| `list_contexts` | — | List all available knowledge contexts |

---

## 7. Database Schema Architecture

**Engine:** PostgreSQL 15 with SQLAlchemy 2.0 ORM
**Connection:** `QueuePool` with event listeners for monitoring
**Connection String:** `postgresql://user:password@host:5432/zubera_bot`

### Entity Relationship

```
                          ┌──────────────┐
                          │    users     │  (Primary Entity)
                          │  user_id PK  │
                          └──────┬───────┘
                                 │
         ┌──────────┬────────────┼────────────┬──────────┐
         │          │            │            │          │
         ▼          ▼            ▼            ▼          ▼
  ┌─────────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐
  │verifications│ │user_pref │ │conversa-│ │recomm- │ │ tickets  │
  │             │ │erences   │ │tions    │ │endations│ │          │
  └─────────────┘ └──────────┘ └─────────┘ └────────┘ └──────────┘
         │
         ├── sessions (session_key → user_id)
         └── user_workspaces (user_id FK)
```

---

### Table 1: `users` — User Profiles

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `user_id` | VARCHAR(100) | **PRIMARY KEY** | Unique identifier (e.g., "whatsapp:919876543210") |
| `phone_number` | VARCHAR(20) | UNIQUE, NOT NULL | WhatsApp phone number |
| `name` | VARCHAR(200) | — | Display name |
| `age` | INTEGER | — | User age |
| `risk_profile` | VARCHAR(20) | — | `conservative` / `moderate` / `aggressive` |
| `email` | VARCHAR(255) | — | Optional email for notifications |
| `is_verified` | BOOLEAN | DEFAULT false | KYC verification status |
| `created_at` | TIMESTAMP | DEFAULT now() | Registration timestamp |

**Relationships:** Has many → verifications, user_preferences, conversations, recommendations, tickets, sessions, user_workspaces

---

### Table 2: `verifications` — KYC Records

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `verification_id` | SERIAL | **PRIMARY KEY** | Auto-increment ID |
| `user_id` | VARCHAR(100) | **FK → users** | User reference |
| `verification_type` | VARCHAR(50) | — | `PAN` / `Aadhaar` / `Bank` |
| `status` | VARCHAR(20) | — | `pending` / `verified` / `failed` |
| `response_data` | JSON | — | KYC API response payload |
| `error_message` | TEXT | — | Error details if verification failed |
| `created_at` | TIMESTAMP | DEFAULT now() | Record creation time |

---

### Table 3: `user_preferences` — Investment Preferences

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `preference_id` | SERIAL | **PRIMARY KEY** | Auto-increment ID |
| `user_id` | VARCHAR(100) | **FK → users** | User reference |
| `risk_tolerance` | VARCHAR(20) | — | `low` / `medium` / `high` |
| `investment_horizon` | VARCHAR(20) | — | `short` / `medium` / `long` |
| `monthly_budget` | NUMERIC | — | Monthly investment budget in INR |
| `preferred_categories` | ARRAY(VARCHAR) | — | `["Equity", "Debt", "Hybrid"]` |
| `preferred_fund_houses` | ARRAY(VARCHAR) | — | `["HDFC", "SBI", "Kotak"]` |
| `updated_at` | TIMESTAMP | DEFAULT now(), ON UPDATE | Last preference update |

---

### Table 4: `conversations` — Chat History

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `conversation_id` | SERIAL | **PRIMARY KEY** | Auto-increment ID |
| `user_id` | VARCHAR(100) | **FK → users** | User reference |
| `message` | TEXT | NOT NULL | User message content |
| `response` | TEXT | — | Bot response content |
| `timestamp` | TIMESTAMP | DEFAULT now() | Message timestamp |

---

### Table 5: `recommendations` — Fund Recommendations

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `recommendation_id` | SERIAL | **PRIMARY KEY** | Auto-increment ID |
| `user_id` | VARCHAR(100) | **FK → users** | User reference |
| `fund_name` | VARCHAR(200) | — | Recommended fund name |
| `fund_type` | VARCHAR(50) | — | `Equity` / `Debt` / `Hybrid` |
| `risk_level` | VARCHAR(20) | — | Risk classification |
| `reason` | TEXT | — | Recommendation rationale |
| `accepted` | BOOLEAN | — | Whether user accepted the recommendation |
| `created_at` | TIMESTAMP | DEFAULT now() | Recommendation timestamp |

---

### Table 6: `sessions` — Database-Backed Chat Sessions

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `session_id` | SERIAL | **PRIMARY KEY** | Auto-increment ID |
| `session_key` | VARCHAR(200) | **UNIQUE** | Format: `channel:chat_id` (e.g., "whatsapp:919876543210@s.whatsapp.net") |
| `user_id` | VARCHAR(100) | — | User identifier |
| `messages` | JSON | — | Full conversation history as JSON array `[{role, content}, ...]` |
| `is_active` | BOOLEAN | DEFAULT true | Session active status |
| `created_at` | TIMESTAMP | DEFAULT now() | Session creation time |
| `last_activity` | TIMESTAMP | DEFAULT now() | Last interaction timestamp |

**Auto-cleanup:** Inactive sessions older than 7 days are automatically archived via `cleanup_inactive_sessions()`.

---

### Table 7: `user_workspaces` — Per-User Isolated Storage

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `workspace_id` | SERIAL | **PRIMARY KEY** | Auto-increment ID |
| `user_id` | VARCHAR(100) | **FK → users** | User reference |
| `workspace_path` | VARCHAR(500) | — | Filesystem path (e.g., `~/.zuberabot/workspaces/<user_id>`) |
| `storage_used_mb` | INTEGER | DEFAULT 0 | Current storage usage in MB |
| `max_storage_mb` | INTEGER | DEFAULT 1000 | Storage quota (1 GB default) |
| `created_at` | TIMESTAMP | DEFAULT now() | Workspace creation time |

---

### Table 8: `tickets` — Support Tickets

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| `id` | SERIAL | **PRIMARY KEY** | Ticket ID |
| `user_id` | VARCHAR(100) | **FK → users** | Reporting user |
| `channel` | VARCHAR(50) | — | Source channel (`whatsapp`) |
| `chat_id` | VARCHAR(100) | — | Chat ID for responses |
| `subject` | VARCHAR(300) | — | Ticket subject line |
| `description` | TEXT | — | Detailed description |
| `status` | VARCHAR(20) | DEFAULT 'open' | `open` → `in_progress` → `resolved` → `closed` |
| `priority` | VARCHAR(10) | DEFAULT 'medium' | `low` / `medium` / `high` |
| `email` | VARCHAR(255) | — | Optional email for follow-up |
| `resolved_at` | TIMESTAMP | — | Resolution timestamp |
| `assigned_to` | VARCHAR(50) | — | Assigned agent/team |
| `extra_data` | JSON | DEFAULT {} | Extensible metadata |
| `created_at` | TIMESTAMP | DEFAULT now() | Ticket creation time |

---

## 8. Feature Inventory

### 🏦 Mutual Fund Advisory
- Risk-profiled recommendations: **Conservative** (debt funds), **Moderate** (hybrid), **Aggressive** (equity)
- Goal-based planning: Retirement, Wealth, Emergency, Child Education, Short-term
- Interactive 3-step questionnaire flow (risk → amount → goal → personalized picks)
- Live NAV data from MFAPI with **1-year and 3-year return** calculations
- Fund comparison tool (up to 3 funds side-by-side)
- Fund search by name/keyword with Indian scheme codes
- Pre-configured fund recommendations with real scheme codes (HDFC, Kotak, SBI, DSP, etc.)

### 📊 Expense Tracking
- Add expenses with categories: food, transport, bills, entertainment, shopping, healthcare, other
- Monthly summaries with category-wise breakdown in **INR (₹)**
- Expense history queries with month and category filters
- Running totals and top-10 recent expenses

### 📈 Real-Time Market Data
- Live stock prices — global + NSE/BSE (e.g., `TATAMOTORS.NS`)
- Fund information: NAV, category, YTD return
- Market news per ticker (latest 3 articles)
- Historical performance data for return calculations

### 🧠 RAG Knowledge Base
- **ChromaDB** vector store with `all-MiniLM-L6-v2` SentenceTransformer embeddings
- Multi-context isolation: `banking`, `personal`, `general` (or custom)
- PDF document ingestion support via `extract_text_from_pdf`
- Semantic search returns top 3 relevant passages
- Context switching for scoped queries

### 🎫 Ticket Management
- Create support tickets with priority levels: `low` / `medium` / `high`
- Status lifecycle: `open` → `in_progress` → `resolved` → `closed`
- Ticket listing and lookup by ID
- Email capture for follow-up notifications
- Extensible metadata via `extra_data` JSON field

### 🤖 Multi-User AI Agent
- Per-user **memory isolation**: long-term `MEMORY.md` + daily date notes (`YYYY-MM-DD.md`)
- Per-user **workspace** with configurable storage quotas (default 1 GB)
- Database-backed **session persistence** with auto-cleanup (7-day inactive threshold)
- **Sub-agent delegation** for complex multi-step tasks via `SpawnTool`
- Up to **20 tool-call iterations** per request
- Multi-modal support: text + image attachments (base64 encoded)
- Auto-reconnect on WhatsApp bridge disconnection (5-second retry)

### 🔍 Web Intelligence
- Brave Search integration for real-time market news and financial articles
- URL content fetching with HTML → Markdown/text extraction via Readability
- Configurable max results (1-10) and content length limits (50,000 chars)

---

## 9. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Runtime** | Python | 3.11+ | Core application |
| **Runtime** | Node.js | 18+ | WhatsApp bridge |
| **Framework** | zuberabot-ai | 0.1.3 | Agent orchestration |
| **LLM Gateway** | LiteLLM | ≥1.0 | Unified multi-provider LLM API |
| **Database** | PostgreSQL | 15 (Alpine) | Primary relational database |
| **Vector DB** | ChromaDB | Latest | RAG knowledge base |
| **ORM** | SQLAlchemy | ≥2.0 | Database object mapping + QueuePool |
| **DB Driver** | psycopg2-binary | ≥2.9 | PostgreSQL Python driver |
| **Validation** | Pydantic + pydantic-settings | ≥2.0 | Config schema + env injection |
| **HTTP Client** | httpx | ≥0.25 | Async HTTP for APIs |
| **Finance** | yfinance | Latest | Stock/fund market data |
| **WhatsApp** | @whiskeysockets/baileys | Latest | WhatsApp Web protocol |
| **WebSocket** | websockets | ≥12.0 | Bridge ↔ Python communication |
| **Embeddings** | SentenceTransformers | Latest | `all-MiniLM-L6-v2` for RAG |
| **Logging** | Loguru | ≥0.7 | Structured logging |
| **CLI** | Typer + Rich | Latest | Rich terminal interface |
| **Scheduler** | croniter | ≥2.0 | Cron-based scheduled tasks |
| **HTML Parser** | readability-lxml | ≥0.8 | URL content extraction |
| **Container** | Docker + Docker Compose | 3.8 | Deployment packaging |
| **Build** | Hatchling | Latest | Python package build system |

---

## 10. Security Model

### Secrets Management
- All API keys stored in `.env` file (gitignored, never committed to version control)
- Environment variable injection via Docker Compose `env_file`
- Pydantic-validated configuration with `NANOBOT_` prefix and nested delimiter `__`

### User Isolation
- Per-user workspace directories with configurable storage quotas
- Session-scoped conversation history keyed by `channel:chat_id`
- Isolated memory stores: long-term `MEMORY.md` + daily date notes
- Phone number-based user identification via WhatsApp JID

### Database Security
- Password-masked connection URLs in all log output (`_safe_url()`)
- Connection pool management via `QueuePool` with connect/close event listeners
- Automatic session cleanup for inactive users (7-day threshold)
- Context manager pattern ensures sessions are properly committed/rolled back

### Financial Safety
- `FinancialOllamaProvider` wraps responses with financial disclaimers
- Calculation verification layer for numerical accuracy
- Fact-checking system prompt enrichment
- Emergency fund always directed to debt instruments regardless of risk profile
- Investment advice tagged with risk warnings

---

## 11. Project Structure

```
zuberabot/
├── .env                          # API keys & environment config
├── .gitignore
├── Dockerfile                    # Container build
├── docker-compose.yml            # Production stack (app + DB)
├── pyproject.toml                # Python project config (Hatch)
├── start_bot.ps1                 # Local dev startup script
├── start_gemini_bot.ps1          # Gemini-configured startup
├── start_gateway.bat             # Gateway mode startup
├── startup_ollama.bat            # Ollama local LLM startup
├── start_vllm.ps1               # vLLM server startup
│
├── zuberabot/                      # ====== PYTHON CORE ======
│   ├── __init__.py               # Package init, version
│   ├── __main__.py               # Entry point
│   │
│   ├── agent/                    # --- Agent Core ---
│   │   ├── loop.py               # AgentLoop - core processing engine
│   │   ├── context.py            # ContextBuilder - prompt assembly
│   │   ├── user_context.py       # UserContextBuilder - per-user prompts
│   │   ├── user_memory.py        # UserMemoryStore - long-term + daily
│   │   ├── memory.py             # Base memory management
│   │   ├── skills.py             # Skill loader
│   │   ├── subagent.py           # Sub-agent delegation
│   │   │
│   │   └── tools/                # --- Agent Tools ---
│   │       ├── base.py           # Tool base class
│   │       ├── registry.py       # Tool registry
│   │       ├── finance.py        # Stock/MF data (yFinance + MFAPI)
│   │       ├── expense.py        # Expense tracking
│   │       ├── ticket.py         # Support ticket management
│   │       ├── rag.py            # RAG knowledge base (ChromaDB)
│   │       ├── web.py            # Web search + URL fetch
│   │       ├── filesystem.py     # File read/write/search
│   │       ├── message.py        # Message sending
│   │       ├── shell.py          # System command execution
│   │       ├── spawn.py          # Sub-agent spawning
│   │       └── fallback.py       # Fallback tool handler
│   │
│   ├── bus/                      # --- Message Bus ---
│   │   ├── events.py             # InboundMessage / OutboundMessage
│   │   └── queue.py              # Async message queue
│   │
│   ├── channels/                 # --- Channel Integrations ---
│   │   ├── base.py               # Base channel class
│   │   ├── manager.py            # Channel manager
│   │   └── whatsapp.py           # WhatsApp channel (bridge client)
│   │
│   ├── config/                   # --- Configuration ---
│   │   ├── schema.py             # Pydantic config models
│   │   └── loader.py             # Config file loader
│   │
│   ├── database/                 # --- Database Layer ---
│   │   ├── models.py             # SQLAlchemy ORM models (8 tables)
│   │   └── postgres.py           # DatabaseManager (CRUD operations)
│   │
│   ├── providers/                # --- LLM Providers ---
│   │   ├── base.py               # LLMProvider base class
│   │   ├── litellm_provider.py   # LiteLLM unified gateway
│   │   ├── ollama.py             # Ollama + FinancialOllamaProvider
│   │   ├── local_llm.py          # Local model provider
│   │   └── transcription.py      # Voice transcription
│   │
│   ├── session/                  # --- Session Management ---
│   │   ├── manager.py            # Session lifecycle
│   │   └── db_manager.py         # DB-backed session store
│   │
│   ├── utils/                    # --- Utilities ---
│   │   ├── helpers.py            # Common helper functions
│   │   └── mf_api.py             # MFAPIClient (Indian MF data)
│   │
│   ├── cli/                      # --- CLI Interface ---
│   ├── cron/                     # --- Scheduled Tasks ---
│   ├── heartbeat/                # --- Health Monitoring ---
│   └── skills/                   # --- Skill Files ---
│
├── bridge/                       # ====== NODE.JS BRIDGE ======
│   ├── package.json              # NPM dependencies
│   ├── tsconfig.json             # TypeScript config
│   └── src/
│       ├── index.ts              # Bridge entry point
│       ├── server.ts             # WebSocket server
│       ├── whatsapp.ts           # Baileys WhatsApp client
│       └── types.d.ts            # Type definitions
│
├── scripts/                      # ====== SCRIPTS ======
├── database/                     # ====== DB MIGRATIONS ======
│
└── tests/                        # ====== TEST FILES ======
    ├── test_database.py
    ├── test_db_simple.py
    ├── test_mf_integration.py
    ├── test_mistral_financial.py
    ├── test_multi_user.py
    └── test_conversational_recommendations.py
```

---

## 12. Deployment Architecture

### Docker Compose Stack

```yaml
services:
  zuberabot:          # Python application
    port: 18790       # Gateway/WebSocket server
    depends_on: db
    volumes: ~/.nanobot (workspace + config)
    command: gateway

  zuberabot-db:       # PostgreSQL 15 Alpine
    port: 5432
    volumes: zubera_pgdata (persistent)

  # Optional: Ollama on host machine
  # port: 11434 (accessed via host.docker.internal)
```

### Deployment Modes

| Mode | Command | Description |
|------|---------|-------------|
| **CLI** | `nanobot chat` | Interactive terminal chat (direct mode) |
| **Gateway** | `nanobot gateway` | WebSocket server for WhatsApp bridge connection |
| **Docker** | `docker-compose up -d` | Full production stack (app + PostgreSQL) |
| **Local Dev** | `start_bot.ps1` | PowerShell script with environment setup |
| **Gemini Mode** | `start_gemini_bot.ps1` | Pre-configured for Gemini provider |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (if using Gemini) | Google Gemini API key |
| `GROQ_API_KEY` | Yes (if using Groq) | Groq API key for fast inference |
| `OPENROUTER_API_KEY` | Optional | OpenRouter multi-model gateway key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `OLLAMA_API_BASE` | Optional | Ollama server URL (default: `http://localhost:11434`) |
| `BRAVE_API_KEY` | Optional | Brave Search API key for web search |
| `PYTHONIOENCODING` | Recommended | Set to `utf-8` for Unicode support |
| `PYTHONPATH` | Dev only | Project root path for imports |

---

> **© 2026 Zubera Technologies** — Confidential | Document Version 1.0 | February 2026
