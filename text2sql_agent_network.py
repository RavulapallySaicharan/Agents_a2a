from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio

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