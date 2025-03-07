import os
import shutil
import ee
import geemap
import argparse
import time
import pandas as pd
import numpy as np
import yaml
from PIL import Image

from src.utils import exportToMinio
from src.utils import get_root_path
from src.contours import get_sampled_country_polygon
from src.download_ee_images import get_s2_from_ee
from src.process_ee_images import upload_satelliteImages
from src.constants import selected_bands
from src.export_clc_plus_labels import download_label


def download_sentinel2(bucket, COUNTRY, START_DATE, END_DATE, CLOUD_FILTER, DIM, SAMPLE_PROP, exportCLC):
    print("Lancement du téléchargement des données SENTINEL2")
    root_path = get_root_path()

    path_s3 = f"""data-preprocessed/patchs/CLCplus-Backbone/SENTINEL2/{COUNTRY}/{int(START_DATE[0:4])}/250/"""
    path_local = os.path.join(
        root_path,
        f"""data/patchs/CLCplus-Backbone/SENTINEL2/{COUNTRY}/{int(START_DATE[0:4])}/250""",
    )

    os.makedirs(path_local, exist_ok=True)

    EPSG = "EPSG:3035"

    filename2bbox = pd.DataFrame(columns=["filename", "bbox"])
    metrics = {"mean": [], "std": []}

    polygons_country = get_sampled_country_polygon(COUNTRY, sample_prop=SAMPLE_PROP)

    for num_poly, polygon_country in enumerate(polygons_country):
        coords = list(polygons_country.exterior.coords)
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

        filename2bbox, metrics = upload_satelliteImages(
            path_local,
            f"s3://{bucket}/{path_s3}",
            DIM,
            14,
            num_poly,
            polygon_country.exterior,
            EPSG,
            filename2bbox,
            metrics,
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
    os.remove(path_filename2bbox)

    metrics_global = {
        key: np.mean(
            np.stack(metrics[key]), axis=0
        ).tolist()
        for key in ["mean", "std"]
    }

    path_metrics_global = os.path.join(
        root_path,
        "metrics-normalization.yaml",
    )

    with open(path_metrics_global, "w") as f:
        yaml.dump(metrics_global, f, default_flow_style=False)

    exportToMinio(path_metrics_global, f"s3://{bucket}/{path_s3}")
    os.remove(path_metrics_global)

    if exportCLC:
        label_dir = os.path.join(
            root_path,
            f"data-preprocessed/labels/CLCplus-Backbone/SENTINEL2/{NUTS3}/{year}/250/",
        )
        os.makedirs(label_dir)
        export_url = f"https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/CLC_plus/CLMS_CLCplus_RASTER_{year}_010m_eu/ImageServer/exportImage"
        for index, row in filename2bbox.iterrows():
            bbox_tuple = tuple(map(int, row.bbox))
            filename = row.filename

            xmin, ymin, xmax, ymax = bbox_tuple

            resolution = 10

            # Calcul de la taille en pixels pour garantir 1 pixel = 10 m
            size_x = int((xmax - xmin) / resolution)
            size_y = int((ymax - ymin) / resolution)

            # Construction de la bounding box sous forme de chaîne
            bbox_str = f"{xmin},{ymin},{xmax},{ymax}"

            # Paramètres communs pour l'export
            common_params = {
                "f": "image",
                "bbox": bbox_str,
                "bboxSR": "3035",   # Lambert-93
                "imageSR": "3035",  # Sortie aussi en Lambert-93
                "size": f"{size_x},{size_y}",  # Ajusté automatiquement pour 1 pixel = 10 m
            }

            download_label("tiff", label_dir+filename, common_params, export_url)

            img = Image.open(label_dir+filename)
            npy_filename = filename.replace(".tif", ".npy")
            np.save(label_dir + npy_filename, np.array(img))

            exportToMinio(
                label_dir+npy_filename,
                f"{"s3://projet-hackathon-ntts-2025"}/{label_dir}",
            )

    print(f"""Le processus est fini et les images sont stockées ici {f"s3://{bucket}/{path_s3}"}""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raster tiling pipeline")
    parser.add_argument("--country", type=str, required=True, help="Country (e.g., 'FR')")
    parser.add_argument("--startDate", type=str, required=True, help="startDate (e.g., '2018-05-01')")
    parser.add_argument("--endDate", type=str, required=True, help="endDate (e.g., '2018-09-01')")
    parser.add_argument("--sampleProp", type=float, required=True, help="samplingProportion (e.g., 0.05)")
    parser.add_argument("--exportCLC", type=tuple, required=True, help="exportCLC (e.g., True)")
    args = parser.parse_args()

    bucket = "projet-hackathon-ntts-2025"
    COUNTRY = args.country
    DIM = 250
    exportCLC = args.exportCLC

    # todo : recup des images sur les 4 saisons
    START_DATE = args.startDate
    END_DATE = args.endDate
    CLOUD_FILTER = 20

    SAMPLE_PROP = args.sampleProp

    start_time = time.time()
    service_account = "slums-detection-sa@ee-insee-sentinel.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(service_account, "GCP_credentials.json")

    # Initialize the library.
    ee.Initialize(credentials)
    download_sentinel2(bucket, COUNTRY, START_DATE, END_DATE, CLOUD_FILTER, DIM, SAMPLE_PROP, exportCLC)

    end_time = time.time() - start_time
    print(f"{COUNTRY} downloaded in {round(end_time/60)} min")
