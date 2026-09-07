"""
Dashboard Streamlit — Défi 1 : Économie Numérique (Togo AI Lab)
Section 1 : Cartographie des infrastructures (agences télécoms + datacenters)
"""
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(
    page_title="Défi 1 — Économie Numérique Togo",
    page_icon="📡",
    layout="wide",
)

RAW_DIR = "data/raw/"

INFRA_FILES = {
    "Agences Télécom": ("agences_telecom.csv", "#2E86DE"),
    "Agences Moov": ("agences_moov.csv", "#F39C12"),
    "Agences Togocom": ("agences_togocom.csv", "#27AE60"),
    "Agences CANAL+": ("agences_canalplus.csv", "#8E44AD"),
    "Datacenters": ("datacenters.csv", "#E74C3C"),
}

# ------------------------------------------------------------------
# CSS custom : header stylisé + cases à cocher façon "badges"
# ------------------------------------------------------------------
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #1a3c6e 0%, #2E86DE 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1.5rem;
}
.main-header h1 { margin: 0; font-size: 1.8rem; }
.main-header p { margin: 0.3rem 0 0 0; opacity: 0.9; }

.filter-bar {
    background: #f7f9fc;
    border: 1px solid #e0e6ed;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.2rem;
}
.filter-title {
    font-weight: 600;
    color: #1a3c6e;
    margin-bottom: 0.6rem;
    font-size: 0.95rem;
}
div[data-testid="stCheckbox"] {
    background: white;
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    border: 1px solid #e0e6ed;
}
</style>
""", unsafe_allow_html=True)


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
# En-tête stylisé
# ------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>📡 Accès aux télécommunications et services numériques — Togo</h1>
    <p>Défi 1 — Économie Numérique · Togo AI Lab</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Barre de filtres horizontale, en badges colorés
# ------------------------------------------------------------------
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
st.markdown('<div class="filter-title">🔎 Couches à afficher sur la carte</div>', unsafe_allow_html=True)

cols = st.columns(len(INFRA_FILES))
selected_layers = []
for col, (layer_name, (filename, color)) in zip(cols, INFRA_FILES.items()):
    with col:
        checked = st.checkbox(layer_name, value=True, key=f"chk_{layer_name}")
        if checked:
            selected_layers.append(layer_name)
st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# Statistiques rapides, en ligne
# ------------------------------------------------------------------
stat_cols = st.columns(len(INFRA_FILES))
for col, (layer_name, (filename, color)) in zip(stat_cols, INFRA_FILES.items()):
    df = load_infra(filename)
    with col:
        st.metric(layer_name, len(df))

# ------------------------------------------------------------------
# Carte pleine largeur
# ------------------------------------------------------------------
st.markdown("### 🗺️ Carte des infrastructures")

m = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")

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
            fill_color=color,
            fill_opacity=0.75,
            weight=1,
            popup=layer_name,
        ).add_to(fg)
    fg.add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, width=1400, height=650, returned_objects=[], key="map_section1")

# ====================================================================
# SECTION 2 : Mobile Money vs Population
# ====================================================================
st.divider()
st.markdown("### 💰 2. Mobile Money vs Population")

import json

@st.cache_data
def load_prefecture_data():
    return pd.read_csv("data/processed/infra_by_prefecture.csv")

@st.cache_data
def load_prefectures_geo():
    with open(RAW_DIR + "prefectures.geojson", encoding="utf-8") as f:
        return json.load(f)

pref_df = load_prefecture_data()
pref_geo = load_prefectures_geo()

# Ratio agents mobile money pour 10 000 habitants (proxy avec densité moyenne)
pref_df["ratio_mm_pop"] = (pref_df["mobile_money"] / pref_df["densite_pop_moyenne"].replace(0, 1)).round(2)

col_a, col_b = st.columns([2, 1])

with col_a:
    m2 = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")
    folium.Choropleth(
        geo_data=pref_geo,
        data=pref_df,
        columns=["prefecture", "mobile_money"],
        key_on="feature.properties.shapeName",
        fill_color="YlOrRd",
        fill_opacity=0.75,
        line_opacity=0.4,
        legend_name="Nombre d'agents mobile money",
        nan_fill_color="lightgray",
    ).add_to(m2)
    st_folium(m2, width=1000, height=500, returned_objects=[], key="map_section2")

with col_b:
    st.markdown("**Top 5 préfectures — agents mobile money**")
    top_mm = pref_df.nlargest(5, "mobile_money")[["prefecture", "mobile_money"]]
    st.dataframe(top_mm, hide_index=True, use_container_width=True)

    st.markdown("**Bottom 5 préfectures — potentiellement sous-desservies**")
    bottom_mm = pref_df.nsmallest(5, "mobile_money")[["prefecture", "mobile_money"]]
    st.dataframe(bottom_mm, hide_index=True, use_container_width=True)

st.caption(
    "⚠️ Le ratio agents/population est calculé à partir de la densité moyenne de population "
    "par préfecture (proxy), et non d'un chiffre de population absolu officiel."
)

# ====================================================================
# SECTION 3 : Infrastructures vs Densité démographique
# ====================================================================
st.divider()
st.markdown("### 🏘️ 3. Infrastructures vs Densité démographique")

col_c, col_d = st.columns([2, 1])

with col_c:
    m3 = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")
    folium.Choropleth(
        geo_data=pref_geo,
        data=pref_df,
        columns=["prefecture", "densite_pop_moyenne"],
        key_on="feature.properties.shapeName",
        fill_color="BuPu",
        fill_opacity=0.75,
        line_opacity=0.4,
        legend_name="Densité de population moyenne (hab/km²)",
        nan_fill_color="lightgray",
    ).add_to(m3)

    # Superposition des points d'infrastructure (total_agences)
    for filename_key in ["agences_telecom.csv", "agences_moov.csv", "agences_togocom.csv", "datacenters.csv"]:
        df_infra = load_infra(filename_key)
        if len(df_infra) == 0:
            continue
        for _, row in df_infra.iterrows():
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=3,
                color="black",
                fill=True,
                fill_color="white",
                fill_opacity=0.8,
                weight=1,
            ).add_to(m3)

    st_folium(m3, width=1000, height=500, returned_objects=[], key="map_section3")

with col_d:
    st.markdown("**Corrélation infra / densité**")
    st.dataframe(
        pref_df[["prefecture", "total_agences", "densite_pop_moyenne"]]
        .sort_values("densite_pop_moyenne", ascending=False)
        .head(8),
        hide_index=True, use_container_width=True,
    )
    correlation = pref_df["total_agences"].corr(pref_df["densite_pop_moyenne"])
    st.metric("Corrélation infra ↔ densité", f"{correlation:.2f}")

# ====================================================================
# SECTION 4 : Couverture réseau mobile & zones blanches
# ====================================================================
st.divider()
st.markdown("### 📶 4. Couverture réseau mobile & zones blanches")

st.info(
    "Proxy méthodologique : faute de couche officielle de couverture réseau, la couverture est "
    "approximée par un rayon de 10 km autour de chaque antenne recensée dans OpenCelliD "
    "(base communautaire, 33 antennes pour tout le Togo). Les zones hors de ces cercles sont "
    "considérées comme des « zones blanches » potentielles."
)

buffer_km = st.slider("Rayon de couverture par antenne (km)", 5, 25, 10)

@st.cache_data
def load_antennes():
    cols = ["radio", "mcc", "net", "area", "cell", "unit", "longitude", "latitude",
            "range", "samples", "changeable", "created", "updated", "averageSignal"]
    return pd.read_csv(RAW_DIR + "antennes_togo.csv", header=None, names=cols)

antennes_df = load_antennes()

m4 = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")

for _, row in antennes_df.iterrows():
    folium.Circle(
        location=[row["latitude"], row["longitude"]],
        radius=buffer_km * 1000,  # mètres
        color="#2E86DE",
        fill=True,
        fill_opacity=0.15,
        weight=1,
    ).add_to(m4)
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=4,
        color="#1a3c6e",
        fill=True,
        fill_color="#1a3c6e",
        fill_opacity=1,
    ).add_to(m4)

st_folium(m4, width=1400, height=550, returned_objects=[], key="map_section4")
st.caption(f"{len(antennes_df)} antennes référencées · rayon de couverture appliqué : {buffer_km} km")