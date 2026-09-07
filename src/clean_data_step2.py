"""
Étape 2 : chargement et vérification des 3 fichiers complémentaires
(préfectures, densité de population, antennes mobiles)
"""
import geopandas as gpd
import pandas as pd
import rasterio

RAW_DIR = "data/raw/"

# Colonnes du fichier OpenCelliD (pas d'en-tête dans le fichier brut)
ANTENNES_COLUMNS = [
    "radio", "mcc", "net", "area", "cell", "unit",
    "longitude", "latitude", "range", "samples",
    "changeable", "created", "updated", "averageSignal",
]


def check_prefectures():
    print("\n=== prefectures.geojson ===")
    gdf = gpd.read_file(RAW_DIR + "prefectures.geojson")
    print(f"Nombre de préfectures : {len(gdf)}")
    print(f"CRS (système de coordonnées) : {gdf.crs}")
    print(f"Colonnes disponibles : {list(gdf.columns)}")
    print(f"Exemples de noms de préfectures : {gdf['shapeName'].head(5).tolist()}")
    return gdf


def check_population():
    print("\n=== population_density.tif ===")
    with rasterio.open(RAW_DIR + "population_density.tif") as src:
        print(f"CRS : {src.crs}")
        print(f"Dimensions (largeur x hauteur) : {src.width} x {src.height}")
        print(f"Emprise géographique (bounds) : {src.bounds}")
        print(f"Valeur 'nodata' : {src.nodata}")


def check_antennes():
    print("\n=== antennes_togo.csv ===")
    df = pd.read_csv(RAW_DIR + "antennes_togo.csv", header=None, names=ANTENNES_COLUMNS)
    print(f"Nombre d'antennes : {len(df)}")
    print(f"Coordonnées manquantes : {df['longitude'].isna().sum()}")
    print(f"Répartition par type de réseau (radio) :")
    print(df["radio"].value_counts())
    return df


if __name__ == "__main__":
    prefectures = check_prefectures()
    check_population()
    antennes = check_antennes()