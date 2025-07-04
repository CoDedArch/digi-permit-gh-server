from shapely.geometry import shape
from shapely.wkt import dumps as shapely_to_wkt
import json


def geojson_to_ewkt(geojson_obj: dict) -> str:
    geom = shape(geojson_obj)  # Convert GeoJSON to Shapely geometry
    wkt = shapely_to_wkt(geom)  # Convert Shapely to WKT
    return f"SRID=4326;{wkt}"
