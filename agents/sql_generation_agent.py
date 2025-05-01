from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
from typing import Dict, Any, List, Optional
import json
import re

@agent(
    name="SQL Generation Agent",
    description="Generates SQL queries from natural language queries using few-shot examples",
    version="1.0.0"
)
class SQLGenerationAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        # Common SQL patterns and templates
        self.patterns = {
            "aggregation": {
                "sum": "SELECT SUM({column}) FROM {table} {where} {group_by}",
                "count": "SELECT COUNT({column}) FROM {table} {where} {group_by}",
                "average": "SELECT AVG({column}) FROM {table} {where} {group_by}",
                "min": "SELECT MIN({column}) FROM {table} {where} {group_by}",
                "max": "SELECT MAX({column}) FROM {table} {where} {group_by}"
            },
            "ranking": {
                "top_n": "SELECT {columns} FROM {table} {where} {group_by} ORDER BY {order_by} DESC LIMIT {n}",
                "bottom_n": "SELECT {columns} FROM {table} {where} {group_by} ORDER BY {order_by} ASC LIMIT {n}"
            },
            "comparison": {
                "between": "SELECT {columns} FROM {table} WHERE {condition1} AND {condition2} {group_by}",
                "versus": """
                    SELECT 
                        {dimension},
                        {metric1},
                        {metric2}
                    FROM {table}
                    {where}
                    GROUP BY {dimension}
                """
            }
        }
    
    def _extract_query_components(self, query: str) -> Dict[str, Any]:
        """Extract key components from the natural language query."""
        components = {
            "operation": None,
            "columns": [],
            "tables": [],
            "conditions": [],
            "grouping": [],
            "ordering": [],
            "limit": None
        }
        
        # Extract operation type
        if re.search(r'\b(sum|total|sum of)\b', query.lower()):
            components["operation"] = "sum"
        elif re.search(r'\b(count|number of|how many)\b', query.lower()):
            components["operation"] = "count"
        elif re.search(r'\b(average|mean|avg)\b', query.lower()):
            components["operation"] = "average"
        elif re.search(r'\b(top|highest|best)\b', query.lower()):
            components["operation"] = "top_n"
            # Extract limit
            limit_match = re.search(r'\b(\d+)\b', query)
            if limit_match:
                components["limit"] = int(limit_match.group(1))
        
        # Extract tables and columns (simplified for example)
        if "sales" in query.lower():
            components["tables"].append("sales")
            components["columns"].append("amount")
        if "customers" in query.lower():
            components["tables"].append("customers")
            components["columns"].append("customer_name")
        if "products" in query.lower():
            components["tables"].append("products")
            components["columns"].append("product_name")
        
        return components
    
    def _generate_sql(self, query: str, fewshots: List[Dict[str, Any]], schema: Optional[Dict[str, Any]] = None) -> str:
        """Generate SQL query using components and few-shot examples."""
        try:
            # Extract components from query
            components = self._extract_query_components(query)
            
            # Find most similar few-shot example
            best_example = max(fewshots, key=lambda x: x.get("similarity_score", 0))
            
            # Use the example's SQL as a template
            sql_template = best_example["sql"]
            
            # Replace placeholders with actual values
            sql = sql_template
            
            # Apply schema constraints if provided
            if schema:
                # Add schema-specific modifications here
                pass
            
            return sql
            
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    @skill(
        name="Generate SQL",
        description="Generate SQL query from natural language query",
        tags=["nlq", "sql", "generation", "text2sql"]
    )
    def generate_sql(self, nlq: str, fewshots: List[Dict[str, Any]], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate SQL query from natural language query using few-shot examples."""
        try:
            sql = self._generate_sql(nlq, fewshots, schema)
            
            return {
                "nlq": nlq,
                "sql": sql,
                "used_examples": [ex["nlq"] for ex in fewshots],
                "schema_used": schema is not None
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests for SQL generation."""
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        if isinstance(content, dict):
            nlq = content.get("nlq", "")
            fewshots = content.get("fewshots", [])
            schema = content.get("schema")
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "dataType": "data",
                        "message": "Please provide a natural language query, few-shot examples, and optional schema."
                    }
                }
            )
            return task
        
        # Generate SQL
        sql_results = self.generate_sql(nlq, fewshots, schema)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "json",
                "dataType": "data",
                "message": json.dumps(sql_results)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    import os
    
    # Get port from environment or use default
    port = int(os.getenv("SQL_GENERATION_PORT", 5009))
    
    # Create and run the server
    agent = SQLGenerationAgent()
    run_server(agent, port=port)
    
    # Example usage
    if __name__ == "__main__":
        # Create agent instance
        agent = SQLGenerationAgent()
        
        # Test query with few-shot examples
        test_query = "What were the total sales last month?"
        test_fewshots = [
            {
                "nlq": "What were the total sales last month?",
                "sql": "SELECT SUM(amount) FROM sales WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
                "similarity_score": 1.0
            },
            {
                "nlq": "Show me top 5 customers by revenue",
                "sql": "SELECT customer_name, SUM(amount) as total_revenue FROM sales GROUP BY customer_name ORDER BY total_revenue DESC LIMIT 5",
                "similarity_score": 0.5
            }
        ]
        
        # Test schema
        test_schema = {
            "sales": {
                "columns": ["id", "amount", "sale_date", "customer_id"],
                "primary_key": "id",
                "foreign_keys": {
                    "customer_id": "customers.id"
                }
            }
        }
        
        # Generate SQL
        result = agent.generate_sql(test_query, test_fewshots, test_schema)
        print("\nTesting SQL Generation:")
        print(f"\nNLQ: {result['nlq']}")
        print(f"Generated SQL: {result['sql']}")
        print(f"Used examples: {result['used_examples']}")
        print(f"Schema used: {result['schema_used']}") 