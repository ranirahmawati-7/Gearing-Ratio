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
st.dataframe(
    df_f.style.format({
        "Value": "Rp {:,.2f}"
    }),
    use_container_width=True
)

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

# ===============================
# AREA CHART – TOTAL BULANAN (KUR GEN 1 + GEN 2)
# ===============================
st.subheader("📈 Tren Outstanding per Bulan (KUR Gen 1 + KUR Gen 2)")

needed_cols = {"Periode", "Value", "Jenis"}

if needed_cols.issubset(df_f.columns):

    df_tren = df_f.copy()

    # Filter KUR Gen 1 & Gen 2
    df_tren = df_tren[df_tren["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])]

    df_tren["Periode"] = pd.to_datetime(df_tren["Periode"], errors="coerce")
    df_tren["Bulan"] = df_tren["Periode"].dt.month

    bulan_id = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    df_tren["Nama_Bulan"] = df_tren["Bulan"].map(bulan_id)

    # Agregasi semua tahun
    agg_df = df_tren.groupby("Nama_Bulan", as_index=False)["Value"].sum()

    urutan_bulan = list(bulan_id.values())
    agg_df["Nama_Bulan"] = pd.Categorical(
        agg_df["Nama_Bulan"],
        categories=urutan_bulan,
        ordered=True
    )
    agg_df = agg_df.sort_values("Nama_Bulan")

    # Konversi ke Triliun
    agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000

    fig = px.area(
        agg_df,
        x="Nama_Bulan",
        y="Value_T",
        markers=True,
        title="Total Outstanding Bulanan (Akumulasi Semua Tahun)"
    )

    fig.update_layout(
        xaxis_title="Bulan",
        yaxis_title="Outstanding",
        hovermode="x unified",
        yaxis=dict(
            tickformat=",.0f",
            ticksuffix="T"
        )
    )

    fig.update_traces(
        hovertemplate="Bulan: %{x}<br>Outstanding: %{y:.2f}T<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

# ===============================
# AREA CHART – TOTAL BULANAN PER TAHUN (KUR GEN 1 + GEN 2)
# ===============================
st.subheader("📈 Tren Outstanding Bulanan per Tahun (KUR Gen 1 + KUR Gen 2)")

needed_cols = {"Periode", "Value", "Jenis"}

if needed_cols.issubset(df_f.columns):

    df_tren = df_f.copy()

    # Filter hanya KUR Gen 1 & Gen 2
    df_tren = df_tren[df_tren["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])]

    # Pastikan datetime
    df_tren["Periode"] = pd.to_datetime(df_tren["Periode"], errors="coerce")

    # Ambil tahun & bulan
    df_tren["Tahun"] = df_tren["Periode"].dt.year
    df_tren["Bulan"] = df_tren["Periode"].dt.month

    # Nama bulan Indonesia
    bulan_id = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    df_tren["Nama_Bulan"] = df_tren["Bulan"].map(bulan_id)

    # Label Bulan Tahun (contoh: Februari 2025)
    df_tren["Bulan_Tahun"] = (
        df_tren["Nama_Bulan"] + " " + df_tren["Tahun"].astype(str)
    )

    # Agregasi per Bulan-Tahun
    agg_df = (
        df_tren
        .groupby(["Tahun", "Bulan", "Bulan_Tahun"], as_index=False)["Value"]
        .sum()
        .sort_values(["Tahun", "Bulan"])
    )

    # Konversi ke Triliun
    agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000

    # Area chart
    fig = px.area(
        agg_df,
        x="Bulan_Tahun",
        y="Value_T",
        markers=True,
        title="Total Outstanding Bulanan per Tahun (KUR Gen 1 + KUR Gen 2)"
    )

    fig.update_layout(
        xaxis_title="Periode",
        yaxis_title="Outstanding",
        hovermode="x unified",
        yaxis=dict(
            tickformat=",.0f",
            ticksuffix="T"
        )
    )

    fig.update_traces(
        hovertemplate="Periode: %{x}<br>Outstanding: %{y:.2f}T<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)


# ===============================
# AREA CHART – TOTAL BULANAN (EKUITAS kur)
# ===============================
st.subheader("📈 Tren Outstanding per Bulan EKUITAS KUR")

needed_cols = {"Periode", "Value", "Jenis"}

if needed_cols.issubset(df_f.columns):

    df_tren = df_f.copy()

    # Filter KUR Gen 1 & Gen 2
    df_tren = df_tren[df_tren["Jenis"].isin(["Ekuitas KUR"])]

    df_tren["Periode"] = pd.to_datetime(df_tren["Periode"], errors="coerce")
    df_tren["Bulan"] = df_tren["Periode"].dt.month

    bulan_id = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    df_tren["Nama_Bulan"] = df_tren["Bulan"].map(bulan_id)

    # Agregasi semua tahun
    agg_df = df_tren.groupby("Nama_Bulan", as_index=False)["Value"].sum()

    urutan_bulan = list(bulan_id.values())
    agg_df["Nama_Bulan"] = pd.Categorical(
        agg_df["Nama_Bulan"],
        categories=urutan_bulan,
        ordered=True
    )
    agg_df = agg_df.sort_values("Nama_Bulan")

    # Konversi ke Triliun
    agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000

    fig = px.area(
        agg_df,
        x="Nama_Bulan",
        y="Value_T",
        markers=True,
        title="Total Outstanding Bulanan (Akumulasi Semua Tahun)"
    )

    fig.update_layout(
        xaxis_title="Bulan",
        yaxis_title="Outstanding",
        hovermode="x unified",
        yaxis=dict(
            tickformat=",.0f",
            ticksuffix="T"
        )
    )

    fig.update_traces(
        hovertemplate="Bulan: %{x}<br>Outstanding: %{y:.2f}T<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)


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
