import logging
import tiktoken
import pandas as pd
import ast
from utils import truncate_content
from execution_manager import prompt_on_df

TOKEN_CAP = 4096

enc = tiktoken.get_encoding("cl100k_base")

def token_count(input_data):
    # Check if input is a DataFrame
    if isinstance(input_data, pd.DataFrame):
        # Convert DataFrame to a string
        string = input_data.to_string()
    else:
        # Assume it's a string
        string = input_data
    
    # Count the tokens
    tokens = sum(1 for _ in enc.encode(string))
    return tokens

def calculate_table_token_cap(prompt_directive):
    prompt_directive_token_count = token_count(prompt_directive)
    answer_token_count_estimate = 250
    table_token_cap = (
        TOKEN_CAP - prompt_directive_token_count - answer_token_count_estimate
    )
    logging.debug(f"Table token cap: {table_token_cap}")
    return table_token_cap

def create_list_of_df_partitions_limited_by_token_count(schema_and_synonyms_df, table_token_cap):
    # Initialize variables
    current_token_count = 0
    current_df_list = []
    partitioned_df_list = []

    # Loop through the DataFrame
    for index, row in schema_and_synonyms_df.iterrows():
        temp_df = pd.DataFrame([row])
        temp_token_count = token_count(temp_df.to_string(header=False, index=True))
        
        if current_token_count + temp_token_count > table_token_cap:
            # If adding this row would exceed the token cap, save the current DataFrame
            partitioned_df_list.append(pd.concat(current_df_list, ignore_index=True))
            
            # Reset variables
            current_df_list = [temp_df]
            current_token_count = temp_token_count
        else:
            # Otherwise, add this row to the current DataFrame
            current_df_list.append(temp_df)
            current_token_count += temp_token_count

    # Add the last remaining DataFrame if it's not empty
    if current_df_list:
        partitioned_df_list.append(pd.concat(current_df_list, ignore_index=False))

    # df_list now contains your partitioned DataFrames
    logging.debug(f"Number of df partitions by token count: {len(partitioned_df_list)}")  
    return partitioned_df_list

def identify_rows_using_LLM(partitioned_df_list, prompt_directive):
    filtered_schema_and_synonyms_df = pd.DataFrame()

    for df in partitioned_df_list:
        prompt_on_df(prompt_directive, df)
        indices = ast.literal_eval(prompt_on_df(prompt_directive, df))

        for index in indices:
            filtered_schema_and_synonyms_df = filtered_schema_and_synonyms_df._append(df.loc[index])

    return filtered_schema_and_synonyms_df

def prompt_for_df_from_token_limited_df(prompt_directive, token_limited_df):
    table_token_cap = calculate_table_token_cap(prompt_directive)
    partitioned_df_list = (create_list_of_df_partitions_limited_by_token_count(token_limited_df, table_token_cap))
    result_df = identify_rows_using_LLM(partitioned_df_list, prompt_directive)
    result_df.reset_index(inplace=True)
    return result_df

def filter_schema_and_synonyms_df(schema_and_synonyms_df, question):

    identify_data_rows_prompt_directive = (
    "I have a user question and a database schema table. "
    "Your task is to identify rows from the database schema table that could be related to the user's question. "
    "Only return the index numbers of those rows as a list. Do not include any descriptions or explanations.\n"
    "Here is the question: " + question + "\nHere is the Database Schema Table:\n"
    )

    schema_and_synonyms_df_filtered_for_data = prompt_for_df_from_token_limited_df(
        identify_data_rows_prompt_directive, schema_and_synonyms_df)


    logging.debug("schema_and_synonyms_df_filtered_for_data:")
    logging.debug(f"PROMPT: {truncate_content(schema_and_synonyms_df_filtered_for_data)}\n")

    identify_join_rows_prompt_directive = (
    "I have a table of columns that need to be joined and a full database schema table. "
    "Your task is to identify rows from the full database schema table that could be used to join the columns from the table of "
    "columns that need to be joined. " 
    "Only return the index numbers of those rows as a list. Do not include any descriptions or explanations.\n"
    "Here is the table of columns that need to be joined:\n" + schema_and_synonyms_df_filtered_for_data.to_string() + 
    "\nHere is the Full Database Schema Table:\n"
    )

    schema_and_synonyms_df_filtered_for_joins = prompt_for_df_from_token_limited_df(
        identify_join_rows_prompt_directive, schema_and_synonyms_df)
    
    logging.debug("schema_and_synonyms_df_filtered_for_joins:")
    logging.debug(f"PROMPT: {truncate_content(schema_and_synonyms_df_filtered_for_joins)}\n")

    schema_and_synonyms_df_for_data_or_joins = schema_and_synonyms_df_filtered_for_data._append(
        schema_and_synonyms_df_filtered_for_joins)
    
    schema_and_synonyms_df_for_data_or_joins.drop_duplicates(inplace=True)

    logging.debug("schema_and_synonyms_df_for_data_or_joins:")
    logging.debug(f"PROMPT: {truncate_content(schema_and_synonyms_df_for_data_or_joins)}\n")

    return schema_and_synonyms_df_for_data_or_joins
