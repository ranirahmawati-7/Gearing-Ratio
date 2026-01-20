import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)
# ===============================
# HEADER DENGAN LOGO
# ===============================
col_logo, col_title = st.columns([1, 8])

with col_logo:
    st.image("gambar/OIP.jpg", width=90)

with col_title:
    st.markdown(
        """
        <h1 style="margin-bottom:0; color:#1f4e79;">
            Dashboard Gearing Ratio KUR & PEN
        </h1>
        <p style="margin-top:0; font-size:16px; color:gray;">
            Analisis Outstanding, Ekuitas, dan Trend Gearing Ratio berbasis data periodik
        </p>
        """,
        unsafe_allow_html=True
    )

st.info("Website ini akan otomatis menampilkan dashboard untuk perhitungan Trend Gearing Ratio setelah anda mengupload file dengan format xlxs atau csv, dan pastikan format tabel yang akan diinput sesuai dengan contoh")
# Tampilkan gambar contoh format Excel
st.image(
    "gambar/ssXlsx.png",
    caption="Contoh format file Excel (.xlsx) yang didukung",
    use_container_width=True
)
st.title("📊 Summary Tend Gearing Ratio")

# ===============================
# UPLOAD FILE
# ===============================
uploaded_file = st.file_uploader(
    "📥 Upload file Excel / CSV",
    type=["csv", "xlsx"],
    key="upload_Gearing"
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
with st.expander("👀 Preview Data (Klik untuk tampil / sembunyi)", expanded=False):

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
with st.expander("📋 Tabel Hasil Pengolahan OS Penjaminan KUR", expanded=False):

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
with st.expander("📋 Tabel Hasil Pengolahan Ekuitas KUR", expanded=False):

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
with st.expander("📋 Tabel Hasil Pengolahan OS Penjaminan KUR & PEN", expanded=False):

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
with st.expander("📋 Tabel Gearing Ratio KUR", expanded=False):

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

#================================================================================================================================================
#===================================================================================================================================================

# ===========================================
# AGREGASI KUR UNTUK GEaring Ratio KUR & PEN
# ===========================================
st.subheader("📈 Gearing Ratio KUR & PEN")

# Ambil KUR Gen 1 + KUR Gen 2 untuk numerator
df_kur_num = df_f[df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2", "PEN Gen 1", "PEN Gen 2"])]

# Jumlahkan Value per Periode_Label (numerator)
df_kur_num_agg = (
    df_kur_num.groupby(["Periode_Label"], as_index=False)
    .agg(KUR_PEN_Total_Rp=("Value", "sum"))
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
df_gear["GR_KUR_PEN"] = df_gear["KUR_PEN_Total_Rp"] / df_gear["Ekuitas_Rp"]

# ===============================
# GRAFIK GEaring Ratio
# ===============================
fig = px.line(
    df_gear,
    x="Periode_Label",
    y="GR_KUR_PEN",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Gearing Ratio KUR dan PEN",
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
with st.expander("📋 Tabel Gearing Ratio KUR dan PEN", expanded=False):

        st.dataframe(
            df_gear.style.format({
                "KUR_PEN_Total_Rp": "Rp {:,.2f}",
                "Ekuitas_Rp": "Rp {:,.2f}",
                "GR_KUR_PEN": "{:.2f}"
            }),
            use_container_width=True
        )
        
        # ===============================
        # DOWNLOAD
        # ===============================
        st.download_button(
            "⬇️ Download Hasil Gearing Ratio KUR dan PEN",
            df_gear.to_csv(index=False).encode("utf-8"),
            "gearing_ratio_kurpen.csv",
            "text/csv"
        )


#====================================================================================================================================================================

import streamlit as st
import pandas as pd

# ===============================
# PAGE CONFIG (HARUS PALING ATAS)
# ===============================
st.set_page_config(
    page_title="Dashboard KUR & PEN",
    layout="wide"
)

st.title("📊 Summary GEN Type")

# ===============================
# UPLOAD FILE
# ===============================
uploaded_file1 = st.file_uploader(
    "📥 Upload file Excel / CSV",
    type=["csv", "xlsx"],
    key="upload_all"
)

if uploaded_file1 is None:
    st.info("Silakan upload file terlebih dahulu")
    st.stop()

# ===============================
# GET SHEET NAMES (JIKA EXCEL)
# ===============================
sheet_names = None

if uploaded_file1.name.endswith(".xlsx"):
    xls = pd.ExcelFile(uploaded_file1)
    sheet_names = xls.sheet_names

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter Data")

if sheet_names:
    selected_sheet = st.sidebar.selectbox(
        "📄 Pilih Sheet",
        sheet_names,
        key="select_sheet"
    )
else:
    selected_sheet = None

# ===============================
# LOAD DATA
# ===============================
@st.cache_data(show_spinner=True)
def load_data(file, sheet_name=None):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file, sheet_name=sheet_name)

df1 = load_data(uploaded_file1, selected_sheet)

# ===============================
# VALIDASI DATA
# ===============================
if df1.empty:
    st.warning("⚠️ Sheet ini kosong")
    st.stop()

# ===============================
# CLEAN VALUE (FORMAT INDONESIA)
# ===============================
def parse_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)

    text = str(val).strip()

    # Format Indonesia: 516.859.837.493,95
    if "." in text and "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text and "," not in text:
        text = text.replace(".", "")

    try:
        return float(text)
    except:
        return None

if "Value" in df1.columns:
    df1["Value"] = df1["Value"].apply(parse_value)

# ===============================
# PREVIEW DATA
# ===============================
with st.expander("👀 Preview Data (Klik untuk tampil / sembunyi)", expanded=False):
    if "Value" in df1.columns:
        st.dataframe(
            df1.style.format({"Value": "Rp {:,.2f}"}),
            use_container_width=True
        )
    else:
        st.dataframe(df1, use_container_width=True)

# ===============================
# INFO DATA
# ===============================
st.markdown("### ℹ️ Info Data")
st.write("Jumlah baris:", len(df1))

# ===============================
# FILTER TAMBAHAN (DATA LEVEL)
# ===============================
required_cols = {"Periode", "KUR/PEN", "Generasi", "Metrics", "Value"}
missing_cols = required_cols - set(df1.columns)

if missing_cols:
    st.error(f"❌ Kolom tidak lengkap: {missing_cols}")
    st.stop()

# Sidebar filters
periode_opt = sorted(df1["Periode"].dropna().unique())
kurpen_opt = sorted(df1["KUR/PEN"].dropna().unique())
gen_opt = sorted(df1["Generasi"].dropna().unique())

selected_periode = st.sidebar.multiselect(
    "📅 Pilih Periode",
    periode_opt,
    default=periode_opt
)

selected_kurpen = st.sidebar.multiselect(
    "🏦 Pilih KUR / PEN",
    kurpen_opt,
    default=kurpen_opt
)

selected_gen = st.sidebar.multiselect(
    "🧬 Pilih Generasi",
    gen_opt,
    default=gen_opt
)

# ===============================
# APPLY FILTER
# ===============================
df_f = df1[
    (df1["Periode"].isin(selected_periode)) &
    (df1["KUR/PEN"].isin(selected_kurpen)) &
    (df1["Generasi"].isin(selected_gen))
].copy()

if df_f.empty:
    st.warning("⚠️ Data kosong setelah filter")
    st.stop()

# ===============================
# AGREGASI (SUM) & KONVERSI KE T
# ===============================
df_agg = (
    df_f
    .groupby("Metrics", as_index=False)
    .agg(Total_Value=("Value", "sum"))
)

# Konversi ke Triliun
df_agg["Total_T"] = df_agg["Total_Value"] / 1_000_000_000_000

# ===============================
# GRAFIK BATANG
# ===============================
import plotly.express as px

st.subheader("📊 Grafik Batang Summary Metrics (Dalam Triliun)")

fig = px.bar(
    df_agg,
    x="Metrics",
    y="Total_T",
    text="Total_T",
    labels={
        "Metrics": "Metrics",
        "Total_T": "Total (Triliun)"
    }
)

fig.update_traces(
    texttemplate="%{text:,.2f} T",
    textposition="outside"
)

fig.update_layout(
    yaxis_title="Total (Triliun)",
    xaxis_title="Metrics",
    uniformtext_minsize=10,
    uniformtext_mode="hide"
)

st.plotly_chart(fig, use_container_width=True)
#=+======Untuk Memperjelas Jumblah Debitur ================================
# ===============================
# PLOT KHUSUS JUMLAH DEBITUR
# ===============================
df_debitur = df_f[df_f["Metrics"].str.lower() == "jumlah debitur"].copy()

if df_debitur.empty:
    st.warning("⚠️ Tidak ada data 'Jumlah Debitur' untuk filter yang dipilih")
else:
    # Agregasi
    df_debitur_agg = (
        df_debitur
        .groupby(["KUR/PEN", "Generasi"], as_index=False)
        .agg(Jumlah_Debitur=("Value", "sum"))
    )

    # Buat label jenis
    df_debitur_agg["Jenis"] = (
        df_debitur_agg["KUR/PEN"] + " - " + df_debitur_agg["Generasi"]
    )

    # ===============================
    # GRAFIK BATANG JUMLAH DEBITUR
    # ===============================
    st.subheader("📊 Jumlah Debitur per Jenis")

    fig_debitur = px.bar(
        df_debitur_agg,
        x="Jenis",
        y="Jumlah_Debitur",
        text="Jumlah_Debitur",
        labels={
            "Jenis": "Jenis",
            "Jumlah_Debitur": "Jumlah Debitur"
        }
    )

    fig_debitur.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig_debitur.update_layout(
        yaxis_title="Jumlah Debitur",
        xaxis_title="Jenis",
        uniformtext_minsize=10,
        uniformtext_mode="hide"
    )

    st.plotly_chart(fig_debitur, use_container_width=True)

    # ===============================
    # TABEL PENDUKUNG
    # ===============================
    with st.expander("📋 Tabel Jumlah Debitur"):
        st.dataframe(
            df_debitur_agg[["Jenis", "Jumlah_Debitur"]]
            .style.format({"Jumlah_Debitur": "{:,.0f}"}),
            use_container_width=True
        )

#==========================================================================================================================
# ===============================
# FOOTER
# ===============================
st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; color:gray; font-size:13px;">
        © 2026 | Dashboard Gearing Ratio KUR & PEN<br>
        Developed with ❤️ using <b>Streamlit</b> & <b>Plotly</b>
    </div>
    """,
    unsafe_allow_html=True
)
