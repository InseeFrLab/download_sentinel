import os
import PIL
from tqdm import tqdm
from shapely.geometry import box, Polygon
import pandas as pd
import numpy as np

from astrovision.data.satellite_image import (
    SatelliteImage,
)
from src.utils import project_polygon, exportToMinio


def upload_satelliteImages(
    lpath,
    rpath,
    dim,
    n_bands,
    num_poly,
    polygon_zone,
    epsg,
    filename2bbox,
    metrics,
    check_include=False,
    check_nbands12=True,
):
    """
    Transforms a raster in a SatelliteImage and calls a function\
        that uploads it on MinIO and deletes it locally.

    Args:
        lpath: path to the raster to transform into SatelliteImage\
            and to upload on MinIO.
        rpath: path to the MinIO repertory in which the image\
            should be uploaded.
        dim: tiles' size.
        n_bands: number of bands of the image to upload.
        polygon_zone: polygon of the zone.
        epsg: EPSG.
        check_nbands12: boolean that, if set to True, allows to check\
            if the image to upload is indeed 12 bands.\
            Usefull in download_sentinel2_ee.py
    """

    images_paths = os.listdir(lpath)

    for i in range(len(images_paths)):
        images_paths[i] = lpath + "/" + images_paths[i]

    print("Lecture des images")
    list_satellite_images = []
    for filename in tqdm(images_paths):
        image_sat = SatelliteImage.from_raster(filename, n_bands=n_bands)
        if image_sat.array.shape[1] >= dim and image_sat.array.shape[2] >= dim:
            list_satellite_images.append(image_sat)

    print(f"Découpage des images en taille {dim}")
    splitted_list_images = [
        im for sublist in tqdm(list_satellite_images) for im in sublist.split(dim)
    ]
    projected_polygon_zone = project_polygon(Polygon(polygon_zone), epsg)

    print("Enregistrement des images sur le s3")
    for i in tqdm(range(len(splitted_list_images))):
        image = splitted_list_images[i]
        bb = image.bounds
        left, bottom, right, top = bb
        bbox = box(left, bottom, right, top)

        if check_include and not projected_polygon_zone.contains(bbox):
            continue  # on récupère uniquement les petites tuiles incluses dans le polygone du département
        elif not check_include or projected_polygon_zone.contains(bbox):
            filename = str(int(bb[0])) + "_" + str(int(bb[1])) + "_" + str(num_poly) + "_" + str(i)

            lpath_image = lpath + "/" + filename + ".tif"

            image.to_raster(lpath_image)

            if check_nbands12:
                try:
                    image = SatelliteImage.from_raster(
                        file_path=lpath_image,
                        n_bands=12,
                    )
                    new_row = pd.DataFrame({"filename": [lpath_image.split('/')[-1]], "bbox": [image.bounds]})
                    filename2bbox = pd.concat([filename2bbox, pd.DataFrame(new_row)], ignore_index=True)

                    metrics["mean"].append(np.mean(image.array, axis=(1, 2)))
                    metrics["std"].append(np.std(image.array, axis=(1, 2)))

                    # exportToMinio(lpath_image, rpath)
                    os.remove(lpath_image)

                except PIL.UnidentifiedImageError:
                    print("L'image ne possède pas assez de bandes")
            else:
                new_row = pd.DataFrame({"filename": [lpath_image.split('/')[-1]], "bbox": [bb]})
                filename2bbox = pd.concat([filename2bbox, pd.DataFrame(new_row)], ignore_index=True)

                metrics["mean"].append(np.mean(image.satellite_image.array, axis=(1, 2)))
                metrics["std"].append(np.std(image.satellite_image.array, axis=(1, 2)))

                # exportToMinio(lpath_image, rpath)
                os.remove(lpath_image)

    return filename2bbox, metrics
