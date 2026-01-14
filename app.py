import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# ===============================
# LOAD DATA
# ===============================
st.title("📊 Outstanding KUR (Gen 1 + Gen 2)")

uploaded_file = st.file_uploader(
    "Upload file Excel",
    type=["xlsx"]
)

if uploaded_file is None:
    st.stop()

df = pd.read_excel(uploaded_file)

# ===============================
# VALIDASI KOLOM
# ===============================
required_cols = {"Periode", "Jenis", "Value"}
if not required_cols.issubset(df.columns):
    st.error(f"Kolom wajib: {required_cols}")
    st.stop()

# ===============================
# CLEAN VALUE (FORMAT INDONESIA)
# ===============================
df["Value"] = (
    df["Value"]
    .astype(str)
    .str.replace(".", "", regex=False)   # hapus pemisah ribuan
    .str.replace(",", ".", regex=False)  # ubah desimal ke format python
)

df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

# ===============================
# FILTER: HANYA KUR GEN 1 & GEN 2
# ===============================
df_f = df[df["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])].copy()

# ===============================
# OLAH PERIODE (BULAN + TAHUN)
# ===============================
df_f["Periode_Raw"] = pd.to_datetime(
    df_f["Periode"],
    errors="coerce"
)

df_f["Periode_Label"] = df_f["Periode_Raw"].dt.strftime("%b %Y")
df_f["SortKey"] = df_f["Periode_Raw"].dt.to_period("M").astype(str)

# ===============================
# AGREGASI
# (GEN 1 + GEN 2 PADA PERIODE YANG SAMA)
# ===============================
agg_df = (
    df_f
    .groupby(["SortKey", "Periode_Label"], as_index=False)["Value"]
    .sum()
    .sort_values("SortKey")
)

# ===============================
# KONVERSI KE TRILIUN
# ===============================
agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000

# ===============================
# AREA CHART
# ===============================
st.subheader("📈 Outstanding KUR (Gen 1 + Gen 2) per Bulan")

fig = px.area(
    agg_df,
    x="Periode_Label",
    y="Value_T",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Outstanding (Triliun Rupiah)",
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
# TABEL CEK (OPSIONAL)
# ===============================
with st.expander("🔍 Lihat Data Hasil Penjumlahan"):
    st.dataframe(
        agg_df.assign(
            Outstanding_Rp=lambda x: x["Value"].map(
                lambda v: f"Rp {v:,.0f}".replace(",", ".")
            )
        )[["Periode_Label", "Outstanding_Rp"]]
    )
