import openai
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from utils import truncate_content

class SQLExecutionError(Exception):
    """Custom exception for SQL execution errors."""
    def __init__(self, original_exception):
        self.original_exception = str(original_exception)
        super().__init__(self.original_exception)

def prompt_on_df(prompt_directive, df, model="gpt-3.5-turbo"):
    prompt = (prompt_directive + df.to_string(index=True))
    completion = openai.ChatCompletion.create(
    model=model,
    temperature=0,
    messages=[{"role": "user", "content": prompt}]
    )
    logging.debug(f"PROMPT: {truncate_content(prompt_directive)}")
    logging.debug(f"RESPONSE: {truncate_content(completion.choices[0].message['content'])}\n")
    return completion.choices[0].message['content']

def run_sql(sql: str, database_url: str) -> pd.DataFrame:
    logging.debug("About to try executing SQL...")  
    
    try:
        logging.debug("Creating engine...")  
        engine = create_engine(database_url)
        logging.debug(f"Engine created: {engine}")

        logging.debug("Executing SQL query...")  
        sql_answer_df = pd.read_sql_query(sql, engine)
        return sql_answer_df
    
    except SQLAlchemyError as e:
        logging.debug("Type of original SQLAlchemy exception:", type(e.orig))
        logging.debug("Attributes of original SQLAlchemy exception:", dir(e.orig))
        logging.debug(e.orig)
        raise SQLExecutionError(e.orig)    
    
    except Exception as e:  # Temporarily catch all exceptions
        logging.debug("An exception occurred!")  
        logging.debug(e)
        # Re-raise as a custom exception
        raise SQLExecutionError(e)

def generate_sql_query(question, filtered_schema_and_synonyms_df):
    prompt_directive = (
        "I provide a question and a Database Schema Table and you provide SQL."
        "Column names are genericly referenced as table_name.column_name using thier "
        "corresponding table name from the table_name column and column name from the column_name column."
        "You will only respond with SQL code and not with any explanations."
        "Here is the question: " +
        question +
        "Here is the Database Schema Table:\n"
    )
    sql_query = prompt_on_df(prompt_directive, filtered_schema_and_synonyms_df)
    return sql_query

def execute_sql_with_fallback(sql_query, database_url, question, filtered_schema_and_synonyms_df, retry_count=0, last_sql_query=None):
    try:
        sql_result = run_sql(sql_query, database_url)
        return sql_result
    except SQLExecutionError as e:
        if sql_query == last_sql_query:
            logging.debug("SQL query is the same for two loops in a row. Switching to error analysis.")
            return execute_sql_with_error_analysis(sql_query, database_url, question, filtered_schema_and_synonyms_df, e.original_exception)
        
        if retry_count < 5:
            logging.debug(f"An error occurred while executing SQL: {e.original_exception}. Retrying... ({retry_count + 1}/5)\n")
            try:
                # Assuming `attempt_to_fix_sql_query` returns a modified SQL query
                fixed_sql_query = attempt_to_fix_sql_query(sql_query, question, e.original_exception, filtered_schema_and_synonyms_df)
                
                # Recursive call with incremented retry_count and last_sql_query updated
                return execute_sql_with_fallback(fixed_sql_query, database_url, question, filtered_schema_and_synonyms_df, retry_count + 1, sql_query)
                
            except Exception as fix_e:
                logging.debug(f"An error occurred while attempting to fix the SQL: {fix_e}. Retrying... ({retry_count + 1}/5)\n")
                return execute_sql_with_fallback(sql_query, database_url, question, filtered_schema_and_synonyms_df, retry_count + 1, sql_query)
        else:
            logging.debug(f"Exceeded maximum number of retries. Latest error: {e.original_exception}. Switching to error analysis.")
            return execute_sql_with_error_analysis(sql_query, database_url, question, filtered_schema_and_synonyms_df, e.original_exception)

