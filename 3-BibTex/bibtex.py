import os
import pandas as pd
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from random import randint
from time import sleep

# Set to track successfully and unsuccessfully processed DOIs
success_set = set()
failure_set = set()

# Function to clear or create the output folder
def clear_output_folder(folder_path):
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"Cleared existing files in {folder_path}")
    else:
        os.makedirs(folder_path)
        print(f"Created folder {folder_path}")

# Function to fetch BibTeX entries from CrossRef API
def fetch_bibtex(doi, max_retries=3, timeout=15):
    api_url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(api_url, timeout=timeout)
            if response.status_code == 200:
                print(f"Successfully fetched BibTeX for DOI {doi}")
                return doi, response.text
            else:
                print(f"HTTP Error {response.status_code} for DOI {doi}")
                failure_set.add(doi)
                return doi, None
        except requests.exceptions.Timeout:
            print(f"Timeout while fetching DOI {doi}, attempt {attempt + 1}/{max_retries}")
        except Exception as error:
            print(f"Error fetching DOI {doi}: {error}")
            failure_set.add(doi)
            return doi, None
        
        # Exponential backoff with random delay
        sleep(randint(1, 3))

    failure_set.add(doi)
    return doi, None

# Function to save BibTeX entries to individual files
def save_bibtex_files(bibtex_entries, output_folder):
    for doi, bibtex_content in bibtex_entries.items():
        if bibtex_content:
            safe_filename = f"{doi.replace('/', '_')}.bib"
            file_path = os.path.join(output_folder, safe_filename)
            
            if os.path.exists(file_path):
                print(f"File already exists for DOI {doi}, skipping.")
                failure_set.add(doi)
                continue
            
            try:
                with open(file_path, 'w') as file:
                    file.write(bibtex_content)
                print(f"Saved BibTeX for DOI {doi} to {file_path}")
                success_set.add(doi)
            except Exception as error:
                print(f"Error saving BibTeX for DOI {doi}: {error}")
                failure_set.add(doi)
        else:
            print(f"No BibTeX content for DOI {doi}, skipping.")
            failure_set.add(doi)

# Function to save failed DOIs to a CSV file
def save_failed_entries(input_csv_path, failed_csv_path):
    input_df = pd.read_csv(input_csv_path)
    failed_df = input_df[input_df['DOI'].isin(failure_set)].drop_duplicates(subset='DOI')
    failed_df.to_csv(failed_csv_path, index=False)
    print(f"Saved failed entries to {failed_csv_path}")

# Function to save successful DOIs to a CSV file
def save_successful_entries(input_csv_path, success_csv_path):
    input_df = pd.read_csv(input_csv_path)
    success_df = input_df[input_df['DOI'].isin(success_set)].drop_duplicates(subset='DOI')
    success_df.to_csv(success_csv_path, index=False)
    print(f"Saved successful entries to {success_csv_path}")

# Function to write the summary to a text file
def save_summary_to_txt(output_folder, total_input_count, total_success, total_failures):
    #summary_file_path = os.path.join(output_folder, 'bibtex_stats.txt')
    summary_file_path = 'bibtex_stats.txt'
    with open(summary_file_path, 'w') as summary_file:
        summary_file.write("\nSummary of Results:\n")
        summary_file.write(f"\nTotal input DOIs: {total_input_count}\n")
        summary_file.write(f"Successfully fetched and saved: {total_success}\n")
        summary_file.write(f"Failed to fetch: {total_failures}\n")
        summary_file.write(f"Files saved in folder: {len(os.listdir(output_folder))}\n")
    print(f"Summary saved to {summary_file_path}")

# Main function to orchestrate the script
def process_bibtex_entries(input_csv, output_folder, failed_csv, success_csv):
    # Clear or create the output folder
    clear_output_folder(output_folder)

    # Read input CSV file
    input_df = pd.read_csv(input_csv)
    dois = input_df['DOI']
    
    bibtex_results = {}

    # Fetch BibTeX entries using multithreading
    print("Starting BibTeX fetch process...")
    start_time = time.time()
    with ThreadPoolExecutor(max_workers = 5) as executor:
        future_to_doi = {executor.submit(fetch_bibtex, doi): doi for doi in dois}
        for future in as_completed(future_to_doi):
            doi, bibtex_content = future.result()
            bibtex_results[doi] = bibtex_content
    end_time = time.time()
    print(f"Fetched BibTeX entries in {end_time - start_time:.2f} seconds")

    # Save BibTeX entries to files
    save_bibtex_files(bibtex_results, output_folder)

    # Save failed and successful DOIs to respective CSV files
    save_failed_entries(input_csv, failed_csv)
    save_successful_entries(input_csv, success_csv)

    # Display final statistics and save summary to text file
    total_input_count = len(dois)
    total_success = len(success_set)
    total_failures = len(failure_set)
    
    print("\nSummary of Results:")
    print(f"Total input DOIs: {total_input_count}")
    print(f"Successfully fetched and saved: {total_success}")
    print(f"Failed to fetch: {total_failures}")
    print(f"Files saved in folder: {len(os.listdir(output_folder))}")

    save_summary_to_txt(output_folder, total_input_count, total_success, total_failures)

    if total_success + total_failures != total_input_count:
        print("Warning: Discrepancy in total processed DOIs.")
    else:
        print("All DOIs processed correctly.")

# Input and output paths
def main():
    input_csv_path = "unique_articles.csv"  # Path to the input CSV
    output_folder_path = "bibtex_files"  # Folder to save BibTeX files
    failed_csv_path = "failed_entries.csv"  # CSV for failed DOIs
    success_csv_path = "saved_entries.csv"  # CSV for successful DOIs

    process_bibtex_entries(input_csv_path, output_folder_path, failed_csv_path, success_csv_path)

if __name__ == "__main__":
    main()
