from multiprocessing import Process, current_process, Queue
from pathlib import Path
import logging
import os
import argparse
import time

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Search for keywords in files using multiprocessing")
parser.add_argument("--source", "-s", required=True,
                    help="Source directory to search in")
parser.add_argument("--keywords", "-k", required=True,
                    nargs="+", help="Keywords to search for")
args = parser.parse_args()

source = Path(args.source)
keywords = args.keywords

# Function to search for keywords in files, adapted for multiprocessing


def search_files(file_paths, keywords, results_queue):
    results = {}
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        if keyword in results:
                            results[keyword].append(str(file_path))
                        else:
                            results[keyword] = [str(file_path)]
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    results_queue.put(results)

# Distribute work across processes


def distribute_work(source, keywords):
    start_time = time.time()

    all_files = [p for p in source.rglob('*') if p.is_file()]
    # Avoid more processes than files
    num_processes = min(os.cpu_count(), len(all_files))
    chunk_size = len(all_files) // num_processes
    file_chunks = [all_files[i:i + chunk_size]
                   for i in range(0, len(all_files), chunk_size)]

    processes = []
    results_queue = Queue()

    for chunk in file_chunks:
        process = Process(target=search_files, args=(
            chunk, keywords, results_queue))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    # Combine results from all processes
    combined_results = {}
    while not results_queue.empty():
        results = results_queue.get()
        for keyword, paths in results.items():
            if keyword in combined_results:
                combined_results[keyword].extend(paths)
            else:
                combined_results[keyword] = paths

    used_time = time.time() - start_time
    return combined_results, used_time


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s: %(message)s", datefmt="%H:%M:%S")

    final_results, used_time = distribute_work(source, keywords)
    for keyword, files in final_results.items():
        logging.info(f"Keyword '{keyword}' found in files: {', '.join(files)}")
    logging.info(f"Total time taken: {used_time} seconds")
