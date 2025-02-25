import shapely
import random
from tqdm import tqdm


def generate_random_bbox_within(polygon, bbox_area_km2):
    """Génère une bbox de superficie bbox_area_km2 km² à l'intérieur d'un polygone"""
    minx, miny, maxx, maxy = polygon.bounds
    bbox_size = (bbox_area_km2 * 1_000_000) ** 0.5  # Convertir km² en m et obtenir la taille du carré

    attempts = 1000  # Nombre max d'essais pour trouver une bbox valide
    for _ in range(attempts):
        rand_x = random.uniform(minx, maxx - bbox_size)
        rand_y = random.uniform(miny, maxy - bbox_size)
        bbox = shapely.geometry.box(rand_x, rand_y, rand_x + bbox_size, rand_y + bbox_size)

        if polygon.contains(bbox):  # Vérifie si la bbox est bien dans le polygone
            return bbox
    return None  # Si aucun bbox valide trouvé


def sample_bboxes_from_multipolygon(multipolygon, bbox_area_km2, sample_ratio=0.1):
    """Sélectionne des bounding boxes de bbox_area_km2 km² couvrant 10% de chaque polygone"""
    sampled_bboxes = []

    print('Sample contry polygon')
    for polygon in tqdm(multipolygon.geoms):  # Boucle sur chaque polygone du MultiPolygon
        polygon_area_km2 = polygon.area / 1_000_000  # Convertir m² en km²

        # Cas où le polygone est trop petit (moins de 10 km²)
        if polygon_area_km2 < bbox_area_km2:
            sampled_bboxes.append(shapely.geometry.box(*polygon.bounds))  # Ajouter la bbox complète du polygone
            continue  # Passer au suivant

        # Nombre de bboxes nécessaires pour échantillonner 10% de la surface
        num_bboxes = int((polygon_area_km2 * sample_ratio) / bbox_area_km2)

        selected_bboxes = set()
        while len(selected_bboxes) < num_bboxes:
            bbox = generate_random_bbox_within(polygon, bbox_area_km2)
            if bbox and bbox not in selected_bboxes:
                selected_bboxes.add(bbox)

        sampled_bboxes.extend(selected_bboxes)

    return sampled_bboxes
