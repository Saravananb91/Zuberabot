# Zuberabot Technical Architecture - WhatsApp Implementation

## Overview

Zuberabot is a lightweight AI assistant framework built on Python that provides WhatsApp communication capabilities, tool execution, and extensible skill management. The system follows a modular architecture optimized for WhatsApp integration with clear separation of concerns.

## Core Components

### 1. Agent Engine (`zuberabot/agent/`)
- **AgentLoop**: Core processing engine that orchestrates message processing
- **ContextBuilder**: Builds conversation context with history, memory, and skills
- **ToolRegistry**: Manages available tools and their execution
- **SubagentManager**: Handles sub-agent spawning and coordination
- **Memory System**: Long-term memory storage and retrieval

### 2. Message Bus (`zuberabot/bus/`)
- **MessageBus**: Async message queue for inter-component communication
- **Events**: Defines inbound/outbound message events
- **Queue**: Implements pub/sub pattern for loose coupling

### 3. WhatsApp Channel Management (`zuberabot/channels/`)
- **ChannelManager**: Manages WhatsApp communication channel
- **WhatsApp**: Primary WhatsApp integration via Baileys library
- **Base**: Abstract channel interface for future extensibility

### 4. LLM Providers (`zuberabot/providers/`)
- **LiteLLMProvider**: Unified interface for multiple LLM providers
- **LocalLLM**: Support for local model execution
- **Ollama**: Integration with Ollama for local models
- **Transcription**: Audio transcription capabilities

### 5. Database Layer (`zuberabot/database/`)
- **PostgreSQL**: Primary data store with SQLAlchemy ORM
- **Models**: Data models for sessions, messages, and metadata
- **Connection Pooling**: Efficient database connection management

### 6. Configuration (`zuberabot/config/`)
- **Schema**: Pydantic-based configuration validation
- **Loader**: Dynamic configuration loading from multiple sources
- **Settings**: Environment-based configuration management

### 7. Skills System (`zuberabot/skills/`)
- **Modular Skills**: Extensible skill framework
- **Built-in Skills**: Weather, GitHub, summarization, tmux
- **Skill Creator**: Tools for creating custom skills

### 8. Scheduling (`zuberabot/cron/`)
- **CronService**: Scheduled task execution
- **Job Management**: Create, enable, disable, and run jobs
- **Integration**: Seamless integration with agent loop

### 9. CLI Interface (`zuberabot/cli/`)
- **Commands**: Comprehensive CLI for all operations
- **Interactive Mode**: Direct agent interaction
- **Management**: Channel, cron, and status commands

## Communication Bridge

### WhatsApp Bridge (`bridge/`)
- **Technology**: Node.js with TypeScript
- **Library**: Baileys for WhatsApp Web API
- **WebSocket**: Real-time communication with Python backend
- **QR Authentication**: Device linking via QR codes

## WhatsApp-First Data Flow Architecture

