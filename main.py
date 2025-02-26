import os
import shutil
import ee
import geemap
import argparse
import time

from src.utils import get_root_path
from src.contours import get_country_polygon
from src.sample_polygon import sample_bboxes_from_multipolygon
from src.download_ee_images import get_s2_from_ee
from src.process_ee_images import upload_satelliteImages
from src.constants import selected_bands


def download_sentinel2(bucket, COUNTRY, START_DATE, END_DATE, CLOUD_FILTER, DIM):
    print("Lancement du téléchargement des données SENTINEL2")
    root_path = get_root_path()

    path_s3 = f"""data-raw/SENTINEL2/{COUNTRY}/{int(START_DATE[0:4])}/"""
    path_local = os.path.join(
        root_path,
        f"""data/SENTINEL2/{COUNTRY}/{int(START_DATE[0:4])}""",
    )

    os.makedirs(path_local, exist_ok=True)

    EPSG = "EPSG:3035"

    polygons_country = get_country_polygon(COUNTRY)
    sampled_bboxes = sample_bboxes_from_multipolygon(polygons_country, bbox_area_km2=5)

    for num_poly, polygon_country in enumerate(sampled_bboxes):
        coords = list(polygon_country.exterior.coords)
        aoi = ee.Geometry.Polygon(coords)

        s2_sr_harmonized = get_s2_from_ee(aoi, START_DATE, END_DATE, CLOUD_FILTER)
        if s2_sr_harmonized.bandNames().getInfo() != selected_bands:
            print('No result for this bbox')
            continue

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
            polygon_country.exterior,
            EPSG,
            True,
        )

        shutil.rmtree(path_local, ignore_errors=True)
        os.makedirs(path_local, exist_ok=True)

    print(f"""Le processus est fini et les images sont stockées ici {f"s3://{bucket}/{path_s3}"}""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raster tiling pipeline")
    parser.add_argument("--country", type=str, required=True, help="Country (e.g., 'FR')")
    args = parser.parse_args()

    bucket = "projet-hackathon-ntts-2025"
    COUNTRY = args.country
    DIM = 250

    # todo : recup des images sur les 4 saisons
    START_DATE = "2018-05-01"
    END_DATE = "2018-09-01"
    CLOUD_FILTER = 20

    start_time = time.time()
    service_account = "slums-detection-sa@ee-insee-sentinel.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(service_account, "GCP_credentials.json")

    # Initialize the library.
    ee.Initialize(credentials)
    download_sentinel2(bucket, COUNTRY, START_DATE, END_DATE, CLOUD_FILTER, DIM)

    end_time = time.time() - start_time
    print(f"{COUNTRY} downloaded in {round(end_time/60)} min")
