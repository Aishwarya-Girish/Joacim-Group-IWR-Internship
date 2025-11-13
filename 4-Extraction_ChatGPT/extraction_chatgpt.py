import pandas as pd
from openai import OpenAI
import json
import os

# Initialize OpenAI client
client = OpenAI(api_key="###")  # <-- Replace with your API key or use environment variable

# Step 1: Read CSV file
df = pd.read_csv("###")  # <-- replace with your file path

# Ensure required columns exist
if not {"Title", "Abstract"}.issubset(df.columns):
    raise ValueError("CSV must contain 'Title' and 'Abstract' columns")

results = []

# Step 2: Loop through each record
for _, row in df.head(100).iterrows():

    title = str(row["Title"])
    abstract = str(row["Abstract"])
    
    text = f"Title: {title}\nAbstract: {abstract}"

    # Step 3: Prompt ChatGPT for plastics, paper type, and source type
    prompt = f"""
    You are an expert in environmental and materials science, specialized in analyzing research literature.

    Read the following research paper title and abstract, and identify three pieces of information:

    1. **Plastics or Polymers**: identify all kinds of plastics or polymers mentioned.
       -  If none are mentioned, reply with a single word: 'None'.
       -  Return only a comma-separated list of plastics (e.g., 'PE, PET, PVC') or 'None'.

    2. **Paper Type**: Determine whether the paper is a 'Review Paper' or a 'Primary Study'.
       - A review paper summarizes prior research.
       - A primary study presents new experiments or data.

    3. **Source Type**: Identify the environmental or sampling source being studied.
       - Examples: River, Estuary, Bay, Lake, Reservoir, Mangrove, WWTP Effluent, Open Ocean, Marine, Intertidal Zone, etc.
       - If unclear, return 'Unknown'.
       
    4.  **Method_AR_Detection**:Summarize the antibiotic resistance detection methodology
        - Examples: qPCR, PCR, Metagenomics, sequencing platforms, reference databases, bioinformatics tools, etc.

    Return your answer strictly in JSON format as:
    {{
        "plastics_found": "...",
        "paper_type": "...",
        "source_type": "...",
        method_ar_detection: "..."
    }}

    Text:
    {text}
    """

    # Step 4: Query ChatGPT
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a scientific text analysis assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Step 5: Extract and parse response
    content = response.choices[0].message.content.strip()

    plastics_found, paper_type, source_type = "None", "Unknown", "Unknown"

    try:
        parsed = json.loads(content)
        plastics_found = parsed.get("plastics_found", "None")
        paper_type = parsed.get("paper_type", "Unknown")
        source_type = parsed.get("source_type", "Unknown")
    except Exception:
        # fallback: simple keyword extraction if JSON parsing fails
        if "Review" in content:
            paper_type = "Review Paper"
        elif "Primary" in content:
            paper_type = "Primary Study"
        for term in ["River", "Estuary", "Lake", "Bay", "Reservoir", "Mangrove", "WWTP", "Ocean", "Marine"]:
            if term.lower() in content.lower():
                source_type = term
                break

    print(f"Processing: {title}")
    print(f"  → Plastics: {plastics_found}")
    print(f"  → Paper Type: {paper_type}")
    print(f"  → Source Type: {source_type}\n")

    # Step 6: Append result
    results.append({
        "title": title,
        "abstract": abstract,
        "plastics_found": plastics_found,
        "paper_type": paper_type,
        "source_type": source_type
    })

# Step 7: Save output
output_df = pd.DataFrame(results)
output_df.to_csv("output_with_source_typexx.csv", index=False)

print("✅ Done! Created 'output_with_source_type.csv' with plastics, paper type, and source type.")
