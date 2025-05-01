from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
from typing import Dict, Any, List
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@agent(
    name="Dynamic Few-Shots Agent",
    description="Retrieves relevant few-shot examples for SQL generation",
    version="1.0.0"
)
class DynamicFewshotsAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        # Initialize example database
        self.examples = [
            {
                "nlq": "What were the total sales last month?",
                "sql": "SELECT SUM(amount) FROM sales WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
                "category": "aggregation"
            },
            {
                "nlq": "Show me top 5 customers by revenue",
                "sql": "SELECT customer_name, SUM(amount) as total_revenue FROM sales GROUP BY customer_name ORDER BY total_revenue DESC LIMIT 5",
                "category": "ranking"
            },
            {
                "nlq": "What is the average order value by region?",
                "sql": "SELECT region, AVG(order_value) as avg_order_value FROM orders GROUP BY region",
                "category": "aggregation"
            },
            {
                "nlq": "Compare sales between this year and last year",
                "sql": """
                    SELECT 
                        DATE_TRUNC('year', sale_date) as year,
                        SUM(amount) as total_sales
                    FROM sales
                    WHERE sale_date >= CURRENT_DATE - INTERVAL '2 years'
                    GROUP BY DATE_TRUNC('year', sale_date)
                    ORDER BY year
                """,
                "category": "comparison"
            },
            {
                "nlq": "List all products with stock below 10 units",
                "sql": "SELECT product_name, stock_quantity FROM products WHERE stock_quantity < 10",
                "category": "filtering"
            },
            {
                "nlq": "What is the total revenue by product category?",
                "sql": """
                    SELECT 
                        p.category,
                        SUM(s.amount) as total_revenue
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    GROUP BY p.category
                """,
                "category": "aggregation"
            },
            {
                "nlq": "Find customers who haven't made a purchase in 6 months",
                "sql": """
                    SELECT customer_name
                    FROM customers c
                    WHERE NOT EXISTS (
                        SELECT 1 FROM sales s
                        WHERE s.customer_id = c.id
                        AND s.sale_date >= CURRENT_DATE - INTERVAL '6 months'
                    )
                """,
                "category": "filtering"
            }
        ]
        
        # Initialize vectorizer for similarity matching
        self.vectorizer = TfidfVectorizer()
        self._update_vectorizer()
    
    def _update_vectorizer(self):
        """Update the TF-IDF vectorizer with current examples."""
        self.vectorizer.fit([ex["nlq"] for ex in self.examples])
    
    def _get_similar_examples(self, query: str, n: int = 3) -> List[Dict[str, Any]]:
        """Find the most similar examples to the query using TF-IDF and cosine similarity."""
        # Transform query and examples
        query_vec = self.vectorizer.transform([query])
        example_vecs = self.vectorizer.transform([ex["nlq"] for ex in self.examples])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vec, example_vecs)[0]
        
        # Get top n similar examples
        top_indices = np.argsort(similarities)[-n:][::-1]
        
        return [
            {
                **self.examples[i],
                "similarity_score": float(similarities[i])
            }
            for i in top_indices
        ]
    
    @skill(
        name="Get Few-Shots",
        description="Retrieve relevant few-shot examples for SQL generation",
        tags=["nlq", "few-shots", "examples", "text2sql"]
    )
    def get_fewshots(self, query: str, n_examples: int = 3) -> Dict[str, Any]:
        """Retrieve relevant few-shot examples for the given query."""
        try:
            similar_examples = self._get_similar_examples(query, n_examples)
            
            return {
                "query": query,
                "examples": similar_examples,
                "total_examples": len(similar_examples)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests for few-shot examples."""
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        if isinstance(content, dict):
            query = content.get("query", "")
            n_examples = content.get("n_examples", 3)
        elif isinstance(content, str):
            query = content
            n_examples = 3
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "dataType": "data",
                        "message": "Please provide a natural language query to find similar examples."
                    }
                }
            )
            return task
        
        # Get few-shot examples
        fewshots_results = self.get_fewshots(query, n_examples)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "json",
                "dataType": "data",
                "message": json.dumps(fewshots_results)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    import os
    
    # Get port from environment or use default
    port = int(os.getenv("FEWSHOTS_PORT", 5008))
    
    # Create and run the server
    agent = DynamicFewshotsAgent()
    run_server(agent, port=port)
    
    # Example usage
    if __name__ == "__main__":
        # Create agent instance
        agent = DynamicFewshotsAgent()
        
        # Test queries
        test_queries = [
            "What were the total sales last month?",
            "Show me top 5 customers by revenue",
            "Compare sales between regions"
        ]
        
        print("\nTesting Few-Shot Example Retrieval:")
        for query in test_queries:
            result = agent.get_fewshots(query)
            print(f"\nQuery: {result['query']}")
            print("\nSimilar examples:")
            for ex in result['examples']:
                print(f"\nNLQ: {ex['nlq']}")
                print(f"SQL: {ex['sql']}")
                print(f"Category: {ex['category']}")
                print(f"Similarity: {ex['similarity_score']:.2f}") 