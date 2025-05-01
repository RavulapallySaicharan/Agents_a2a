from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, Any, List
import json

@agent(
    name="Data Visualization Agent",
    description="Generates various visualizations from input DataFrames",
    version="1.0.0"
)
class DataVisualizationAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        # Set style for all plots
        plt.style.use('seaborn')
    
    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_str
    
    @skill(
        name="Generate Visualizations",
        description="Generate various visualizations from a pandas DataFrame",
        tags=["data", "visualization", "plots", "charts"]
    )
    def generate_visualizations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a comprehensive set of visualizations from the input DataFrame."""
        try:
            visualizations = {}
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            # 1. Distribution plots for numeric columns
            if len(numeric_cols) > 0:
                for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
                    
                    # Histogram with KDE
                    sns.histplot(data=df, x=col, kde=True, ax=ax1)
                    ax1.set_title(f'Distribution of {col}')
                    
                    # Box plot
                    sns.boxplot(data=df, y=col, ax=ax2)
                    ax2.set_title(f'Box Plot of {col}')
                    
                    visualizations[f'distribution_{col}'] = self._fig_to_base64(fig)
            
            # 2. Correlation heatmap for numeric columns
            if len(numeric_cols) > 1:
                fig, ax = plt.subplots(figsize=(10, 8))
                corr_matrix = df[numeric_cols].corr()
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
                ax.set_title('Correlation Heatmap')
                visualizations['correlation_heatmap'] = self._fig_to_base64(fig)
            
            # 3. Bar plots for categorical columns
            if len(categorical_cols) > 0:
                for col in categorical_cols[:3]:  # Limit to first 3 categorical columns
                    fig, ax = plt.subplots(figsize=(10, 6))
                    value_counts = df[col].value_counts()
                    sns.barplot(x=value_counts.index, y=value_counts.values, ax=ax)
                    ax.set_title(f'Distribution of {col}')
                    ax.tick_params(axis='x', rotation=45)
                    visualizations[f'barplot_{col}'] = self._fig_to_base64(fig)
            
            # 4. Pair plot for numeric columns (limited to first 5 columns)
            if len(numeric_cols) > 1:
                subset_cols = numeric_cols[:5]
                fig = sns.pairplot(df[subset_cols])
                visualizations['pairplot'] = self._fig_to_base64(fig.fig)
            
            # 5. Missing values visualization
            if df.isnull().any().any():
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.heatmap(df.isnull(), yticklabels=False, cbar=False, cmap='viridis', ax=ax)
                ax.set_title('Missing Values Heatmap')
                visualizations['missing_values'] = self._fig_to_base64(fig)
            
            return {
                "visualizations": visualizations,
                "metadata": {
                    "numeric_columns": numeric_cols.tolist(),
                    "categorical_columns": categorical_cols.tolist(),
                    "total_plots": len(visualizations)
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests for data visualization."""
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
                        "message": "Please provide a pandas DataFrame for visualization."
                    }
                }
            )
            return task
        
        # Generate visualizations
        viz_results = self.generate_visualizations(df)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "json",
                "dataType": "data",
                "message": json.dumps(viz_results, default=str)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    import os
    
    # Get port from environment or use default
    port = int(os.getenv("DATA_VISUALIZATION_PORT", 5004))
    
    # Create and run the server
    agent = DataVisualizationAgent()
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
        agent = DataVisualizationAgent()
        
        # Generate visualizations
        results = agent.generate_visualizations(df)
        print(f"Generated {results['metadata']['total_plots']} visualizations") 