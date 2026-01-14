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

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(f"❌ Gagal membaca file: {e}")
    st.stop()

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
# PARSING PERIODE STRING
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
# CLEAN VALUE
# ===============================
df["Value"] = (
    df["Value"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

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

# ===============================
# KHUSUS KUR:
# GEN 1 + GEN 2 DIGABUNG
# ===============================
if "Jenis" in df_f.columns:
    kur_mask = df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])

    df_kur = (
        df_f[kur_mask]
        .groupby(
            ["SortKey", "Periode_Label", "Year", "Month"],
            as_index=False
        )["Value"]
        .sum()
    )

    df_kur["Jenis"] = "KUR (Gen 1 + Gen 2)"

    # data selain KUR
    df_non_kur = df_f[~kur_mask]

    # gabungkan kembali
    df_f = pd.concat([df_non_kur, df_kur], ignore_index=True)

# ===============================
# PREVIEW DATA
# ===============================
st.subheader("👀 Preview Data")
st.dataframe(
    df_f.style.format({"Value": "Rp {:,.0f}"}),
    use_container_width=True
)

# ===============================
# AREA CHART – OUTSTANDING
# ===============================
st.subheader("📈 Outstanding per Bulan")

agg_df = (
    df_f
    .groupby(["SortKey", "Periode_Label"], as_index=False)["Value"]
    .sum()
    .sort_values("SortKey")
)

agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000

fig = px.area(
    agg_df,
    x="Periode_Label",
    y="Value_T",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Outstanding (Triliun)",
    yaxis=dict(ticksuffix=" T"),
    hovermode="x unified"
)

fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=agg_df["Periode_Label"].tolist(),
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABLE DETAIL
# ===============================
st.subheader("📋 Data Detail (Final)")
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
