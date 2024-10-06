''' code for scraping accords and notes of already scraped perfumes'''

import pyodbc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import random

# Set up the headless browser option

options = Options()
options.add_argument('--headless')  # Enable headless mode
options.add_argument('--no-sandbox')

# Initialize the WebDriver

# Azure SQL Database connection settings
conn_str = (
    f"DRIVER={config['connection_string']['DRIVER']};"
    f"SERVER={config['connection_string']['SERVER']};"
    f"DATABASE={config['connection_string']['DATABASE']};"
    f"UID={config['connection_string']['UID']};"
    f"PWD={config['connection_string']['PWD']};"
)

conn = pyodbc.connect(conn_str)




driver_count = 0
driver_limit = 9

def get_driver():
    global driver_count
    # Alternate between Firefox and Edge after every 60 requests
    if driver_count < driver_limit:
        print("Switching to Edge...")
        driver = webdriver.Edge(options=options)
        
    else:
        print("Using Firefox...")
        driver = webdriver.Firefox(options=options)
        if driver_count >= driver_limit * 2:
            # Reset the counter to alternate back to Firefox
            driver_count = 0

    driver_count += 1
    return driver



# Function to scrape perfume data
def scrap_perfume(url):
    time.sleep(random.uniform(20, 30))  # Delay between requests
    # driver=get_driver()
    choice=random.choice(['Firefox','Edge'])
    if choice=='Edge':
        driver = webdriver.Edge(options=options)
    else:
        driver = webdriver.Firefox(options=options)

    driver.get(url)
    page_text = driver.find_element(By.TAG_NAME, "body").text
    lines = page_text.splitlines()
    
    if lines:
        main_accords = []
        top_notes = []
        heart_notes = []
        base_notes = []

        # Initialize flags and state
        collecting = None

        # Process each line
        for line in lines:
            line = line.strip()

            if 'main accords' in line:
                collecting = 'main accords'
                continue
            elif 'I have it' in line:
                collecting = 'skip'
                continue
            elif 'Top Notes' in line:
                collecting = 'Top Notes'
                continue
            elif 'Middle Notes' in line:
                collecting = 'Middle Notes'
                continue
            elif 'Base Notes' in line:
                collecting = 'Base Notes'
                continue
            elif 'Vote' in line:
                collecting = None
                continue

            # Collect data based on the current section
            if collecting == 'main accords' and line:
                main_accords.append(line)

            elif collecting == 'Top Notes' and line:
                top_notes.append(line)

            elif collecting == 'Middle Notes' and line:
                heart_notes.append(line)

            elif collecting == 'Base Notes' and line:
                base_notes.append(line)
        driver.quit()

        return {
            'Main Accords': ', '.join(main_accords),
            'Fragrance Pyramid': {
                'Top Notes': ', '.join(top_notes),
                'Heart Notes': ', '.join(heart_notes),
                'Base Notes': ', '.join(base_notes)
            }
        }
    else:
        return {'Error': 'Failed to retrieve the webpage'}

# Fetch data from Azure SQL Database
def fetch_links_from_db():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, perfume_name, perfume_brand, perfume_link, main_accords, top_notes, heart_notes, base_notes 
        FROM dbo.perfumes
    """)
    return cursor.fetchall()

# Update the database with scraped data
def update_db_with_scraped_data(id, main_accords, top_notes, heart_notes, base_notes):
    cursor = conn.cursor()
    query = """
    UPDATE dbo.perfumes
    SET main_accords = ?, top_notes = ?, heart_notes = ?, base_notes = ? 
    WHERE id = ?
    """
    cursor.execute(query, (main_accords, top_notes, heart_notes, base_notes, id))
    conn.commit()

# Main function to scrape and update
def main():
    rows = fetch_links_from_db()
    
    for row in rows:
        id, perfume_name, perfume_brand, link, main_accords, top_notes, heart_notes, base_notes = row

        # Skip rows that already have values in these columns
        if not (main_accords or top_notes or heart_notes or base_notes):
            print(f"Scraping perfume: {perfume_name} - {link}")
            
            scraped_data = scrap_perfume(link)
            
            if 'Error' not in scraped_data:
                main_accords = scraped_data['Main Accords']
                top_notes = scraped_data['Fragrance Pyramid']['Top Notes']
                heart_notes = scraped_data['Fragrance Pyramid']['Heart Notes']
                base_notes = scraped_data['Fragrance Pyramid']['Base Notes']
                
                # Update the scraped data in the database
                update_db_with_scraped_data(id, main_accords, top_notes, heart_notes, base_notes)
            else:
                print(f"Failed to scrape {link}")
        else:
            print(f"Skipping already updated perfume: {perfume_name} - {link}")

    # Close the WebDriver and database connection
    conn.close()

# Run the main scraping and update process
main()
