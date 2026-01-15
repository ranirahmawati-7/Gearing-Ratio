import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ===============================
# CONFIG (WAJIB PALING ATAS)
# ===============================
st.set_page_config(
    page_title="Dashboard KUR & PEN",
    layout="wide"
)

# ===============================
# CSS PEMBEDA HEADER & FOOTER
# ===============================
st.markdown(
    """
    <style>
    .header-box {
        background-color: #f5f7fa;
        padding: 15px 20px;
        border-bottom: 3px solid #1f4e79;
        margin-bottom: 20px;
    }
    .footer-box {
        background-color: #f5f7fa;
        padding: 12px;
        border-top: 3px solid #1f4e79;
        margin-top: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ===============================
# HEADER (VISUAL "FROZEN")
# ===============================
st.markdown('<div class="header-box">', unsafe_allow_html=True)

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

st.markdown("</div>", unsafe_allow_html=True)

# ===============================
# INFO & CONTOH FILE
# ===============================
st.info(
    "Website ini akan otomatis menampilkan dashboard untuk perhitungan Trend Gearing Ratio "
    "setelah anda mengupload file dengan format xlxs atau csv, "
    "dan pastikan format tabel yang akan diinput sesuai dengan contoh"
)

st.image(
    "gambar/ssXlsx.png",
    caption="Contoh format file Excel (.xlsx) yang didukung",
    use_container_width=True
)

st.title("📊 Summary Trend Gearing Ratio")

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
# FLAG AUDITED
# ===============================
df["Is_Audited"] = df["Periode_Raw"].str.contains(
    "audit", case=False, na=False
).astype(int)

# ===============================
# CLEAN VALUE
# ===============================
def parse_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)

    text = str(val).strip()
    if "." in text and "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text:
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

available_years = sorted(df_f["Year"].unique())
selected_years = st.sidebar.multiselect(
    "Tahun",
    available_years,
    default=available_years
)

df_f = df_f[df_f["Year"].isin(selected_years)]

df_f["Bulan_Nama"] = df_f["Month"].map(bulan_id)

selected_months = st.sidebar.multiselect(
    "Bulan",
    list(bulan_id.values()),
    default=list(bulan_id.values())
)

df_f = df_f[df_f["Bulan_Nama"].isin(selected_months)]

# ===============================
# PREVIEW DATA
# ===============================
st.subheader("👀 Preview Data")
st.dataframe(
    df_f.style.format({"Value": "Rp {:,.2f}"}),
    use_container_width=True
)

# ===============================
# (SEMUA BAGIAN PERHITUNGAN KAMU)
# ⛔ TIDAK DIUBAH SAMA SEKALI
# ===============================
# ... ISI TETAP SAMA PERSIS DENGAN SCRIPT YANG KAMU KIRIM ...
# (OS KUR, Ekuitas, OS KUR & PEN, Gearing Ratio, dst)
# ===============================

# ===============================
# FOOTER (VISUAL TERPISAH)
# ===============================
st.markdown('<div class="footer-box">', unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align:center; color:gray; font-size:13px;">
        © 2026 | Dashboard Gearing Ratio KUR & PEN<br>
        Developed with ❤️ using <b>Streamlit</b> & <b>Plotly</b>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)
