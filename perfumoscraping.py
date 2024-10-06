import pyodbc
import re
import requests
from bs4 import BeautifulSoup
import random
import time


# Function to format strings for URLs
def format_for_url(text):
    return re.sub(r'[^a-zA-Z0-9]', '_', text).lower()

# Function to clean up perfume brand
def clean_perfume_brand(brand):
    # Remove the word "perfumes" and any leading spaces
    cleaned_brand = re.sub(r'\s*perfumes\s*', '', brand, flags=re.IGNORECASE)
    return cleaned_brand.strip()

# Database connection parameters
conn_str = (
    f"DRIVER={config['connection_string']['DRIVER']};"
    f"SERVER={config['connection_string']['SERVER']};"
    f"DATABASE={config['connection_string']['DATABASE']};"
    f"UID={config['connection_string']['UID']};"
    f"PWD={config['connection_string']['PWD']};"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Query to fetch required columns where main_accords is empty
query = """
    SELECT perfume_name, perfume_brand
    FROM dbo.perfumes
    WHERE main_accords IS NULL OR main_accords = ''
"""
cursor.execute(query)

# Base URL
base_url = "https://www.parfumo.com/perfumes/"
urls = []

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
    # Add more user agents as needed
]


# Process each row and construct URLs
for row in cursor.fetchall():
    perfume_name = row.perfume_name
    perfume_brand = row.perfume_brand
    
    # Clean and format names
    cleaned_perfume_brand = clean_perfume_brand(perfume_brand)
    formatted_perfume_name = format_for_url(perfume_name)
    formatted_perfume_brand = format_for_url(cleaned_perfume_brand)
    
    # Construct the URL variations
    url_with_underscores = f"{base_url}{formatted_perfume_brand}/{formatted_perfume_name}"
    url_with_both_hyphens = f"{base_url}{formatted_perfume_brand.replace('_', '-')}/{formatted_perfume_name.replace('_', '-')}"
    
    urls.append((url_with_underscores, url_with_both_hyphens, perfume_name))

# Function to scrape details from a URL
def scrape_perfume_details(url):
    headers = {
        'User-Agent': random.choice(user_agents)
    }

    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return {'Error': f'Failed to retrieve the webpage: {e}'}

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract the full page text
    page_text = soup.get_text(separator='\n', strip=True)
    lines = page_text.splitlines()

    # Initialize data containers
    main_accords = []
    top_notes = []
    heart_notes = []
    base_notes = []

    # Initialize flags and state
    collecting = None

    # Process each line
    for line in lines:
        line = line.strip()

        if 'Main accords' in line:
            collecting = 'Main accords'
            continue
        elif 'Fragrance Pyramid' in line:
            collecting = 'Fragrance Pyramid'
            continue
        elif 'Top Notes' in line:
            collecting = 'Top Notes'
            continue
        elif 'Heart Notes' in line:
            collecting = 'Heart Notes'
            continue
        elif 'Base Notes' in line:
            collecting = 'Base Notes'
            continue
        elif 'Perfumers' in line or 'Perfumer' in line or 'Ratings' in line:
            collecting = None
            continue

        # Collect data based on the current section
        if collecting == 'Main accords' and line:
            main_accords.append(line)
        elif collecting == 'Top Notes' and line:
            top_notes.append(line)
        elif collecting == 'Heart Notes' and line:
            heart_notes.append(line)
        elif collecting == 'Base Notes' and line:
            base_notes.append(line)

    return {
        'Main Accords': ', '.join(main_accords),
        'Fragrance Pyramid': {
            'Top Notes': ', '.join(top_notes),
            'Heart Notes': ', '.join(heart_notes),
            'Base Notes': ', '.join(base_notes)
        }
    }

# Update data in the SQL table
update_query = """
    UPDATE dbo.perfumes
    SET main_accords = ?,
        top_notes = ?,
        heart_notes = ?,
        base_notes = ?
    WHERE perfume_name = ?
"""

for url_with_underscores, url_with_both_hyphens, perfume_name in urls:
    details = scrape_perfume_details(url_with_underscores)
    
    if 'Error' in details:
        # If failed with underscores, try other URL format
        details = scrape_perfume_details(url_with_both_hyphens)
        if 'Error' in details:
            print(f"Skipping {perfume_name}: {details['Error']}")
            continue

    # Extract details
    main_accords = details['Main Accords']
    top_notes = details['Fragrance Pyramid']['Top Notes']
    heart_notes = details['Fragrance Pyramid']['Heart Notes']
    base_notes = details['Fragrance Pyramid']['Base Notes']
    
    # Update database
    cursor.execute(update_query, (main_accords, top_notes, heart_notes, base_notes, perfume_name))
    conn.commit()
    print(f"Updated {perfume_name}")
    time.sleep(3)

# Close the connection
conn.close()
