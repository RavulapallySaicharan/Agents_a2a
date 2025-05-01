from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import pandas as pd
import numpy as np
from typing import Dict, Any
import json

@agent(
    name="Data Analysis Agent",
    description="Performs exploratory data analysis (EDA) on input DataFrames",
    version="1.0.0"
)
class DataAnalysisAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
    
    @skill(
        name="Analyze DataFrame",
        description="Perform exploratory data analysis on a pandas DataFrame",
        tags=["data", "analysis", "eda", "statistics"]
    )
    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive EDA on the input DataFrame."""
        try:
            # Basic DataFrame information
            info = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum()
            }
            
            # Summary statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            stats = {
                "numeric_summary": df[numeric_cols].describe().to_dict() if len(numeric_cols) > 0 else {},
                "categorical_summary": {
                    col: df[col].value_counts().to_dict() for col in categorical_cols
                } if len(categorical_cols) > 0 else {}
            }
            
            # Missing values analysis
            missing_values = df.isnull().sum()
            missing_percentage = (missing_values / len(df)) * 100
            missing_analysis = {
                "missing_counts": missing_values.to_dict(),
                "missing_percentages": missing_percentage.to_dict()
            }
            
            # Correlation analysis for numeric columns
            correlation = df[numeric_cols].corr().to_dict() if len(numeric_cols) > 0 else {}
            
            # Basic insights
            insights = []
            if len(numeric_cols) > 0:
                # Find top correlated features
                corr_matrix = df[numeric_cols].corr().abs()
                upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                top_correlations = []
                for col in upper.columns:
                    top_corr = upper[col].nlargest(3)
                    for idx, val in top_corr.items():
                        if val > 0.5:  # Only include strong correlations
                            top_correlations.append(f"{col} and {idx}: {val:.2f}")
                if top_correlations:
                    insights.append("Top correlated features:")
                    insights.extend(top_correlations)
            
            return {
                "info": info,
                "statistics": stats,
                "missing_analysis": missing_analysis,
                "correlation": correlation,
                "insights": insights
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests for data analysis."""
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        if isinstance(content, dict) and "dataframe" in content:
            df = pd.DataFrame(content["dataframe"])
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "dataType": "data",
                        "message": "Please provide a pandas DataFrame for analysis."
                    }
                }
            )
            return task
        
        # Perform analysis
        analysis_results = self.analyze_dataframe(df)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "json",
                "dataType": "data",
                "message": json.dumps(analysis_results, default=str)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    import os
    
    # Get port from environment or use default
    port = int(os.getenv("DATA_ANALYSIS_PORT", 5003))
    
    # Create and run the server
    agent = DataAnalysisAgent()
    run_server(agent, port=port)
    
    # Example usage
    if __name__ == "__main__":
        # Create sample DataFrame
        df = pd.DataFrame({
            'A': np.random.normal(0, 1, 100),
            'B': np.random.normal(0, 1, 100),
            'C': ['cat', 'dog', 'bird'] * 33 + ['cat'],
            'D': np.random.choice([1, 2, 3, None], 100)
        })
        
        # Create agent instance
        agent = DataAnalysisAgent()
        
        # Perform analysis
        results = agent.analyze_dataframe(df)
        print(json.dumps(results, indent=2)) 