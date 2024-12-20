import geojson
import json
import os
import re
import subprocess
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import shutil

# Set up Selenium WebDriver options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument(f'user-agent={UserAgent().chrome}')

def find_chromedriver_path():
    if os.name == 'nt':  # Windows
        result = subprocess.run(['where', 'chromedriver.exe'], capture_output=True, text=True)
        if result.returncode == 0:
            paths = result.stdout.splitlines()
            if paths:
                return paths[0]
        raise FileNotFoundError("chromedriver.exe not found in PATH")
    else:  # Linux or macOS
        return '/usr/bin/chromedriver'  # Update with the path to your chromedriver

chromedriver_path = find_chromedriver_path()
service = ChromeService(executable_path=chromedriver_path)

# Set up WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Constants
URL = 'https://www.boite-a-lire.com/'

# Set the folder path to "bookcases"
folder_path = 'bookcases'

# Delete the folder if it exists
if os.path.exists(folder_path):
    shutil.rmtree(folder_path)

# Create the folder
os.makedirs(folder_path, exist_ok=True)

# Get the webpage content
driver.get(URL)

# Wait for the relevant script tags to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "script")))

# Extract page source
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

# Regex pattern to find JSON variables
pattern = re.compile(r'var json[0-9]+ = ({.*?});', re.DOTALL)

# Extract JSON objects directly using regex
jsonArray = []
for script in soup.find_all('script'):
    if script.string:
        matches = pattern.findall(script.string)
        for match in matches:
            try:
                json_obj = json.loads(match)
                jsonArray.append(json_obj)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {str(e)}")
                print(f"JSON string: {match}")

total_bookcases = len(jsonArray)
print(f"Found {total_bookcases} bookcases on the webpage")

# Sort data by id in descending order
jsonArray.sort(key=lambda x: x["id"], reverse=True)

# Initialize GeoJSON structures
features = []
seen_coordinates = set()
duplicates = 0

# Check for duplicates and convert to GeoJSON
for item in jsonArray:
    coordinates = tuple(map(float, item["coord_gps"].split(',')))
    feature = geojson.Feature(
        geometry=geojson.Point((coordinates[1], coordinates[0])),
        properties=item
    )
    if coordinates not in seen_coordinates:
        seen_coordinates.add(coordinates)
        features.append(feature)
    else:
        duplicates += 1

# Create GeoJSON FeatureCollection
geojson_data = geojson.FeatureCollection(features)

# Save the GeoJSON to a file
output_file_path = os.path.join(folder_path, "bookcases.geojson")
with open(output_file_path, 'w', encoding='utf-8') as file:
    geojson.dump(geojson_data, file, ensure_ascii=False, indent=4)

# Log the results
print(f"GeoJSON created: {output_file_path}")
print(f"Total bookcases: {total_bookcases}")
print(f"Unique bookcases: {len(geojson_data['features'])}")
print(f"Duplicate bookcases: {duplicates}")

# Exit with a non-zero status code if no bookcases were found
if len(geojson_data['features']) == 0:
    print("No bookcases found. Exiting with an error.")
    exit(1)

driver.quit()
