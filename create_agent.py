from agent_creation_scripts.create_agent_script import create_agent_file

# Create a Text Summarization Agent
summarization_agent_path = create_agent_file(
    agent_name="Text Summarizer",
    # agent_url="https://api.openai.com/v1/chat/completions",
    agent_inputs=["text"],
    agent_skills=["summarize", "extract_key_points", "maintain_context"],
    agent_description="Creates concise summaries of long text while preserving key information",
    agent_goal="Generate accurate and coherent summaries of input text",
    agent_tags=["nlp", "summarization", "text-processing"],
    agent_port=5012,
    overwrite=True
)

# Create a Sentiment Analysis Agent
sentiment_agent_path = create_agent_file(
    agent_name="Sentiment Analyzer",
    # agent_url="https://api.openai.com/v1/chat/completions",
    agent_inputs=["text"],
    agent_skills=["analyze_sentiment", "detect_emotions", "identify_keywords"],
    agent_description="Analyzes text to determine sentiment and emotional tone",
    agent_goal="Provide accurate sentiment analysis and emotional insights from text",
    agent_tags=["nlp", "sentiment-analysis", "emotion-detection"],
    agent_port=5013,
    overwrite=True
)