def attempt_to_fix_sql_query(sql_query, question, exception, reference_df):
    prompt_directive = (
        "I provide you with an SQL query that has produced an error, along with the original question it's meant to answer,"
        "the specific error message and a Database Schema Table. Your task is to diagnose the error based on "
        "the given information and provide a new, corrected SQL query that should successfully execute and is "
        "different from the original. Your response must be different from the original query. "
        "Column names are genericly referenced as table_name.column_name using thier "
        "corresponding table name from the table_name column and column name from the column_name column."
        "Please only respond with the corrected SQL code, without additional explanations.\n"
        "Here is the original question the query is meant to answer: " +
        question +
        "\nHere is the original query:\n" +
        sql_query +
        "\nHere is the error message:\n" +
        exception +
        "\nHere is the Database Schema Table:\n"
    )
    fixed_sql_result = prompt_on_df(prompt_directive, reference_df)
    logging.debug(f"Original SQL query: {sql_query}\n")
    logging.debug(f"Fixed SQL query: {fixed_sql_result}\n")
    return fixed_sql_result

def prompt_on_directive(messages, model="gpt-3.5-turbo"):
    completion = openai.ChatCompletion.create(
        model=model,
        temperature=0,
        messages=messages
    )
    logging.debug(f"PROMPT: {truncate_content(messages)}")
    logging.debug(f"RESPONSE: {truncate_content(completion.choices[0].message['content'])}\n")
    return completion.choices[0].message['content']

def execute_sql_with_error_analysis(sql_query, database_url, question, filtered_schema_and_synonyms_df, exception):
    conversation = []

    # Set Direction and Summarize the User's Original Question
    directive1 = (
        "I provide you with an SQL query that has produced an error, along with the original question it's meant to answer,"
        "the specific error message, and a Database Schema Table. Your task is to help diagnose and correct the issue. "
        "Please start by summarizing the user's original question: " + question
                )
    conversation.append({"role": "user", "content": directive1})
    summary_response = prompt_on_directive(conversation)
    conversation.append({"role": "assistant", "content": summary_response})
    
    # Original SQL Query Intent
    directive2 = "What do you think the original SQL query is trying to do?\nSQL Query: " + sql_query
    conversation.append({"role": "user", "content": directive2})
    intent_response = prompt_on_directive(conversation)
    conversation.append({"role": "assistant", "content": intent_response})

    # Error Message Interpretation
    directive3 = "What do you make of the following error message?\nError Message: " + exception
    conversation.append({"role": "user", "content": directive3})
    error_interpretation = prompt_on_directive(conversation)
    conversation.append({"role": "assistant", "content": error_interpretation})

    # Schema-based Revision Needs
    directive4 = "Based on this Database Schema, what changes would you suggest for the original query?\nDatabase Schema:\n" + filtered_schema_and_synonyms_df.to_string(index=True)
    conversation.append({"role": "user", "content": directive4})
    schema_revision_suggestion = prompt_on_directive(conversation)
    conversation.append({"role": "assistant", "content": schema_revision_suggestion})
    
    # Steps to Fix SQL Query
    directive5 = "What are the steps to correct the SQL query based on the above information?"
    conversation.append({"role": "user", "content": directive5})
    steps_to_fix = prompt_on_directive(conversation)
    conversation.append({"role": "assistant", "content": steps_to_fix})

    # Corrected SQL Query
    directive6 = (
        "Based on all the information and suggestions, please provide a corrected SQL query that should successfully execute. "
        "Please only respond with the corrected SQL code, without additional explanations. "
        "Column names are genericly referenced as table_name.column_name using thier "
        "corresponding table name from the table_name column and column name from the column_name column."
        "For example, do not preface your response with 'The corrected SQL query is...'\n"
        "\nOriginal Question:"  + question + "\nOriginal SQL Query: " + sql_query + "\nError Message: " + exception + 
        "\nDatabase Schema:\n" + filtered_schema_and_synonyms_df.to_string(index=True)      
                )  
    conversation.append({"role": "user", "content": directive6})
    corrected_sql_query = prompt_on_directive(conversation)
    try:
        sql_result = run_sql(corrected_sql_query, database_url)
        return sql_result
    except SQLExecutionError as e:
        logging.debug("Corrected SQL query still produces an error. Quitting.")
        return "Unable to answer."
