# Zuberabot Comprehensive Architecture Document

## 1. Overall System Architecture

### High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ZUBERABOT SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   WhatsApp     │    │   Web          │    │   CLI           │         │
│  │   Interface    │    │   Interface    │    │   Interface    │         │
│  └─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘         │
│            │                      │                      │                   │
│            └──────────────────────┼──────────────────────┘                   │
│                                   │                                      │
│                    ┌─────────────▼─────────────┐                          │
│                    │    Gateway Layer          │                          │
│                    │  (WebSocket + REST API)   │                          │
│                    └─────────────┬─────────────┘                          │
│                                  │                                      │
│                    ┌─────────────▼─────────────┐                          │
│                    │    Message Bus            │                          │
│                    │  (Async Queue System)      │                          │
│                    └─────────────┬─────────────┘                          │
│                                  │                                      │
│                    ┌─────────────▼─────────────┐                          │
│                    │    Agent Engine           │                          │
│                    │  ┌─────────────────────┐  │                          │
│                    │  │   Context Builder  │  │                          │
│                    │  │   Session Manager  │  │                          │
│                    │  │   Tool Registry    │  │                          │
│                    │  │   LLM Provider    │  │                          │
│                    │  │   Memory System   │  │                          │
│                    │  └─────────────────────┘  │                          │
│                    └─────────────┬─────────────┘                          │
│                                  │                                      │
│          ┌───────────────────────┼───────────────────────┐               │
│          │                       │                       │               │
│  ┌───────▼───────┐    ┌─────────▼─────────┐    ┌───────▼───────┐       │
│  │   Database    │    │   File System    │    │   External    │       │
│  │   Layer       │    │   (Workspace)    │    │   APIs       │       │
│  │               │    │                  │    │               │       │
│  │ - PostgreSQL  │    │ - User Files     │    │ - MF APIs     │       │
│  │ - Sessions    │    │ - Skills         │    │ - LLM APIs    │       │
│  │ - Users       │    │ - Memory         │    │ - Web APIs    │       │
│  │ - Expenses    │    │ - Temp Files     │    │ - Search APIs │       │
│  │ - MF Data     │    │ - Configs        │    │               │       │
│  └───────────────┘    └──────────────────┘    └───────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Core Architectural Patterns

1. **Microservices Architecture**: Modular components with clear boundaries
2. **Event-Driven Design**: Message bus for loose coupling
3. **Async Processing**: Non-blocking I/O throughout the system
4. **Plugin Architecture**: Extensible tools and skills system
5. **Multi-Tenant Design**: User isolation and workspace separation

## 2. Database Architecture

