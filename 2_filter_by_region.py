import os
import json
from shapely.geometry import shape, Point, Polygon
from datetime import datetime
import csv

# Constants
folder = "bookcases"

# Define the order of the columns
column_order = ['date', 'total', 'out_of_region', 'Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté', 'Bretagne', 'Centre-Val de Loire', 'Corse', 'Grand Est', 'Hauts-de-France', 'Île-de-France', 'Normandie', 'Nouvelle-Aquitaine', 'Occitanie', 'Pays de la Loire', 'Provence-Alpes-Côte d\'Azur']

# Paths to the input files
regions_file_path = 'assets/georef-france-region-custom.geojson'
bookcases_file_path = f'{folder}/bookcases.geojson'
csv_output_path = 'assets/bookcase_count_history.csv'

# Load the regions and bookcases data
with open(regions_file_path, 'r', encoding='utf-8') as f:
    regions_data = json.load(f)

# Load the bookcases data
with open(bookcases_file_path, 'r', encoding='utf-8') as f:
    bookcases_data = json.load(f)

# Create the output directory inside folder
output_dir = f'{folder}/Régions Françaises'
os.makedirs(output_dir, exist_ok=True)

# Function to check if a point is inside a region
def is_point_in_region(point, region_shape):
    return region_shape.contains(point)

# Preprocess regions to convert geometries to shapes
regions_shapes = [
    (region['properties']['reg_name'], shape(region['geometry']) if region['geometry']['type'] != 'LineString' else Polygon(region['geometry']['coordinates']))
    for region in regions_data['features']
]

# Initialize GeoJSON structures
out_of_region_bookcases = {
    "type": "FeatureCollection",
    "features": []
}

total_bookcases = len(bookcases_data['features'])

# Dictionary to hold bookcases for each region
region_bookcases = {region_name: {"type": "FeatureCollection", "features": []} for region_name, _ in regions_shapes}

# Process each bookcase
for bookcase in bookcases_data['features']:
    point = Point(bookcase['geometry']['coordinates'])
    in_any_region = False
    for region_name, region_shape in regions_shapes:
        if is_point_in_region(point, region_shape):
            region_bookcases[region_name]['features'].append(bookcase)
            in_any_region = True
            break
    if not in_any_region:
        out_of_region_bookcases['features'].append(bookcase)

# Export bookcases to .geojson files for each region
for region_name, bookcases in region_bookcases.items():
    geojson_output_path = os.path.join(output_dir, f'{region_name}.geojson')
    with open(geojson_output_path, 'w', encoding='utf-8') as f:
        json.dump(bookcases, f, ensure_ascii=False, indent=2)

# Export out-of-region bookcases to .geojson
out_geojson_output_path = f'{folder}/out-france-metro.geojson'
with open(out_geojson_output_path, 'w', encoding='utf-8') as f:
    json.dump(out_of_region_bookcases, f, ensure_ascii=False, indent=2)

# Create CSV header if the file doesn't exist
if not os.path.exists(csv_output_path):
    with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_order)

# Get the current date
current_date = datetime.now().strftime("%Y-%m-%d")

# Prepare data for CSV
region_counts = {region_name: len(bookcases['features']) for region_name, bookcases in region_bookcases.items()}
total_in_regions = sum(region_counts.values())
row = [current_date, total_bookcases, len(out_of_region_bookcases['features'])] + [region_counts.get(region_name, 0) for region_name in column_order[3:]]

# Write data to CSV
with open(csv_output_path, 'a', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(row)

# Print completion message
print(f"CSV file updated at {csv_output_path}")
print("Processing complete!")
