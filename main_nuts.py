import os
import shutil
import ee
import geemap
import argparse
import time
import pandas as pd

from src.utils import exportToMinio
from src.utils import get_root_path
from src.contours import get_nuts3_polygon
from src.download_ee_images import get_s2_from_ee
from src.process_ee_images import upload_satelliteImages
from src.constants import selected_bands


def download_sentinel2(bucket, NUTS3, START_DATE, END_DATE, CLOUD_FILTER, DIM):
    print("Lancement du téléchargement des données SENTINEL2")
    root_path = get_root_path()

    path_s3 = f"""data-raw/SENTINEL2/{NUTS3}/{int(START_DATE[0:4])}/"""
    path_local = os.path.join(
        root_path,
        f"""data/SENTINEL2/{NUTS3}/{int(START_DATE[0:4])}""",
    )

    os.makedirs(path_local, exist_ok=True)

    EPSG = "EPSG:3035"

    polygons_nuts3 = get_nuts3_polygon(NUTS3)
    filename2bbox = pd.DataFrame(columns=["filename", "bbox"])

    for num_poly, polygon_nuts3 in enumerate(polygons_nuts3.geoms):
        coords = list(polygon_nuts3.exterior.coords)
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

        filename2bbox = upload_satelliteImages(
            path_local,
            f"s3://{bucket}/{path_s3}",
            DIM,
            14,
            num_poly,
            polygon_nuts3.exterior,
            EPSG,
            filename2bbox,
            True,
        )

        shutil.rmtree(path_local, ignore_errors=True)
        os.makedirs(path_local, exist_ok=True)

    path_filename2bbox = os.path.join(
        root_path,
        "filename2bbox.parquet",
    )
    filename2bbox.to_parquet(path_filename2bbox, index=False)
    exportToMinio(path_filename2bbox, f"s3://{bucket}/{path_s3}")
    print(f"""Le processus est fini et les images sont stockées ici {f"s3://{bucket}/{path_s3}"}""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raster tiling pipeline")
    parser.add_argument("--nuts3", type=str, required=True, help="NUTS3 (e.g., 'BE100')")
    parser.add_argument("--startDate", type=str, required=True, help="startDate (e.g., '2018-05-01')")
    parser.add_argument("--endDate", type=str, required=True, help="endDate (e.g., '2018-09-01')")
    args = parser.parse_args()

    bucket = "projet-hackathon-ntts-2025"
    NUTS3 = args.nuts3
    DIM = 250

    # todo : recup des images sur les 4 saisons
    START_DATE = args.startDate
    END_DATE = args.endDate
    CLOUD_FILTER = 20

    start_time = time.time()
    service_account = "slums-detection-sa@ee-insee-sentinel.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(service_account, "GCP_credentials.json")

    # Initialize the library.
    ee.Initialize(credentials)
    download_sentinel2(bucket, NUTS3, START_DATE, END_DATE, CLOUD_FILTER, DIM)

    end_time = time.time() - start_time
    print(f"{NUTS3} downloaded in {round(end_time/60)} min")
