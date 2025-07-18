# adk-base

A base ReAct agent built with Google's Agent Development Kit (ADK)
Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.8.0`

## Project Structure

This project is organized as follows:

```
adk-base/
├── app/                 # Core application code
│   ├── agent.py         # Main agent logic
│   ├── agent_engine_app.py # Agent Engine application logic
│   └── utils/           # Utility functions and helpers
├── deployment/          # Infrastructure and deployment scripts
├── notebooks/           # Jupyter notebooks for prototyping and evaluation
├── tests/               # Unit, integration, and load tests
├── Makefile             # Makefile for common commands
├── GEMINI.md            # AI-assisted development guide
└── pyproject.toml       # Project dependencies and configuration
```

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager - [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Terraform**: For infrastructure deployment - [Install](https://developer.hashicorp.com/terraform/downloads)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/) (pre-installed on most Unix-based systems)


## Quick Start (Local Testing)

Install required packages and launch the local development environment:

```bash
make install && make playground
```

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make playground`    | Launch Streamlit interface for testing agent locally and remotely |
| `make backend`       | Deploy agent to Agent Engine |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (codespell, ruff, mypy)                                             |
| `make setup-dev-env` | Set up development environment resources using Terraform                         |
| `make slack-bot`     | Launch Slack bot for real-time agent interaction                                           |
| `uv run jupyter lab` | Launch Jupyter notebook                                                                     |

For full command options and usage, refer to the [Makefile](Makefile).


## Usage

This template follows a "bring your own agent" approach - you focus on your business logic, and the template handles everything else (UI, infrastructure, deployment, monitoring).

1. **Prototype:** Build your Generative AI Agent using the intro notebooks in `notebooks/` for guidance. Use Vertex AI Evaluation to assess performance.
2. **Integrate:** Import your agent into the app by editing `app/agent.py`.
3. **Test:** Explore your agent functionality using the Streamlit playground with `make playground`. The playground offers features like chat history, user feedback, and various input types, and automatically reloads your agent on code changes.
4. **Deploy:** Set up and initiate the CI/CD pipelines, customizing tests as necessary. Refer to the [deployment section](#deployment) for comprehensive instructions. For streamlined infrastructure deployment, simply run `uvx agent-starter-pack setup-cicd`. Check out the [`agent-starter-pack setup-cicd` CLI command](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd.html). Currently only supporting Github.
5. **Monitor:** Track performance and gather insights using Cloud Logging, Tracing, and the Looker Studio dashboard to iterate on your application.

The project includes a `GEMINI.md` file that provides context for AI tools like Gemini CLI when asking questions about your template.


## Deployment

> **Note:** For a streamlined one-command deployment of the entire CI/CD pipeline and infrastructure using Terraform, you can use the [`agent-starter-pack setup-cicd` CLI command](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd.html). Currently only supporting Github.

### Dev Environment

You can test deployment towards a Dev Environment using the following command:

```bash
gcloud config set project <your-dev-project-id>
make backend
```


The repository includes a Terraform configuration for the setup of the Dev Google Cloud project.
See [deployment/README.md](deployment/README.md) for instructions.

### Production Deployment

The repository includes a Terraform configuration for the setup of a production Google Cloud project. Refer to [deployment/README.md](deployment/README.md) for detailed instructions on how to deploy the infrastructure and application.


## Monitoring and Observability
> You can use [this Looker Studio dashboard](https://lookerstudio.google.com/reporting/46b35167-b38b-4e44-bd37-701ef4307418/page/tEnnC
) template for visualizing events being logged in BigQuery. See the "Setup Instructions" tab to getting started.

The application uses OpenTelemetry for comprehensive observability with all events being sent to Google Cloud Trace and Logging for monitoring and to BigQuery for long term storage.

## Slack Bot Integration

This project includes Slack bot integration that allows you to interact with the ADK agent through Slack.

### Setup

1. **Create a Slack App**: Visit [Slack API](https://api.slack.com/apps) and create a new app for your workspace.

2. **Configure Bot Token Scopes**: In your Slack app settings, add the following OAuth scopes:
   - `app_mentions:read`
   - `chat:write`
   - `channels:read`
   - `groups:read`
   - `im:read`
   - `mpim:read`
   - `commands`

3. **Enable Socket Mode**: Enable Socket Mode in your Slack app and generate an App-Level Token with `connections:write` scope.

4. **Enable Event Subscriptions**: In Event Subscriptions, enable events and add the following bot events:
   - `app_mention`
   - `message.channels`
   - `message.groups` 
   - `message.im`
   - `message.mpim`

4. **Set Environment Variables**: Copy `.env.example` to `.env` and fill in your tokens:
   ```bash
   cp .env.example .env
   # Edit .env with your actual tokens
   ```

5. **Install Dependencies and Run**:
   ```bash
   make install
   make slack-bot
   ```

### Available Slack Commands

- **Direct Messages**: Mention the bot or send direct messages for general conversations
- **`/weather [location]`**: Get weather information for a specific location
- **`/time [location]`**: Get current time for a specific location
- **App Mentions**: Use `@your-bot-name` to interact with the agent in channels

The bot maintains separate conversation sessions for each user and integrates seamlessly with the ADK agent's capabilities.

## Langfuse Integration

This project supports prompt management through Langfuse, allowing you to manage and version your prompts externally.

### Setup

1. **Start Langfuse with Docker Compose**:
   ```bash
   docker-compose up -d
   ```
   
   This will start:
   - Langfuse UI at http://localhost:3000
   - PostgreSQL database for Langfuse

2. **Access Langfuse UI**:
   - Navigate to http://localhost:3000
   - Create an account on first access
   - Create a new project and obtain your API keys

3. **Configure Environment Variables**:
   ```bash
   # Add these to your .env file
   LANGFUSE_PUBLIC_KEY=your_public_key
   LANGFUSE_SECRET_KEY=your_secret_key
   LANGFUSE_HOST=http://localhost:3000
   ```

4. **Create Prompts in Langfuse**:
   - Go to the Prompts section in Langfuse UI
   - Create prompts with names matching those in `app/agent.py`:
     - `search_agent_instruction`
     - `root_agent_instruction`
   - Set labels (e.g., "production", "development") for version management

### Usage

The application automatically loads prompts from Langfuse when available. If Langfuse is not configured or prompts are not found, it falls back to default prompts defined in the code.

To manage Langfuse services:
```bash
# Start Langfuse
docker-compose up -d

# Stop Langfuse
docker-compose down

# View logs
docker-compose logs -f langfuse
```

### Benefits

- **Version Control**: Track prompt changes over time
- **A/B Testing**: Test different prompt versions
- **Collaboration**: Share and manage prompts across teams
- **Hot Reloading**: Update prompts without redeploying code
- **Analytics**: Monitor prompt performance and usage


## TODO

- v3のlangfuseを使うようにしたい
- langfuseのotel実装
- _run_agentが関数の中に関数定義してるが、やめたい。generationの管理、本当にこんなコード必要なのか深堀したい
