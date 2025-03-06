import requests
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon
from src.constants import contries_filepath, nuts3_filepath


def get_dep_polygon(code_dep: str) -> MultiPolygon:
    code_dep_new = code_dep[:2]

    url_geo = f"https://apicarto.ign.fr/api/cadastre/commune?code_dep={code_dep_new}"
    resp_geo = requests.get(url_geo)

    if resp_geo.status_code == 200:
        dep_geojson = resp_geo.json()
        gdf = gpd.GeoDataFrame.from_features(dep_geojson["features"])
    else:
        print(f"⚠️ Erreur sur la commune {code_dep}: {resp_geo.status_code}")

    if code_dep_new != code_dep:
        gdf = gdf[gdf['code_insee'].str[:3] == code_dep]

    # 3. Fusionner les polygones des communes pour obtenir celui du département
    dep_polygon = unary_union(gdf.geometry)

    # 4. Lisser le polygone (facteur de tolérance ajustable)
    tolerance = 0.001
    dep_smooth = dep_polygon.simplify(tolerance, preserve_topology=True)

    # Si c'est un polygon, je le passe en multipolygon pour toujours avoir un multipolygon peu importe le département
    # Il existe des départements avec des îles (ex Guadeloupe avec Marie Galante) et donc qui ont plusieurs polygones
    if isinstance(dep_smooth, Polygon):
        dep_smooth = MultiPolygon([dep_smooth])

    return dep_smooth


def get_country_polygon(country_id: str):
    gdf = gpd.read_file(contries_filepath)
    # gdf_eu = gdf[gdf['EU_STAT'] == 'T'][['CNTR_ID', 'NAME_ENGL']]

    poly_country = gdf[gdf['CNTR_ID'] == country_id].iloc[0].geometry

    # Lisser le polygone (facteur de tolérance ajustable)
    tolerance = 0.001
    poly_country_smooth = poly_country.simplify(tolerance, preserve_topology=True)

    if isinstance(poly_country_smooth, Polygon):
        poly_country_smooth = MultiPolygon([poly_country_smooth])

    return poly_country_smooth


def get_nuts3_polygon(nuts3_id: str):
    gdf = gpd.read_file(nuts3_filepath)

    poly_nuts3 = gdf[gdf['NUTS_ID'] == nuts3_id].iloc[0].geometry

    # Lisser le polygone (facteur de tolérance ajustable)
    tolerance = 0.001
    poly_nuts3_smooth = poly_nuts3.simplify(tolerance, preserve_topology=True)

    if isinstance(poly_nuts3_smooth, Polygon):
        poly_nuts3_smooth = MultiPolygon([poly_nuts3_smooth])

    return poly_nuts3_smooth