### Database Schema Design

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          POSTGRESQL DATABASE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │     USERS      │    │  CONVERSATIONS  │    │   SESSIONS      │         │
│  │                │    │                 │    │                 │         │
│  │ user_id (PK)   │◄───┤ user_id (FK)   │◄───┤ user_id (FK)   │         │
│  │ phone_number   │    │ conversation_id │    │ session_id (PK) │         │
│  │ name           │    │ message         │    │ session_key    │         │
│  │ age            │    │ response        │    │ messages (JSON)│         │
│  │ profession     │    │ timestamp       │    │ metadata (JSON)│         │
│  │ income_range   │    │                 │    │ created_at     │         │
│  │ risk_profile   │    │                 │    │ updated_at     │         │
│  │ created_at     │    │                 │    │ last_accessed  │         │
│  │ updated_at     │    │                 │    │ is_active      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ VERIFICATIONS  │    │ RECOMMENDATIONS │    │   EXPENSES      │         │
│  │                │    │                 │    │                 │         │
│  │ verification_id│    │ recommend_id(PK)│    │ expense_id (PK) │         │
│  │ user_id (FK)   │◄───┤ user_id (FK)   │◄───┤ user_id (FK)   │         │
│  │ verification_  │    │ scheme_code     │    │ amount         │         │
│  │ type           │    │ fund_name       │    │ category       │         │
│  │ identifier     │    │ recommended_amt │    │ description    │         │
│  │ status         │    │ allocation_%    │    │ date           │         │
│  │ verified_at    │    │ reason          │    │ created_at     │         │
│  │ response_data  │    │ accepted        │    │                 │         │
│  │ error_message  │    │ created_at      │    │                 │         │
│  │ created_at     │    │                 │    │                 │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                                      │
│           └──────────────────────┘                                      │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │USER_PREFERENCES │    │USER_WORKSPACES  │    │    TICKETS      │         │
│  │                │    │                 │    │                 │         │
│  │ preference_id  │    │ workspace_id(PK)│    │ ticket_id (PK)  │         │
│  │ user_id (FK)   │◄───┤ user_id (FK)   │◄───┤ user_id (FK)   │         │
│  │ investment_    │    │ workspace_path  │    │ channel        │         │
│  │ goal           │    │ storage_used_mb │    │ chat_id        │         │
│  │ investment_    │    │ max_storage_mb  │    │ subject        │         │
│  │ horizon        │    │ created_at      │    │ description    │         │
│  │ monthly_inv_   │    │                 │    │ status         │         │
│  │ capacity       │    │                 │    │ priority       │         │
│  │ preferred_     │    │                 │    │ created_at     │         │
│  │ categories     │    │                 │    │ resolved_at    │         │
│  │ tax_saving_    │    │                 │    │ assigned_to    │         │
│  │ preference     │    │                 │    │ extra_data     │         │
│  │ preferred_     │    │                 │    │                 │         │
│  │ fund_houses    │    │                 │    │                 │         │
│  │ updated_at     │    │                 │    │                 │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Database Design Principles

1. **Normalization**: Proper foreign key relationships and data integrity
2. **Indexing Strategy**: Optimized for common query patterns
3. **JSON Fields**: Flexible storage for metadata and semi-structured data
4. **Audit Trails**: Created/updated timestamps for all entities
5. **Soft Deletes**: Logical deletion where appropriate

### Key Database Features

- **Connection Pooling**: Efficient connection management
- **Transaction Management**: ACID compliance for data integrity
- **Migration System**: Version-controlled schema updates
- **Backup Strategy**: Automated backups and point-in-time recovery

## 3. RAG (Retrieval-Augmented Generation) Architecture

### RAG System Components

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RAG ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   USER QUERY   │    │  CONTEXT       │    │  KNOWLEDGE      │         │
│  │                │    │  RETRIEVAL      │    │  BASES          │         │
│  │ - Intent       │    │                 │    │                 │         │
│  │ - Entities     │───►│ - Semantic      │◄───│ - Vector DB     │         │
│  │ - History      │    │   Search        │    │ - Document DB  │         │
│  │ - Preferences  │    │ - Keyword       │    │ - Graph DB      │         │
│  └─────────────────┘    │   Search        │    │ - Cache         │         │
│           │            │ - Hybrid         │    │                 │         │
│           │            │   Retrieval      │    │                 │         │
│           │            └─────────┬───────┘    └─────────────────┘         │
│           │                      │                                      │
│           │            ┌─────────▼───────┐                              │
│           │            │  CONTEXT       │                              │
│           │            │  RANKING       │                              │
│           │            │                 │                              │
│           │            │ - Relevance     │                              │
│           │            │ - Recency       │                              │
│           │            │ - User Profile  │                              │
│           │            │ - Diversity     │                              │
│           │            └─────────┬───────┘                              │
│           │                      │                                      │
│           │            ┌─────────▼───────┐                              │
│           │            │  AUGMENTED      │                              │
│           │            │  PROMPT         │                              │
│           │            │                 │                              │
│           │            │ - System Prompt  │                              │
│           │            │ - Retrieved     │                              │
│           │            │   Context       │                              │
│           │            │ - User History  │                              │
│           │            │ - Task Context  │                              │
│           │            └─────────┬───────┘                              │
│           │                      │                                      │
│           ▼            ┌─────────▼───────┐                              │
│  ┌─────────────────┐   │   LLM          │                              │
│  │   ENHANCED     │   │   INFERENCE    │                              │
│  │   RESPONSE     │   │                 │                              │
│  │                │   │ - Generation    │                              │
│  │ - Citations    │   │ - Reasoning     │                              │
│  │ - Sources      │   │ - Tool Use      │                              │
│  │ - Confidence   │   │ - Fact Check    │                              │
│  └─────────────────┘   └─────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### RAG Implementation Strategy