```
┌─────────────────┐
│   WhatsApp      │
│   User          │
└─────────┬───────┘
          │ (WhatsApp Message)
          │
┌─────────▼───────┐
│   WhatsApp      │
│   Bridge        │
│   (Node.js)     │
└─────────┬───────┘
          │ (WebSocket)
          │
┌─────────▼───────┐
│   WhatsApp      │
│   Channel       │
│   (Python)      │
└─────────┬───────┘
          │ (InboundMessage)
          │
┌─────────▼───────┐
│      Message Bus│
│   (Async Queue) │
└─────────┬───────┘
          │
┌─────────▼───────┐
│      Agent Loop │
│                 │
│  ┌─────────────┐ │
│  │Session Mgmt │ │
│  └─────────────┘ │
│  ┌─────────────┐ │
│  │Context Build│ │
│  │- History    │ │
│  │- Memory     │ │
│  │- Skills     │ │
│  └─────────────┘ │
│  ┌─────────────┐ │
│  │LLM Provider │ │
│  │(OpenRouter │ │
│  │ Anthropic   │ │
│  │ OpenAI etc.)│ │
│  └─────────────┘ │
│  ┌─────────────┐ │
│  │Tool Registry│ │
│  │- File Ops   │ │
│  │- Web Search │ │
│  │- Shell Exec │ │
│  │- Custom     │ │
│  └─────────────┘ │
└─────────┬───────┘
          │ (OutboundMessage)
          │
┌─────────▼───────┐
│   WhatsApp      │
│   Channel       │
└─────────┬───────┘
          │ (WebSocket)
          │
┌─────────▼───────┐
│   WhatsApp      │
│   Bridge        │
└─────────┬───────┘
          │ (WhatsApp Message)
          │
┌─────────▼───────┐
│   WhatsApp      │
│   User          │
└─────────────────┘

Side Systems:
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL     │  │   File System   │  │   External      │
│   Database       │  │   Workspace     │  │   APIs          │
│                 │  │                 │  │                 │
│ - Sessions       │  │ - Skills        │  │ - dockdock go Search  │
│ - Messages       │  │ - Memory        │  │ - Web Content   │
│ - User Data      │  │ - Temp Files    │  │ - vLLM       │
│ - Cron Jobs      │  │ - Configs       │  │ - LLM APIs     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Detailed Technical Workflow

### 1. Message Reception Workflow

```
WhatsApp User → WhatsApp Bridge → WhatsApp Channel → Message Bus → Agent Loop
```

**Step-by-Step Process:**

1. **WhatsApp Message Reception**
   - User sends message to Zuberabot WhatsApp number
   - WhatsApp servers deliver message to connected device

2. **Bridge Processing (Node.js)**
   ```javascript
   // Bridge receives WhatsApp message
   whatsapp.on('message', async (message) => {
     const processedMessage = {
       id: message.id,
       from: message.from,
       content: message.body,
       timestamp: message.timestamp,
       type: message.type
     };
     
     // Send to Python backend via WebSocket
     websocket.send(JSON.stringify(processedMessage));
   });
   ```

3. **Channel Reception (Python)**
   ```python
   async def handle_websocket_message(self, data: dict):
       inbound_message = InboundMessage(
           channel="whatsapp",
           chat_id=data["from"],
           content=data["content"],
           message_id=data["id"],
           timestamp=data["timestamp"]
       )
       await self.bus.publish_inbound(inbound_message)
   ```

4. **Message Bus Routing**
   ```python
   class MessageBus:
       async def publish_inbound(self, message: InboundMessage):
           await self.inbound_queue.put(message)
   ```

### 2. Agent Processing Workflow

```
Agent Loop → Context Building → LLM Processing → Tool Execution → Response Generation
```

**Detailed Agent Loop:**

1. **Session Management**
   ```python
   async def process_message(self, message: InboundMessage):
       session = await self.session_manager.get_or_create_session(
           chat_id=message.chat_id,
           channel=message.channel
       )
   ```

2. **Context Building**
   ```python
   context = await self.context_builder.build(
       session=session,
       message=message,
       workspace=self.workspace
   )
   # Context includes:
   # - Conversation history (last N messages)
   # - User preferences and memory
   # - Available skills and tools
   # - System prompts and personality
   ```

3. **LLM Provider Call**
   ```python
   response = await self.provider.completion(
       messages=context.messages,
       model=self.model,
       tools=context.available_tools,
       max_tokens=self.max_tokens
   )
   ```

4. **Tool Execution Loop**
   ```python
   if response.tool_calls:
       for tool_call in response.tool_calls:
           result = await self.tool_registry.execute(tool_call)
           # Add result back to conversation
           await self.process_tool_result(result)
   ```

### 3. Response Delivery Workflow

```
Agent Loop → Message Bus → WhatsApp Channel → WhatsApp Bridge → WhatsApp User
```

**Response Processing:**

1. **Outbound Message Creation**
   ```python
   outbound_message = OutboundMessage(
       channel="whatsapp",
       chat_id=session.chat_id,
       content=response.content,
       message_id=generate_id(),
       timestamp=unix_timestamp()
   )
   ```

2. **Message Bus Publishing**
   ```python
   await self.bus.publish_outbound(outbound_message)
   ```

3. **Channel Processing**
   ```python
   async def send_message(self, message: OutboundMessage):
       await self.websocket.send(json.dumps({
           "type": "outbound",
           "to": message.chat_id,
           "content": message.content
       }))
   ```

4. **Bridge Delivery**
   ```javascript
   websocket.on('message', async (data) => {
     const message = JSON.parse(data);
     await whatsapp.sendMessage(message.to, message.content);
   });
   ```

### 4. Tool Execution Workflow

```
Tool Registry → Tool Execution → Result Processing → Context Update
```

**Tool Categories:**

1. **File System Tools**
   ```python
   class ReadFileTool:
       async def execute(self, path: str) -> str:
           # Security: Validate path is within workspace
           full_path = self.workspace / path
           if not self.is_safe_path(full_path):
               raise SecurityError("Path access denied")
           return full_path.read_text()
   ```

2. **Web Search Tools**
   ```python
   class WebSearchTool:
       async def execute(self, query: str) -> List[SearchResult]:
           async with httpx.Client() as client:
               response = await client.get(
                   f"https://api.search.brave.com/res/v1/web/search",
                   params={"q": query},
                   headers={"X-API-Key": self.api_key}
               )
               return self.parse_results(response.json())
   ```

3. **Shell Execution Tools**
   ```python
   class ExecTool:
       async def execute(self, command: str) -> str:
           # Security: Command validation and sandboxing
           if not self.is_safe_command(command):
               raise SecurityError("Command not allowed")
           
           result = await asyncio.create_subprocess_shell(
               command,
               stdout=asyncio.subprocess.PIPE,
               stderr=asyncio.subprocess.PIPE,
               cwd=self.workspace
           )
           stdout, stderr = await result.communicate()
           return stdout.decode() + stderr.decode()
   ```

### 5. Database Operations Workflow

```
Agent Loop → Database Manager → PostgreSQL → Result Processing
```

**Key Database Operations:**

1. **Session Storage**
   ```python
   async def save_session(self, session: Session):
       async with self.db_manager.get_session() as db_session:
           db_session.add(session.to_db_model())
           await db_session.commit()
   ```

2. **Message History**
   ```python
   async def get_message_history(self, chat_id: str, limit: int = 50):
       async with self.db_manager.get_session() as db_session:
           messages = await db_session.query(MessageModel)\
               .filter(MessageModel.chat_id == chat_id)\
               .order_by(MessageModel.timestamp.desc())\
               .limit(limit)\
               .all()
           return [msg.to_domain() for msg in reversed(messages)]
   ```

### 6. Error Handling and Recovery

```
Error Detection → Logging → Fallback Response → User Notification
```

**Error Handling Strategy:**

1. **Bridge Errors**
   - WebSocket reconnection logic
   - WhatsApp re-authentication prompts
   - Message queuing during downtime

2. **Agent Errors**
   - LLM API timeout handling
   - Tool execution failure recovery
   - Graceful degradation responses

3. **Database Errors**
   - Connection pool management
   - Transaction rollback on failures
   - Caching for read operations during outages

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: Asyncio-based architecture
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Message Queue**: Custom async implementation
- **Configuration**: Pydantic settings management

### External Integrations
- **LLM Providers**: OpenRouter, Anthropic, OpenAI, Gemini, Groq, Local models
- **Web**: HTTP client for API calls and web scraping
- **Search**: Brave Search API integration
- **File System**: Workspace management with sandboxing

### WhatsApp Integration
- **Bridge**: Node.js with TypeScript
- **WhatsApp Library**: Baileys for WhatsApp Web API
- **Communication**: WebSocket server for real-time messaging
- **Authentication**: QR code-based device linking

### Deployment
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for development
- **Process Management**: Graceful shutdown and restart
- **Logging**: Structured logging with Loguru

## Configuration Management

### Configuration Sources (Priority Order)
1. Environment variables
2. `.env` file
3. `~/.zuberabot/config.json`
4. Default values

### Key Configuration Sections
- **Providers**: API keys and endpoints for LLM providers
- **WhatsApp**: WhatsApp channel configuration and bridge URL
- **Agents**: Default model settings and limits
- **Tools**: Tool-specific configurations
- **Database**: Connection parameters

## Security Architecture

### API Key Management
- Environment-based storage
- No hardcoded credentials
- Provider-specific key rotation support

### WhatsApp Security
- Device-based authentication via WhatsApp Web
- Access control lists for allowed phone numbers
- Message validation and content sanitization
- Bridge-to-backend WebSocket authentication

### Tool Execution Security
- Sandboxed file system access
- Command validation and filtering
- Resource usage limits

## Scalability Considerations

### Horizontal Scaling
- Stateless agent design
- Database connection pooling
- Message bus for load distribution

### Performance Optimizations
- Async I/O throughout
- Connection pooling for databases and APIs
- Efficient memory management
- Tool execution timeouts

### Monitoring
- Structured logging
- Health checks via heartbeat service
- Performance metrics collection

## Development Workflow

### Project Structure
```
zuberabot/
├── zuberabot/                 # Core Python package
│   ├── agent/              # Agent engine
│   ├── channels/           # Communication channels
│   ├── providers/          # LLM providers
│   ├── database/           # Database layer
│   ├── config/             # Configuration
│   ├── skills/             # Skill system
│   ├── cli/                # Command-line interface
│   └── utils/              # Utilities
├── bridge/                 # WhatsApp bridge (Node.js)
├── database/               # Database scripts
├── scripts/                # Utility scripts
└── tests/                  # Test suite
```

### Build Process
- Python: Hatchling build system
- Bridge: TypeScript compilation
- Docker: Multi-stage builds
- Dependencies: Separate dev and production requirements

## Deployment Architecture

### Development Environment
```yaml
services:
  nanobot:
    build: .
    ports: ["18790:18790"]
    volumes: ["./workspace:/root/.zuberabot/workspace"]
    depends_on: [db]
  
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: zubera
      POSTGRES_PASSWORD: zubera_password
      POSTGRES_DB: zubera_bot
