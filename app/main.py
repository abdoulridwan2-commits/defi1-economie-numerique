"""
Dashboard Streamlit — Défi 1 : Économie Numérique (Togo AI Lab)
5 sections, mise en page pleine largeur : filtres -> carte -> graphique -> tableau -> interprétation
"""
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import re
import json

st.set_page_config(page_title="Défi 1 — Économie Numérique Togo", page_icon="📡", layout="wide")

RAW_DIR = "data/raw/"

INFRA_FILES = {
    "Agences Télécom": ("agences_telecom.csv", "#2E86DE"),
    "Agences Moov": ("agences_moov.csv", "#F39C12"),
    "Agences Togocom": ("agences_togocom.csv", "#27AE60"),
    "Agences CANAL+": ("agences_canalplus.csv", "#8E44AD"),
    "Datacenters": ("datacenters.csv", "#E74C3C"),
}

st.markdown("""
<style>
.main-header { background: linear-gradient(90deg, #1a3c6e 0%, #2E86DE 100%);
    padding: 1.5rem 2rem; border-radius: 12px; color: white; margin-bottom: 1.5rem; }
.main-header h1 { margin: 0; font-size: 1.8rem; }
.main-header p { margin: 0.3rem 0 0 0; opacity: 0.9; }
.filter-bar { background: #f7f9fc; border: 1px solid #e0e6ed; border-radius: 12px;
    padding: 1rem 1.5rem; margin-bottom: 1rem; }
.filter-title { font-weight: 600; color: #1a3c6e; margin-bottom: 0.6rem; font-size: 0.95rem; }
.interpretation { background: #eef5ff; border-left: 4px solid #2E86DE; border-radius: 8px;
    padding: 0.9rem 1.2rem; margin-top: 0.8rem; font-size: 0.92rem; }
.reco-card { background: white; border: 1px solid #e0e6ed; border-left: 5px solid #2E86DE;
    border-radius: 10px; padding: 1.1rem 1.3rem; margin-bottom: 1rem; }
.reco-card h5 { margin: 0 0 0.4rem 0; color: #1a3c6e; }
.reco-card .tag { display: inline-block; background: #eef5ff; color: #2E86DE; font-size: 0.75rem;
    padding: 0.15rem 0.6rem; border-radius: 20px; margin-bottom: 0.5rem; font-weight: 600; }
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


@st.cache_data
def load_prefecture_data():
    return pd.read_csv("data/processed/infra_by_prefecture.csv")


@st.cache_data
def load_prefectures_geo():
    with open(RAW_DIR + "prefectures.geojson", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_antennes():
    cols = ["radio", "mcc", "net", "area", "cell", "unit", "longitude", "latitude",
            "range", "samples", "changeable", "created", "updated", "averageSignal"]
    return pd.read_csv(RAW_DIR + "antennes_togo.csv", header=None, names=cols)


def interpretation_box(text):
    st.markdown(f'<div class="interpretation">💡 <b>Interprétation</b> — {text}</div>', unsafe_allow_html=True)


pref_df = load_prefecture_data()
pref_geo = load_prefectures_geo()
pref_df["ratio_infra_densite"] = pref_df["total_agences"] / pref_df["densite_pop_moyenne"].replace(0, 1)
pref_df["ratio_mm_pop"] = (pref_df["mobile_money"] / pref_df["densite_pop_moyenne"].replace(0, 1)).round(2)

st.markdown("""
<div class="main-header">
    <h1>📡 Accès aux télécommunications et services numériques — Togo</h1>
    <p>Défi 1 — Économie Numérique · Togo AI Lab</p>
</div>
""", unsafe_allow_html=True)

# ====================================================================
# SECTION 1 : Cartographie des infrastructures
# ====================================================================
st.markdown("## 🗺️ 1. Cartographie des infrastructures")

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
st.markdown('<div class="filter-title">🔎 Filtres</div>', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
with f1:
    selected_layers = st.multiselect("Type d'infrastructure", options=list(INFRA_FILES.keys()),
                                      default=list(INFRA_FILES.keys()))
with f2:
    all_regions = sorted(set().union(*[
        set(load_infra(f)["region_nom_bdd"].dropna().unique()) if len(load_infra(f)) > 0 else set()
        for f, c in INFRA_FILES.values()
    ]))
    selected_region = st.selectbox("Région", options=["Toutes"] + all_regions)
with f3:
    st.write("")
st.markdown('</div>', unsafe_allow_html=True)

# Carte pleine largeur
m = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")
all_filtered_rows = []

for layer_name in selected_layers:
    filename, color = INFRA_FILES[layer_name]
    df = load_infra(filename)
    if len(df) == 0:
        continue
    if selected_region != "Toutes":
        df = df[df["region_nom_bdd"] == selected_region]

    fg = folium.FeatureGroup(name=layer_name)
    for _, row in df.iterrows():
        nom = row.get("etab_nom", row.get("operateur", layer_name))
        popup_html = (
            f"<b>{nom}</b><br>"
            f"Type : {layer_name}<br>"
            f"Région : {row.get('region_nom_bdd', '—')}<br>"
            f"Préfecture : {row.get('prefecture_nom_bdd', '—')}<br>"
            f"Commune : {row.get('commune_nom_bdd', '—')}"
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]], radius=6,
            color=color, fill=True, fill_color=color, fill_opacity=0.8, weight=1,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=nom,
        ).add_to(fg)
    fg.add_to(m)
    df_tagged = df.copy()
    df_tagged["type_infra"] = layer_name
    all_filtered_rows.append(df_tagged)

folium.LayerControl().add_to(m)
st_folium(m, width=None, height=550, returned_objects=[], key="map_section1")
st.caption("Clique sur un point pour voir le nom de l'établissement, la région, la préfecture et la commune.")

# Graphique pleine largeur, lié à la carte (mêmes filtres)
combined_df = pd.concat(all_filtered_rows, ignore_index=True) if all_filtered_rows else pd.DataFrame()
if len(combined_df) > 0:
    counts_by_type = combined_df["type_infra"].value_counts().reset_index()
    counts_by_type.columns = ["Type", "Nombre"]
    fig1 = px.bar(counts_by_type, x="Type", y="Nombre", color="Type",
                  color_discrete_map={name: color for name, (f, color) in INFRA_FILES.items()},
                  title=f"Répartition des infrastructures{' — ' + selected_region if selected_region != 'Toutes' else ' (toutes régions)'}")
    fig1.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander(f"📋 Voir le détail ({len(combined_df)} établissements)"):
        display_cols = ["type_infra", "etab_nom", "region_nom_bdd", "prefecture_nom_bdd", "commune_nom_bdd"]
        display_cols = [c for c in display_cols if c in combined_df.columns]
        st.dataframe(
            combined_df[display_cols].rename(columns={
                "type_infra": "Type", "etab_nom": "Nom", "region_nom_bdd": "Région",
                "prefecture_nom_bdd": "Préfecture", "commune_nom_bdd": "Commune"
            }), hide_index=True, use_container_width=True,
        )

    n_canal = len(load_infra("agences_canalplus.csv"))
    interpretation_box(
        f"Togocom et le réseau télécom générique dominent la présence physique sur "
        f"{'la région ' + selected_region if selected_region != 'Toutes' else 'l’ensemble du territoire'}. "
        f"CANAL+ ne compte aucune agence recensée ({n_canal}) dans les données ouvertes — une lacune "
        f"à signaler plutôt qu'une absence confirmée. Les datacenters restent très concentrés, "
        f"cohérent avec une infrastructure numérique centralisée."
    )
else:
    st.warning("Aucune donnée pour cette combinaison de filtres.")

# ====================================================================
# SECTION 2 : Mobile Money vs Population
# ====================================================================
st.divider()
st.markdown("## 💰 2. Mobile Money vs Population")

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
metric_choice = st.radio("Indicateur affiché", options=["Nombre d'agents mobile money", "Ratio agents / densité population"], horizontal=True)
st.markdown('</div>', unsafe_allow_html=True)
metric_col = "mobile_money" if metric_choice == "Nombre d'agents mobile money" else "ratio_mm_pop"

m2 = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")
folium.Choropleth(
    geo_data=pref_geo, data=pref_df, columns=["prefecture", metric_col],
    key_on="feature.properties.shapeName", fill_color="YlOrRd", fill_opacity=0.75,
    line_opacity=0.4, legend_name=metric_choice, nan_fill_color="lightgray",
).add_to(m2)
folium.GeoJson(
    pref_geo, style_function=lambda x: {"fillOpacity": 0, "color": "transparent"},
    tooltip=folium.GeoJsonTooltip(fields=["shapeName"], aliases=["Préfecture :"]),
).add_to(m2)
st_folium(m2, width=None, height=550, returned_objects=[], key="map_section2")

top15 = pref_df.nlargest(15, metric_col)[["prefecture", metric_col]]
fig2 = px.bar(top15, x="prefecture", y=metric_col, labels={metric_col: metric_choice, "prefecture": "Préfecture"},
              title=f"Top 15 préfectures — {metric_choice}")
fig2.update_layout(height=350, xaxis_tickangle=-40)
st.plotly_chart(fig2, use_container_width=True)

with st.expander(f"📋 Voir toutes les préfectures (37)"):
    st.dataframe(
        pref_df[["prefecture", "mobile_money", "ratio_mm_pop", "densite_pop_moyenne"]].rename(columns={
            "prefecture": "Préfecture", "mobile_money": "Agents MM", "ratio_mm_pop": "Ratio MM/densité",
            "densite_pop_moyenne": "Densité (hab/km²)"
        }).sort_values("Agents MM", ascending=False),
        hide_index=True, use_container_width=True,
    )

n_sans_mm = (pref_df["mobile_money"] == 0).sum()
interpretation_box(
    f"Le mobile money est présent dans presque toutes les préfectures ({37 - n_sans_mm}/37). "
    f"C'est le canal d'inclusion numérique le plus capillaire au Togo — Lomé Commune et Golfe "
    f"concentrent logiquement les volumes les plus élevés du fait de leur densité urbaine, mais "
    f"le ratio agents/densité révèle des préfectures rurales bien desservies proportionnellement "
    f"à leur population."
)

# ====================================================================
# SECTION 3 : Infrastructures vs Densité démographique
# ====================================================================
st.divider()
st.markdown("## 🏘️ 3. Infrastructures vs Densité démographique")

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
min_density = st.slider("Densité minimale à afficher (hab/km²)", 0, int(pref_df["densite_pop_moyenne"].max()), 0)
st.markdown('</div>', unsafe_allow_html=True)

filtered_pref = pref_df[pref_df["densite_pop_moyenne"] >= min_density]

m3 = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")
folium.Choropleth(
    geo_data=pref_geo, data=pref_df, columns=["prefecture", "densite_pop_moyenne"],
    key_on="feature.properties.shapeName", fill_color="BuPu", fill_opacity=0.75, line_opacity=0.4,
    legend_name="Densité de population moyenne (hab/km²)", nan_fill_color="lightgray",
).add_to(m3)
for filename_key in ["agences_telecom.csv", "agences_moov.csv", "agences_togocom.csv", "datacenters.csv"]:
    df_infra = load_infra(filename_key)
    if len(df_infra) == 0:
        continue
    for _, row in df_infra.iterrows():
        folium.CircleMarker(location=[row["latitude"], row["longitude"]], radius=3,
                             color="black", fill=True, fill_color="white", fill_opacity=0.8, weight=1,
                             tooltip=row.get("etab_nom", "")).add_to(m3)
st_folium(m3, width=None, height=550, returned_objects=[], key="map_section3")

fig3 = px.scatter(filtered_pref, x="densite_pop_moyenne", y="total_agences", text="prefecture",
                   labels={"densite_pop_moyenne": "Densité (hab/km²)", "total_agences": "Nb agences"},
                   trendline="ols", title="Corrélation densité de population / nombre d'agences")
fig3.update_traces(textposition="top center", marker=dict(size=8, color="#2E86DE"))
fig3.update_layout(height=400)
st.plotly_chart(fig3, use_container_width=True)

with st.expander(f"📋 Voir le détail ({len(filtered_pref)} préfectures affichées)"):
    st.dataframe(
        filtered_pref[["prefecture", "total_agences", "densite_pop_moyenne"]].rename(columns={
            "prefecture": "Préfecture", "total_agences": "Agences", "densite_pop_moyenne": "Densité (hab/km²)"
        }).sort_values("Densité (hab/km²)", ascending=False),
        hide_index=True, use_container_width=True,
    )

correlation = pref_df["total_agences"].corr(pref_df["densite_pop_moyenne"])
interpretation_box(
    f"La corrélation entre densité de population et nombre d'agences est de {correlation:.2f} — "
    f"{'plutôt forte' if correlation > 0.5 else 'modérée' if correlation > 0.2 else 'faible'}. "
    f"Certaines préfectures densément peuplées mais peu équipées apparaissent comme des points "
    f"hors tendance — ce sont les cibles prioritaires détaillées en section 5."
)

# ====================================================================
# SECTION 4 : Couverture réseau mobile & zones blanches
# ====================================================================
st.divider()
st.markdown("## 📶 4. Couverture réseau mobile & zones blanches")

st.info(
    "Proxy méthodologique : faute de couche officielle de couverture réseau, la couverture est "
    "approximée par un rayon autour de chaque antenne recensée dans OpenCelliD (33 antennes)."
)

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    buffer_km = st.slider("Rayon de couverture par antenne (km)", 5, 25, 10)
with c2:
    radio_filter = st.multiselect("Type de réseau", options=["LTE", "UMTS"], default=["LTE", "UMTS"])
st.markdown('</div>', unsafe_allow_html=True)

antennes_df = load_antennes()
antennes_filtered = antennes_df[antennes_df["radio"].isin(radio_filter)]

m4 = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="CartoDB positron")
for _, row in antennes_filtered.iterrows():
    folium.Circle(location=[row["latitude"], row["longitude"]], radius=buffer_km * 1000,
                  color="#2E86DE", fill=True, fill_opacity=0.15, weight=1).add_to(m4)
    folium.CircleMarker(location=[row["latitude"], row["longitude"]], radius=4,
                         color="#1a3c6e", fill=True, fill_color="#1a3c6e", fill_opacity=1,
                         popup=f"Antenne {row['radio']}").add_to(m4)
st_folium(m4, width=None, height=550, returned_objects=[], key="map_section4")

radio_counts = antennes_df["radio"].value_counts().reset_index()
radio_counts.columns = ["Type", "Nombre"]
fig4 = px.pie(radio_counts, names="Type", values="Nombre", hole=0.5,
              color_discrete_sequence=["#2E86DE", "#F39C12"], title="Répartition des antennes par type de réseau")
fig4.update_layout(height=350)
st.plotly_chart(fig4, use_container_width=True)

with st.expander(f"📋 Voir le détail ({len(antennes_filtered)} antennes affichées)"):
    st.dataframe(antennes_filtered[["radio", "latitude", "longitude", "range"]].rename(columns={
        "radio": "Type", "latitude": "Latitude", "longitude": "Longitude", "range": "Portée déclarée (m)"
    }), hide_index=True, use_container_width=True)

interpretation_box(
    f"Avec seulement {len(antennes_df)} antennes recensées pour tout le pays (base crowdsourcée, "
    f"sous-représentation probable), une large partie du territoire togolais apparaît en 'zone "
    f"blanche' sur cette carte. Ce constat ne signifie pas une absence réelle de réseau, mais "
    f"souligne un manque de données ouvertes officielles sur la couverture mobile."
)

# ====================================================================
# SECTION 5 : Recommandations stratégiques
# ====================================================================
st.divider()
st.markdown("## 🎯 5. Recommandations stratégiques")

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
top_n = st.slider("Nombre de préfectures prioritaires par recommandation", 3, 10, 5)
st.markdown('</div>', unsafe_allow_html=True)

priorite_infra = pref_df.nsmallest(top_n, "ratio_infra_densite")[["prefecture", "total_agences", "densite_pop_moyenne", "mobile_money"]]
zones_sans_antenne = pref_df[pref_df["antennes_mobiles"] == 0].sort_values("densite_pop_moyenne", ascending=False).head(top_n)

st.markdown(f"""
<div class="reco-card">
    <span class="tag">PRIORITÉ 1 — INFRASTRUCTURE</span>
    <h5>🔴 Étendre les agences télécoms dans les préfectures sous-équipées</h5>
    <p><b>Constat :</b> {top_n} préfectures cumulent une densité de population notable et un nombre
    d'agences télécoms très faible, alors qu'elles montrent déjà une activité mobile money significative.</p>
    <p><b>Action recommandée :</b> prioriser l'implantation d'agences (Moov/Togocom) dans ces zones,
    en commençant par celles où le volume mobile money est le plus élevé — signe d'une demande déjà existante.</p>
    <p><b>Zones concernées :</b> {", ".join(priorite_infra["prefecture"].tolist())}</p>
</div>
""", unsafe_allow_html=True)
fig5a = px.bar(priorite_infra, x="prefecture", y="densite_pop_moyenne",
               labels={"densite_pop_moyenne": "Densité (hab/km²)", "prefecture": ""},
               color_discrete_sequence=["#E74C3C"])
fig5a.update_layout(height=300)
st.plotly_chart(fig5a, use_container_width=True)

st.markdown(f"""
<div class="reco-card" style="border-left-color:#F39C12;">
    <span class="tag" style="color:#F39C12; background:#fff5e6;">PRIORITÉ 2 — COUVERTURE RÉSEAU</span>
    <h5>🟠 Auditer la couverture réseau dans les zones denses non couvertes</h5>
    <p><b>Constat :</b> {top_n} préfectures à densité de population élevée n'ont aucune antenne
    recensée dans la base disponible.</p>
    <p><b>Action recommandée :</b> lancer un audit terrain de la couverture réelle dans ces zones,
    et pousser les opérateurs/le régulateur à publier une couche de couverture réseau officielle et ouverte.</p>
    <p><b>Zones concernées :</b> {", ".join(zones_sans_antenne["prefecture"].tolist())}</p>
</div>
""", unsafe_allow_html=True)
fig5b = px.bar(zones_sans_antenne, x="prefecture", y="densite_pop_moyenne",
               labels={"densite_pop_moyenne": "Densité (hab/km²)", "prefecture": ""},
               color_discrete_sequence=["#F39C12"])
fig5b.update_layout(height=300)
st.plotly_chart(fig5b, use_container_width=True)

st.markdown("""
<div class="reco-card" style="border-left-color:#27AE60;">
    <span class="tag" style="color:#27AE60; background:#eafaf1;">PRIORITÉ 3 — CONSTAT STRUCTUREL</span>
    <h5>🟢 S'appuyer sur le mobile money comme canal d'inclusion numérique</h5>
    <p><b>Constat :</b> le mobile money (19 788 points) est bien plus répandu que les agences
    physiques des opérateurs (183 au total). CANAL+ n'a aucune agence recensée dans les données ouvertes.</p>
    <p><b>Action recommandée :</b> utiliser le réseau mobile money existant comme point d'appui pour
    étendre d'autres services numériques en zone rurale (paiement, information, formation), plutôt
    que de dépendre uniquement de l'extension physique des agences télécoms, plus coûteuse.</p>
</div>
""", unsafe_allow_html=True)

with st.expander("📋 Voir la table complète des priorités"):
    st.dataframe(
        pref_df[["prefecture", "total_agences", "mobile_money", "antennes_mobiles", "densite_pop_moyenne"]]
        .rename(columns={"prefecture": "Préfecture", "total_agences": "Agences", "mobile_money": "Agents MM",
                          "antennes_mobiles": "Antennes", "densite_pop_moyenne": "Densité"}),
        hide_index=True, use_container_width=True,
    )