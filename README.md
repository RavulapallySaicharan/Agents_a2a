# A2A Agent Network

A sophisticated multi-agent system that leverages AI to process and transform text through specialized agents. This implementation demonstrates a Python-based A2A (Agent-to-Agent) network with specialized agents and an intelligent router for optimal task distribution.

## Components

### Core Networks
1. **Text Processing Network**
   - Summarizer Agent: Condenses text using GPT models
   - Translator Agent: Handles multilingual translation

2. **EDA (Exploratory Data Analysis) Network**
   - Data Analysis Agent: Performs EDA on DataFrames
   - Data Visualization Agent: Generates visualizations
   - Data Wrangling Agent: Cleans and preprocesses data

3. **Text2SQL Network**
   - NLQ Reconstruction Agent: Refines natural language queries
   - Gating Agent: Evaluates query suitability
   - Dynamic Few-Shots Agent: Retrieves relevant examples
   - SQL Generation Agent: Converts queries to SQL

4. **Network Management**
   - Agent Network Manager: Orchestrates communication
   - AI-Powered Router: Routes queries to appropriate agents

## Features

- 🤖 Multiple specialized AI agents
- 🔄 Automatic API fallback (OpenAI → Azure OpenAI)
- 🌐 Language-agnostic translation
- 📝 Intelligent text summarization
- 📊 Advanced data analysis and visualization
- 💾 Natural language to SQL conversion
- 🔌 Modular architecture

## Quick Start

1. **Setup**
   ```bash
   git clone https://github.com/yourusername/Agents_a2a.git
   cd Agents_a2a
   python -m venv venv
   # Windows: .\venv\Scripts\activate
   # Unix/MacOS: source venv/bin/activate
   pip install -r requirements.txt
   cp env.template .env
   ```

2. **Configure Environment**
   ```
   # Standard OpenAI API (primary)
   OPENAI_API_KEY=your_openai_api_key_here

   # Azure OpenAI API (fallback)
   AZURE_OPENAI_API_KEY=your_azure_openai_key_here
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
   AZURE_OPENAI_API_VERSION=2023-05-15
   ```

3. **Run the Network**
   ```bash
   # Run complete network
   python run_agent_network.py

   # Run individual networks
   python networks/text_processing_agent.py
   python networks/eda_agent_network.py
   python networks/text2sql_agent_network.py
   ```

## Project Structure
```
Agents_a2a/
├── agents/
│   ├── text_processing/
│   ├── eda/
│   └── text2sql/
├── networks/
├── tests/
├── .env.template
├── requirements.txt
└── run_agent_network.py
```

## Agent Creation and Management

### Guideline Agent Template
The `guideline_agent.py` serves as a template for creating new agents:
- Provides a standardized structure for agent implementation
- Includes placeholders for customization
- Demonstrates best practices for agent development
- Features clear documentation and error handling

### Workflow Agent Creation
The `workflow_agent_creation_script.py` generates workflow-based multi-agent systems:
- Supports linear, parallel, and mixed workflow patterns
- Automatically generates agent network setup
- Handles agent configuration validation
- Creates workflow orchestration code
- Example usage:
  ```python
  # Linear workflow
  linear_pattern = "agent1->agent2->agent3"
  # Mixed workflow with parallel processing
  mixed_pattern = "agent1->agent2,agent3->agent4"
  ```

### Router Agent Creation
The `router_agent_creation_script.py` generates intelligent routing systems:
- Creates AI-powered routers for multi-agent networks
- Implements OpenAI-based routing decisions
- Handles agent discovery and management
- Provides confidence scoring for routing decisions
- Features automatic API fallback mechanism

## Example Queries

### Text Processing
- "Summarize the following paragraph: The industrial revolution began in Britain..."
- "Translate this text to French: Hello, how are you today?"

### EDA
- "Analyze this dataset and provide key statistics"
- "Create a bar chart showing sales by region"

### Text2SQL
- "What were the total sales last month?"
- "Show me the top 10 customers by revenue"

## Development

### Creating New Agents
Use the `guideline_agent.py` template to create new agents:
```bash
python agents/guideline_agent.py
```

### Testing
```bash
python -m pytest tests/
```

## Troubleshooting

1. **API Issues**
   - Verify API keys in `.env`
   - Check internet connection
   - Ensure API quota availability

2. **Port Conflicts**
   - Check running processes
   - Modify ports in configuration

3. **Dependencies**
   - Update pip: `pip install --upgrade pip`
   - Reinstall requirements: `pip install -r requirements.txt`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request 