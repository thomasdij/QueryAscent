from database_and_synonym_manager import set_database_connection, set_schema, add_synonyms_if_available, set_API_key
from data_preparation_manager import filter_schema_and_synonyms_df
from execution_manager import execute_sql_with_fallback, generate_sql_query
from global_event_publisher import event_publisher
import logging

logging.basicConfig(level=logging.INFO)

def main_program(question):
    set_API_key()
    database_url = set_database_connection()
    df_schema = set_schema(database_url)
    schema_and_synonyms_df = add_synonyms_if_available(df_schema)
    filtered_schema_and_synonyms_df = filter_schema_and_synonyms_df(schema_and_synonyms_df, question)
    sql_query = generate_sql_query(question, filtered_schema_and_synonyms_df)
    answer = execute_sql_with_fallback(sql_query, database_url, question, filtered_schema_and_synonyms_df)
    event_publisher.emit("answer_set", answer)
    print(answer)

if __name__ == "__main__":
    question = input("Enter a question: ")
    main_program(question)