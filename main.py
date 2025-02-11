import os
import shutil

import ee
import geemap

from src.utils import (
    get_root_path,
    upload_satelliteImages
    )

from src.contours import get_dep_polygon
from src.earth_engine_utils import (
    get_s2_sr_cld_col,
    add_cld_shdw_mask,
    apply_cld_shdw_mask,
    )


def download_sentinel2(bucket, EPSG, DEP, START_DATE, END_DATE, CLOUD_FILTER):
    print("Lancement du téléchargement des données SENTINEL2")
    root_path = get_root_path()

    path_s3 = f"""data-raw/SENTINEL2/{int(START_DATE[0:4])}/{DEP}/"""
    path_local = os.path.join(
        root_path,
        f"""data/SENTINEL2/{int(START_DATE[0:4])}/{DEP}""",
    )

    os.makedirs(path_local, exist_ok=True)

    polygon_dep = get_dep_polygon(DEP)

    coords = list(polygon_dep.exterior.coords)
    aoi = ee.Geometry.Polygon(coords)

    s2_sr_cld_col = get_s2_sr_cld_col(aoi, START_DATE, END_DATE, CLOUD_FILTER)
    s2_sr_median = s2_sr_cld_col.map(add_cld_shdw_mask).map(apply_cld_shdw_mask).median()

    fishnet = geemap.fishnet(aoi, rows=4, cols=4, delta=0.5)
    geemap.download_ee_image_tiles(
        s2_sr_median,
        fishnet,
        path_local,
        prefix="data_",
        crs=EPSG,
        scale=10,
        num_threads=50,
    )

    upload_satelliteImages(
        path_local,
        f"s3://{bucket}/{path_s3}",
        DEP,
        int(START_DATE[0:4]),
        250,
        12,
        True,
    )

    shutil.rmtree(path_local, ignore_errors=True)

    print(f"""Le processus est fini et les images sont stockées ici {f"s3://{bucket}/{path_s3}"}""")


if __name__ == "__main__":
    bucket = "projet-hackaton-ntts-2025"

    EPSG = "EPSG:2154"
    DEP = "69"

    START_DATE = "2024-05-01"
    END_DATE = "2024-09-01"
    CLOUD_FILTER = 60

    service_account = "slums-detection-sa@ee-insee-sentinel.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(service_account, "GCP_credentials.json")

    # Initialize the library.
    ee.Initialize(credentials)
    download_sentinel2(bucket, EPSG, DEP, START_DATE, END_DATE, CLOUD_FILTER)
