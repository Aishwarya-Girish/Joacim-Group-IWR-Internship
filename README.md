# 🦠 Accelerating Systematic Reviews: An AI-Aided Workflow for Synthesizing the Microplastic-Antimicrobial Resistance Knowledge Landscape

This repository contains the analysis code and results from a study on the cellular mechanisms underlying reproductive fate decisions in the freshwater planarian *Phagocata morgani*.

The project report can be viewed at 🔗[https://aishwarya-girish.github.io/Joacim-Group-IWR-Internship/](https://aishwarya-girish.github.io/Joacim-Group-IWR-Internship/).

## 🦠 Overview

This repository presents a **quantitative framework** to:

- Infer trajectories using pseudotime
- Identify bifurcation points along these trajectories
- Model cell-type abundance and variance changes across transitions
- Statistically detect cell types enriched near bifurcation points that may drive reproductive fate
- Model size-independent covariance in the cell types

## 📂 Repository Structure
```
Main Files
├── 1-Article_Data/                    # Phase 1: Raw Data Acquisition
    ├── Data/                          # Outputs from the databases
        ├── embase.csv                 # Manual export from EMBASE
        ├── greenfile.csv              # Manual export from GreenFILE
        ├── pubmed.csv                 # Automated export via PubMed API
        ├── wos1.csv                   # Manual export from Web of Science (Part 1)
        ├── wos2.csv                   # Manual export from Web of Science (Part 2)
    ├── pubmed.py                      # Automated PubMed API retrieval script
    ├── query.txt                      # Base search query used across databases
├── 2-ASR_Input                       # Phase 2: Data Unification for ASReview
    ├── Compilation_Output
        ├── articles_with_no_doi.csv   # Records lacking a DOI for referencing
        ├── compiled_articles_from_all_databases.csv # Master file pre-deduplication
        ├── repeated_articles.csv      # List of identified duplicates
        ├── stats.txt                  # Summary counts (total, unique, duplicates)
        ├── unique_articles.csv        # Deduplicated corpus for ASReview screening
    ├── database_compilation.py        # Script for merging & deduplicating datasets
├── 3-BibTeX                          # Phase 3: Bibliographic Management
    ├── bibtex_files/                  # Directory for individual .bib citation files
        ├── bibtex.py                  # Script for automated BibTeX retrieval via Crossref API
        ├── bibtex_stats.txt           # Summary of retrieval success/failure rates
        ├── failed_entries.csv         # DOIs that could not be fetched automatically
        ├── saved_entries.csv          # Successfully retrieved BibTeX entries
        ├── unique_articles.csv        # Input file containing DOIs for fetching
├── 4-Extraction_ChatGPT              # Phase 4: Preliminary Data Extraction
      ├── extraction_chatgpt.py        # Script for LLM-powered metadata extraction from abstracts

Extras                                 # Supplementary Project Assets
├── docs                              # Documentation and supplementary materials
├── quarto_files                      # Source files for the Quarto project report
└── README.md                         # Project overview, setup, and usage instructions
```

## 📎 Requirements

All analyses are performed within an Python framework using Python (version 3.13). Other dependencies and libraries are clearly mentioned in the respective code files.

## 🦠 How to Run the Analysis

To reproduce the full analysis:

1. **Clone this repository:**
   ```bash
   git clone https://github.com/Aishwarya-Girish/Joacim-Group-IWR-Internship.git
   cd Joacim-Group-IWR-Internship
2. Open the folder of interest in VSCode or equivalent.
3. Run the code to reproduce results.

## 🦠 Academia Bifurcations: This is not a UMAP, it's a career path 😁

![alt text](https://github.com/Aishwarya-Girish/Joacim-Group-IWR-Internship/blob/main/quarto_files/images/resource_page_illustration.svg)