1. **Vector Database**: Semantic search for document retrieval
2. **Hybrid Search**: Combines semantic and keyword search
3. **Context Ranking**: Multi-factor relevance scoring
4. **Dynamic Prompting**: Context-aware prompt engineering
5. **Citation Tracking**: Source attribution and verification

### Knowledge Sources

- **Financial Documents**: MF prospectuses, market analysis
- **User History**: Conversations, preferences, recommendations
- **External APIs**: Real-time market data, news feeds
- **Skill Documentation**: Tool descriptions, usage examples
- **System Knowledge**: Configuration, troubleshooting guides

## 4. Application Workflow Architecture

### Message Processing Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MESSAGE PROCESSING PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   MESSAGE      │    │   PRE-         │    │   USER          │         │
│  │   INGESTION    │───►│   PROCESSING   │───►│   AUTHENTICATION│         │
│  │                │    │                 │    │                 │         │
│  │ - WhatsApp     │    │ - Validation    │    │ - Identity      │         │
│  │ - CLI          │    │ - Sanitization │    │ - Permissions  │         │
│  │ - Web          │    │ - Parsing       │    │ - Rate Limiting │         │
│  │ - Format       │    │ - Classification│    │ - Session Mgmt │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────▼─────────┐    ┌─────────────────┐         │
│  │   INTENT       │    │   CONTEXT        │    │   RAG           │         │
│  │   RECOGNITION  │    │   BUILDING       │    │   RETRIEVAL     │         │
│  │                │    │                 │    │                 │         │
│  │ - NLP Analysis │    │ - History       │    │ - Semantic      │         │
│  │ - Entity       │    │ - Memory        │    │ - Search        │         │
│  │   Extraction   │    │ - Preferences   │    │ - Ranking       │         │
│  │ - Classification│   │ - Skills        │    │ - Context       │         │
│  │ - Confidence   │    │ - Tools         │    │   Augmentation  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────▼─────────┐    ┌─────────────────┐         │
│  │   AGENT        │    │   TOOL          │    │   RESPONSE      │         │
│  │   EXECUTION    │    │   EXECUTION     │    │   GENERATION    │         │
│  │                │    │                 │    │                 │         │
│  │ - LLM Call     │◄───│ - Finance       │───►│ - Formatting    │         │
│  │ - Reasoning    │    │ - Expense       │    │ - Personalization│         │
│  │ - Planning     │    │ - Search        │    │ - Validation   │         │
│  │ - Decision     │    │ - File Ops      │    │ - Safety Check  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────▼─────────┐    ┌─────────────────┐         │
│  │   POST-        │    │   DELIVERY      │    │   FEEDBACK      │         │
│  │   PROCESSING    │    │                 │    │   LOOP          │         │
│  │                │    │ - WhatsApp      │    │                 │         │
│  │ - Logging      │    │ - CLI           │    │ - Analytics     │         │
│  │ - Analytics    │    │ - Web           │    │ - Learning      │         │
│  │ - Storage      │    │ - Notifications │    │ - Optimization  │         │
│  │ - Monitoring   │    │ - Queuing       │    │ - Adaptation    │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Workflow States and Transitions

