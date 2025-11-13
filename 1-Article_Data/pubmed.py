import requests
from lxml import etree  # Replaced xml.etree.ElementTree with lxml
from bs4 import BeautifulSoup
import csv
import os

# Base URL for NCBI E-utilities
base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def clean_html(raw_html):
    """
    Cleans HTML content by removing all tags and returning the text.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text()

def fetch_all_pubmed_data(query, start_date=None, end_date=None):
    """
    Fetches all PubMed data for a given search query, handling HTML tags properly.
    Allows optional filtering by publication year range.
    """
    # Construct the query with optional data filters
    if start_date and end_date:
        query += f' AND ({start_date}[PDAT] : {end_date}[PDAT])'

    # Initialize parameters for pagination
    esearch_url = f"{base_url}esearch.fcgi"
    batch_size = 200  # Number of PMIDs to fetch per request
    retstart = 0      # Start index for each batch
    all_pmids = []    # List to store all PMIDs

    print("Fetching PMIDs sorted by Best Match...")

    while True:
        # Fetch a batch of PMIDs
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmax": batch_size,
            "retstart": retstart,
            "retmode": "xml",
            "sort": "relevance",  # Ensures "Best Match" sorting
        }
        esearch_response = requests.get(esearch_url, params=esearch_params)

        if esearch_response.status_code != 200:
            print(f"Error: {esearch_response.status_code}")
            print(esearch_response.text)
            break

        try:
            # Parse using lxml
            esearch_tree = etree.fromstring(esearch_response.content)
        except etree.XMLSyntaxError as e:
            print(f"XML Parse Error: {e}")
            break

        pmids = [id_elem.text for id_elem in esearch_tree.findall(".//Id")]

        if not pmids:
            break

        all_pmids.extend(pmids)
        retstart += batch_size
        print(f"Fetched {len(all_pmids)} PMIDs so far...")

    print(f"Total PMIDs fetched: {len(all_pmids)}")

    print("Fetching article details...")
    results = []
    batch_size = 200  # Fetch up to 200 PMIDs per request
    for i in range(0, len(all_pmids), batch_size):
        batch_pmids = all_pmids[i:i+batch_size]
        efetch_url = f"{base_url}efetch.fcgi"
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(batch_pmids),
            "retmode": "xml",
        }
        efetch_response = requests.get(efetch_url, params=efetch_params)

        if efetch_response.status_code != 200:
            print(f"Error: {efetch_response.status_code}")
            print(efetch_response.text)
            break

        try:
            # Explicitly decode the response content as UTF-8
            response_content = efetch_response.content.decode('utf-8')
            # Parse using lxml
            efetch_tree = etree.fromstring(response_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            print(f"XML Parse Error: {e}")
            break

        for article in efetch_tree.findall(".//PubmedArticle"):
            pmid_element = article.find(".//PMID")
            pmid = pmid_element.text if pmid_element is not None else "No PMID available"

            title_element = article.find(".//ArticleTitle")
            title = title_element.text if title_element is not None else "No title available"

            if title_element is not None:
                title_xml = etree.tostring(title_element, encoding="unicode", method="xml")
                title = clean_html(title_xml).encode('utf-8').decode('utf-8').rstrip('.')  # Remove trailing period

            # Fetching full abstract information
            abstract_element = article.find(".//AbstractText")
            abstract = "No abstract available"
            if abstract_element is not None:
                abstract_xml = etree.tostring(abstract_element, encoding="unicode", method="xml")
                abstract = clean_html(abstract_xml).encode('utf-8').decode('utf-8')

            authors = []
            for author in article.findall(".//Author"):
                firstname = author.find("ForeName").text if author.find("ForeName") is not None else ""
                lastname = author.find("LastName").text if author.find("LastName") is not None else ""
                if firstname and lastname:
                    authors.append(f"{firstname} {lastname}")

            # Updated DOI fetching mechanism
            doi = None
            for eid in article.findall(".//ELocationID[@EIdType='doi']"):
                doi = eid.text
                break
            if not doi:  # Fallback mechanism
                for article_id in article.findall(".//ArticleId[@IdType='doi']"):
                    doi = article_id.text
                    break
            doi = doi if doi else "No DOI"

            journal_element = article.find(".//Title")
            journal = journal_element.text if journal_element is not None else "No journal available"

            # Locate the PubDate element in the JournalIssue section.
            pubdate_element = article.find(".//Journal/JournalIssue/PubDate")
            publication_date = "No publication date available"
            if pubdate_element is not None:
                # First, try to get the Year, Month, and Day if available.
                year = pubdate_element.find("Year")
                month = pubdate_element.find("Month")
                day = pubdate_element.find("Day")

                if year is not None:
                    # Build the publication date string
                    publication_date = year.text
                    if month is not None:
                        publication_date += "-" + month.text
                    if day is not None:
                        publication_date += "-" + day.text
                else:
                    # Some records provide a MedlineDate instead of individual elements.
                    medline_date = pubdate_element.find("MedlineDate")
                    if medline_date is not None:
                        publication_date = medline_date.text

            volume_element = article.find(".//Volume")
            volume = volume_element.text if volume_element is not None else "No volume available"

            issue_element = article.find(".//Issue")
            issue = issue_element.text if issue_element is not None else "No issue available"

            pages_element = article.find(".//MedlinePgn")
            pages = pages_element.text if pages_element is not None else "No pages available"

            publication_type_elements = article.findall(".//PublicationType")
            publication_types = ", ".join(pt.text for pt in publication_type_elements if pt.text is not None)

            keywords = []
            for keyword in article.findall(".//Keyword"):
                if keyword.text is not None:
                    keywords.append(keyword.text)

            pmc = article.find(".//ArticleId[@IdType='pmc']")
            pmc_id = pmc.text if pmc is not None else "No PMC ID"

            mesh_terms = [mesh.text for mesh in article.findall(".//MeshHeadingList/MeshHeading/DescriptorName")]
            mesh = ", ".join(mesh_terms) if mesh_terms else "No MeSH terms"

            grant_info = ", ".join([grant.text for grant in article.findall(".//GrantList/Grant/GrantID")]) or "No grant information"
            language = article.find(".//Language").text if article.find(".//Language") is not None else "No language information"
            issn = article.find(".//ISSN").text if article.find(".//ISSN") is not None else "No ISSN available"

            results.append({
                "PMID": pmid,
                "Title": title,
                "Authors": ", ".join(authors),
                "Abstract": abstract,
                "DOI": doi,
                "Journal": journal,
                "PublicationDate": publication_date,
                "Volume": volume,
                "Issue": issue,
                "Pages": pages,
                "PublicationType": publication_types,
                "Keywords": ", ".join(keywords) if keywords else "No keywords available",
                "PMC_ID": pmc_id,
                "MeSH_Terms": mesh,
                "GrantInfo": grant_info,
                "Language": language,
                "ISSN": issn,
            })

        print(f"Fetched details for {i + len(batch_pmids)} articles...")

    return results

def save_to_csv(data, filename):
    """
    Saves parsed article data to a CSV file in the 'Data' folder.
    If the folder does not exist, it will be created.
    """
    output_dir = "Data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Build the full file path
    file_path = os.path.join(output_dir, filename)

    with open(file_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["PMID", "Title", "Authors", "Abstract", "DOI",
                                                  "Journal", "PublicationDate", "Volume", "Issue",
                                                  "Pages", "PublicationType", "Keywords", "PMC_ID", "MeSH_Terms",
                                                  "GrantInfo", "Language", "ISSN"])
        writer.writeheader()
        writer.writerows(data)

def main():
    """
    Main function to execute the script.
    """
    query_file = "query.txt"
    if not os.path.exists(query_file):
        print(f"Error: {query_file} not found.")
        return

    with open(query_file, "r", encoding="utf-8") as file:
        query = file.read().strip()

    date_filter = input("Would you like to filter by publication date range? (yes/no): ").strip().lower()
    start_date = None
    end_date = None

    if date_filter == "yes":
        start_date = input("Enter start date (YYYY/MM/DD): ").strip()
        end_date = input("Enter end date (YYYY/MM/DD): ").strip()


    articles = fetch_all_pubmed_data(query, start_date, end_date)
    save_to_csv(articles, "pubmed.csv")
    print("Data saved to pubmed.csv.")

if __name__ == "__main__":
    main()
