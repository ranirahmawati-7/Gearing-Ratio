import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Dashboard Ekuitas",
    layout="wide"
)

st.title("📊 Dashboard Ekuitas")

# ===============================
# UPLOAD DATA
# ===============================
uploaded_file = st.file_uploader(
    "Upload file CSV atau Excel",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("📥 Silakan upload file data terlebih dahulu.")
    st.stop()

# ===============================
# READ DATA
# ===============================
try:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Gagal membaca file: {e}")
    st.stop()

# ===============================
# VALIDASI KOLOM WAJIB
# ===============================
required_columns = ["Periode", "Jenis", "Value"]

missing_cols = [c for c in required_columns if c not in df.columns]
if missing_cols:
    st.error(f"Kolom berikut tidak ditemukan: {missing_cols}")
    st.stop()

# ===============================
# DATA CLEANING
# ===============================
df["Periode"] = pd.to_datetime(df["Periode"], errors="coerce")
df = df.dropna(subset=["Periode", "Value"])
df = df.sort_values("Periode")

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter")

jenis_list = st.sidebar.multiselect(
    "Pilih Jenis",
    options=sorted(df["Jenis"].unique()),
    default=sorted(df["Jenis"].unique())
)

periode_min = df["Periode"].min().date()
periode_max = df["Periode"].max().date()

periode_range = st.sidebar.date_input(
    "Pilih Rentang Periode",
    value=[periode_min, periode_max]
)

# ===============================
# FILTER DATA
# ===============================
filtered_df = df[
    (df["Jenis"].isin(jenis_list)) &
    (df["Periode"].dt.date >= periode_range[0]) &
    (df["Periode"].dt.date <= periode_range[1])
]

if filtered_df.empty:
    st.warning("⚠️ Tidak ada data pada filter yang dipilih.")
    st.stop()

# ===============================
# KPI
# ===============================
latest_value = filtered_df.iloc[-1]["Value"]

previous_value = (
    filtered_df.iloc[-2]["Value"]
    if len(filtered_df) > 1
    else latest_value
)

delta = latest_value - previous_value
delta_pct = (delta / previous_value * 100) if previous_value != 0 else 0

col1, col2, col3 = st.columns(3)

col1.metric("📌 Nilai Terakhir", f"{latest_value:,.2f}")
col2.metric("📈 Perubahan", f"{delta:,.2f}", f"{delta_pct:.2f}%")
col3.metric("📅 Periode Terakhir", filtered_df.iloc[-1]["Periode"].strftime("%Y-%m-%d"))

# ===============================
# LINE CHART
# ===============================
fig = px.line(
    filtered_df,
    x="Periode",
    y="Value",
    color="Jenis",
    markers=True,
    title="Tren Nilai Ekuitas"
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Value",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABLE
# ===============================
st.subheader("📋 Data Detail")

st.dataframe(
    filtered_df.style.format({"Value": "{:,.2f}"}),
    use_container_width=True
)

# ===============================
# DOWNLOAD
# ===============================
csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Data Filtered",
    data=csv,
    file_name="data_filtered.csv",
    mime="text/csv"
)
