import argparse
import logging
from pathlib import Path
from threading import Thread, Lock
import time

# Setup command line argument parsing
parser = argparse.ArgumentParser(description="Search for keywords in files")
parser.add_argument("--source", "-s", required=True,
                    help="Source directory to search in")
parser.add_argument("--keywords", "-k", required=True,
                    nargs="+", help="Keywords to search for")
args = vars(parser.parse_args())

source = Path(args["source"])
keywords = args["keywords"]

folders = []
results = {}  # Dictionary for storing search results
results_lock = Lock()  # Lock for synchronizing access to the results dictionary

# Function to recursively collect folders for searching


def get_folders(path: Path):
    for file in path.iterdir():
        if file.is_dir():
            folders.append(file)
            get_folders(file)


# Function to search for keywords in files
def search_files(folder, keywords):
    for file in folder.iterdir():
        if file.is_file():
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    for keyword in keywords:
                        if keyword.lower() in content.lower():
                            with results_lock:  # Locking access to the results dictionary
                                if keyword in results:
                                    results[keyword].append(str(file))
                                else:
                                    results[keyword] = [str(file)]
            except Exception as e:
                logging.error(f"Error reading file {file}: {e}")


# Function to distribute work among threads and collect results
def distribute_work(source, keywords):
    start_time = time.time()
    folders.append(source)
    get_folders(source)

    # Creating and starting threads for file searching
    threads = []
    for folder in folders:
        thread = Thread(target=search_files, args=(folder, keywords))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    used_time = time.time() - start_time

    return used_time, results


if __name__ == "__main__":
    format = "%(threadName)s %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    used_time, results = distribute_work(source, keywords)

    # Search results
    for keyword, files in results.items():
        logging.info(f"Keyword '{keyword}' found in files: {', '.join(files)}")
    logging.info(f"Total time taken: {used_time} seconds")
