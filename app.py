import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Dashboard KUR & PEN",
    layout="wide"
)

st.title("📊 Summary Outstanding Penjaminan KUR & PEN")

# ===============================
# UPLOAD FILE
# ===============================
uploaded_file = st.file_uploader(
    "📥 Upload file Excel / CSV",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("Silakan upload file terlebih dahulu")
    st.stop()

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(f"❌ Gagal membaca file: {e}")
    st.stop()

# ===============================
# BASIC CLEANING
# ===============================
if "Periode" in df.columns:
    df["Periode"] = pd.to_datetime(df["Periode"], errors="coerce")

if "Value" in df.columns:
    df["Value"] = (
        df["Value"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(".", "", regex=False)
    )
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

if "Jumlah Debitur" in df.columns:
    df["Jumlah Debitur"] = pd.to_numeric(df["Jumlah Debitur"], errors="coerce")

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter Data")

df_f = df.copy()

if "Jenis" in df.columns:
    jenis_filter = st.sidebar.multiselect(
        "Jenis",
        sorted(df["Jenis"].dropna().unique()),
        default=sorted(df["Jenis"].dropna().unique())
    )
    df_f = df_f[df_f["Jenis"].isin(jenis_filter)]

if "Generasi" in df.columns:
    gen_filter = st.sidebar.multiselect(
        "Generasi",
        sorted(df["Generasi"].dropna().unique()),
        default=sorted(df["Generasi"].dropna().unique())
    )
    df_f = df_f[df_f["Generasi"].isin(gen_filter)]

# ===============================
# PREVIEW DATA
# ===============================
st.subheader("👀 Preview Data (Filtered)")
st.dataframe(
    df_f.style.format({"Value": "Rp {:,.0f}"}),
    use_container_width=True
)

# ===============================
# BAR CHART – JUMLAH DEBITUR
# ===============================
st.subheader("👥 Jumlah Debitur")

if {"Jenis", "Jumlah Debitur"}.issubset(df_f.columns):
    deb_df = df_f.groupby("Jenis", as_index=False)["Jumlah Debitur"].sum()

    fig = px.bar(
        deb_df,
        x="Jenis",
        y="Jumlah Debitur",
        text_auto=True
    )

    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

# ===============================
# AREA CHART – BULANAN AKUMULASI (SEMUA TAHUN)
# ===============================
st.subheader("📈 Outstanding Bulanan (Akumulasi Semua Tahun)")

bulan_id = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

if {"Periode", "Value", "Jenis"}.issubset(df_f.columns):

    df_tren = df_f[df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])].copy()

    df_tren["Month"] = df_tren["Periode"].dt.month
    df_tren["Nama_Bulan"] = df_tren["Month"].map(bulan_id)

    agg_df = (
        df_tren
        .groupby("Month", as_index=False)["Value"]
        .sum()
        .sort_values("Month")
    )

    agg_df["Nama_Bulan"] = agg_df["Month"].map(bulan_id)
    agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000_000

    fig = px.area(
        agg_df,
        x="Nama_Bulan",
        y="Value_T",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Bulan",
        yaxis_title="Outstanding (T)",
        yaxis=dict(ticksuffix="T"),
        hovermode="x unified"
    )

    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=agg_df["Nama_Bulan"].tolist(),
        tickmode="array",
        tickvals=agg_df["Nama_Bulan"].tolist(),
        ticktext=agg_df["Nama_Bulan"].tolist()
    )

    st.plotly_chart(fig, use_container_width=True)

# ===============================
# AREA CHART – BULANAN PER TAHUN
# ===============================
st.subheader("📈 Outstanding Bulanan per Tahun")

if {"Periode", "Value", "Jenis"}.issubset(df_f.columns):

    df_tren = df_f[df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])].copy()

    df_tren["Year"] = df_tren["Periode"].dt.year
    df_tren["Month"] = df_tren["Periode"].dt.month
    df_tren["SortKey"] = df_tren["Year"] * 100 + df_tren["Month"]

    df_tren["Bulan_Tahun"] = (
        df_tren["Month"].map(bulan_id) + " " + df_tren["Year"].astype(str)
    )

    agg_df = (
        df_tren
        .groupby(["SortKey", "Bulan_Tahun"], as_index=False)["Value"]
        .sum()
        .sort_values("SortKey")
    )

    agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000_000

    fig = px.area(
        agg_df,
        x="Bulan_Tahun",
        y="Value_T",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Periode",
        yaxis_title="Outstanding (T)",
        yaxis=dict(ticksuffix="T"),
        hovermode="x unified"
    )

    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=agg_df["Bulan_Tahun"].tolist(),
        tickmode="array",
        tickvals=agg_df["Bulan_Tahun"].tolist(),
        ticktext=agg_df["Bulan_Tahun"].tolist(),
        tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABLE DETAIL
# ===============================
st.subheader("📋 Data Detail")
st.dataframe(df_f, use_container_width=True)

# ===============================
# DOWNLOAD
# ===============================
st.download_button(
    "⬇️ Download Data Filtered",
    df_f.to_csv(index=False).encode("utf-8"),
    "data_filtered.csv",
    "text/csv"
)
