"""
Dashboard Streamlit — Défi 1 : Économie Numérique (Togo AI Lab)
Section 1 : Cartographie des infrastructures (agences télécoms + datacenters)
"""
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

# ------------------------------------------------------------------
# Configuration de la page (doit être la première commande Streamlit)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Défi 1 — Économie Numérique Togo",
    page_icon="📡",
    layout="wide",
)

RAW_DIR = "data/raw/"

INFRA_FILES = {
    "Agences Télécom": ("agences_telecom.csv", "blue"),
    "Agences Moov": ("agences_moov.csv", "orange"),
    "Agences Togocom": ("agences_togocom.csv", "green"),
    "Agences CANAL+": ("agences_canalplus.csv", "purple"),
    "Datacenters": ("datacenters.csv", "red"),
}


def extract_lon_lat(geometry_str):
    if pd.isna(geometry_str):
        return None, None
    match = re.search(r"POINT \(([-\d.]+) ([-\d.]+)\)", str(geometry_str))
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None


@st.cache_data
def load_infra(filename):
    df = pd.read_csv(RAW_DIR + filename)
    if len(df) == 0:
        return df
    df["longitude"], df["latitude"] = zip(*df["geometry"].map(extract_lon_lat))
    return df


# ------------------------------------------------------------------
# En-tête
# ------------------------------------------------------------------
st.title("📡 Accès aux télécommunications et services numériques — Togo")
st.markdown("**Défi 1 — Économie Numérique · Togo AI Lab**")

# ------------------------------------------------------------------
# Sidebar : filtres
# ------------------------------------------------------------------
st.sidebar.header("Filtres")
selected_layers = st.sidebar.multiselect(
    "Couches à afficher",
    options=list(INFRA_FILES.keys()),
    default=list(INFRA_FILES.keys()),
)

# ------------------------------------------------------------------
# Section 1 : Carte des infrastructures
# ------------------------------------------------------------------
st.header("1. Cartographie des infrastructures")

# Carte centrée sur le Togo
m = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")

total_points = 0
for layer_name in selected_layers:
    filename, color = INFRA_FILES[layer_name]
    df = load_infra(filename)

    if len(df) == 0:
        continue

    fg = folium.FeatureGroup(name=layer_name)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=layer_name,
        ).add_to(fg)
    fg.add_to(m)
    total_points += len(df)

folium.LayerControl().add_to(m)

col1, col2 = st.columns([3, 1])
with col1:
    st_folium(m, width=None, height=500)
with col2:
    st.metric("Points affichés", total_points)
    for layer_name in selected_layers:
        filename, _ = INFRA_FILES[layer_name]
        df = load_infra(filename)
        st.write(f"**{layer_name}** : {len(df)}")