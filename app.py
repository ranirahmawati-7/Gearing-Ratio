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
    "Upload file Excel / CSV",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("📥 Silakan upload file terlebih dahulu")
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
# PREVIEW DATA
# ===============================
st.subheader("👀 Preview Data")
st.dataframe(df, use_container_width=True)

# ===============================
# BASIC CLEANING (AMAN)
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
# SIDEBAR FILTER (DINAMIS)
# ===============================
st.sidebar.header("🔎 Filter")

if "Jenis" in df.columns:
    jenis_filter = st.sidebar.multiselect(
        "Jenis",
        df["Jenis"].dropna().unique(),
        default=df["Jenis"].dropna().unique()
    )
else:
    jenis_filter = []

if "Generasi" in df.columns:
    gen_filter = st.sidebar.multiselect(
        "Generasi",
        df["Generasi"].dropna().unique(),
        default=df["Generasi"].dropna().unique()
    )
else:
    gen_filter = []

# FILTER DATA (AMAN)
df_f = df.copy()

if "Jenis" in df.columns and jenis_filter:
    df_f = df_f[df_f["Jenis"].isin(jenis_filter)]

if "Generasi" in df.columns and gen_filter:
    df_f = df_f[df_f["Generasi"].isin(gen_filter)]

# ===============================
# BAR CHART – JUMLAH DEBITUR
# ===============================
st.subheader("👥 Jumlah Debitur")

needed_cols = {"Jenis", "Jumlah Debitur"}

if needed_cols.issubset(df_f.columns):
    deb_df = df_f.groupby("Jenis", as_index=False)["Jumlah Debitur"].sum()

    fig = px.bar(
        deb_df,
        x="Jenis",
        y="Jumlah Debitur",
        text_auto=True,
        title="Jumlah Debitur"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(
        f"❌ Grafik tidak dapat ditampilkan. Kolom kurang: "
        f"{needed_cols - set(df_f.columns)}"
    )

# ===============================
# LINE / AREA CHART – TREN PER BULAN (AGREGAT TAHUNAN)
# ===============================
st.subheader("📈 Tren Outstanding (Akumulasi Tahunan per Bulan)")

needed_cols = {"Periode", "Value", "Jenis"}

if needed_cols.issubset(df_f.columns):

    df_tren = df_f.copy()

    # Pastikan Periode datetime
    df_tren["Periode"] = pd.to_datetime(df_tren["Periode"], errors="coerce")

    # Ambil komponen waktu
    df_tren["Tahun"] = df_tren["Periode"].dt.year
    df_tren["Bulan"] = df_tren["Periode"].dt.month
    df_tren["Tanggal"] = df_tren["Periode"].dt.day

    # Label bulan + tanggal (contoh: 31 Januari)
    df_tren["Bulan_Tanggal"] = (
        df_tren["Tanggal"].astype(str)
        + " "
        + df_tren["Periode"].dt.month_name(locale="id")
    )

    # Agregasi: jumlah Value per Tahun, Bulan_Tanggal, Jenis
    agg_df = (
        df_tren
        .groupby(["Tahun", "Bulan", "Bulan_Tanggal", "Jenis"], as_index=False)
        ["Value"]
        .sum()
        .sort_values(["Tahun", "Bulan"])
    )

    # Area chart (line + bayangan)
    fig = px.area(
        agg_df,
        x="Bulan_Tanggal",
        y="Value",
        color="Jenis",
        line_group="Tahun",
        markers=True,
        title="Tren Outstanding (Akumulasi Tahunan per Bulan)"
    )

    fig.update_layout(
        xaxis_title="Periode (Tanggal - Bulan)",
        yaxis_title="Total Outstanding",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning(
        f"❌ Grafik tren tidak dapat ditampilkan. Kolom kurang: "
        f"{needed_cols - set(df_f.columns)}"
    )

# ===============================
# TABLE (SELALU TAMPIL)
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
