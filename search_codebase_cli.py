import subprocess


def main():
    # Asking for search type and validate input
    search_type = None
    while search_type not in ['1', '2', '3', 'q']:
        print("What do you want to search for?")
        print("1. Content (e.g., keywords in code)")
        print("2. Function Name")
        print("3. Class Name")
        print("q to Quit")

        search_type = input("Enter the number corresponding to your search type (1/2/3), or 'q' to quit: ")

        if search_type == '1':
            search_type = "content"
        elif search_type == '2':
            search_type = "function"
        elif search_type == '3':
            search_type = "class"
        elif search_type == 'q':
            print("Quitting the search.")
            return
        else:
            print("Invalid selection. Please try again.")
            # Resetting to "None" to re-prompt the user
            search_type = None

    # Asking for search query
    search_query = input(f"Enter the {search_type} query you want to search for (or 'q' to quit): ")

    if search_query.lower() == 'q':
        print("Quitting the search.")
        return

    # Calling the "search_codebase.py" script with the given query and search type
    try:
        result = subprocess.run(['./search_codebase.py', search_query, search_type], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
