import os
from pathlib import Path
import s3fs
import PIL
from tqdm import tqdm

from astrovision.data.satellite_image import (
    SatelliteImage,
)


def get_root_path() -> Path:
    """
    Return root path of project.

    Returns:
        Path: Root path.
    """
    return Path(__file__).parent.parent.parent


def upload_satelliteImages(
    lpath,
    rpath,
    dep,
    year,
    dim,
    n_bands,
    num_poly,
    check_nbands12=False,
):
    """
    Transforms a raster in a SatelliteImage and calls a function\
        that uploads it on MinIO and deletes it locally.

    Args:
        lpath: path to the raster to transform into SatelliteImage\
            and to upload on MinIO.
        rpath: path to the MinIO repertory in which the image\
            should be uploaded.
        dep: department number of the DOM.
        dim: tiles' size.
        n_bands: number of bands of the image to upload.
        check_nbands12: boolean that, if set to True, allows to check\
            if the image to upload is indeed 12 bands.\
            Usefull in download_sentinel2_ee.py
    """

    images_paths = os.listdir(lpath)

    for i in range(len(images_paths)):
        images_paths[i] = lpath + "/" + images_paths[i]

    print("Lecture des images")
    list_satellite_images = [
        SatelliteImage.from_raster(filename, n_bands=n_bands)
        for filename in tqdm(images_paths)
    ]

    print(f"Découpage des images en taille {dim}")
    splitted_list_images = [
        im for sublist in tqdm(list_satellite_images) for im in sublist.split(dim)
    ]

    print("Enregistrement des images sur le s3")
    for i in tqdm(range(len(splitted_list_images))):
        image = splitted_list_images[i]
        bb = image.bounds
        filename = str(int(bb[0])) + "_" + str(int(bb[1])) + "_" + str(num_poly) + "_" + str(i)

        lpath_image = lpath + "/" + filename + ".tif"

        image.to_raster(lpath_image)

        if check_nbands12:
            try:
                image = SatelliteImage.from_raster(
                    file_path=lpath_image,
                    n_bands=12,
                )
                exportToMinio(lpath_image, rpath)
                os.remove(lpath_image)

            except PIL.UnidentifiedImageError:
                print("L'image ne possède pas assez de bandes")
        else:
            exportToMinio(lpath_image, rpath)
            os.remove(lpath_image)


def exportToMinio(lpath, rpath):
    fs = s3fs.S3FileSystem(
        client_kwargs={'endpoint_url': 'https://'+'minio.lab.sspcloud.fr'},
        key=os.environ["AWS_ACCESS_KEY_ID"],
        secret=os.environ["AWS_SECRET_ACCESS_KEY"],
        token=os.environ["AWS_SESSION_TOKEN"])

    return fs.put(lpath, rpath, True)
