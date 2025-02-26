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
    os.environ["AWS_ACCESS_KEY_ID"] = 'MG9Z09WRP5R8UAJT21IS'
    os.environ["AWS_SECRET_ACCESS_KEY"] = 'Apc4LnQ29L9edEa5XtcGAvPVabiIpahUT7PbLzO7'
    os.environ["AWS_SESSION_TOKEN"] = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiJNRzlaMDlXUlA1UjhVQUpUMjFJUyIsImFsbG93ZWQtb3JpZ2lucyI6WyIqIl0sImF1ZCI6WyJtaW5pby1kYXRhbm9kZSIsIm9ueXhpYSIsImFjY291bnQiXSwiYXV0aF90aW1lIjoxNzQwMDQ4NTkxLCJhenAiOiJvbnl4aWEiLCJlbWFpbCI6InJheWEuYmVyb3ZhQGluc2VlLmZyIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImV4cCI6MTc0MTE2OTY1MCwiZmFtaWx5X25hbWUiOiJCRVJPVkEiLCJnaXZlbl9uYW1lIjoiUmF5YSIsImdyb3VwcyI6WyJVU0VSX09OWVhJQSIsImdhaWEiLCJoYWNrYXRob24tbnR0cy0yMDI1Iiwic2x1bXMtZGV0ZWN0aW9uIl0sImlhdCI6MTc0MDU2NDg0OSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmxhYi5zc3BjbG91ZC5mci9hdXRoL3JlYWxtcy9zc3BjbG91ZCIsImp0aSI6ImZhNDRkZWI2LWVkZmMtNDM3NC1iNmViLWZlNzQwNTQ4OTk0OSIsIm5hbWUiOiJSYXlhIEJFUk9WQSIsInBvbGljeSI6InN0c29ubHkiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJyYXlhYmVyb3ZhIiwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iLCJkZWZhdWx0LXJvbGVzLXNzcGNsb3VkIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtc3NwY2xvdWQiXSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBncm91cHMgZW1haWwiLCJzaWQiOiI5ODQ1NzM1OS1iMzUxLTQ4NzItOWFjMy1jMDkxMTUyZTI3OTUiLCJzdWIiOiJlNGJmNmFhMi0zNWRkLTQ1ODAtODQ1Mi1iOWRkYzlkMmNmMDUiLCJ0eXAiOiJCZWFyZXIifQ.3hJeX81njhg_15BtlkH5Uj7HPqr8YhH_O03oRM7C1hCTfSMIp2oZ0Q6iiJ2Ot9l6lOjygTxBLCXA-dJfGGDI5Q'
    os.environ["AWS_DEFAULT_REGION"] = 'us-east-1'
    fs = s3fs.S3FileSystem(
        client_kwargs={'endpoint_url': 'https://'+'minio.lab.sspcloud.fr'},
        key = os.environ["AWS_ACCESS_KEY_ID"], 
        secret = os.environ["AWS_SECRET_ACCESS_KEY"], 
        token = os.environ["AWS_SESSION_TOKEN"])
    return fs.put(lpath, rpath, True)
