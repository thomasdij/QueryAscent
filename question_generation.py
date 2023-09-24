from database_and_synonym_manager import set_database_connection, set_schema, set_API_key
from execution_manager import run_sql, prompt_on_df
import pandas as pd
import ast


def sample_data_from_schema(df_schema: pd.DataFrame, database_url: str) -> pd.DataFrame:
    # Initialize new columns for storing sample values
    df_schema['sample_value_1'] = None
    df_schema['sample_value_2'] = None
    df_schema['sample_value_3'] = None

    for idx, row in df_schema.iterrows():
        table = row['table_name']
        column = row['column_name']

        # Create the SQL query to fetch up to 3 sample values
        sql = f'SELECT "{column}" FROM "{table}" LIMIT 3'

        # Run the query and fetch the results
        sample_values = run_sql(sql, database_url)
        
        # If the query returned results, store them in the new columns
        if not sample_values.empty:
            for i, val in enumerate(sample_values[column]):
                df_schema.at[idx, f'sample_value_{i+1}'] = val
                
    return df_schema

def create_question_list(df_schema: pd.DataFrame) -> list:
    directive = (
        "write me 100 questions to ask based on the below information about my database. "
        "Give your answer as a list of strings."
        )
    question_list = ast.literal_eval(prompt_on_df(df_schema, directive))
    return question_list

def main_program():
    set_API_key()
    database_url = set_database_connection()
    df_schema = set_schema(database_url)
    schema_with_samples_df = sample_data_from_schema(df_schema, database_url)


if __name__ == "__main__":
    main_program()