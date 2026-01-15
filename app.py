import streamlit as st
import pandas as pd
import plotly.express as px
import re

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

df = load_data(uploaded_file)

# ===============================
# VALIDASI KOLOM
# ===============================
required_cols = ["Periode", "Value"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan")
        st.stop()

# ===============================
# SIMPAN PERIODE ASLI
# ===============================
df["Periode_Raw"] = df["Periode"].astype(str)

# ===============================
# PARSING PERIODE
# ===============================
bulan_map = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "mei": 5, "jun": 6, "jul": 7,
    "aug": 8, "agu": 8, "sep": 9,
    "oct": 10, "okt": 10,
    "nov": 11, "dec": 12
}

def parse_periode(val):
    try:
        dt = pd.to_datetime(val)
        return dt.year, dt.month
    except:
        pass

    text = str(val).lower()
    for b, m in bulan_map.items():
        if b in text:
            year_match = re.search(r"(20\d{2}|\d{2})", text)
            if year_match:
                y = int(year_match.group())
                if y < 100:
                    y += 2000
                return y, m
    return None, None

df[["Year", "Month"]] = df["Periode_Raw"].apply(
    lambda x: pd.Series(parse_periode(x))
)

df = df.dropna(subset=["Year", "Month"])
df["SortKey"] = df["Year"] * 100 + df["Month"]

# ===============================
# LABEL BULAN
# ===============================
bulan_id = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
}

df["Periode_Label"] = (
    df["Month"].map(bulan_id) + " " + df["Year"].astype(int).astype(str)
)

# ===============================
# FLAG AUDITED (PRIORITAS)
# ===============================
df["Is_Audited"] = df["Periode_Raw"].str.contains(
    "audit", case=False, na=False
).astype(int)

# ===============================
# CLEAN VALUE (AMAN FORMAT INDONESIA)
# ===============================
def parse_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)

    text = str(val).strip()

    # format Indonesia: 516.859.837.493,95
    if "." in text and "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text and "," not in text:
        text = text.replace(".", "")

    try:
        return float(text)
    except:
        return None

df["Value"] = df["Value"].apply(parse_value)

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter Data")

df_f = df.copy()

# ===============================
# FILTER TAHUN
# ===============================
available_years = sorted(df_f["Year"].unique())
selected_years = st.sidebar.multiselect(
    "Tahun",
    available_years,
    default=available_years
)

df_f = df_f[df_f["Year"].isin(selected_years)]

# ===============================
# FILTER BULAN
# ===============================
df_f["Bulan_Nama"] = df_f["Month"].map(bulan_id)

selected_months = st.sidebar.multiselect(
    "Bulan",
    list(bulan_id.values()),
    default=list(bulan_id.values())
)

df_f = df_f[df_f["Bulan_Nama"].isin(selected_months)]

# ===============================
# PREVIEW DATA (MENTAH - TANPA AGREGASI)
# ===============================
st.subheader("👀 Preview Data (Raw / As Is)")
st.dataframe(
    df_f.style.format({"Value": "Rp {:,.2f}"}),
    use_container_width=True
)

# ===============================
# AGREGASI KHUSUS KUR (AUDITED PRIORITY)
# ===============================
st.subheader("📈 OS Penjaminan KUR")

df_kur = df_f[df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])]

# Urutkan: audited diutamakan
df_kur_sorted = df_kur.sort_values(
    ["SortKey", "Is_Audited"],
    ascending=[True, False]
)

# Ambil audited jika ada, jika tidak ambil data biasa
df_kur_agg = (
    df_kur_sorted
    .groupby(["SortKey", "Periode_Label"], as_index=False)
    .agg(OS_KUR_Rp=("Value", "last"))
    .sort_values("SortKey")
)

df_kur_agg["OS_KUR_T"] = df_kur_agg["OS_KUR_Rp"] / 1_000_000_000_000

# ===============================
# GRAFIK
# ===============================
fig = px.area(
    df_kur_agg,
    x="Periode_Label",
    y="OS_KUR_T",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Outstanding KUR (Triliun)",
    yaxis=dict(ticksuffix=" T"),
    hovermode="x unified"
)

fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=df_kur_agg["Periode_Label"].tolist(),
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABEL HASIL OLAHAN
# ===============================
st.subheader("📋 Tabel Hasil Pengolahan OS Penjaminan KUR")

st.dataframe(
    df_kur_agg.style.format({
        "OS_KUR_Rp": "Rp {:,.2f}",
        "OS_KUR_T": "{:.2f}"
    }),
    use_container_width=True
)

# ===============================
# DOWNLOAD
# ===============================
st.download_button(
    "⬇️ Download Hasil OS KUR",
    df_kur_agg.to_csv(index=False).encode("utf-8"),
    "os_penjaminan_kur.csv",
    "text/csv"
)

#=============================================================================================================================
#========================================================================================================================================

# ===============================
# AGREGASI KHUSUS KUR (AUDITED PRIORITY)
# ===============================
st.subheader("📈 Ekuitas KUR")

df_kur = df_f[df_f["Jenis"].isin(["Ekuitas KUR"])]

# Urutkan: audited diutamakan
df_kur_sorted = df_kur.sort_values(
    ["SortKey", "Is_Audited"],
    ascending=[True, False]
)

# Ambil audited jika ada, jika tidak ambil data biasa
df_kur_agg = (
    df_kur_sorted
    .groupby(["SortKey", "Periode_Label"], as_index=False)
    .agg(Ekuitas_KUR_Rp=("Value", "last"))
    .sort_values("SortKey")
)

