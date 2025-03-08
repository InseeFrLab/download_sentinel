import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from src.constants import nuts3_filepath, polygon_ukraine_next_ue
import random


def get_sampled_country_polygon(country_id: str, sample_prop: float):
    gdf = gpd.read_file(nuts3_filepath)

    country_gdf = gdf[gdf['CNTR_CODE'] == country_id]

    nuts3_polygons = country_gdf.geometry.tolist()

    if sample_prop != 1:
        k = len(nuts3_polygons)*sample_prop
        nuts3_polygons_sampled = random.sample(nuts3_polygons, k)
    else:
        nuts3_polygons_sampled = nuts3_polygons

    nuts3_polygons_sampled_extended = []
    for poly in nuts3_polygons_sampled:
        if isinstance(poly, Polygon):
            nuts3_polygons_sampled_extended.append()
        if isinstance(poly, MultiPolygon):
            for mini_poly in poly.geoms:
                nuts3_polygons_sampled_extended.append(mini_poly)

    return nuts3_polygons_sampled_extended


def get_nuts3_polygon(nuts3_id: str):
    if nuts3_id == "UKRAINE":
        poly_nuts3 = Polygon(polygon_ukraine_next_ue["coordinates"][0])

    else:
        gdf = gpd.read_file(nuts3_filepath)
        poly_nuts3 = gdf[gdf['NUTS_ID'] == nuts3_id].iloc[0].geometry

    # Lisser le polygone (facteur de tolérance ajustable)
    tolerance = 0.001
    poly_nuts3_smooth = poly_nuts3.simplify(tolerance, preserve_topology=True)

    if isinstance(poly_nuts3_smooth, Polygon):
        poly_nuts3_smooth = MultiPolygon([poly_nuts3_smooth])

    return poly_nuts3_smooth
