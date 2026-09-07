"""
Étape 1 : chargement et vérification des 6 fichiers d'infrastructures
(agences télécoms, datacenters, mobile money)
"""
import pandas as pd
import re

RAW_DIR = "data/raw/"

FILES = {
    "telecom": "agences_telecom.csv",
    "moov": "agences_moov.csv",
    "togocom": "agences_togocom.csv",
    "canalplus": "agences_canalplus.csv",
    "datacenters": "datacenters.csv",
    "mobile_money": "mobile_money.csv",
}


def extract_lon_lat(geometry_str):
    """Extrait (lon, lat) depuis une chaîne 'POINT (lon lat)'."""
    if pd.isna(geometry_str):
        return None, None
    match = re.search(r"POINT \(([-\d.]+) ([-\d.]+)\)", str(geometry_str))
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


def load_and_check(name, filename):
    path = RAW_DIR + filename
    df = pd.read_csv(path)

    print(f"\n=== {name} ({filename}) ===")
    print(f"Nombre de lignes : {len(df)}")

    if len(df) == 0:
        print("⚠️  Fichier vide (0 lignes de données) — à noter dans le rapport.")
        return df

    # Extraction des coordonnées
    df["longitude"], df["latitude"] = zip(*df["geometry"].map(extract_lon_lat))

    # Vérifications
    missing_coords = df["longitude"].isna().sum()
    print(f"Coordonnées manquantes/invalides : {missing_coords}")

    # Le Togo est globalement entre lon [-0.2, 1.9] et lat [6.0, 11.2]
    out_of_bounds = df[
        (df["longitude"] < -0.5) | (df["longitude"] > 2.0) |
        (df["latitude"] < 5.5) | (df["latitude"] > 11.5)
    ]
    print(f"Coordonnées hors des limites du Togo : {len(out_of_bounds)}")

    duplicates = df.duplicated(subset=["longitude", "latitude"]).sum()
    print(f"Doublons (mêmes coordonnées exactes) : {duplicates}")

    return df


if __name__ == "__main__":
    dataframes = {}
    for name, filename in FILES.items():
        dataframes[name] = load_and_check(name, filename)

    print("\n=== Résumé ===")
    for name, df in dataframes.items():
        print(f"{name}: {len(df)} lignes")