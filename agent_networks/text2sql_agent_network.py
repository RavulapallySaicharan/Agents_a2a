from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio
from typing import Dict, List, Optional

class Text2SQLAgentNetwork:
    def __init__(self):
        self.network = AgentNetwork()
        self.network.add("nlq_reconstruction", "http://localhost:5007")
        self.network.add("gating", "http://localhost:5008")
        self.network.add("dynamic_few_shots", "http://localhost:5009")
        self.network.add("sql_generation", "http://localhost:5010")
        
        # Create a router
        self.router = AIAgentRouter(
            llm_client=self.network.get_agent("nlq_reconstruction"),
            agent_network=self.network
        )
        
        # Define the text-to-SQL workflow
        self.flow = Flow(agent_network=self.network, router=self.router, name="Text-to-SQL Workflow")
        
        # Step 1: NLQ Reconstruction
        self.flow.ask("nlq_reconstruction", "Reconstruct the natural language query: {query}")
        
        # Step 2: Gating
        self.flow.ask("gating", "Determine if the query requires SQL generation: {reconstructed_query}")
        
        # Step 3: Dynamic Few Shots
        self.flow.ask("dynamic_few_shots", "Generate relevant few-shot examples for: {reconstructed_query}")
        
        # Step 4: SQL Generation
        self.flow.ask("sql_generation", "Generate SQL query based on: {reconstructed_query} and {few_shots}")

    async def process_query(self, query: str, schema: str) -> Dict:
        """Process a natural language query and convert it to SQL."""
        try:
            result = await self.flow.run({
                "query": query,
                "schema": schema
            })
            
            return {
                "agent": "text2sql",
                "confidence": 1.0,  # You might want to implement actual confidence scoring
                "response": result
            }
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}")

    def list_agents(self) -> List[Dict]:
        """List all available agents in the network."""
        return [
            {
                "name": "NLQ Reconstruction",
                "description": "Reconstructs natural language queries for better understanding"
            },
            {
                "name": "Gating",
                "description": "Determines if the query requires SQL generation"
            },
            {
                "name": "Dynamic Few Shots",
                "description": "Generates relevant few-shot examples for SQL generation"
            },
            {
                "name": "SQL Generation",
                "description": "Converts the processed query into SQL"
            }
        ]

async def main():
    # Create an agent network
    network = AgentNetwork()
    network.add("nlq_reconstruction", "http://localhost:5007")
    network.add("gating", "http://localhost:5008")
    network.add("dynamic_few_shots", "http://localhost:5009")
    network.add("sql_generation", "http://localhost:5010")
    
    # Create a router
    router = AIAgentRouter(
        llm_client=network.get_agent("nlq_reconstruction"),  # Using nlq_reconstruction as LLM for routing
        agent_network=network
    )
    
    # Define the text-to-SQL workflow
    flow = Flow(agent_network=network, router=router, name="Text-to-SQL Workflow")
    
    # Step 1: NLQ Reconstruction
    flow.ask("nlq_reconstruction", "Reconstruct the natural language query: {query}")
    
    # Step 2: Gating
    flow.ask("gating", "Determine if the query requires SQL generation: {reconstructed_query}")
    
    # Step 3: Dynamic Few Shots
    flow.ask("dynamic_few_shots", "Generate relevant few-shot examples for: {reconstructed_query}")
    
    # Step 4: SQL Generation
    flow.ask("sql_generation", "Generate SQL query based on: {reconstructed_query} and {few_shots}")
    
    # Execute the workflow with initial context
    result = await flow.run({
        "query": "Show me all customers who made purchases in the last month",
        "schema": "customers(id, name, email), purchases(id, customer_id, amount, date)"
    })
    
    print("Workflow result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())