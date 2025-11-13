import pandas as pd
import string
import os
import glob

# Set working directory

"""
Set working directory to the main folder containing the sub-folders (Article_Data, ASR_Input, ASR_Output etc.)

"""
working_directory = "/mnt/d/Lab Rotation/Litterature_S_automation-main_Marcus/Litterature_S_automation-main/gpt_trial/Organized_Folder"

# Function to load data files
def load_data():

    # Load Web of Science Data
    """
    Web of Science (wos) can export metadata for a maximum of 1000 articles at a time. Hence, there can be two or more 
    files saved as 'wos1.xls' and wos2.xls' respectively. In case of more than 2000 articles, one can save it
    as a third file and later also update all the input and return variables in the functions that use it (ie.
    "load_data" and "compile_database_information" functions).

    """
    # Load PubMed Data
    pubmed_df = pd.read_csv(working_directory + '/1-Article_Data/Data/pubmed.csv')
    
    # Initialize WoS Data
    wos_df = pd.DataFrame()

    # Dynamically load all WoS files matching the pattern
    wos_files = glob.glob(working_directory + '/1-Article_Data/Data/wos*.xls')
    if wos_files:
        wos_df_list = [pd.read_excel(wos_file) for wos_file in wos_files]
        wos_df = pd.concat(wos_df_list, ignore_index=True)
    else:
        print("Warning: No WoS files found. Proceeding without WoS data.")
    
    # Load Greenfile Data
    greenfile_df = pd.read_csv(working_directory + '/1-Article_Data/Data/greenfile.csv')

    # Load Embase Data
    embase_df = pd.read_csv(working_directory + '/1-Article_Data/Data/embase.csv', skiprows=3, delimiter=',')
    
    return pubmed_df, wos_df, greenfile_df, embase_df

# Function to normalize text for identifying duplicates
def normalize_text(text):

    """ 
    Normalize text by removing punctuation and converting to lowercase.
    This is mainly required for formatting the title, abstract and other columns for 
    correct identification of replicates in case they can't be identified by DOI.

    """
    if isinstance(text, str):
        return ''.join([char.lower() for char in text if char not in string.punctuation])
    return ''

# Function to compile and normalize data from all sources
def compile_database_information(pubmed_df, wos_df, greenfile_df, embase_df):
    # Extract and standardize columns
    pubmed_df_new = pubmed_df[['Title', 'Abstract', 'Authors', 'DOI', 'Journal']]
    wos_df_new = wos_df[['Article Title', 'Abstract', 'Authors', 'DOI', 'Source Title']].rename(columns={'Article Title': 'Title', 'Source Title': 'Journal'})
    greenfile_df_new = greenfile_df[['title', 'abstract', 'contributors', 'doi', 'source']].rename(columns={'title': 'Title', 'abstract': 'Abstract', 'contributors': 'Authors', 'doi': 'DOI', 'source': 'Journal'})
    embase_df_new = embase_df[['Title', 'Abstract', 'Author Names', 'DOI', 'Source title']].rename(columns={'Author Names': 'Authors', 'Source title': 'Journal'})

    # Concatenate all dataframes
    columns = ['Title', 'Abstract', 'Authors', 'DOI', 'Journal']
    dataframes = [df.reindex(columns=columns) for df in [pubmed_df_new, wos_df_new, greenfile_df_new, embase_df_new]]
    compiled_df = pd.concat(dataframes, ignore_index=True)

    # Normalize text columns for consistency
    for col in ['Title', 'Authors', 'Journal']:
        compiled_df[col] = compiled_df[col].astype(str).str.strip().str.lower().str.title()

    # Fill missing values
    for col in columns:
        compiled_df[col] = compiled_df[col].fillna(f'No {col}')

    # Save the compiled data
    compiled_df.to_csv(os.path.join(working_directory + '/2-ASR_Input/' + output_dir + '/compiled_articles_from_all_databases.csv'), index=False)

    return pubmed_df_new, wos_df_new, greenfile_df_new, embase_df_new, compiled_df

