import unittest
from unittest.mock import patch
from main import main_program  # Make sure to import main_program appropriately

class TestMainProgram(unittest.TestCase):

    @patch('builtins.input', side_effect=["Question1", "Question2", "Question3"])
    @patch('builtins.print')
    def test_main_program(self, mock_print, mock_input):
        questions = [
            "What is the frequency of each film genre?",
            "How many customers have made more than five rentals?"
        ]

        log_file = "test_log.txt"

        run_number = 1  # Initialize run number

        with open(log_file, "w") as f:
            for question in questions:
                # Run the program
                main_program(question)

                # Log the output to file
                output = "\n".join([str(args[0]) for args, _ in mock_print.call_args_list])
                f.write(f"Run Number: {run_number}\n")  # Log the run number
                f.write(f"Question: {question}\n")
                f.write(f"Output:\n{output}\n")
                f.write("-------\n")

                # Increment run number
                run_number += 1

                # Clear the mock's call list for the next iteration
                mock_print.reset_mock()

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