```

### Production Considerations
- Environment-specific configurations
- Database migrations
- Backup strategies
- Monitoring and alerting
- Load balancing for high availability

### Extension Points

#### Custom WhatsApp Features
- Implement custom message handlers
- Add WhatsApp-specific tools (media processing, etc.)
- Extend message formatting for WhatsApp rich content
- Implement custom authentication methods

#### Custom Tools
- Implement tool interface
- Register with `ToolRegistry`
- Define input/output schemas

#### Custom Skills
- Follow skill template structure
- Include metadata and documentation
- Register with skill system

#### Custom LLM Providers
- Implement `LLMProvider` interface
- Handle authentication and rate limiting
- Support streaming responses

## Testing Strategy

### Unit Tests
- Component isolation
- Mock external dependencies
- Configuration validation

### Integration Tests
- End-to-end WhatsApp message flow
- Bridge-to-backend WebSocket communication
- Database interactions
- External API integrations

### Performance Tests
- Load testing for message processing
- Memory usage profiling
- Database query optimization

## Monitoring and Observability

### Logging
- Structured JSON logging
- Log levels and filtering
- Correlation IDs for request tracing

### Metrics
- Message processing rates
- Tool execution times
- Error rates and types
- Resource utilization

### Health Checks
- Database connectivity
- External API availability
- WhatsApp bridge status
- Agent responsiveness
- WebSocket connection health

## Future Enhancements

### Planned Features
- Advanced WhatsApp features (media processing, groups, etc.)
- Enhanced WhatsApp message formatting and rich content
- Advanced tool orchestration
- Multi-agent collaboration
- Enhanced memory management
- Real-time analytics dashboard
- WhatsApp Business API integration

### Architecture Improvements
- Microservice decomposition
- Event sourcing for message history
- Caching layer for performance
- Advanced security features
- GraphQL API for external integrations
