from rich import print
from rich.table import Table
from rich.console import Console
import csv
from tmdbv3api import TMDb, TV
from dotenv import load_dotenv
import os
from check_upd import *
from sys import exit


class App:
    def __init__(self) -> None:
        # load environment variables
        load_dotenv(dotenv_path="key.env")
        # initialize tmdb object
        self.tmdb = tmdb = TMDb()

        # set api key
        tmdb.api_key = os.getenv("API_KEY")
        # config
        tmdb.language = "en"
        tmdb.debug = True

        self.tv = TV()

        # run CSV check method at app startup
        self.check_for_csv()

    def check_for_csv(self):
        """Creates a CSV file to store data if it does not yet exist"""

        # path to the CSV file
        path = ".\serie_db.csv"

        try:
            # check for the CSV file in the current working directory
            if not os.path.exists(path):
                print("Creating database file (first time user)")
                print("................................")

                # a simple context manager execution as "w" will create the file for us
                with open("serie_db.csv", "w") as file:
                    pass

                print("Database created")
                print()

        except OSError as e:
            print("Unable to create database file!")
            print()
            quit()

    def welcome(self):
        """The welcome screen of the app. Shows a list of options to the user, takes user input and feeds the input to other functions in the program."""

        print("Hello, what would you like to do?")

        print("Input 1 to enter a TV show into the local database.")
        print("Input 2 to view the shows stored in the local database")
        print("Input 3 to check for show updates.")

        ask_input = int(input("Else, input 0 to quit the program: "))

        return ask_input

    def search_for_show(self):
        """Look for the user-entered search term and return the results for further use by the 'results' method."""

        proper_search_term = False

        while not proper_search_term:
            print()

            search_term = input("Enter the TV show to look for, or 0 to go back: ")

            if search_term == "0":
                return 0

            search_results = self.tv.search(search_term)

            if search_results != []:
                # the search was executed properly
                proper_search_term = True

            else:
                print(
                    "Your search term did not result in any results, please try again!"
                )

        print("Now scouring the TMDb database for results.")

        return search_results[:8]

    def print_results(self, results):
        """Prints the search results in a list manner, while hashing the appropriate data."""

        print("Showing the most relevant results.")
        print()

        list_len = len(results)

        show_index = {}

        for i in range(list_len):
            # map the shows in the list to a dictionary
            show_index[i + 1] = results

            # print the show name, year of origin and country of origin (CoO is in list form, print the 1st entry)

            print(
                "{}. {}, {}, {}".format(
                    i + 1,
                    results[i]["name"],
                    results[i]["first_air_date"][:4],
                    results[i]["origin_country"][0],
                )
            )

        return show_index, list_len

    def get_user_choice(self, show_index, list_len):
        """Give the user a prompt to select their choice of TV show from the list generated by 'print_results' class method."""

        valid_choice = False

        print(
            "Input a number to select the show of your choice. Your choice will then be saved in the local database."
        )

        while not valid_choice:
            # giving users the option to go back since it can be a major hassle to be re-executing everything if you make a simple typo
            if list_len > 1:

                ask_choice = int(
                    input(
                        f"Enter a number between 1 and {list_len} or 0 if you want to go back: "
                    )
                )

            else:
                ask_choice = int(
                    input(
                        f"Enter 1 if you want to select the show or 0 if you want to go back: "
                    )
                )

            if 0 <= ask_choice <= list_len:
                valid_choice = True

        if not ask_choice:
            # go back to main screen
            return ask_choice

        show_info = show_index[ask_choice]
        # the format is of a dict wrapped inside a list
        show_info = show_info[0]

        # we cannot get detailed information unless we use the show id
        show_name, show_id = show_info["name"], show_info["id"]

        # while searching a show by name gives a dict inside a list, searching a show by its id gives you a nested dictionary.
        season_count = self.tv.details(show_id)["number_of_seasons"]

        return show_name, season_count, show_id

    def write_to_csv(self, show_name, season_count, show_id):
        """This method saves the user-selected show to the CSV file."""

        file_name = "serie_db.csv"

        # initializing the field titles
        fields = ["Show Name", "Seasons", "Show ID"]
        show_info = [show_name, season_count, show_id]

        # check to confirm if the fields have already been written to the csv. if so, we have made modifications before
        header_check = False
        existing_data = False

        with open(file_name, newline="") as file:
            r = csv.reader(file, delimiter=",")

            for row in r:
                if fields == row:
                    # if the fields and row have same information,
                    # we have already once written to the csv before
                    header_check = True

                # if show information already exists,
                # the user has already saved it once before
                # convert the current info set to string
                # because csv data is in string format
                if show_info[0] == row[0]:
                    existing_data = True

        # we can start writing the data now that
        # our prelinimary checks are complete
        with open(file_name, "a+", newline="") as file:
            writer = csv.writer(file)

            # if header exists, we just need to write the show info
            if header_check and not existing_data:
                writer.writerow(show_info)

                print()
                print("Saved the show in the database.")

            elif not header_check and not existing_data:
                writer.writerow(fields)
                writer.writerow(show_info)

                print()
                print("Saved the show in the database.")

            else:
                print()
                print("Uh oh. Looks like you've already saved this show before.")

        print()


class DrawTable:
    def get_data(self):
        """Reads and extracts data from the CSV file and prepares it for output in a tabular form."""

        file_name = "serie_db.csv"

        if not os.path.getsize(file_name):
            print("There is no saved data! Please save a show first before accessing!")

            return False

        with open(file_name) as file:
            reader = csv.reader(file, delimiter=",")

            # reading the first line to get the header
            header = next(reader)
            # converting fields from list to tuple for usage in tabulate
            header = tuple(header)

            show_info = []

            for data in reader:
                show_info.append(data)

        return header, show_info

    def make_table(self, header, show_info):
        """Takes the extracted data from the 'get_data' class method and presents it in a tabular form to the user."""

        table = Table(title="TV Show Index", show_header=True, header_style="bold cyan")
        console = Console()

        # adding elements to the table
        table.add_column(header[0], style="bold yellow", justify="center", width=18)

        table.add_column(header[1], style="bold green", justify="center")

        table.add_column(header[2], style="bold purple", justify="center")

        # adding the data rows
        for i in show_info:
            table.add_row(i[0], i[1], i[2])

        console.print(table)


if __name__ == "__main__":
    # using a while loop here to keep executing the app
    # until the user decides to quit
    app_persist = True

    while app_persist:
        app = App()
        init = app.welcome()

        if init == 1:

            search = app.search_for_show()

            if search != 0:

                print_results = app.print_results(search)

                user_choice = app.get_user_choice(*print_results)

                if user_choice != 0:
                    csv_writer = app.write_to_csv(*user_choice)

            os.system("pause")
            print()

        elif init == 2:
            table = DrawTable()
            get_data = table.get_data()
            # if get_data == False, no shows stored in the db
            try:
                draw_table = table.make_table(*get_data)
            except TypeError:
                pass

            os.system("pause")
            print()

        elif init == 3:
            pass

        elif init == 0:
            exit()
