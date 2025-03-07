# Télécharger les images Sentinel

## Get started

```
git clone https://github.com/InseeFrLab/download_sentinel.git
cd download_sentinel
source ./setup.sh
```

## Département en France

Pour lancer le téléchargement des images sur un département de France Métropolitaine

```
nohup python main_dep_fr.py &
```

## NUTS 3 in UE

Polygons of NUTS-3 downloaded [here](https://gisco-services.ec.europa.eu/distribution/v2/nuts/nuts-2021-files.html). File : NUTS_RG_01M_2021_4326_LEVL_3.gpkg

```
nohup python main_nuts.py --nuts3 "BE100" --startDate "2018-05-01" --endDate "2018-09-01" &
```

## Sample of a europeen country

```
nohup python main_nuts.py --country "BE" --startDate "2018-05-01" --endDate "2018-09-01" --sampleProp 0.05 &
```
