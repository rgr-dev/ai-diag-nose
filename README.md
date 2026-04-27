# Autonomous Service Diagnostics and Remediation System

An AI-powered autonomous agent system that monitors, diagnoses, and remediates service issues using LangGraph workflows with human-in-the-loop (HITL) oversight via Telegram.

## 🎯 Project Overview

This system automatically detects errors in your microservices by querying logs, performing root cause analysis, and executing remediation actions with human approval. It leverages Large Language Models (LLMs) for intelligent decision-making and integrates with various tools and services to maintain system health.

### Key Features

- **Automated Service Monitoring**: Queries Loki logs to detect errors across multiple services
- **Intelligent Diagnosis**: Uses LLMs to analyze errors, code context, and service dependencies
- **Skills-Based Remediation**: Dynamically loads and suggests relevant skills/tools based on the diagnosis
- **Human-in-the-Loop**: Integrates with Telegram for approval workflows and human guidance, leveraged on postgres checkpointing to manage workflow state during interrupts
- **Autonomous Agent Execution**: Executes remediation plans using an autonomous agent with tool access
- **Stateful Workflows**: Uses PostgreSQL checkpointing to pause, resume, and track workflow state
- **Multi-Service Support**: Manages multiple services through a manifest configuration
- **Git Integration**: Analyzes recently modified files and service code context
- **Secrets Management**: Retrieves and manages AWS Secrets Manager configurations

---

## 🏗️ Architecture

The system is built using:

