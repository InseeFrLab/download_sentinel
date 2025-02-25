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

## Sample of a europeen contry

Europeen contries polygons downloaded on the [eurostat website](https://ec.europa.eu/eurostat/web/gisco/geodata/administrative-units/countries). Scale = 10M, EPSG: 4326.

```
nohup python main.py &
```

