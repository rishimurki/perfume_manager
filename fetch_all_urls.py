import pyodbc
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Function to connect to Azure SQL Database

conn_str = (
    f"DRIVER={config['connection_string']['DRIVER']};"
    f"SERVER={config['connection_string']['SERVER']};"
    f"DATABASE={config['connection_string']['DATABASE']};"
    f"UID={config['connection_string']['UID']};"
    f"PWD={config['connection_string']['PWD']};"
)

conn = pyodbc.connect(conn)

cursor = conn.cursor()

# Function to insert perfume data into the database
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



# Function to fetch perfumes and insert them into the database
def fertch_all_perfumes(li, conn):
    # Loop through all URLs in the list
    for i in range(20,len(li)):
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
   
        try:
            # Open the webpage
            driver.get(li[i][0])

            # Find and extract the elements with class 'flex-child-auto'
            elements = driver.find_elements(By.XPATH, "//div[@class='flex-child-auto']")
            for element in elements:
                try:
                    # Inside the div, find the h3 and the <a> tag
                    link_element = element.find_element(By.XPATH, ".//h3/a")
                    link = link_element.get_attribute("href")
                    link_text = link_element.text
                    print(f"Link: {link}, Text: {link_text}")
                    
                    # Insert data into the database
                    insert_perfume(link_text, li[i][1], link)
                    
                except Exception as e:
                    print(f"Error finding <a> tag: {e}")
                    print('here')
        except Exception as e:
            print(f"Error fetching {li[i][0]}: {e}")
    
        # Close the WebDriver after scraping each URL
        driver.quit()

# Function to get brand names and links from the search page
def get_brand_names():
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    
    li = []
    li2=[]
    driver.get('https://www.fragrantica.com/search/')
    
    try:
        elements = driver.find_elements(By.XPATH, "//div[@style='display: flex; align-items: start; text-align: start; line-height: 1.2em; height: 1.7em; overflow: hidden;']")
        
        for element in elements:
            try:
                # Inside the span, find the <a> tag and extract the link and text
                link_element = element.find_element(By.XPATH, ".//span[@style='display: -webkit-box; -webkit-line-clamp: 1; -moz-box-orient: vertical; overflow: hidden; text-overflow: ellipsis;']//a")
                link = link_element.get_attribute("href")
                link_text = link_element.text     
                li.append([link, link_text])
                li2.append(link_text)
            except Exception as e:
                print(f"Error finding <a> tag inside span: {e}")
    except Exception as e:
        print(f"Error finding div with style attribute: {e}")
    
    driver.quit()
    print(li2)
    return None
    return li

# Main function to scrape and insert data into Azure SQL Database
def main():
    perfume_data = get_brand_names()  # Get list of perfume URLs and names
    fertch_all_perfumes(perfume_data, conn)  # Fetch perfumes and insert into DB
    conn.close()  # Close the database connection

# Run the main function
main()

