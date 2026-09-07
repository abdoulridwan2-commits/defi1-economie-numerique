"""
Étape 3 (fin du J1) : agrégation de toutes les données par préfecture
- comptage des infrastructures (agences, datacenters, mobile money, antennes)
- densité de population moyenne
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from rasterstats import zonal_stats
import re

RAW_DIR = "data/raw/"
PROCESSED_DIR = "data/processed/"

INFRA_FILES = {
    "agences_telecom": "agences_telecom.csv",
    "agences_moov": "agences_moov.csv",
    "agences_togocom": "agences_togocom.csv",
    "agences_canalplus": "agences_canalplus.csv",
    "datacenters": "datacenters.csv",
    "mobile_money": "mobile_money.csv",
}

ANTENNES_COLUMNS = [
    "radio", "mcc", "net", "area", "cell", "unit",
    "longitude", "latitude", "range", "samples",
    "changeable", "created", "updated", "averageSignal",
]


def extract_lon_lat(geometry_str):
    if pd.isna(geometry_str):
        return None, None
    match = re.search(r"POINT \(([-\d.]+) ([-\d.]+)\)", str(geometry_str))
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


def load_infra_as_gdf(filename):
    df = pd.read_csv(RAW_DIR + filename)
    if len(df) == 0:
        return gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:4326")
    df["longitude"], df["latitude"] = zip(*df["geometry"].map(extract_lon_lat))
    geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
    return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


def main():
    prefectures = gpd.read_file(RAW_DIR + "prefectures.geojson")[["shapeName", "geometry"]]
    prefectures = prefectures.rename(columns={"shapeName": "prefecture"})

    # 1. Compter chaque type d'infrastructure par préfecture (jointure spatiale point-dans-polygone)
    result = prefectures.copy()
    for name, filename in INFRA_FILES.items():
        gdf = load_infra_as_gdf(filename)
        if len(gdf) == 0:
            result[name] = 0
            continue
        joined = gpd.sjoin(gdf, prefectures, how="left", predicate="within")
        counts = joined.groupby("prefecture").size()
        result[name] = result["prefecture"].map(counts).fillna(0).astype(int)

    # 2. Antennes mobiles (mêmes étapes)
    antennes_df = pd.read_csv(RAW_DIR + "antennes_togo.csv", header=None, names=ANTENNES_COLUMNS)
    antennes_geom = [Point(xy) for xy in zip(antennes_df["longitude"], antennes_df["latitude"])]
    antennes_gdf = gpd.GeoDataFrame(antennes_df, geometry=antennes_geom, crs="EPSG:4326")
    joined_antennes = gpd.sjoin(antennes_gdf, prefectures, how="left", predicate="within")
    counts_antennes = joined_antennes.groupby("prefecture").size()
    result["antennes_mobiles"] = result["prefecture"].map(counts_antennes).fillna(0).astype(int)

    # 3. Densité de population moyenne par préfecture (zonal statistics sur le raster)
    stats = zonal_stats(
        prefectures, RAW_DIR + "population_density.tif",
        stats=["mean"], nodata=-99999
    )
    result["densite_pop_moyenne"] = [s["mean"] if s["mean"] is not None else 0 for s in stats]

    # 4. Total infrastructures (hors mobile money, trop nombreux, et hors antennes)
    result["total_agences"] = (
        result["agences_telecom"] + result["agences_moov"] +
        result["agences_togocom"] + result["agences_canalplus"] +
        result["datacenters"]
    )

    result_df = result.drop(columns="geometry")
    result_df.to_csv(PROCESSED_DIR + "infra_by_prefecture.csv", index=False)
    print(f"Fichier sauvegardé : {PROCESSED_DIR}infra_by_prefecture.csv")
    print(f"\nAperçu (top 10 préfectures par total agences) :")
    print(result_df.sort_values("total_agences", ascending=False).head(10).to_string(index=False))


if __name__ == "__main__":
    main()