1. **Ingestion State**: Raw message reception and validation
2. **Authentication State**: User verification and session management
3. **Analysis State**: Intent recognition and context building
4. **Retrieval State**: RAG knowledge retrieval and ranking
5. **Execution State**: Agent reasoning and tool execution
6. **Generation State**: Response creation and formatting
7. **Delivery State**: Response delivery and feedback collection

### Error Handling and Recovery

- **Circuit Breakers**: Prevent cascade failures
- **Retry Mechanisms**: Handle transient failures
- **Fallback Strategies**: Graceful degradation
- **Dead Letter Queues**: Handle failed messages
- **Monitoring**: Real-time error tracking

## 5. Feature Architecture

### 5.1 Mutual Fund Recommendation System

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MF RECOMMENDATION ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   USER PROFILE │    │   RISK          │    │   GOAL          │         │
│  │   ANALYSIS     │───►│   ASSESSMENT    │───►│   MAPPING       │         │
│  │                │    │                 │    │                 │         │
│  │ - Age          │    │ - Risk Tolerance│    │ - Time Horizon  │         │
│  │ - Income       │    │ - Capacity      │    │ - Amount        │         │
│  │ - Profession  │    │ - Psychology   │    │ - Purpose       │         │
│  │ - Experience  │    │ - Constraints   │    │ - Priority      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────▼─────────┐    ┌─────────────────┐         │
│  │   MARKET       │    │   ALGORITHM     │    │   FUND          │         │
│  │   ANALYSIS     │    │   SELECTION     │    │   FILTERING     │         │
│  │                │    │                 │    │                 │         │
│  │ - Trends       │    │ - Scoring       │    │ - Performance   │         │
│  │ - Volatility   │    │ - Weighting     │    │ - Risk Metrics  │         │
│  │ - Sectors      │    │ - Optimization  │    │ - Expense Ratio │         │
│  │ - Economy      │    │ - Diversification│   │ - AUM          │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────▼─────────┐    ┌─────────────────┐         │
│  │   PORTFOLIO     │    │   RECOMMENDATION │    │   EXPLANATION   │         │
│  │   OPTIMIZATION  │    │   GENERATION     │    │   ENGINE        │         │
│  │                │    │                 │    │                 │         │
│  │ - Allocation   │    │ - Fund Selection │    │ - Why Selected │         │
│  │ - Rebalancing  │    │ - Amount        │    │ - Risk Profile │         │
│  │ - Tax          │    │ - SIP/Lumpsum   │    │ - Expected     │         │
│  │   Efficiency   │    │ - Timeline      │    │   Returns      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### MF Recommendation Features

1. **Interactive Questionnaire**: Step-by-step user profiling
2. **Risk Assessment**: Multi-dimensional risk analysis
3. **Goal-Based Planning**: Customized recommendations for different life goals
4. **Real-Time Data**: Live NAV, performance metrics, market data
5. **Portfolio Optimization**: Modern Portfolio Theory implementation
6. **Tax Optimization**: ELSS recommendations for tax saving
7. **Performance Tracking**: Monitor recommended funds over time

