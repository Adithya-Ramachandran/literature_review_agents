from src import initialise_state, database
from src.graph import create_graph
from src import utils
import definitions
import glob
import os
from dotenv import load_dotenv

load_dotenv()

def main():

    # --- Setup ---
    # database.reinitialize_database() # Uncomment to wipe the DB on startup
    database.create_database()
    graph = create_graph()

    # --- Ingestion: Just get the list of files ---
    path = definitions.paper_path # Or your rename_path
    paper_list = glob.glob(str(path) + "/*.pdf")

    # --- Processing Loop ---
    for paper_path in paper_list:  # iterate through the files
        file_name = os.path.basename(paper_path)

        if database.paper_exists(paper_path):
            print(f"--- SKIPPING {file_name}: Already in database. ---\n")
            continue

        print(f"------------------------------------------------------------------------")
        print(f"--- PROCESSING {file_name}: {paper_path} ---")

        # 2. Set up the initial state for the graph
        initial_state = initialise_state.initialise_state()
        initial_state['path'] = paper_path

        # 3. Invoke the graph to run the full pipeline
        final_state = graph.invoke(initial_state)
        utils.pretty_print_dict(final_state)

        # 4. Save the results
        if final_state.get('relevancy') is True:
            database.upsert_paper(final_state)
            print(f"--- Saved relevant paper {file_name} to database. ---\n")
        else:
            print(f"--- Discarded paper {file_name} - not relevant. ---\n")


if __name__ == "__main__":
    main()