df_kur_agg["Ekuitas_KUR_T"] = df_kur_agg["Ekuitas_KUR_Rp"] / 1_000_000_000_000

# ===============================
# GRAFIK
# ===============================
fig = px.area(
    df_kur_agg,
    x="Periode_Label",
    y="Ekuitas_KUR_T",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Ekuitas KUR (Triliun)",
    yaxis=dict(ticksuffix=" T"),
    hovermode="x unified"
)

fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=df_kur_agg["Periode_Label"].tolist(),
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABEL HASIL OLAHAN
# ===============================
st.subheader("📋 Tabel Hasil Pengolahan Ekuitas KUR")

st.dataframe(
    df_kur_agg.style.format({
        "Ekuitas_KUR_Rp": "Rp {:,.2f}",
        "Ekuitas_KUR_T": "{:.2f}"
    }),
    use_container_width=True
)

# ===============================
# DOWNLOAD
# ===============================
st.download_button(
    "⬇️ Download Hasil Ekuitas KUR",
    df_kur_agg.to_csv(index=False).encode("utf-8"),
    "Ekuitas_kur.csv",
    "text/csv"
)

#============================================================================================================================================
#==============================================================================================================================================

# ===============================
# AGREGASI KHUSUS KUR (AUDITED PRIORITY)
# ===============================
st.subheader("📈 OS Penjaminan KUR Dan PEN")

df_kur = df_f[df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2","PEN Gen 1", "PEN Gen 2"])]

# Urutkan: audited diutamakan
df_kur_sorted = df_kur.sort_values(
    ["SortKey", "Is_Audited"],
    ascending=[True, False]
)

# Ambil audited jika ada, jika tidak ambil data biasa
df_kur_agg = (
    df_kur_sorted
    .groupby(["SortKey", "Periode_Label"], as_index=False)
    .agg(OS_KUR_PEN_Rp =("Value", "last"))
    .sort_values("SortKey")
)

df_kur_agg["OS_KUR_PEN_T"] = df_kur_agg["OS_KUR_PEN_Rp"] / 1_000_000_000_000

# ===============================
# GRAFIK
# ===============================
fig = px.area(
    df_kur_agg,
    x="Periode_Label",
    y="OS_KUR_PEN_T",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Outstanding KUR_PEN (Triliun)",
    yaxis=dict(ticksuffix=" T"),
    hovermode="x unified"
)

fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=df_kur_agg["Periode_Label"].tolist(),
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABEL HASIL OLAHAN
# ===============================
st.subheader("📋 Tabel Hasil Pengolahan OS Penjaminan KUR & PEN")

st.dataframe(
    df_kur_agg.style.format({
        "OS_KUR_PEN_Rp": "Rp {:,.2f}",
        "OS_KUR_PEN_T": "{:.2f}"
    }),
    use_container_width=True
)

# ===============================
# DOWNLOAD
# ===============================
st.download_button(
    "⬇️ Download Hasil OS KUR_PEN",
    df_kur_agg.to_csv(index=False).encode("utf-8"),
    "os_penjaminan_kur_pen.csv",
    "text/csv"
)

#================================================================================================================================================
#===================================================================================================================================================

# ===============================
# AGREGASI KUR UNTUK GEaring Ratio
# ===============================
st.subheader("📈 Gearing Ratio KUR")

# Ambil KUR Gen 1 + KUR Gen 2 untuk numerator
df_kur_num = df_f[df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])]

# Jumlahkan Value per Periode_Label (numerator)
df_kur_num_agg = (
    df_kur_num.groupby(["Periode_Label"], as_index=False)
    .agg(KUR_Total_Rp=("Value", "sum"))
)

# Ambil Ekuitas KUR (asumsi ada di df_f, misal Jenis == "Ekuitas KUR")
df_ekuitas = df_f[df_f["Jenis"] == "Ekuitas KUR"]

# Gabungkan numerator dan ekuitas berdasarkan Periode_Label
df_gear = pd.merge(
    df_kur_num_agg,
    df_ekuitas[["Periode_Label", "Value"]].rename(columns={"Value": "Ekuitas_Rp"}),
    on="Periode_Label",
    how="left"
)

# Hitung Gearing Ratio
df_gear["Gearing_Ratio"] = df_gear["KUR_Total_Rp"] / df_gear["Ekuitas_Rp"]

# ===============================
# GRAFIK GEaring Ratio
# ===============================
fig = px.line(
    df_gear,
    x="Periode_Label",
    y="Gearing_Ratio",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Gearing Ratio KUR",
    yaxis=dict(ticksuffix="x"),  # misal ratio dikali 1
    hovermode="x unified"
)

fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=df_gear["Periode_Label"].tolist(),
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABEL HASIL
# ===============================
st.subheader("📋 Tabel Gearing Ratio KUR")

st.dataframe(
    df_gear.style.format({
        "KUR_Total_Rp": "Rp {:,.2f}",
        "Ekuitas_Rp": "Rp {:,.2f}",
        "Gearing_Ratio": "{:.2f}"
    }),
    use_container_width=True
)

# ===============================
# DOWNLOAD
# ===============================
st.download_button(
    "⬇️ Download Hasil Gearing Ratio KUR",
    df_gear.to_csv(index=False).encode("utf-8"),
    "gearing_ratio_kur.csv",
    "text/csv"
)
