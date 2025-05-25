from agent_creation_scripts.create_agent_script import create_agent_file

# # Create a Text Summarization Agent
# agent_path = create_agent_file(
#     agent_name="Text2SQL",
#     agent_url="http://10.135.80.150:5057/text_to_sql_agent",
#     agent_inputs=["userInput"],
#     agent_description="Creates sql from user nlq",
#     agent_goal="Generate sql based on the user nlq",
#     agent_tags=["nlq", "sql", "text2sql"],
#     agent_port=5012,
#     overwrite=True
# )

# Create a Sentiment Analysis Agent
create_agent_file(
    agent_name="Sentiment Analyzer",
    agent_inputs=["text"],
    agent_description="Analyzes text to determine sentiment and emotional tone",
    agent_goal="Provide accurate sentiment analysis and emotional insights from text",
    agent_tags=["nlp", "sentiment-analysis", "emotion-detection"],
    agent_port=5013,
    overwrite=True
)


create_agent_file(
    agent_name="Product Description Generator",
    agent_inputs=["product_name", "features", "category"],
    agent_description="Generates compelling product descriptions for e-commerce listings",
    agent_goal="Create persuasive and SEO-friendly product descriptions using given product data",
    agent_tags=["ecommerce", "copywriting", "product-description"],
    agent_port=5014,
    overwrite=True
)


create_agent_file(
    agent_name="Summarizer",
    agent_inputs=["text"],
    agent_description="Summarizes text",
    agent_goal="Create a concise summary of the given text",
    agent_tags=["summarization", "text-summary", "summary"],
    agent_port=5015,
    overwrite=True
)