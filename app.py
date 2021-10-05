from rich import print
from rich.table import Table
from rich.console import Console
import csv
from tmdbv3api import TMDb, TV
from dotenv import load_dotenv
import os
from sys import exit
import pandas
from win10toast_persist import ToastNotifier
from time import sleep
from pathlib import Path


class App:
    def __init__(self) -> None:

        # run CSV check method at app startup
        self.check_for_csv()

    def check_for_csv(self):
        """
        Creates a CSV file to store data if it does not yet exist.
        """

        # path to the CSV file
        db_path = "serie_db.csv"

        try:
            # check for the CSV file in the current working directory
            if not os.path.exists(db_path):
                print("Creating database file (first time user)")
                print("................................")

                # a simple context manager execution as "w" will create the file for us
                with open(db_path, "w") as file:
                    pass

                print("Database created")
                print()

        except OSError as e:
            print("Unable to create database file!")
            print()
            quit()

    def welcome(self):
        """
        The welcome screen of the app. Shows a list of options to the user, takes user input and feeds the input to other functions in the program.
        """

        print("Hello, what would you like to do?")

        print("Input 1 to enter a TV show into the local database.")
        print("Input 2 to view the shows stored in the local database")
        print("Input 3 to check for show updates.")

        ask_input = int(input("Else, input 0 to quit the program: "))

        return ask_input

    def search_for_show(self):
        """
        Look for the user-entered search term and return the results for further use by the 'results' method.
        """

        proper_search_term = False

        while not proper_search_term:
            print()

            search_term = input("Enter the TV show to look for, or 0 to go back: ")

            if search_term == "0":
                return 0

            search_results = tv.search(search_term)

            if search_results != []:
                # the search was executed properly
                proper_search_term = True

            else:
                print(
                    "Your search term did not result in any results, please try again!"
                )

        print("Now scouring the TMDb database for results.")

        try:
            # if there are too many results, restrict them to a max of 9
            search_results = search_results[:8]

        except IndexError:
            # otherwise, let the list pass as is
            pass

        return search_results

    def print_results(self, results):
        """
        Prints the search results in a list manner, while hashing the appropriate data.
        """

        print("Showing the most relevant results.")
        print()

        list_len = len(results)

        show_index = {}

        for i in range(list_len):
            # map the shows in the list to a dictionary
            show_index[i + 1] = results

            # print the show name, year of origin and country of origin (CoO is in list form, print the 1st entry)

            try:
                # some shows might have incorrect or incomplete data somewhere, for example in really old shows

                print(
                    "{}. {}, {}, {}".format(
                        i + 1,
                        results[i]["name"],
                        results[i]["first_air_date"][:4],
                        results[i]["origin_country"][0],
                    )
                )

            except IndexError:
                pass

        return show_index, list_len

    def get_user_choice(self, show_index, list_len):
        """
        Give the user a prompt to select their choice of TV show from the list generated by 'print_results' class method."""

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
        season_count = tv.details(show_id)["number_of_seasons"]

        return show_name, season_count, show_id

    def write_to_csv(self, show_name, season_count, show_id):
        """
        This method saves the user-selected show to the CSV file."""

        file_name = "G:/Py/2021/MyProj/Series-Lookup/serie_db.csv"

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
        """
        Reads and extracts data from the CSV file and prepares it for output in a tabular form.
        """

        file_name = "G:/Py/2021/MyProj/Series-Lookup/serie_db.csv"

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
        """
        Takes the extracted data from the 'get_data' class method and presents it in a tabular form to the user.
        """

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


class Updates:
    def read_data(self):
        """
        Read the database and collect show information for further use by other methods.
        """

        self.file_name = "G:/Py/2021/MyProj/Series-Lookup/serie_db.csv"

        # using os' "getsize" method to check if the user has saved any tv shows
        check_for_db = os.path.getsize(self.file_name)

        if not check_for_db:
            # if the db file does not exist, print an error message and exit
            print("There is no saved data! Please save a show first before accessing!")

            return []

        with open(self.file_name, "r+", newline="") as file:
            reader = csv.reader(file)

            # ignore the header
            fields = next(reader)

            shows_data = [info for info in reader]

        return shows_data

    def get_updates(self, shows_data):
        """
        Use the tmdb api to search for updates for the shows stored in the local database.
        """

        if shows_data == []:
            print("There is no saved data! Please save a show first before accessing!")

            return

        new_seasons = []

        for data in shows_data:
            name = data[0]
            curr_seasons = int(data[1])
            tmdb_id = int(data[2])

            try:
                check_seasons = tv.details(tmdb_id)["number_of_seasons"]

            except:
                print("Please enter an API key first!")

                return

            # now, only push the check_update integer into the list if
            # the show received an update, else scrape it
            if check_seasons > curr_seasons:
                new_seasons.append((name, check_seasons, tmdb_id))

        return new_seasons

    def update_db(self, new_seasons):
        """
        Update the data for the TV show(s) in the database if there has been an update.
        """
        if new_seasons == []:
            return

        db_path = "G:/Py/2021/MyProj/Series-Lookup/serie_db.csv"

        # we'll use pandas to convert the csv to a dataframe, make needed changes and then convert it back
        csv_df = pandas.read_csv(db_path)

        for data in new_seasons:
            name, seasons = data[0], data[1]

            # using loc to specify what cell data to look for
            # if show name == name in the list, then set the new season count
            csv_df.loc[csv_df["Show Name"] == name, "Seasons"] = f"{str(seasons)}"

        # write changes to the file
        csv_df.to_csv(db_path, index=False)

    def send_notification(self, new_seasons):
        """
        Send toast notifications to the user if there have been updates.
        """

        notifier = ToastNotifier()

        if new_seasons == []:
            notifier.show_toast("Overview", "No updates.", duration=None)

            print()

            return

        count = 0

        for data in new_seasons:

            # duration=None makes the notification persist
            notifier.show_toast(
                "New Season Alert!",
                f"The show {data[0]} has a new season!",
                duration=None,
            )

            sleep(7)

            count = count + 1

        # send an overview notification
        notifier.show_toast("Overview", f"{count} updates.", duration=None)


if __name__ == "__main__":
    # load environment variables
    load_dotenv(dotenv_path="key.env")
    api_key = os.getenv("API_KEY")

    tmdb = TMDb()

    # set api key
    tmdb.api_key = api_key
    # tmdb.api_key = "ENTER KEY HERE!"

    # config
    tmdb.language = "en"
    tmdb.debug = True

    tv = TV()

    # using a while loop here to keep executing the app
    # until the user decides to quit
    app_persist = True

    while app_persist:
        app = App()

        if tmdb.api_key == "ENTER KEY HERE!":
            print(
                "The app won't work without a TMDB API key, please generate one and enter it in line 410 of the python file."
            )

            os.system("pause")
            print()
            exit()

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
            updates = Updates()
            read_csv = updates.read_data()

            if read_csv == []:
                pass

            else:

                get_updates = updates.get_updates(read_csv)

                save_updates = updates.update_db(get_updates)

                notifier = updates.send_notification(get_updates)

            os.system("pause")
            print()

        elif init == 0:
            exit()
