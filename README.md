# A2A Agent Network for Text Processing

A sophisticated multi-agent system that leverages AI to process and transform text through specialized agents. This implementation demonstrates a Python-based A2A (Agent-to-Agent) network with specialized agents and an intelligent router for optimal task distribution.

## Table of Contents
- [Components](#components)
- [Features](#features)
- [Setup Instructions](#setup-instructions)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Components

### Text Processing Network
1. **Summarizer Agent**: Specialized in condensing text content using OpenAI's GPT models
2. **Translator Agent**: Handles multilingual text translation with automatic language detection

### EDA (Exploratory Data Analysis) Network
3. **Data Analysis Agent**: Performs exploratory data analysis on input DataFrames
4. **Data Visualization Agent**: Generates various visualizations from input DataFrames
5. **Data Wrangling Agent**: Cleans and preprocesses input DataFrames

### Text2SQL Network
6. **NLQ Reconstruction Agent**: Refines and reconstructs natural language queries for better SQL generation
7. **Gating Agent**: Determines if a natural language query is suitable for SQL generation
8. **Dynamic Few-Shots Agent**: Retrieves relevant few-shot examples for SQL generation
9. **SQL Generation Agent**: Converts processed queries into SQL using few-shot examples

### Network Management
10. **Agent Network Manager**: Orchestrates communication and task distribution between agents
11. **AI-Powered Router**: Uses natural language understanding to route queries to the most appropriate agent

## Features

- 🤖 Multiple specialized AI agents working in concert
- 🔄 Automatic API fallback mechanism (OpenAI → Azure OpenAI)
- 🌐 Language-agnostic translation capabilities
- 📝 Intelligent text summarization
- 📊 Advanced data analysis and visualization
- 🔄 Automated data cleaning and preprocessing
- 💾 Natural language to SQL conversion
- 🔌 Modular and extensible architecture
- ⚡ Real-time processing and response

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- OpenAI API key or Azure OpenAI credentials
- Git (for cloning the repository)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Agents_a2a.git
   cd Agents_a2a
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp env.template .env
   ```

5. Edit `.env` with your API credentials:

   **Standard OpenAI API** (primary):
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   **Azure OpenAI API** (fallback):
   ```
   AZURE_OPENAI_API_KEY=your_azure_openai_key_here
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
   AZURE_OPENAI_API_VERSION=2023-05-15
   ```

## Project Structure

```
Agents_a2a/
├── agents/
│   ├── text_processing/
│   │   ├── summarizer.py
│   │   └── translator.py
│   ├── eda/
│   │   ├── data_analysis_agent.py
│   │   ├── data_visualization_agent.py
│   │   └── data_wrangling_agent.py
│   └── text2sql/
│       ├── nlq_reconstruction_agent.py
│       ├── gating_agent.py
│       ├── dynamic_fewshots_agent.py
│       └── sql_generation_agent.py
├── networks/
│   ├── text_processing_agent.py
│   ├── eda_agent_network.py
│   └── text2sql_agent_network.py
├── tests/
│   ├── test_text_processing.py
│   ├── test_eda.py
│   └── test_text2sql.py
├── .env.template
├── requirements.txt
├── run_agent_network.py
└── README.md
```

## Usage

### Running the Complete Network

Start all components with a single command:
```bash
python run_agent_network.py
```

This will:
- Initialize all agents in their respective networks
- Start the agent network manager
- Run sample queries for each network

### Running Individual Networks

#### Text Processing Network
```bash
python networks/text_processing_agent.py
```

#### EDA Network
```bash
python networks/eda_agent_network.py
```

#### Text2SQL Network
```bash
python networks/text2sql_agent_network.py
```

### Running Individual Agents

#### Text Processing Agents
```bash
python agents/text_processing/summarizer.py
python agents/text_processing/translator.py
```

#### EDA Agents
```bash
python agents/eda/data_analysis_agent.py
python agents/eda/data_visualization_agent.py
python agents/eda/data_wrangling_agent.py
```

#### Text2SQL Agents
```bash
python agents/text2sql/nlq_reconstruction_agent.py
python agents/text2sql/gating_agent.py
python agents/text2sql/dynamic_fewshots_agent.py
python agents/text2sql/sql_generation_agent.py
```

### Running Tests
```bash
python -m pytest tests/
```

## Example Queries

### Text Processing
- Summarization: "Summarize the following paragraph: The industrial revolution began in Britain..."
- Translation: "Translate this text to French: Hello, how are you today?"
- Implicit Summarization: "Can you make this shorter? It's a long article about..."
- Implicit Translation: "Convert this to Spanish: I would like to order a coffee, please."

### EDA (Exploratory Data Analysis)
- Data Analysis: "Analyze this dataset and provide key statistics"
- Data Visualization: "Create a bar chart showing sales by region"
- Data Wrangling: "Clean this dataset by handling missing values and outliers"

### Text2SQL
- NLQ Reconstruction: "What were the total sales last month?"
- SQL Generation: "Show me the top 10 customers by revenue"
- Query Evaluation: "Is this query suitable for SQL generation?"
- Few-Shot Examples: "Find similar examples for this query"

## How It Works

1. **Query Processing Pipeline**:
   - Query received by the agent network
   - AI router analyzes query intent
   - Intelligent routing to appropriate agent
   - Processing and response generation
   - Result returned to user

2. **Summarization Process**:
   - Text analysis for key points
   - GPT-powered summarization
   - Quality checks and refinement
   - Concise output generation

3. **Translation Process**:
   - Language detection
   - Context-aware translation
   - Cultural adaptation
   - Quality verification

4. **API Fallback System**:
   - Primary: Standard OpenAI API
   - Automatic fallback to Azure OpenAI
   - Seamless transition
   - Error handling and recovery

## Customization

- **Port Configuration**: Modify ports in `.env`
- **Model Selection**: Adjust GPT models in agent files
- **Agent Extension**: Create new agents following the established pattern
- **API Configuration**: Configure preferred API in `.env`

## Troubleshooting

Common issues and solutions:

1. **API Connection Issues**:
   - Verify API keys in `.env`
   - Check internet connection
   - Ensure API quota availability

2. **Port Conflicts**:
   - Check for running processes
   - Modify ports in configuration
   - Restart the application

3. **Dependency Problems**:
   - Update pip: `pip install --upgrade pip`
   - Reinstall requirements: `pip install -r requirements.txt`
   - Check Python version compatibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Example Queries

- Summarization: "Summarize the following paragraph: The industrial revolution began in Britain..."
- Translation: "Translate this text to French: Hello, how are you today?"
- Implicit Summarization: "Can you make this shorter? It's a long article about..."
- Implicit Translation: "Convert this to Spanish: I would like to order a coffee, please." 