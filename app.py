import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ===============================
# COPY DATA
# ===============================
df_f = df.copy()

# ===============================
# NORMALISASI NILAI (FORMAT INDONESIA)
# ===============================
df_f["Value"] = (
    df_f["Value"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .astype(float)
)

# ===============================
# DETEKSI PERIODE (BULAN & TAHUN)
# ===============================
bulan_map = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

def parse_periode(row):
    txt = str(row["Periode"])

    audited = "audited" in txt.lower()

    m = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{2,4})", txt)
    if not m:
        return None

    bulan = bulan_map[m.group(1)]
    tahun = int(m.group(2))
    if tahun < 100:
        tahun += 2000

    sortkey = tahun * 100 + bulan

    label = f"{m.group(1)} {str(tahun)[-2:]}"
    if audited:
        label += " Audited"

    return pd.Series([bulan, tahun, sortkey, audited, label])

df_f[["Bulan", "Tahun", "SortKey", "IsAudited", "Periode_Label"]] = (
    df_f.apply(parse_periode, axis=1)
)

df_f = df_f.dropna(subset=["SortKey"])

# ===============================
# 🔥 LOGIKA PENGGANTIAN AUDITED
# ===============================
audited_keys = df_f.loc[df_f["IsAudited"], "SortKey"].unique()

df_f = df_f[
    (df_f["IsAudited"]) |
    (~df_f["SortKey"].isin(audited_keys))
]

# ===============================
# FILTER SIDEBAR (PERIODE & TAHUN)
# ===============================
st.sidebar.header("🔎 Filter Data")

tahun_filter = st.sidebar.multiselect(
    "Tahun",
    sorted(df_f["Tahun"].unique()),
    default=sorted(df_f["Tahun"].unique())
)

bulan_filter = st.sidebar.multiselect(
    "Bulan",
    sorted(df_f["Bulan"].unique()),
    default=sorted(df_f["Bulan"].unique())
)

df_f = df_f[
    (df_f["Tahun"].isin(tahun_filter)) &
    (df_f["Bulan"].isin(bulan_filter))
]

# ===============================
# AGREGASI (KUR GEN 1 + GEN 2)
# ===============================
agg_df = (
    df_f
    .groupby(["SortKey", "Periode_Label"], as_index=False)["Value"]
    .sum()
    .sort_values("SortKey")
)

agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000_000

# ===============================
# AREA CHART
# ===============================
fig = px.area(
    agg_df,
    x="Periode_Label",
    y="Value_T",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Outstanding KUR (Triliun)",
    yaxis=dict(ticksuffix=" T"),
    hovermode="x unified"
)

fig.update_xaxes(
    categoryorder="array",
    categoryarray=agg_df["Periode_Label"].tolist(),
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)
