
# Digital Culture Scan – Reid & Compañía S. A.
# Streamlit dashboard (KPI eNPS, Radar, Heatmap, RAG) with filters by Área and Nivel

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# Optional plotting libs
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="DCS – Reid & Compañía", layout="wide")

st.title("Digital Culture Scan (DCS) – Reid & Compañía S. A.")
st.caption("Presentado al Comité de Transformación Digital · Fuente: Comité TD Reid & Co., 2025")

# --- DATA LOADING ---
st.sidebar.header("Fuente de datos")
default_path = "Dataset_DCS_ReidCo.xlsx"
uploaded = st.sidebar.file_uploader("Sube el dataset Excel (Dataset_DCS_ReidCo.xlsx)", type=["xlsx"])

def load_data(file):
    raw = pd.read_excel(file, sheet_name="Raw")
    # normalize columns (some excel writers add spaces)
    raw.columns = [c.strip().replace(" ", "") if c != "Área" and c != "Nivel" else c for c in raw.columns]
    return raw

try:
    if uploaded:
        df = load_data(uploaded)
    else:
        df = load_data(default_path)
except Exception as e:
    st.error("No se pudo leer el dataset. Sube el archivo Dataset_DCS_ReidCo.xlsx en la barra lateral.")
    st.stop()

# --- CALCULATED FIELDS ---
def compute_enps(series):
    # eNPS is from -100, 0, 100 values
    promotores = (series == 100).sum()
    detractores = (series == -100).sum()
    total = series.notna().sum()
    if total == 0:
        return 0
    return (promotores - detractores) / total * 100

df["PromedioGeneral"] = df[["Agilidad","Empoderamiento","MentalidadDatos","CorajeInnovar"]].mean(axis=1)

# --- FILTERS ---
areas = ["(Todas)"] + sorted(df["Área"].dropna().unique().tolist())
niveles = ["(Todos)"] + sorted(df["Nivel"].dropna().unique().tolist())
c1, c2 = st.sidebar.columns(2)
area_sel = c1.selectbox("Área", areas, index=0)
nivel_sel = c2.selectbox("Nivel", niveles, index=0)

df_f = df.copy()
if area_sel != "(Todas)":
    df_f = df_f[df_f["Área"] == area_sel]
if nivel_sel != "(Todos)":
    df_f = df_f[df_f["Nivel"] == nivel_sel]

# --- KPI eNPS ---
enps_global = compute_enps(df_f["eNPS"]) if len(df_f) else 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("eNPS Global", f"{enps_global:.0f}")
kpi2.metric("Promedio General", f"{df_f['PromedioGeneral'].mean():.2f}" if len(df_f) else "0.00")
kpi3.metric("N° Respuestas", f"{len(df_f)}")

st.markdown("---")

# --- RADAR (Plotly) ---
radar_dims = ["Agilidad","Empoderamiento","MentalidadDatos","CorajeInnovar"]
vals = [df_f[col].mean() if len(df_f) else 0 for col in radar_dims]
radar_df = pd.DataFrame({"Dimensión": radar_dims, "Valor": vals})

radar_fig = go.Figure()
radar_fig.add_trace(go.Scatterpolar(
    r=radar_df["Valor"].tolist() + [radar_df["Valor"].iloc[0]],
    theta=radar_df["Dimensión"].tolist() + [radar_df["Dimensión"].iloc[0]],
    fill='toself',
    name='Promedio (1-5)'
))
radar_fig.update_layout(
    title="Dimensiones de Cultura Digital (Radar)",
    polar=dict(radialaxis=dict(visible=True, range=[0,5])),
    showlegend=False,
    margin=dict(l=20,r=20,t=60,b=20)
)

# --- BARS by Área ---
bars_df = df_f.groupby("Área")[radar_dims].mean().reset_index() if len(df_f) else pd.DataFrame(columns=["Área"]+radar_dims)
bars_fig = px.bar(
    bars_df.melt(id_vars="Área", var_name="Dimensión", value_name="Promedio"),
    x="Dimensión", y="Promedio", color="Área", barmode="group", title="Comparativo por Dimensión y Área",
    range_y=[0,5]
)

cA, cB = st.columns([1,1])
with cA:
    st.plotly_chart(radar_fig, use_container_width=True)
with cB:
    st.plotly_chart(bars_fig, use_container_width=True)

# --- HEATMAP (fricciones por área) ---
hm_df = df_f.groupby("Área")[radar_dims].mean().reset_index()
if not hm_df.empty:
    hm_long = hm_df.melt(id_vars="Área", var_name="Dimensión", value_name="Promedio")
    heatmap_fig = px.density_heatmap(
        hm_long, x="Dimensión", y="Área", z="Promedio", color_continuous_scale="RdYlGn", range_color=[2,4],
        title="Mapa de Fricciones Culturales (bajo=verde, alto=rojo)"
    )
    st.plotly_chart(heatmap_fig, use_container_width=True)
else:
    st.info("No hay datos para construir el heatmap con los filtros aplicados.")

# --- RAG SCATTER (Plan de acción) ---
rag_data = pd.DataFrame({
    "Iniciativa": ["Daily Learning Nugget","Célula Ágil Piloto","Academia de Datos","Incentivos Digitales","Gobernanza DCS"],
    "Impacto": [5, 4, 5, 4, 5],
    "Urgencia": [5, 3, 2, 4, 2],
    "Categoría": ["Quick Win","180 días","365 días","90-365 días","Gobernanza"]
})
rag_fig = px.scatter(rag_data, x="Urgencia", y="Impacto", text="Iniciativa", color="Categoría",
                     range_x=[0,6], range_y=[0,6], title="Matriz Impacto × Urgencia (RAG)")
rag_fig.update_traces(textposition='top center')
st.plotly_chart(rag_fig, use_container_width=True)

# --- DATA PREVIEW ---
with st.expander("Ver datos filtrados (previa)"):
    st.dataframe(df_f)

st.caption("© 2025 Reid & Compañía S. A. · Dashboard DCS · Fuente: Comité de Transformación Digital")
