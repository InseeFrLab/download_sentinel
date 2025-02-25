import os
from pathlib import Path
import s3fs
from shapely.geometry import Polygon
from pyproj import Transformer


def get_root_path() -> Path:
    """
    Return root path of project.

    Returns:
        Path: Root path.
    """
    return Path(__file__).parent.parent.parent


def project_polygon(polygon, destination_epsg, origin_epsg="EPSG:4326"):
    coords = polygon.exterior.coords
    transformer = Transformer.from_crs(origin_epsg, destination_epsg, always_xy=True)
    transformed_coords = [transformer.transform(lon, lat) for lon, lat in coords]
    projected_poly = Polygon(transformed_coords)
    return projected_poly


def exportToMinio(lpath, rpath):
    fs = s3fs.S3FileSystem(
        client_kwargs={'endpoint_url': 'https://'+'minio.lab.sspcloud.fr'},
        key=os.environ["AWS_ACCESS_KEY_ID"], 
        secret=os.environ["AWS_SECRET_ACCESS_KEY"], 
        token="")
    return fs.put(lpath, rpath, True)
