import streamlit as st
import pandas as pd
import plotly.express as px

# TAMBAHKAN INI
import matplotlib.pyplot as plt
import calendar
import re


# ===============================
# LOAD DATA
# ===============================
# contoh:
# df = pd.read_excel("data.xlsx")
# pastikan kolom:
# - "Periode"
# - "Nilai" (atau ganti sesuai nama kolommu)

nilai_kolom = "Nilai"   # GANTI jika nama kolom berbeda

# ===============================
# SIMPAN PERIODE ASLI
# ===============================
df["Periode_Raw"] = df["Periode"]

# coba parse datetime (tidak merusak string)
df["Periode_DT"] = pd.to_datetime(df["Periode"], errors="coerce")

# label asli (untuk fallback)
df["Periode_Label"] = df["Periode_Raw"].astype(str)

# ===============================
# MAP BULAN (STRING)
# ===============================
bulan_map = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "okt": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# ===============================
# FUNGSI EKSTRAK BULAN & TAHUN
# ===============================
def extract_month_year(raw, dt):
    # kalau datetime valid
    if pd.notna(dt):
        return dt.month, dt.year

    if pd.isna(raw):
        return None, None

    text = str(raw).lower()

    month = None
    for k, v in bulan_map.items():
        if k in text:
            month = v
            break

    year = None
    m = re.search(r"(20\d{2}|\d{2})", text)
    if m:
        y = int(m.group())
        year = 2000 + y if y < 100 else y

    return month, year

# ===============================
# TERAPKAN EKSTRAKSI
# ===============================
df[["Month", "Year"]] = df.apply(
    lambda r: pd.Series(extract_month_year(r["Periode_Raw"], r["Periode_DT"])),
    axis=1
)

# ===============================
# SORT KEY (UNTUK URUTAN)
# ===============================
df["SortKey"] = df["Year"] * 100 + df["Month"]

# ===============================
# LABEL SUMBU X (BULAN + TAHUN)
# ===============================
df["X_Label"] = df.apply(
    lambda r: f"{calendar.month_abbr[int(r['Month'])]} {int(r['Year'])}"
    if pd.notna(r["Month"]) and pd.notna(r["Year"])
    else r["Periode_Label"],
    axis=1
)

# ===============================
# GROUP & SORT
# ===============================
df_group = (
    df.groupby(["SortKey", "X_Label"], as_index=False)[nilai_kolom]
      .sum()
      .sort_values("SortKey")
)

# ===============================
# PLOT
# ===============================
plt.figure(figsize=(10, 5))

plt.plot(
    df_group["X_Label"],
    df_group[nilai_kolom],
    marker="o"
)

plt.xlabel("Periode")
plt.ylabel(nilai_kolom)
plt.title("Total Nilai per Periode")
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
