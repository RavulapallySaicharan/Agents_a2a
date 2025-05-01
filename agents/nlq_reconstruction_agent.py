from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import re
from typing import Dict, Any
import json

@agent(
    name="NLQ Reconstruction Agent",
    description="Refines and reconstructs natural language queries for better SQL generation",
    version="1.0.0"
)
class NLQReconstructionAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        # Common patterns for query reconstruction
        self.patterns = {
            r'^(sales|revenue|profit)(\s+last\s+year)?$': 'What were the total {0} figures for the last calendar year?',
            r'^(top|highest|best)(\s+\d+)?(\s+\w+)?$': 'What are the {0} {1} {2}?',
            r'^(compare|difference)(\s+\w+)(\s+and\s+\w+)?$': 'What is the comparison between {1} and {2}?',
            r'^(how\s+many|count)(\s+\w+)?$': 'What is the total count of {1}?',
            r'^(average|mean)(\s+\w+)?$': 'What is the average value of {1}?'
        }
    
    def _clean_query(self, query: str) -> str:
        """Clean the input query by removing extra spaces and normalizing case."""
        return ' '.join(query.lower().split())
    
    def _reconstruct_query(self, query: str) -> str:
        """Reconstruct the query using pattern matching and common transformations."""
        cleaned_query = self._clean_query(query)
        
        # Check for pattern matches
        for pattern, template in self.patterns.items():
            match = re.match(pattern, cleaned_query)
            if match:
                # Extract groups and format the template
                groups = match.groups()
                return template.format(*[g if g else '' for g in groups])
        
        # If no pattern matches, ensure the query is a proper question
        if not cleaned_query.endswith('?'):
            if cleaned_query.startswith(('what', 'how', 'when', 'where', 'who', 'why')):
                return cleaned_query + '?'
            else:
                return 'What is ' + cleaned_query + '?'
        
        return cleaned_query
    
    @skill(
        name="Reconstruct NLQ",
        description="Refine and reconstruct a natural language query",
        tags=["nlq", "reconstruction", "query", "text2sql"]
    )
    def reconstruct_nlq(self, query: str) -> Dict[str, Any]:
        """Reconstruct the natural language query for better clarity and SQL generation."""
        try:
            reconstructed = self._reconstruct_query(query)
            
            return {
                "original_query": query,
                "reconstructed_query": reconstructed,
                "transformation_applied": reconstructed != query.lower()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests for NLQ reconstruction."""
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        if isinstance(content, dict) and "query" in content:
            query = content["query"]
        elif isinstance(content, str):
            query = content
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "dataType": "data",
                        "message": "Please provide a natural language query to reconstruct."
                    }
                }
            )
            return task
        
        # Reconstruct the query
        reconstruction_results = self.reconstruct_nlq(query)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "json",
                "dataType": "data",
                "message": json.dumps(reconstruction_results)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    import os
    
    # Get port from environment or use default
    port = int(os.getenv("NLQ_RECONSTRUCTION_PORT", 5006))
    
    # Create and run the server
    agent = NLQReconstructionAgent()
    run_server(agent, port=port)
    
    # Example usage
    if __name__ == "__main__":
        # Create agent instance
        agent = NLQReconstructionAgent()
        
        # Test queries
        test_queries = [
            "sales last year",
            "top 5 customers",
            "compare revenue and profit",
            "how many orders",
            "average order value"
        ]
        
        print("\nTesting NLQ Reconstruction:")
        for query in test_queries:
            result = agent.reconstruct_nlq(query)
            print(f"\nOriginal: {result['original_query']}")
            print(f"Reconstructed: {result['reconstructed_query']}") 