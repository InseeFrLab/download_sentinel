import requests
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon


def get_dep_polygon(code_dep):
    url_geo = f"https://apicarto.ign.fr/api/cadastre/commune?code_dep={code_dep}"
    resp_geo = requests.get(url_geo)

    if resp_geo.status_code == 200:
        dep_geojson = resp_geo.json()
        gdf = gpd.GeoDataFrame.from_features(dep_geojson["features"])
    else:
        print(f"⚠️ Erreur sur la commune {code_dep}: {resp_geo.status_code}")

    # 3. Fusionner les polygones des communes pour obtenir celui du département
    tarn_polygon = unary_union(gdf.geometry)

    # 4. Lisser le polygone (facteur de tolérance ajustable)
    tolerance = 0.001
    tarn_smooth = tarn_polygon.simplify(tolerance, preserve_topology=True)

    return Polygon(tarn_smooth.exterior)