- **[LangGraph](https://github.com/langchain-ai/langgraph)**: Stateful agent workflow orchestration
- **[LangChain](https://github.com/langchain-ai/langchain)**: LLM integration and middleware
- **PostgreSQL**: Persistent checkpointing and state storage
- **Telegram Bot**: Human interaction interface
- **AWS Secrets Manager**: Secure configuration retrieval
- **Loki**: Log aggregation and querying
- **Git/Bitbucket**: Source code analysis

> More components and integrations can be added as needed (e.g., Slack, Datadog, etc.)

---

## 📊 Workflow Overview

The system operates in two distinct flows:

### 1. **Initial Workflow** (`main.py`)

The initial workflow starts fresh diagnostics for all configured services.

**Purpose**: Automatically scan all services for errors and initiate diagnosis workflows.

**Trigger**: Manual execution of `python main.py`

**Process**:
1. Loads service configurations from `services-manifest.yml`
2. For each service, creates a unique workflow thread
3. Initializes the diagnostic workflow with service context
4. Executes the full workflow (detailed below)

**Use Cases**:
- Scheduled health checks (e.g., via cron)
- Manual service audits
- After deployments to verify service health

### 2. **Resume Workflow** (`main_workflow_resume.py`)

The resume workflow continues interrupted workflows based on human input.

**Purpose**: Resume workflows that are waiting for human approval or advice.

**Trigger**: 
- Telegram bot callbacks (approval/rejection buttons)
- Direct human advice via Telegram message replies

**Process**:
1. Listens for Telegram bot events continuously
2. When a user responds (approve, reject, or provide advice):
   - Extracts the workflow thread ID
   - Resumes the workflow from the interrupt point
   - Passes the human decision/advice to the workflow
3. Continues execution based on the human input

**Use Cases**:
- Approving automated remediation actions
- Rejecting inappropriate fixes
- Providing custom guidance when the agent needs help

---

## 🔄 Detailed Workflow Description

Below is the complete workflow as visualized in `workflow_graph.png`:

### **Phase 1: Error Detection & Context Gathering**

#### 1. **query_logs_task**
- **Action**: Queries Loki for error logs based on the service's `logs_query` pattern
- **Output**: Log entries containing errors
- **Routing**: 
  - If logs contain errors → proceed to `git_fetch_task`
  - If logs are clean → END (workflow completes successfully)

#### 2. **git_fetch_task**
- **Action**: Clones or fetches the latest code from the service's Git repository
- **Purpose**: Ensure we have up-to-date source code for analysis
- **Next**: `last_touched_files_task`

#### 3. **last_touched_files_task**
- **Action**: Identifies recently modified files using `git log`
- **Purpose**: Focus analysis on recent changes that may have introduced bugs
- **Next**: `load_service_info_task`

#### 4. **load_service_info_task**
- **Action**: Loads service documentation (README.md, AGENTS.md, etc.)
- **Purpose**: Understand service architecture, dependencies, and known issues
- **Next**: `secrets_retriever_task`

#### 5. **secrets_retriever_task**
- **Action**: Retrieves service configuration from AWS Secrets Manager
- **Purpose**: Compare configurations between problematic and reference services
- **Next**: `diagnosis_llm`

### **Phase 2: Diagnosis & Analysis**

#### 6. **diagnosis_llm**
- **Action**: LLM analyzes:
  - Error logs
  - Recently modified files
  - Service documentation
  - Configuration differences
- **Output**: Initial diagnosis report
- **Next**: `diagnosis_check_llm`

#### 7. **diagnosis_check_llm**
- **Action**: Quality check on the diagnosis
- **Purpose**: Ensure the diagnosis is comprehensive and actionable
- **Routing**:
  - If diagnosis is sufficient → `skills_loader_task`
  - If more information needed → `dummy_node_a` → END (request more data)

### **Phase 3: Remediation Planning**

#### 8. **skills_loader_task**
- **Action**: Loads available skills/tools from the `app/skills/` directory
- **Purpose**: Discover what remediation capabilities are available
- **Next**: `skills_suggestion_llm`

#### 9. **skills_suggestion_llm**
- **Action**: LLM suggests relevant skills/tools for remediation
- **Output**: List of recommended skills (e.g., database-rights, secrets-manager)
- **Next**: `remediation_llm`

#### 10. **remediation_llm**
- **Action**: LLM creates step-by-step remediation plan
- **Output**: Detailed remediation steps using suggested skills
- **Next**: `send_diagnosis_message_task`

### **Phase 4: Human Approval (HITL)**

#### 11. **send_diagnosis_message_task**
- **Action**: Sends diagnosis report and remediation plan to Telegram
- **Format**: Message with inline buttons (Proceed, Dismiss, Give advice)
- **Next**: `approval_hitl`

#### 12. **approval_hitl**
- **Action**: **INTERRUPT** - Workflow pauses here
- **Purpose**: Wait for human decision via Telegram
- **Resume Triggers**: 
  - User clicks "Proceed" → `remediation_executor_agent`
  - User clicks "Dismiss" → `dummy_node_b` → END
  - User clicks "Give advice" → `get_advice_hitl`

### **Phase 5: Remediation Execution**

#### 13. **remediation_executor_agent**
- **Action**: Autonomous agent executes remediation using middleware:
  - **select_tools**: Dynamically loads tools based on suggested skills
  - **add_context**: Injects remediation plan and secrets into system prompt
  - **log_response**: Logs agent actions
- **Tools Available**: Database scripts, AWS Secrets Manager operations, etc.
- **Process**: 
  - Agent follows the remediation plan
  - Executes tools (e.g., update secrets, modify DB permissions)
  - Reports results
- **Next**: `dummy_node_c` → END

### **Alternative Path: Human Advice**

#### 14. **get_advice_hitl**
- **Action**: **INTERRUPT** - Wait for custom human advice
- **Trigger**: When user clicks "Give advice" or replies with custom instructions
- **Next**: `human_advice_processor_llm`

#### 15. **human_advice_processor_llm**
- **Action**: LLM processes human advice and updates remediation plan
- **Output**: Adjusted recommendations based on human guidance
- **Routing**:
  - If advice leads to actionable plan → `dummy_node_a` → END
  - If advice rejects action → `dummy_node_b` → END

> Dummy nodes represent workflow debug termination points based on different outcomes. they can be deleted or replaced with actual nodes as needed.
---

## 📦 Prerequisites

- **Python 3.14+** (or compatible version)
- **PostgreSQL** database for checkpointing
- **Git** for repository cloning
- **Access to**:
  - Loki instance for log querying
  - AWS account with Secrets Manager
  - Bitbucket/Git repositories
  - Telegram Bot API
  - OpenAI API (or Ollama for local LLMs)

---

## ⚙️ Configuration

### 1. **Environment Variables**

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required Configuration**:

```bash
# Database (PostgreSQL) - for workflow checkpointing
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=postgres
DB_PASSWORD=your_password

# AWS - for Secrets Manager
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_ENDPOINT_URL=http://localhost:4566  # For LocalStack testing

# Bitbucket/Git
BITBUCKET_TOKEN=your_bitbucket_token
BITBUCKET_USER=your_email@example.com

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_IDS=123456789,987654321  # Comma-separated chat IDs

# OpenAI
OPENAI_API_KEY=sk-proj-your_api_key
OPENAI_MODEL=gpt-4o-mini

# Loki - for log querying
LOKI_URL=http://localhost:3100/loki/api/v1/query_range

# Application Paths
GIT_REPOS_PATH=/path/to/git/repos  # Where to clone repositories
SKILLS_SCRIPTS_DIR=/path/to/skills/scripts  # Optional: custom skills location
```

### 2. **Service Manifest**

Copy `services-manifest.example.yml` to `services-manifest.yml` and define your services:

```yaml
services:
  - name: my-api-service
    repository: git@bitbucket.org:company/my-api.git
    service_endpoint: https://api.example.com
    description_file: AGENTS.md  # Service documentation
    logs_query: '{service="my-api"} |= `ERROR` or `Caused by`'
    reference_services:
      - reference-service  # Healthy service for comparison
    service_dependencies:
      - postgres-db
      - redis-cache

dependencies:
  - name: postgres-db
    type: database
    vendor: postgres
  - name: redis-cache
    type: database
    vendor: redis
```

**Service Configuration Options**:
- `name`: Service identifier
- `repository`: Git repository URL
- `service_endpoint`: API endpoint for the service
- `description_file`: Documentation file (README.md, AGENTS.md, etc.)
- `troubleshooting_file`: Optional troubleshooting guide (default: `troubleshooting-skill.md`)
- `logs_query`: LogQL query pattern for Loki
- `reference_services`: List of healthy services to compare against
- `service_dependencies`: Infrastructure dependencies

### 3. **Database Setup**

Create PostgreSQL database and tables:

```bash
createdb your_database
```

The LangGraph checkpointer will automatically create required tables on first run.

---

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rgr-dev/ai-diag-nose
   cd ai-diag-nose
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Configure services**:
   ```bash
   cp services-manifest.example.yml services-manifest.yml
   # Edit services-manifest.yml with your services
   ```

---

## 📖 Usage

### Running Initial Workflow

Start fresh diagnostics for all configured services:

```bash
python main.py
```

**What happens**:
- Queries logs for all services in `services-manifest.yml`
- For each service with errors:
  - Creates a workflow thread (e.g., `diagnosis-my-api-a1b2c3d4`)
  - Runs through diagnosis pipeline
  - Sends Telegram message with approval buttons
  - Waits at `approval_hitl` interrupt

**Output**:
- Console logs showing workflow progress
- `workflow_graph.png` - visual representation of the workflow
- Telegram messages with diagnosis reports

### Running Resume Workflow

Listen for human responses and resume workflows:

```bash
python main_workflow_resume.py
```

**What happens**:
- Continuously polls Telegram for bot events (every 30 seconds)
- When a user interacts:
  - **Clicks "Proceed"**: Resumes workflow → executes remediation
  - **Clicks "Dismiss"**: Ends workflow without action
  - **Clicks "Give advice"**: Prompts for custom input → processes advice
  - **Replies to bot message**: Captures custom instructions → resumes workflow

**Keep this running**:
```bash
# Run in background or as a service
nohup python main_workflow_resume.py &

# Or use a process manager like systemd or supervisor
```

---

## 🛠️ Workflow Components

### Nodes
- **Task Nodes**: Execute specific actions (query logs, fetch git, etc.)
- **LLM Nodes**: AI-powered decision making (diagnosis, remediation planning)
- **Agent Nodes**: Autonomous tool-using agents (remediation executor)
- **HITL Nodes**: Human interaction interrupts (approval, advice)
- **Dummy Nodes**: Workflow termination points

### Middleware
- **select_tools**: Dynamically loads tools based on suggested skills
- **add_context**: Injects state context into agent prompts
- **log_response**: Logs agent responses for debugging

### Skills
Located in `app/skills/`:
- `database-rights/`: Database permission management
- `secrets-manager/`: AWS Secrets Manager operations
- Add custom skills by creating new directories with `SKILL.md`

---

## 📁 Project Structure

```
.
├── main.py                          # Initial workflow entry point
├── main_workflow_resume.py          # Resume workflow entry point
├── requirements.txt                 # Python dependencies
├── services-manifest.yml            # Service configurations
├── .env                             # Environment variables
├── workflow_graph.png               # Generated workflow visualization
│
├── app/
│   ├── constants.py                 # Application constants
│   ├── agents/
│   │   ├── llm_factory.py          # LLM initialization
│   │   └── prompts.py              # System prompts
│   ├── domain/
│   │   └── state.py                # State schemas
│   ├── graph/
│   │   ├── middlewares.py          # Agent middleware
│   │   └── workflow.py             # Workflow definition
│   ├── nodes/
│   │   ├── agents_catalog.py       # Agent node wrappers
│   │   ├── edges_catalog.py        # Routing logic
│   │   ├── hitl_interruptors.py    # Human-in-the-loop nodes
│   │   ├── task_nodes_catalog.py   # Task implementations
│   │   └── utils.py                # Node utilities
│   ├── scripts/
│   │   ├── db_connection.py        # Database utilities
│   │   ├── git_scripts.py          # Git operations
│   │   ├── logs.py                 # Loki log queries
│   │   ├── service_reg.py          # Service manifest loader
│   │   ├── skills_loader.py        # Skills discovery
│   │   ├── t_bot.py                # Telegram bot integration
│   │   ├── tools_loader.py         # Tool loading
│   │   └── yml_fm_loader.py        # YAML frontmatter parsing
│   └── skills/
│       ├── database-rights/
│       │   └── SKILL.md
│       ├── secrets-manager/
│       │   └── SKILL.md
│       └── scripts/
│           ├── aws_secrets_scripts.py
│           └── database_scripts_executor.py
│
└── git_repos/                       # Cloned service repositories this location can be configured in .env
    ├── service-a/
    └── service-b/
```

---

## 🔍 Troubleshooting

### Workflow doesn't start
- Check PostgreSQL connection in `.env`
- Ensure database exists and is accessible
- Verify Loki URL is reachable

### No Telegram messages
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check `TELEGRAM_CHAT_IDS` includes your chat ID
- Ensure bot has permission to send messages

### Agent errors with tools
- Check `SKILLS_SCRIPTS_DIR` path is correct
- Verify skill scripts are executable
- Review agent logs for specific tool errors

### Workflow stuck at interrupt
- Run `main_workflow_resume.py` to listen for responses
- Check Telegram bot is receiving callbacks
- Verify thread ID matches in logs

---

## 📝 License

See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

1. Add new skills in `app/skills/<skill-name>/SKILL.md`
2. Implement skill scripts in `app/skills/scripts/`
3. Update `tools_loader.py` to register new tools
4. Test with a service configuration in `services-manifest.yml`

---

## 🔮 Future Enhancements

- [ ] Flow for resume from HITL advice with custom instructions
- [ ] Automated rollback on failed remediation
- [ ] Web dashboard for workflow monitoring
- [ ] Metrics and analytics dashboard
- [ ] Slack integration as alternative to Telegram
- [ ] Multi-tenant support
- [ ] Machine learning for pattern recognition

---

For questions or support, please open an issue or contact the development team.
