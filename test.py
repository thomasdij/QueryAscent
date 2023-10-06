import unittest
from unittest.mock import patch
from main import main_program
from database_and_synonym_manager import set_database_connection, set_schema, set_API_key
from execution_manager import run_sql, prompt_on_df
from global_event_publisher import event_publisher
import pandas as pd
import ast
import os
from datetime import datetime
import csv
from dotenv import load_dotenv

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
        "Write me 100 questions to ask based on the below information about my database. "
        "Give your answer as a list of strings."
        "Instead of using the column names, use normal English words. "
        )
    question_list = ast.literal_eval(prompt_on_df(df_schema, directive))
    return question_list

def generate_questions():
    set_API_key()
    database_url = set_database_connection()
    df_schema = set_schema(database_url)
    schema_with_samples_df = sample_data_from_schema(df_schema, database_url)
    return create_question_list(schema_with_samples_df)


class TestMainProgram(unittest.TestCase):

    @patch('builtins.input', side_effect=["Question1", "Question2", "Question3"])
    @patch('builtins.print')
    def test_main_program(self, mock_print, mock_input):

        # Check if DATABASE environment variable is set
        load_dotenv()
        database_name = os.getenv("DATABASE")
        if database_name is None:
            raise EnvironmentError("DATABASE environment variable is not set")

        questions = [
           "What is the frequency of each film genre?",
           "What percentage of movies had male actors?",
        ]

        column_names = ["test_case_number", "iteration_number", "database_name", "question",
                        "schema_partitions", "filtered_schema_and_synonyms_df",
                        "initial_sql_query", "fallback_exception_1",
                        "fallback_query_2", "fallback_exception_2", "fallback_query_3",
                        "fallback_exception_3", "fallback_query_4", "fallback_exception_4",
                        "fallback_query_5", "fallback_exception_5", "fallback_query_5", "fallback_exception_5", 
                        "error_analysis_content_1", "error_analysis_content_2", "error_analysis_content_3",
                        "error_analysis_content_4", "error_analysis_content_5",
                        "error_analysis_content_6", "answer"]

        # Create test_logs directory
        if not os.path.exists('test_logs'):
            os.makedirs('test_logs')

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        csv_file = f"test_logs/test_log_{timestamp}.csv"

        test_case_number = 1
        iteration_quantity = 2

        captured_data = {}
        events = ["schema_partitions_set", "filtered_schema_and_synonyms_set",
                  "initial_sql_query_set", "fallback_exception_0_set",
                  "fallback_query_1_set", "fallback_exception_1_set",
                  "fallback_query_2_set", "fallback_exception_2_set", "fallback_query_3_set",
                  "fallback_exception_3_set", "fallback_query_4_set", "fallback_exception_4_set",
                  "fallback_query_5_set", "fallback_exception_5_set", "error_analysis_content_1_set",
                  "error_analysis_content_2_set", "error_analysis_content_3_set",
                  "error_analysis_content_4_set", "error_analysis_content_5_set",
                  "error_analysis_content_6_set", "answer_set"] 

        def capture_event(data, event_name):
            print(f"Captured event: {event_name}")  # Debugging
            captured_data[event_name] = data

        for event_name in events:
            def handler(data, event_name=event_name):
                capture_event(data, event_name)
            event_publisher.on(event_name, handler)

        try:
            with open(csv_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(column_names)

                for question in questions:
                    for iteration_number in range(1, iteration_quantity + 1):
                        
                        # Clear the mock's call list and captured data
                        mock_print.reset_mock()
                        captured_data.clear()
                        
                        # Run the program
                        main_program(question)

                        row_data = [test_case_number, iteration_number, database_name, question]
                        
                        for event_name in events:
                            row_data.append(captured_data.get(event_name, None))

                        writer.writerow(row_data)

                    test_case_number += 1
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    unittest.main()


        # questions = [
        #     "What is the frequency of each film genre?"
        #     "How many customers have made more than five rentals?"
        #     "What is the average rental duration for each film rating?"
        #     "What percentage of movies from 1999 are scary?",
        #     "What is the average length of films?",
        #     "How many items are currently in stock?",
        #     "When was the last time country data was updated?",
        #     "What is the postal code for a particular customer?",
        #     "What are the email addresses of staff members?",
        #     "Which locations have additional addresses provided?",
        #     "When were all movies last updated?",
        #     "What are the total sales for each store?",
        #     "Can you list all available movie titles?",
        #     "What are the last names of all the actors?",
        #     "What is the most recent customer sign-up date?",
        #     "Are there any movies updated after 8/26/2011?",
        #     "How many different ways can you pay?",
        #     "What are the staff members' phone numbers?",
        #     "What are the IDs for all customers?",
        #     "What special features are available in the movies?",
        #     "What different movie ratings exist?",
        #     "How many distinct addresses are there?",
        #     "Can you list the dates when movies were rented last month?",
        #     "Which stores have the highest overall sales?",
        #     "What's the address ID for a particular customer?",
        #     "What are the main addresses for customers?",
        #     "How many movies are in each category?",
        #     "What are the titles in the movie list?",
        #     "In which countries do customers live?",
        #     "What's the ID for the US?",
        #     "Which stores have the most stock?",
        #     "What languages can be found in the language options?",
        #     "What are the districts for each location?",
        #     "When were the actors last updated?",
        #     "What are the return dates for all rentals?",
        #     "Who is the staff member associated with a certain payment?",
        #     "What are the available ratings in the slower but more detailed movie list?",
        #     "What's the ID for Los Angeles?",
        #     "When were categories last updated?",
        #     "Who are the active customers?",
        #     "What is the price for each movie?",
        #     "What notes are there for each customer?",
        #     "What are the postal codes for each location?",
        #     "When were cities last updated?",
        #     "What are the film descriptions in the slower but more detailed movie list?",
        #     "What are the last names of all customers?",
        #     "Which address is associated with each store?",
        #     "Who are the actors associated in the actor-movie relationship?",
        #     "When were customers last updated?",
        #     "What is the first name of each actor in the detailed actor information?",
        #     "What is the name of each staff member?",
        #     "What are the total sales for each category?",
        #     "What are the last update timestamps for each staff member?",
        #     "What are the last names of customers named 'Mary'?",
        #     "Which staff members are in management positions?",
        #     "Which movies include a specific actor according to the actor-movie relationship?",
        #     "Is the active status mostly true or false for customers?",
        #     "Which staff members have a specific ending in their password?",
        #     "What cities are in countries with a low ID?",
        #     "Which movies are longer than 100 minutes?",
        #     "What are the different categories available in sales by category?",
        #     "Who are the staff members who were updated most recently?"
        # ]
