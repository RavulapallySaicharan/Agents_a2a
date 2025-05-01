from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import re
from typing import Dict, Any, Tuple
import json

@agent(
    name="Gating Agent",
    description="Determines if a natural language query is suitable for SQL generation",
    version="1.0.0"
)
class GatingAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        # Define patterns for valid and invalid queries
        self.valid_patterns = [
            r'what.*(sales|revenue|profit|orders|customers|products)',
            r'how.*many.*(sales|orders|customers|products)',
            r'compare.*(sales|revenue|profit)',
            r'top.*\d+.*(customers|products|sales)',
            r'average.*(order|sale|revenue)',
            r'sum.*(sales|revenue|profit)',
            r'count.*(orders|customers|products)',
            r'list.*(customers|products|orders)',
            r'find.*(customers|products|orders)',
            r'show.*(sales|revenue|profit)'
        ]
        
        self.invalid_patterns = [
            r'how.*to.*(create|update|delete|insert)',
            r'can.*you.*(help|explain|tell)',
            r'what.*is.*(the|a|an)',
            r'why.*(is|are|do|does)',
            r'when.*(is|are|do|does)',
            r'where.*(is|are|do|does)',
            r'who.*(is|are|do|does)'
        ]
    
    def _calculate_confidence(self, query: str) -> Tuple[float, str]:
        """Calculate confidence score and provide reasoning for the decision."""
        query = query.lower()
        
        # Check for invalid patterns
        for pattern in self.invalid_patterns:
            if re.search(pattern, query):
                return 0.0, "Query appears to be a general question or request for explanation"
        
        # Check for valid patterns
        valid_matches = 0
        for pattern in self.valid_patterns:
            if re.search(pattern, query):
                valid_matches += 1
        
        # Calculate confidence based on matches
        if valid_matches > 0:
            confidence = min(0.5 + (valid_matches * 0.1), 1.0)
            reason = f"Query matches {valid_matches} valid pattern(s) for SQL generation"
        else:
            confidence = 0.3
            reason = "Query doesn't match any known patterns but might be valid"
        
        # Additional checks
        if '?' not in query:
            confidence *= 0.8
            reason += " (Query is not in question format)"
        
        if len(query.split()) < 3:
            confidence *= 0.7
            reason += " (Query is too short)"
        
        return confidence, reason
    
    @skill(
        name="Evaluate Query",
        description="Evaluate if a natural language query is suitable for SQL generation",
        tags=["nlq", "gating", "evaluation", "text2sql"]
    )
    def evaluate_query(self, query: str) -> Dict[str, Any]:
        """Evaluate if the query is suitable for SQL generation."""
        try:
            confidence, reason = self._calculate_confidence(query)
            
            return {
                "query": query,
                "proceed": confidence >= 0.5,
                "confidence": confidence,
                "reason": reason
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests for query evaluation."""
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
                        "message": "Please provide a natural language query to evaluate."
                    }
                }
            )
            return task
        
        # Evaluate the query
        evaluation_results = self.evaluate_query(query)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "json",
                "dataType": "data",
                "message": json.dumps(evaluation_results)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    import os
    
    # Get port from environment or use default
    port = int(os.getenv("GATING_PORT", 5007))
    
    # Create and run the server
    agent = GatingAgent()
    run_server(agent, port=port)
    
    # Example usage
    if __name__ == "__main__":
        # Create agent instance
        agent = GatingAgent()
        
        # Test queries
        test_queries = [
            "What were the total sales last month?",
            "How to create a new customer?",
            "Show me top 5 products by revenue",
            "What is the meaning of life?",
            "Compare sales between regions"
        ]
        
        print("\nTesting Query Evaluation:")
        for query in test_queries:
            result = agent.evaluate_query(query)
            print(f"\nQuery: {result['query']}")
            print(f"Proceed: {result['proceed']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Reason: {result['reason']}") 