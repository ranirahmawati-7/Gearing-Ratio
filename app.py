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

# FILTER DATA
df_f = df.copy()

if "Jenis" in df.columns and jenis_filter:
    df_f = df_f[df_f["Jenis"].isin(jenis_filter)]

if "Generasi" in df.columns and gen_filter:
    df_f = df_f[df_f["Generasi"].isin(gen_filter)]

# ===============================
# LINE / AREA CHART – TOTAL PER BULAN (KUR Gen 1 + KUR Gen 2, SEMUA TAHUN)
# ===============================
st.subheader("📈 Tren OS Penjamin KUR")

needed_cols = {"Periode", "Value", "Jenis"}

if needed_cols.issubset(df_f.columns):

    df_tren = df_f.copy()

    # Filter hanya KUR Gen 1 & KUR Gen 2
    df_tren = df_tren[df_tren["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])]

    # Pastikan datetime
    df_tren["Periode"] = pd.to_datetime(df_tren["Periode"], errors="coerce")

    # Ambil bulan
    df_tren["Bulan"] = df_tren["Periode"].dt.month

    # Mapping bulan Indonesia
    bulan_id = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    df_tren["Nama_Bulan"] = df_tren["Bulan"].map(bulan_id)

    # Agregasi: SUM Value per Bulan (gabungkan KUR Gen 1 + KUR Gen 2, semua tahun)
    agg_df = df_tren.groupby("Nama_Bulan", as_index=False)["Value"].sum()

    # Urutkan bulan Jan → Des
    urutan_bulan = list(bulan_id.values())
    agg_df["Nama_Bulan"] = pd.Categorical(agg_df["Nama_Bulan"], categories=urutan_bulan, ordered=True)
    agg_df = agg_df.sort_values("Nama_Bulan")

    # Konversi ke Triliun
    agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000

    # Area chart dengan sumbu Y T (1T, 2T)
    fig = px.area(
        agg_df,
        x="Nama_Bulan",
        y="Value_T",
        markers=True,
        title="Tren Outstanding per Bulan (KUR Gen 1 + KUR Gen 2, Total Semua Tahun)"
    )

    # Atur format sumbu Y menjadi 1T, 2T
    fig.update_layout(
        xaxis_title="Bulan",
        yaxis_title="Outstanding (Triliun)",
        hovermode="x unified",
        yaxis=dict(tickformat="~s")  # otomatis T, M, B
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning(
        f"❌ Grafik tren tidak dapat ditampilkan. Kolom kurang: "
        f"{needed_cols - set(df_f.columns)}"
    )

# ===============================
# TABLE
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
