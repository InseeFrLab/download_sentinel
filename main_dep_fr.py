import os
import shutil
import ee
import geemap

from src.utils import get_root_path
from src.constants import dep_dom_to_crs
from src.contours import get_dep_polygon
from src.download_ee_images import get_s2_from_ee
from src.process_ee_images import upload_satelliteImages


def download_sentinel2(bucket, DEP, START_DATE, END_DATE, CLOUD_FILTER, DIM):
    print("Lancement du téléchargement des données SENTINEL2")
    root_path = get_root_path()

    path_s3 = f"""data-raw/SENTINEL2/{DEP}/{int(START_DATE[0:4])}/"""
    path_local = os.path.join(
        root_path,
        f"""data/SENTINEL2/{DEP}/{int(START_DATE[0:4])}""",
    )

    os.makedirs(path_local, exist_ok=True)

    if DEP in dep_dom_to_crs.keys():
        EPSG = dep_dom_to_crs[DEP]
    else:
        EPSG = "EPSG:2154"

    polygons_dep = get_dep_polygon(DEP)

    for num_poly, polygon_dep in enumerate(polygons_dep.geoms):
        coords = list(polygon_dep.exterior.coords)
        aoi = ee.Geometry.Polygon(coords)

        s2_sr_harmonized = get_s2_from_ee(aoi, START_DATE, END_DATE, CLOUD_FILTER)

        fishnet = geemap.fishnet(aoi, rows=4, cols=4, delta=0.5)
        geemap.download_ee_image_tiles(
            s2_sr_harmonized,
            fishnet,
            path_local,
            prefix="data_",
            crs=EPSG,
            scale=10,
            num_threads=10,
        )

        upload_satelliteImages(
            path_local,
            f"s3://{bucket}/{path_s3}",
            DIM,
            12,
            num_poly,
            polygon_dep.exterior,
            EPSG,
            False,
        )

        shutil.rmtree(path_local, ignore_errors=True)
        os.makedirs(path_local, exist_ok=True)

    print(f"""Le processus est fini et les images sont stockées ici {f"s3://{bucket}/{path_s3}"}""")


if __name__ == "__main__":
    bucket = "projet-hackathon-ntts-2025"
    DEP = "976"
    DIM = 250

    # todo : recup des images sur les 4 saisons
    START_DATE = "2024-10-15"
    END_DATE = "2024-11-29"
    CLOUD_FILTER = 20

    service_account = "slums-detection-sa@ee-insee-sentinel.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(service_account, "GCP_credentials.json")

    # Initialize the library.
    ee.Initialize(credentials)
    download_sentinel2(bucket, DEP, START_DATE, END_DATE, CLOUD_FILTER, DIM)