### 5.2 Expense Tracking System

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     EXPENSE TRACKING ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   EXPENSE      │    │   CATEGORY      │    │   BUDGET        │         │
│  │   CAPTURE      │    │   CLASSIFICATION│    │   MANAGEMENT    │         │
│  │                │    │                 │    │                 │         │
│  │ - Manual Entry │    │ - Auto ML       │    │ - Limits       │         │
│  │ - Voice Input  │    │ - Rules Engine  │    │ - Alerts       │         │
│  │ - OCR Receipts │    │ - NLP Analysis  │    │ - Forecasting  │         │
│  │ - Bank Sync    │    │ - Learning      │    │ - Optimization  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────▼─────────┐    ┌─────────────────┐         │
│  │   ANALYTICS    │    │   VISUALIZATION  │    │   INSIGHTS      │         │
│  │   ENGINE       │    │                 │    │                 │         │
│  │                │    │ - Charts         │    │ - Patterns      │         │
│  │ - Trends       │    │ - Graphs        │    │ - Anomalies     │         │
│  │ - Patterns     │    │ - Reports       │    │ - Recommendations│         │
│  │ - Forecasts    │    │ - Dashboards    │    │ - Savings       │         │
│  │ - Comparisons  │    │ - Export        │    │   Opportunities │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  │                                      │
│  ┌─────────────────┐    ┌─────────▼─────────┐    ┌─────────────────┐         │
│  │   INTEGRATION   │    │   NOTIFICATION   │    │   REPORTING     │         │
│  │   HUB          │    │   SYSTEM        │    │   ENGINE        │         │
│  │                │    │                 │    │                 │         │
│  │ - Bank APIs    │    │ - Budget Alerts │    │ - Monthly      │         │
│  │ - Credit Cards │    │ - Overspend     │    │ - Weekly       │         │
│  │ - Digital      │    │   Warnings      │    │ - Custom       │         │
│  │   Wallets      │    │ - Reminders    │    │ - Tax          │         │
│  │ - UPI Apps     │    │ - Summaries    │    │   Reports      │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Expense Tracking Features

1. **Multi-Channel Input**: WhatsApp, voice, OCR, manual entry
2. **Smart Categorization**: ML-based automatic categorization
3. **Budget Management**: Set limits, track spending, get alerts
4. **Analytics Dashboard**: Visual insights and trends
5. **Integration Hub**: Connect with banks, cards, wallets
6. **Intelligent Insights**: AI-powered spending recommendations
7. **Reporting Engine**: Custom reports for tax and financial planning

### 5.3 Additional Core Features

#### KYC Verification System
- **Document Processing**: PAN, Aadhaar, bank verification
- **API Integration**: Surepass API for verification
- **Status Tracking**: Real-time verification status
- **Compliance**: Regulatory compliance and audit trails

#### Conversational AI
- **Natural Language Understanding**: Intent recognition and entity extraction
- **Context Management**: Multi-turn conversation handling
- **Personalization**: User-specific responses and recommendations
- **Multi-Language Support**: Regional language capabilities

#### Skill System
- **Modular Architecture**: Plugin-based skill development
- **Built-in Skills**: Weather, GitHub, summarization, tmux
- **Custom Skills**: User-defined skills and workflows
- **Skill Marketplace**: Community-contributed skills

#### Scheduling and Automation
- **Cron Jobs**: Scheduled task execution
- **Automated Workflows**: Trigger-based automation
- **Reminder System**: Personalized reminders and notifications
- **Batch Processing**: Efficient bulk operations

## 6. Technology Stack Summary

### Backend Technologies
- **Language**: Python 3.11+
- **Framework**: Asyncio, FastAPI, SQLAlchemy
- **Database**: PostgreSQL with connection pooling
- **Message Queue**: Custom async implementation
- **Caching**: Redis for performance optimization

### AI/ML Technologies
- **LLM Integration**: OpenRouter, Anthropic, OpenAI, local models
- **Vector Database**: ChromaDB for semantic search
- **NLP Libraries**: spaCy, transformers
- **ML Frameworks**: scikit-learn, pandas, numpy

### Frontend/Bridge Technologies
- **WhatsApp Bridge**: Node.js with TypeScript
- **WhatsApp Library**: Baileys for WhatsApp Web API
- **Communication**: WebSocket for real-time messaging
- **UI Components**: Rich for CLI, web components for dashboard

### DevOps and Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose, Kubernetes ready
- **Monitoring**: Structured logging, metrics collection
- **CI/CD**: Automated testing and deployment pipelines

### External Integrations
- **Financial APIs**: Mutual fund APIs, market data providers
- **Verification APIs**: Surepass for KYC
- **Search APIs**: Brave Search for web search
- **Communication APIs**: WhatsApp, email, SMS gateways

This comprehensive architecture provides a solid foundation for building a scalable, maintainable, and feature-rich financial assistant platform with WhatsApp as the primary interface.
