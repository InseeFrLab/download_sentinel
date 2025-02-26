import random
import math
from shapely.geometry import box
import geopandas as gpd
from tqdm import tqdm


def sample_bboxes_from_multipolygon(multipolygon, bbox_area_km2, sample_ratio=0.01):
    sampled_bboxes = []

    print('Sample country polygon')
    for polygon in tqdm(multipolygon.geoms):
        if polygon.area*10000 < 6000:
            poly_selected_bboxes = [polygon]
        else:
            poly_selected_bboxes = random_squares_in_polygon(polygon, square_percent_area=0.05, total_percent_area=1.0)
        if poly_selected_bboxes:
            sampled_bboxes.extend(poly_selected_bboxes)

    return sampled_bboxes


def random_squares_in_polygon(big_polygon, square_percent_area=0.05, total_percent_area=1.0):
    """
    Sélectionne des polygones carrés aléatoires dans un grand polygone pour couvrir un % donné du territoire.

    Args:
        big_polygon (shapely.geometry.Polygon): Le polygone englobant (en WGS 84, EPSG:4326).
        square_percent_area (float): Pourcentage de la surface totale à couvrir par chaque carré (ex: 0.05 pour 0,05%).
        total_percent_area (float): Pourcentage total du territoire à couvrir (ex: 1 pour 1%).

    Returns:
        list of shapely.geometry.Polygon: Liste de carrés aléatoires non chevauchants.
    """
    # Convertir en projection métrique (EPSG:3857) pour obtenir la surface en km²
    gdf = gpd.GeoDataFrame(geometry=[big_polygon], crs="EPSG:4326").to_crs("EPSG:3857")
    big_polygon_m = gdf.geometry.iloc[0]
    total_area_km2 = big_polygon_m.area / 1e6  # Conversion m² → km²

    # Calculer la surface cible totale et par carré
    total_target_area_km2 = (total_percent_area / 100) * total_area_km2
    square_target_area_km2 = (square_percent_area / 100) * total_area_km2

    # Déterminer combien de carrés sont nécessaires
    num_squares = math.ceil(total_target_area_km2 / square_target_area_km2)

    # Convertir en EPSG:4326 pour la génération des carrés
    gdf = gdf.to_crs("EPSG:4326")
    big_polygon = gdf.geometry.iloc[0]

    # Calculer la taille d'un carré en km
    square_size_km = math.sqrt(square_target_area_km2)

    selected_squares = []
    attempts = 0
    max_attempts = 5000  # Éviter une boucle infinie

    while len(selected_squares) < num_squares and attempts < max_attempts:
        attempts += 1
        # Choisir un point de départ aléatoire dans la bounding box
        minx, miny, maxx, maxy = big_polygon.bounds
        rand_x = random.uniform(minx, maxx)
        rand_y = random.uniform(miny, maxy)

        # Convertir la taille en degrés
        square_size_deg_lat = square_size_km / 111.0  # Approximation
        square_size_deg_lon = square_size_km / (111.0 * abs(math.cos(math.radians(rand_y))) + 1e-6)

        # Créer le carré
        square = box(rand_x, rand_y, rand_x + square_size_deg_lon, rand_y + square_size_deg_lat)

        # Vérifier qu'il est bien dans le polygone et qu'il ne chevauche pas les autres
        if big_polygon.contains(square) and all(not square.intersects(s) for s in selected_squares):
            selected_squares.append(square)

    if len(selected_squares) < num_squares:
        raise ValueError(f"Impossible de placer {num_squares} carrés sans chevauchement après {max_attempts} essais.")

    return selected_squares
