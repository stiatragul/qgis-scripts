## plotting distribution as seperate layers
## When visualising distribution of different species. I usually want to different species to show up as different colours but it usually takes time to load in the map and then manually classify different species. 
## This script assumes you have two things (examples of both can be found in the data folder of this repo). 
# 1. A shape file for your base map
# 2. a csv file with lat/long, genus, species, and optionally lineage within the species. 
# Run this script in the Python console of QGIS.


from qgis.core import QgsVectorLayer, QgsPointXY, QgsProject, QgsField, QgsFeature, QgsGeometry, QgsRendererCategory, QgsCategorizedSymbolRenderer
from qgis.PyQt.QtCore import QVariant
import csv
import random

# Path to your CSV file
csv_file_path = "./data/example.csv"
# csv_file_path = "path/to/your/file.csv"

# Path to your Australia shapefile
australia_shapefile_path = "./data/aust_cd66states.shp"
# australia_shapefile_path = "./data/aust_cd66states.shp"

# Load Australia shapefile as a layer
australia_layer = QgsVectorLayer(australia_shapefile_path, "Australia", "ogr")

# Check if the layer loaded successfully
if not australia_layer.isValid():
    print("Error: Failed to load Australia shapefile")
else:
    # Set the fill color of the Australia layer to light gray
    australia_layer.renderer().symbol().setColor(QColor("#f0f0f0"))  # Light gray color
    australia_layer.triggerRepaint()  # Refresh the layer to apply changes

    # Add the layer to the map canvas
    QgsProject.instance().addMapLayer(australia_layer)

    # Read the CSV file and create point layers for each genus_species
    with open(csv_file_path, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        genus_species_layers = {}  # Dictionary to store point layers for each genus_species
        for row in csvreader:
            genus = row["genus"]  # Get genus from "genus" column
            species = row["species"]  # Get species from "species" column
            genus_species = f"{genus}_{species}"  # Join genus and species with underscore
            if genus_species not in genus_species_layers:
                # Create a new point layer for the genus_species if it doesn't exist
                layer_name = f"{genus_species}"  # Name the layer based on genus_species
                crs = QgsProject.instance().crs()
                point_layer = QgsVectorLayer("Point?crs={}".format(crs.authid()), layer_name, "memory")
                # Define fields for the layer
                fields = QgsFields()
                fields.append(QgsField("Lineage", QVariant.String))  # Add field for lineage classification
                # Add more fields if needed
                point_layer.dataProvider().addAttributes(fields)
                point_layer.updateFields()
                # Add the layer to the map canvas and store it in the dictionary
                QgsProject.instance().addMapLayer(point_layer)
                genus_species_layers[genus_species] = point_layer
            else:
                # Get the existing point layer for the genus_species
                point_layer = genus_species_layers[genus_species]

            # Add point feature to the layer
            lineage = row["lineage"]  # Get lineage from "lineage" column
            latitude_str = row["decimal_latitude"]  # Get latitude from "decimal_latitude" column
            longitude_str = row["decimal_longitude"]  # Get longitude from "decimal_longitude" column
            # Check if latitude and longitude values are valid
            if latitude_str != 'NA' and longitude_str != 'NA':
                try:
                    latitude = float(latitude_str)
                    longitude = float(longitude_str)
                    point = QgsPointXY(longitude, latitude)
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromPointXY(point))
                    # Assign attributes including lineage
                    feature.setAttributes([lineage])  # Assign lineage value to the "Lineage" field
                    point_layer.dataProvider().addFeature(feature)
                except ValueError:
                    print(f"Invalid latitude or longitude value: {latitude_str}, {longitude_str}")

            # Set symbology for each genus_species layer
            random.seed(42)  # Set seed for reproducible random colors
            for genus_species, point_layer in genus_species_layers.items():
                # Define the categorized symbol renderer
                renderer = QgsCategorizedSymbolRenderer("Lineage")
                # Define categories based on unique lineage values
                unique_lineages = list(point_layer.uniqueValues(point_layer.fields().indexFromName("Lineage")))
                for lineage in unique_lineages:
                    symbol = QgsSymbol.defaultSymbol(point_layer.geometryType())
                    category_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))  # Generate random color
                    symbol.setColor(category_color)
                    # Use circle symbol for all lineages
                    symbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': category_color.name()})
                    category = QgsRendererCategory(lineage, symbol, str(lineage))
                    renderer.addCategory(category)  # Use addCategory() method to add categories
                point_layer.setRenderer(renderer)

                # Refresh the layer to apply symbology changes
                point_layer.triggerRepaint()

    # Refresh the map canvas
    iface.mapCanvas().refresh()