# Function to calculate stats and replicates based on DOI and other fields
def process_replicates_and_dois(df):

    """
    Process the given DataFrame containing article metadata to calculate statistics related to 
    repeated articles based on DOI (since it is a unique identifier). It also goes a step further 
    and tries to identify replicates even in articles with 'No DOI'.
    The statistics include:
    - Total number of entries in the dataframe
    - Number of artilces with unique DOIs
    - Number of repeated articles
    - Number of articles with 'No DOI' (if any)
    - Number of replicates for article with 'No DOI' based on Title, Abstract, Authors, Journal

    """

    results = {}
    
    # Count occurrences of each DOI
    replicate_counts = df['DOI'].value_counts()
    no_doi_count = replicate_counts.get('No DOI', 0)

    # Filter entries with duplicates   
    filtered_replicates = replicate_counts[replicate_counts > 1].reset_index()
    filtered_replicates.columns = ['DOI', 'ReplicateCounts']
    filtered_replicates = filtered_replicates[filtered_replicates['DOI'] != 'No DOI']
    sum_x = (filtered_replicates['ReplicateCounts'] - 1).sum()

    """
    Note: ReplicateCounts fetches value counts of all copies of the data hence the sum_x is used to 
    fetch all "repeated copies" of the data. 
    Example: Let's say two DOI entries have 4 and 3 value counts respectively 
    (ie., the articles have 4 total copies and 3 total copies in the compiled list), 
    then the number of "repeated copies" is counted as 3 and 2 respectively. 

    """
    
    # Count unique DOIs and save unique articles to .csv
    unique_dois_df = df[df['DOI'] != 'No DOI'].drop_duplicates(subset='DOI')
    unique_dois_df.to_csv(os.path.join(working_directory + '/2-ASR_Input/' + output_dir + '/unique_articles.csv'), index=False)
    
    # Count repeated DOIs and save unique articles to .csv
    repeated_articles_df = df[df['DOI'].isin(filtered_replicates['DOI']) & df.duplicated(subset='DOI', keep='first')]
    repeated_articles_df.to_csv(os.path.join(working_directory + '/2-ASR_Input/' + output_dir + '/repeated_articles.csv'), index=False)
    
    # Prepare basic stats
    results.update({
        'total_entries': df.shape[0],
        'total_unique_dois': unique_dois_df.shape[0],
        'sum_x': sum_x,
        'no_doi_count': no_doi_count
    })
    
    # Save articles with 'No DOI'
    if no_doi_count > 0:
        df_no_doi = df[df['DOI'] == 'No DOI'].copy()
        df_no_doi.to_csv(os.path.join(working_directory + '/2-ASR_Input/' + output_dir + '/articles_with_no_doi.csv'), index=False)

        # Normalize relevant columns        
        for col in ['Title', 'Abstract', 'Authors', 'Journal']:
            df_no_doi[f'Normalized_{col}'] = df_no_doi.loc[:, col].apply(normalize_text)
        
        # Find replicates by normalized columns
        replicate_columns = {}
        for col in ['Normalized_Title', 'Normalized_Abstract', 'Normalized_Authors', 'Normalized_Journal']:
            replicates = df_no_doi.groupby(col).size().reset_index(name='ReplicateCounts')
            replicates_filtered = replicates[replicates['ReplicateCounts'] > 1]
            replicate_columns[col] = replicates_filtered['ReplicateCounts'].sum() - len(replicates_filtered)
        
        # Combine results
        results.update({
            'sum_x_titles': replicate_columns['Normalized_Title'],
            'sum_x_abstracts': replicate_columns['Normalized_Abstract'],
            'sum_x_authors': replicate_columns['Normalized_Authors'],
            'sum_x_journals': replicate_columns['Normalized_Journal']
        })
    
    return results

# Function to calculate stats for each source and save to file
def stats(pubmed_df_new, wos_df_new, greenfile_df_new, embase_df_new, compiled_df, replicate_stats=None):
    with open(os.path.join(working_directory + '/2-ASR_Input/' + output_dir + '/stats.txt'), 'w') as f:
        # Stats for individual sources
        f.write(f"Database Statistics:\n")
        f.write(f"Number of entries in PubMed: {len(pubmed_df_new)}\n")
        f.write(f"Number of entries in WoS: {len(wos_df_new)}\n")
        f.write(f"Number of entries in GreenFile: {len(greenfile_df_new)}\n")
        f.write(f"Number of entries in Embase: {len(embase_df_new)}\n")
        f.write(f"Total number of articles compiled from all databases: {(len(compiled_df))}\n")

        if replicate_stats:
            # Stats from DOI processing
            f.write(f"\nReplicate Statistics:\n")
            f.write(f"Total number of articles in compiled database: {replicate_stats['total_entries']}\n")
            f.write(f"Number of unique articles: {replicate_stats['total_unique_dois']}\n")
            f.write(f"Number of repeated articles: {replicate_stats['sum_x']}\n")
            f.write(f"Number of articles with 'No DOI': {replicate_stats['no_doi_count']}\n")

            if replicate_stats['no_doi_count'] > 0:
                f.write(f"\nFor aricles with 'No DOI':\n")
                f.write(f"Number of replicates in Title for articles with 'No DOI': {replicate_stats['sum_x_titles']}\n")
                f.write(f"Number of replicates in Abstract for articles with 'No DOI': {replicate_stats['sum_x_abstracts']}\n")
                f.write(f"Number of replicates in Authors for articles with 'No DOI': {replicate_stats['sum_x_authors']}\n")
                f.write(f"Number of replicates in Journals for articles with 'No DOI': {replicate_stats['sum_x_journals']}\n")

# Main script
if __name__ == "__main__":

    """
    Code Explanation: 
    Example: "pubmed_df, wos_df_1, wos_df_2, greenfile_df, embase_df = load_data()"
    It simplifies the process of assigning multiple datasets from a single function call into individual variables.

    Used to unpack datasets returned by load_data() into separate variables for PubMed, 
    WoS (2 parts), GreenFile, and Embase

    """

    # Create an output directory for the results of the compilation 
    output_dir = "Compilation_Outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pubmed_df, wos_df, greenfile_df, embase_df = load_data()
    pubmed_df_new, wos_df_new, greenfile_df_new, embase_df_new, compiled_df = compile_database_information(pubmed_df, wos_df, greenfile_df, embase_df)
    replicate_stats = process_replicates_and_dois(compiled_df)
    stats(pubmed_df_new, wos_df_new, greenfile_df_new, embase_df_new, compiled_df, replicate_stats)
