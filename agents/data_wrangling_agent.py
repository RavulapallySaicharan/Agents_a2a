from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from typing import Dict, Any, Tuple
import json

@agent(
    name="Data Wrangling Agent",
    description="Cleans and preprocesses input DataFrames",
    version="1.0.0"
)
class DataWranglingAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        self.numeric_imputer = SimpleImputer(strategy='mean')
        self.categorical_imputer = SimpleImputer(strategy='most_frequent')
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    
    def _identify_column_types(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.Index]:
        """Identify numeric and categorical columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        return numeric_cols, categorical_cols
    
    @skill(
        name="Clean and Preprocess",
        description="Clean and preprocess a pandas DataFrame",
        tags=["data", "cleaning", "preprocessing", "wrangling"]
    )
    def clean_and_preprocess(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Clean and preprocess the input DataFrame."""
        try:
            # Make a copy to avoid modifying the original
            df_cleaned = df.copy()
            
            # Identify column types
            numeric_cols, categorical_cols = self._identify_column_types(df_cleaned)
            
            # Track preprocessing steps
            preprocessing_steps = []
            
            # 1. Handle missing values
            if df_cleaned.isnull().any().any():
                # Numeric columns: impute with mean
                if len(numeric_cols) > 0:
                    df_cleaned[numeric_cols] = self.numeric_imputer.fit_transform(df_cleaned[numeric_cols])
                    preprocessing_steps.append("Imputed missing values in numeric columns with mean")
                
                # Categorical columns: impute with most frequent
                if len(categorical_cols) > 0:
                    df_cleaned[categorical_cols] = self.categorical_imputer.fit_transform(df_cleaned[categorical_cols])
                    preprocessing_steps.append("Imputed missing values in categorical columns with most frequent value")
            
            # 2. Handle categorical variables
            if len(categorical_cols) > 0:
                # One-hot encode categorical variables
                encoded_data = self.encoder.fit_transform(df_cleaned[categorical_cols])
                encoded_cols = self.encoder.get_feature_names_out(categorical_cols)
                
                # Create DataFrame with encoded columns
                encoded_df = pd.DataFrame(encoded_data, columns=encoded_cols, index=df_cleaned.index)
                
                # Drop original categorical columns and add encoded ones
                df_cleaned = df_cleaned.drop(columns=categorical_cols)
                df_cleaned = pd.concat([df_cleaned, encoded_df], axis=1)
                
                preprocessing_steps.append(f"One-hot encoded {len(categorical_cols)} categorical columns into {len(encoded_cols)} binary columns")
            
            # 3. Scale numeric variables
            if len(numeric_cols) > 0:
                df_cleaned[numeric_cols] = self.scaler.fit_transform(df_cleaned[numeric_cols])
                preprocessing_steps.append("Scaled numeric columns using StandardScaler")
            
            # 4. Remove duplicates
            initial_rows = len(df_cleaned)
            df_cleaned = df_cleaned.drop_duplicates()
            if len(df_cleaned) < initial_rows:
                preprocessing_steps.append(f"Removed {initial_rows - len(df_cleaned)} duplicate rows")
            
            # 5. Remove constant columns
            constant_cols = [col for col in df_cleaned.columns if df_cleaned[col].nunique() == 1]
            if constant_cols:
                df_cleaned = df_cleaned.drop(columns=constant_cols)
                preprocessing_steps.append(f"Removed {len(constant_cols)} constant columns")
            
            return {
                "cleaned_dataframe": df_cleaned.to_dict(),
                "preprocessing_steps": preprocessing_steps,
                "metadata": {
                    "original_shape": df.shape,
                    "cleaned_shape": df_cleaned.shape,
                    "numeric_columns": numeric_cols.tolist(),
                    "categorical_columns": categorical_cols.tolist(),
                    "removed_columns": constant_cols
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests for data wrangling."""
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
                        "message": "Please provide a pandas DataFrame for cleaning and preprocessing."
                    }
                }
            )
            return task
        
        # Clean and preprocess the data
        wrangling_results = self.clean_and_preprocess(df)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "json",
                "dataType": "data",
                "message": json.dumps(wrangling_results, default=str)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    import os
    
    # Get port from environment or use default
    port = int(os.getenv("DATA_WRANGLING_PORT", 5005))
    
    # Create and run the server
    agent = DataWranglingAgent()
    run_server(agent, port=port)
    
    # Example usage
    if __name__ == "__main__":
        # Create sample DataFrame
        df = pd.DataFrame({
            'A': np.random.normal(0, 1, 100),
            'B': np.random.normal(0, 1, 100),
            'C': ['cat', 'dog', 'bird'] * 33 + ['cat'],
            'D': np.random.choice([1, 2, 3, None], 100),
            'E': [1] * 100  # Constant column
        })
        
        # Create agent instance
        agent = DataWranglingAgent()
        
        # Clean and preprocess
        results = agent.clean_and_preprocess(df)
        print("\nPreprocessing steps:")
        for step in results['preprocessing_steps']:
            print(f"- {step}") 