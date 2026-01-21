import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Dashboard Gearing Ratio KUR & PEN",
    layout="wide"
)

def bagian_1_proyeksi():
    import plotly.express as px
    import re
    
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
    st.title("📈 Summary Tend Gearing Ratio")
    
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
    
     # ===============================
    # FOOTER
    # ===============================
    st.markdown("---")
    
    st.markdown(
        """
        <div style="text-align:center; color:gray; font-size:13px;">
            © 2026 | PT.Askrindo<br>
            by @Rehanda Umamil Hadi & @Rani Rahmawati<br>
            Developed with ❤️ using <b>Streamlit</b> & <b>Plotly</b>
        </div>
        """,
        unsafe_allow_html=True
    )
    #====================================================================================================================================================================


def bagian_2_penjaminan():
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.title("📊 Dashboard Summary Outstanding Penjamin")
    
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
    # GET SHEET NAMES
    # ===============================
    if uploaded_file.name.endswith(".xlsx"):
        sheet_names = pd.ExcelFile(uploaded_file).sheet_names
    else:
        sheet_names = ["CSV"]
    
    # Skip sheet Proyeksi
    #sheet_names = [s for s in sheet_names if s.lower() != "proyeksi"]
    
    # ===============================
    # LOAD DATA
    # ===============================
    @st.cache_data(show_spinner=False)
    def load_data(file, sheet=None):
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_excel(file, sheet_name=sheet)
    
    # ===============================
    # PARSE VALUE (FORMAT INDONESIA)
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
    
    # ===============================
    # LOOP PER SHEET
    # ===============================
    for sheet in sheet_names:
    
        st.divider()
        st.header(f"📘 by {sheet}")
    
        df_raw = load_data(uploaded_file, sheet if sheet != "CSV" else None)
    
        if df_raw.empty:
            st.warning("Sheet kosong")
            continue
    
        # ===============================
        # VALIDASI STRUKTUR MINIMAL
        # ===============================
        cols = list(df_raw.columns)
    
        if len(cols) < 5:
            st.warning("Struktur kolom tidak memenuhi standar → dilewati")
            continue
    
        # ===============================
        # MAPPING BERDASARKAN POSISI KOLOM
        # ===============================
        COL_PERIODE = cols[0]
        COL_KURPEN = cols[1]
        COL_DIMENSI = cols[2]   # <<< KUNCI UTAMA
        COL_METRICS = "Metrics"
        COL_VALUE = "Value"
    
        dimensi_label = COL_DIMENSI  # Untuk UI
    
        df = df_raw.rename(columns={
            COL_PERIODE: "Periode",
            COL_KURPEN: "KUR/PEN",
            COL_DIMENSI: "Dimensi"
        })
    
        # ===============================
        # CLEAN VALUE
        # ===============================
        if "Value" in df.columns:
            df["Value"] = df["Value"].apply(parse_value)
        else:
            st.warning("Kolom Value tidak ditemukan")
            continue
    
        # ===============================
        # PREVIEW DATA
        # ===============================
        with st.expander("👀 Preview Data", expanded=False):
            df_prev = df.copy()
    
            if "Metrics" in df_prev.columns:
                def fmt(row):
                    if "debitur" in str(row["Metrics"]).lower():
                        return f"{row['Value']:,.0f}" if pd.notna(row["Value"]) else ""
                    return f"Rp {row['Value']:,.2f}" if pd.notna(row["Value"]) else ""
    
                df_prev["Value"] = df_prev.apply(fmt, axis=1)
    
            st.dataframe(df_prev, use_container_width=True)
    
        # ===============================
        # FILTER (STRUKTURAL)
        # ===============================
        c1, c2, c3 = st.columns(3)
    
        with c1:
            per = st.multiselect(
                "📅 Periode",
                sorted(df["Periode"].dropna().unique()),
                default=sorted(df["Periode"].dropna().unique()),
                key=f"per_{sheet}"
            )
    
        with c2:
            kp = st.multiselect(
                "🏦 KUR / PEN",
                sorted(df["KUR/PEN"].dropna().unique()),
                default=sorted(df["KUR/PEN"].dropna().unique()),
                key=f"kp_{sheet}"
            )
    
        with c3:
            dim = st.multiselect(
                f"🏷️ {dimensi_label}",
                sorted(df["Dimensi"].dropna().unique()),
                default=sorted(df["Dimensi"].dropna().unique()),
                key=f"dim_{sheet}"
            )
    
        df_f = df[
            df["Periode"].isin(per) &
            df["KUR/PEN"].isin(kp) &
            df["Dimensi"].isin(dim)
        ]
    
        if df_f.empty:
            st.warning("Data kosong setelah filter")
            continue
    #=============================================================================
        # ===============================
        # KHUSUS SHEET PROYEKSI
        # OS GROSS & OS NET + FILTER TENOR
        # ===============================
        if sheet.lower() == "proyeksi":
        
            # ===============================
            # AMBIL KOLOM TENOR (KOLOM KE-4)
            # ===============================
            TENOR_COL = df_raw.columns[3]
            df_f["Tenor"] = df_raw[TENOR_COL]
        
            # ===============================
            # FILTER TENOR (UI)
            # ===============================
            tenor_list = sorted(df_f["Tenor"].dropna().unique())
        
            selected_tenor = st.multiselect(
                "⏳ Pilih Tenor",
                tenor_list,
                default=tenor_list,
                key="tenor_proyeksi"
            )
        
            df_f = df_f[df_f["Tenor"].isin(selected_tenor)]
        
            if df_f.empty:
                st.warning("Data kosong setelah filter Tenor")
                continue
        
            col_dim = "Dimensi"
            col_per = "Periode"
            col_val = "Value"
        
            # ===============================
            # OS GROSS
            # ===============================
            # st.markdown("### 🔹 OS Gross")
        
            df_gross = df_f[
                df_f[col_dim].str.lower() == "os gross"
            ].dropna(subset=[col_val])
        
            if df_gross.empty:
                st.warning("Data OS Gross tidak tersedia")
            else:
                df_gross_agg = (
                    df_gross
                    .groupby(col_per, as_index=False)
                    .agg(Total_Value=(col_val, "sum"))
                )
        
                fig_gross = px.bar(
                    df_gross_agg,
                    x=col_per,
                    y="Total_Value",
                    text="Total_Value",
                    title="📊 Proyeksi OS Gross"
                )
        
                fig_gross.update_traces(
                    texttemplate="%{text:,.0f}",
                    textposition="outside"
                )
        
                fig_gross.update_layout(
                    yaxis_title="Nilai (Rp)",
                    height=450
                )
        
                st.plotly_chart(fig_gross, use_container_width=True)
        
            # ===============================
            # OS NETT
            # ===============================
            # st.markdown("### 🔹 OS Nett")
        
            df_net = df_f[
                df_f[col_dim].str.lower() == "os nett"
            ].dropna(subset=[col_val])
        
            if df_net.empty:
                st.warning("Data OS Nett tidak tersedia")
            else:
                df_net_agg = (
                    df_net
                    .groupby(col_per, as_index=False)
                    .agg(Total_Value=(col_val, "sum"))
                )
        
                fig_net = px.bar(
                    df_net_agg,
                    x=col_per,
                    y="Total_Value",
                    text="Total_Value",
                    title="📊 Proyeksi OS Nett"
                )
        
                fig_net.update_traces(
                    texttemplate="%{text:,.0f}",
                    textposition="outside"
                )
        
                fig_net.update_layout(
                    yaxis_title="Nilai (Rp)",
                    height=450
                )
        
                st.plotly_chart(fig_net, use_container_width=True)
        
            continue  # ⬅️ PENTING
    
        # ===============================
        # KHUSUS SHEET TENOR
        # PLOT VALUE vs TENOR
        # ===============================
        if sheet.lower() == "tenor":   
            # Pastikan tenor numerik & urut
            df_tenor = df_f.copy()
            df_tenor["Dimensi"] = pd.to_numeric(df_tenor["Dimensi"], errors="coerce")
        
            df_tenor = df_tenor.dropna(subset=["Dimensi", "Value"])
        
            # Agregasi per tenor
            df_tenor_agg = (
                df_tenor
                .groupby("Dimensi", as_index=False)
                .agg(Total_Value=("Value", "sum"))
                .sort_values("Dimensi")
            )
        
            fig_tenor = px.bar(
                df_tenor_agg,
                x="Dimensi",
                y="Total_Value",
                text="Total_Value",
                labels={
                    "Dimensi": "Tenor (Tahun)",
                    "Total_Value": "Nilai"
                }
            )
        
            fig_tenor.update_traces(
                texttemplate="%{text:,.2f}",
                textposition="outside"
            )
        
            fig_tenor.update_layout(
                xaxis=dict(
                    tickmode="linear",
                    tick0=1,
                    dtick=1
                ),
                yaxis_title="Nilai (Rupiah)",
                title="📊 Total Nilai per Tenor",
                height=450
            )
        
            st.plotly_chart(fig_tenor, use_container_width=True)
    
        #-------------------------------------------------------------------------------------------
        # ===============================
        # KHUSUS SHEET JENIS POLIS
        # PLOT VALUE vs JENIS POLIS
        # ===============================
        if sheet.lower() == "jenis polis":    
            df_polis = df_f.copy()
            # Pastikan data valid
            df_polis = df_polis.dropna(subset=["Dimensi", "Value"])
            # Agregasi per Jenis Polis (SPR, NEW, dll)
            df_polis_agg = (
                df_polis
                .groupby("Dimensi", as_index=False)
                .agg(Total_Value=("Value", "sum"))
                .sort_values("Dimensi")
            )
        
            fig_polis = px.bar(
                df_polis_agg,
                x="Dimensi",
                y="Total_Value",
                text="Total_Value",
                labels={
                    "Dimensi": "Jenis Polis",
                    "Total_Value": "Nilai"
                }
            )
        
            fig_polis.update_traces(
                texttemplate="%{text:,.2f}",
                textposition="outside"
            )
        
            fig_polis.update_layout(
                xaxis_title="Jenis Polis",
                yaxis_title="Nilai (Rupiah)",
                title="📊 Total Nilai berdasarkan Jenis Polis",
                height=450
            )
        
            st.plotly_chart(fig_polis, use_container_width=True)
    
        # ===============================
        # KHUSUS SHEET JENIS KREDIT (KUR)
        # PLOT VALUE vs JENIS KREDIT
        # ===============================
        if "jenis kredit" in sheet.lower():    
            df_kredit = df_f.copy()
        
            # Pastikan data valid
            df_kredit = df_kredit.dropna(subset=["Dimensi", "Value"])
        
            if df_kredit.empty:
                st.warning("Data Jenis Kredit kosong setelah filter")
            else:
                # Agregasi per Jenis Kredit
                df_kredit_agg = (
                    df_kredit
                    .groupby("Dimensi", as_index=False)
                    .agg(Total_Value=("Value", "sum"))
                    .sort_values("Dimensi")
                )
        
                fig_kredit = px.bar(
                    df_kredit_agg,
                    x="Dimensi",
                    y="Total_Value",
                    text="Total_Value",
                    labels={
                        "Dimensi": "Jenis Kredit (KUR)",
                        "Total_Value": "Nilai"
                    }
                )
        
                fig_kredit.update_traces(
                    texttemplate="%{text:,.2f}",
                    textposition="outside"
                )
        
                fig_kredit.update_layout(
                    xaxis_title="Jenis Kredit (KUR)",
                    yaxis_title="Nilai (Rupiah)",
                    title="📊 Total Nilai berdasarkan Jenis Kredit KUR",
                    height=450
                )
        
                st.plotly_chart(fig_kredit, use_container_width=True)
    
        # ===============================
        # KHUSUS SHEET BANK
        # PLOT VALUE vs BANK
        # ===============================
        if "bank" in sheet.lower():    
            df_bank = df_f.copy()
        
            # Pastikan data valid
            df_bank = df_bank.dropna(subset=["Dimensi", "Value"])
        
            if df_bank.empty:
                st.warning("Data Jenis Kredit kosong setelah filter")
            else:
                # Agregasi per Jenis Kredit
                df_bank_agg = (
                    df_bank
                    .groupby("Dimensi", as_index=False)
                    .agg(Total_Value=("Value", "sum"))
                    .sort_values("Dimensi")
                )
        
                fig_bank = px.bar(
                    df_bank_agg,
                    x="Dimensi",
                    y="Total_Value",
                    text="Total_Value",
                    labels={
                        "Dimensi": "Bank",
                        "Total_Value": "Nilai"
                    }
                )
        
                fig_bank.update_traces(
                    texttemplate="%{text:,.2f}",
                    textposition="outside"
                )
        
                fig_bank.update_layout(
                    xaxis_title="Bank",
                    yaxis_title="Nilai (Rupiah)",
                    title="📊 Total Nilai berdasarkan BANK",
                    height=450
                )
        
                st.plotly_chart(fig_bank, use_container_width=True) 
    
        # ===============================
        # KHUSUS SHEET KOTA
        # PLOT VALUE vs KOTA
        # ===============================
        sheet_norm = sheet.lower().strip()
        
        if "kota" in sheet_norm:    
            df_kota = df_f.copy()
        
            # Bersihkan kolom Dimensi (Kota)
            df_kota["Dimensi"] = df_kota["Dimensi"].astype(str).str.strip()
        
            df_kota = df_kota[
                (df_kota["Dimensi"] != "") &
                (df_kota["Dimensi"].str.lower() != "nan")
            ]
        
            df_kota = df_kota.dropna(subset=["Value"])
        
            if df_kota.empty:
                st.warning("⚠️ Data Kota kosong setelah filter")
            else:
                # Agregasi per Kota
                df_kota_agg = (
                    df_kota
                    .groupby("Dimensi", as_index=False)
                    .agg(Total_Value=("Value", "sum"))
                    .sort_values("Total_Value", ascending=False)
                )
        
                fig_kota = px.bar(
                    df_kota_agg,
                    x="Dimensi",
                    y="Total_Value",
                    text="Total_Value",
                    labels={
                        "Dimensi": "Kota",
                        "Total_Value": "Nilai"
                    }
                )
        
                fig_kota.update_traces(
                    texttemplate="%{text:,.2f}",
                    textposition="outside"
                )
        
                fig_kota.update_layout(
                    xaxis_title="Kota",
                    yaxis_title="Nilai (Rupiah)",
                    title="📊 Total Nilai berdasarkan Kota",
                    height=500
                )
        
                st.plotly_chart(fig_kota, use_container_width=True)
    
        
    
        # ===============================
        # AGREGASI METRICS
        # ===============================
        df_agg = (
            df_f.groupby("Metrics", as_index=False)
            .agg(Total_Value=("Value", "sum"))
        )
    
        df_agg["Total_T"] = df_agg["Total_Value"] / 1_000_000_000_000
    
        # ===============================
        # GRAFIK BATANG (TRILIUN)
        # ===============================
        fig = px.bar(
            df_agg,
            x="Metrics",
            y="Total_T",
            text="Total_T",
            title=f"📊 Summary Metrics berdasarkan {dimensi_label}"
        )
    
        fig.update_traces(
            texttemplate="%{text:,.2f} T",
            textposition="outside"
        )
    
        fig.update_layout(
            yaxis_title="Nilai Finansial (Triliun)",
            xaxis_title="Metrics"
        )
    
        st.plotly_chart(fig, use_container_width=True)
    
        # ===============================
        # GRAFIK DUAL AXIS (FOKUS DEBITUR)
        # ===============================
        df_agg["Jenis"] = df_agg["Metrics"].apply(
            lambda x: "Debitur" if "debitur" in str(x).lower() else "Finansial"
        )
    
        df_agg["Value_T"] = df_agg.apply(
            lambda r: r["Total_T"] if r["Jenis"] == "Finansial" else None,
            axis=1
        )
    
        df_agg["Value_Debitur"] = df_agg.apply(
            lambda r: r["Total_Value"] if r["Jenis"] == "Debitur" else None,
            axis=1
        )
    
        fig2 = go.Figure()
    
        fig2.add_bar(
            x=df_agg["Metrics"],
            y=df_agg["Value_T"],
            name="Nilai Finansial (Triliun)",
            yaxis="y"
        )
    
        fig2.add_bar(
            x=df_agg["Metrics"],
            y=df_agg["Value_Debitur"],
            name="Jumlah Debitur",
            yaxis="y2"
        )
    
        fig2.update_layout(
            title=f"📊 Metrics vs Jumlah Debitur berdasarkan {dimensi_label}",
            barmode="group",
            yaxis=dict(title="Triliun Rupiah"),
            yaxis2=dict(
                title="Jumlah Debitur",
                overlaying="y",
                side="right"
            )
        )
    
        st.plotly_chart(fig2, use_container_width=True)
    
    
    #==========================================================================================================================
    # ===============================
    # FOOTER
    # ===============================
    st.markdown("---")
    
    st.markdown(
        """
        <div style="text-align:center; color:gray; font-size:13px;">
            © 2026 | PT.Askrindo<br>
            by @Rehanda Umamil Hadi & @Rani Rahmawati<br>
            Developed with ❤️ using <b>Streamlit</b> & <b>Plotly</b>
        </div>
        """,
        unsafe_allow_html=True
    )

st.set_page_config(
    page_title="Dashboard Gearing Ratio & Penjaminan",
    layout="wide"
)

st.sidebar.title("📌 Menu Utama")

menu = st.sidebar.radio(
    "Pilih Analisis",
    [
        "📈 Gearing Ratio",
        "📊 Outstanding Penjaminan"
    ]
)

if menu == "📈 Gearing Ratio":
    bagian_1_proyeksi()

elif menu == "📊 Outstanding Penjaminan":
    bagian_2_penjaminan()

# menu = st.radio(
#     "📌 Pilih Perhitungan",
#     [
#         "Bagian 1 – Proyeksi & Gearing Ratio",
#         "Bagian 2 – Outstanding Penjaminan"
#     ]
# )

# st.divider()

# if menu == "Bagian 1 – Proyeksi & Gearing Ratio":
#     bagian_1_proyeksi()

# elif menu == "Bagian 2 – Outstanding Penjaminan":
#     bagian_2_penjaminan()
