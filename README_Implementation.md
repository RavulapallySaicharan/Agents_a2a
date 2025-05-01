# A2A Agent Network for Text Processing

This implementation demonstrates a Python A2A agent network with two specialized agents and an AI-powered router.

## Components

1. **Summarizer Agent**: Summarizes text content using OpenAI API
2. **Translator Agent**: Translates text to specified languages using OpenAI API
3. **Agent Network**: Connects and manages both agents
4. **AI-Powered Router**: Intelligently routes queries to the appropriate agent

## Setup Instructions

### Prerequisites

- Python 3.8+
- An OpenAI API key or Azure OpenAI credentials

### Installation

1. Clone this repository or download the files

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file by copying the template:
   ```bash
   cp env.template .env
   ```

4. Edit the `.env` file to add your API credentials. You can use either:
   
   **Standard OpenAI API** (primary):
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   **OR Azure OpenAI API** (used as fallback):
   ```
   AZURE_OPENAI_API_KEY=your_azure_openai_key_here
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
   AZURE_OPENAI_API_VERSION=2023-05-15
   ```
   
   You can configure both for automatic fallback functionality.

### Running the Agent Network

You can run the entire agent network with a single command:

```bash
python run_agent_network.py
```

This will:
1. Start the Summarizer Agent on port 5001
2. Start the Translator Agent on port 5002
3. Wait for both to initialize
4. Run a test of the Agent Network with sample queries

### Running Individual Components

#### Summarizer Agent

```bash
python agents/summarizer.py
```

#### Translator Agent

```bash
python agents/translator.py
```

#### Agent Network Tests

```bash
python agent_network.py
```

## How It Works

1. **Query Processing**:
   - Incoming queries are sent to the agent network
   - The AI router analyzes the query content
   - The router determines which agent is best suited to handle the query
   - The query is forwarded to the selected agent
   - The agent processes the query and returns a response

2. **Summarization**:
   - The Summarizer Agent handles requests to condense text
   - It uses OpenAI's GPT to generate concise summaries

3. **Translation**:
   - The Translator Agent handles requests to translate text
   - It automatically detects the target language from the query
   - It uses OpenAI's GPT to generate accurate translations

4. **API Fallback Mechanism**:
   - The system attempts to use the standard OpenAI API first
   - If initialization fails (due to missing credentials or API issues), it automatically falls back to Azure OpenAI
   - This fallback happens transparently with no manual intervention required

## Customization

- **Ports**: You can change the ports by editing the `.env` file
- **Models**: You can adjust the OpenAI models used in each agent file
- **Adding Agents**: Extend the network by creating new agent files following the same pattern
- **API Preferences**: Set only your preferred API credentials in the `.env` file if you don't want the fallback

## Example Queries

- Summarization: "Summarize the following paragraph: The industrial revolution began in Britain..."
- Translation: "Translate this text to French: Hello, how are you today?"
- Implicit Summarization: "Can you make this shorter? It's a long article about..."
- Implicit Translation: "Convert this to Spanish: I would like to order a coffee, please." 