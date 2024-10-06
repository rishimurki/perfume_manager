# conn = pyodbc.connect(conn_str)
import pyodbc
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

# Database connection details
conn_str = (
    f"DRIVER={config['connection_string']['DRIVER']};"
    f"SERVER={config['connection_string']['SERVER']};"
    f"DATABASE={config['connection_string']['DATABASE']};"
    f"UID={config['connection_string']['UID']};"
    f"PWD={config['connection_string']['PWD']};"
)


# Connect to the Azure SQL Database
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Create the 'perfumes' table if it doesn't exist
cursor.execute('''
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='perfumes' AND xtype='U')
    CREATE TABLE perfumes (
        id INT PRIMARY KEY IDENTITY(1,1),
        perfume_name NVARCHAR(255),
        perfume_brand NVARCHAR(255),
        perfume_link NVARCHAR(255)
    )
''')
conn.commit()

# Function to insert data into the database
def insert_perfume(perfume_name, perfume_brand, perfume_link):
    # Check if a perfume with the same name already exists
    cursor.execute('''
        SELECT COUNT(*) FROM perfumes
        WHERE perfume_name = ?
    ''', (perfume_name,))
    count = cursor.fetchone()[0]

    if count == 0:
        # Insert the new perfume if it does not already exist
        cursor.execute('''
            INSERT INTO perfumes (perfume_name, perfume_brand, perfume_link)
            VALUES (?, ?, ?)
        ''', (perfume_name, perfume_brand, perfume_link))
        conn.commit()
        print(f"Inserted: {perfume_name} - {perfume_brand}")
    else:
        print(f"Perfume with name '{perfume_name}' already exists, skipping insertion.")


# Start Selenium and scrape data
driver = webdriver.Firefox()
driver.get('https://www.fragrantica.com/search/')

def click_show_more_results():
    try:
        # Wait until the button is clickable
        show_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show more results')]"))
        )
        # Scroll to the button and click it
        driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
        driver.execute_script("arguments[0].click();", show_more_button)       
        print("Clicked 'Show More Results' button")
    except Exception as e:
        print(f"Error clicking 'Show More Results': {e}")

# Click the "Show More Results" button several times
for _ in range(100):
    click_show_more_results()

time.sleep()

# Now continue scraping
try:
    elements = driver.find_elements(By.XPATH, "//div[@id='app']//div[contains(@class, 'cell card fr-news-box')]")
    for element in elements:
        details = element.text.splitlines()
        if len(details) >= 2:  # Ensure there are at least 2 lines
            perfume_name = details[0]
            perfume_brand = details[1]
            print(perfume_brand, perfume_name)
            try:
                link = element.find_element(By.XPATH, ".//a[contains(@href, '.html')]")
                perfume_link = link.get_attribute("href")
                print("Perfume Link:", perfume_link)
            except:
                perfume_link = None
                print("No link found for this perfume.")
            
            # Insert data into the database
            insert_perfume(perfume_name, perfume_brand, perfume_link)
except Exception as e:
    print(f"Error: {e}")

# Close the WebDriver and database connection
driver.quit()
conn.close()
