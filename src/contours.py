import requests
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon
from src.constants import shapefile_path


def get_dep_polygon(code_dep: str) -> MultiPolygon:
    url_geo = f"https://apicarto.ign.fr/api/cadastre/commune?code_dep={code_dep}"
    resp_geo = requests.get(url_geo)

    if resp_geo.status_code == 200:
        dep_geojson = resp_geo.json()
        gdf = gpd.GeoDataFrame.from_features(dep_geojson["features"])
    else:
        print(f"⚠️ Erreur sur la commune {code_dep}: {resp_geo.status_code}")

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


def get_contry_polygon(contry_id: str):
    gdf = gpd.read_file(shapefile_path)
    poly_contry = gdf[gdf['CNTR_ID'] == contry_id].iloc[0].geometry

    # Lisser le polygone (facteur de tolérance ajustable)
    tolerance = 0.001
    poly_contry_smooth = poly_contry.simplify(tolerance, preserve_topology=True)

    if isinstance(poly_contry_smooth, Polygon):
        poly_contry_smooth = MultiPolygon([poly_contry_smooth])

    return poly_contry_smooth
