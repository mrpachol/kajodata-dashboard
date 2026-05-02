import numpy as np
import pandas as pd

from config import MONTH_MAP

def prepare_customer_base(df_full):
    customer_first = (
        df_full.sort_values("Data transakcji")
        .groupby("Klient", as_index=False)
        .first()[["Klient", "Data transakcji", "Kwota"]]
        .rename(columns={
            "Data transakcji": "pierwsza_data",
            "Kwota": "kwota_pierwszej_transakcji"
        })
    )

    customer_first["pierwszy_miesiąc"] = (
        customer_first["pierwsza_data"].dt.to_period("M").dt.to_timestamp()
    )

    q1 = customer_first["kwota_pierwszej_transakcji"].quantile(0.33)
    q2 = customer_first["kwota_pierwszej_transakcji"].quantile(0.66)

    customer_first["segment_cenowy"] = pd.cut(
        customer_first["kwota_pierwszej_transakcji"],
        bins=[-np.inf, q1, q2, np.inf],
        labels=["Niższa cena wejścia", "Cena standardowa", "Wyższa cena wejścia"]
    )

    df_customers = df_full.merge(
        customer_first[
            ["Klient", "pierwsza_data", "pierwszy_miesiąc", "kwota_pierwszej_transakcji", "segment_cenowy"]
        ],
        on="Klient",
        how="left"
    )

    df_customers["typ_klienta"] = np.where(
        df_customers["rok_miesiąc"] == df_customers["pierwszy_miesiąc"],
        "nowy",
        "powracający",
    )

    return df_customers

def filter_data_by_date_range(df, date_range):
    filtered = df.copy()

    if date_range is None:
        return filtered

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        filtered = filtered[
            (filtered["Data transakcji"] >= start_date) &
            (filtered["Data transakcji"] <= end_date)
        ]
    return filtered

def format_month_year_pl(ts):
    if pd.isna(ts):
        return ""
    return f"{MONTH_MAP.get(ts.month, ts.month)} {ts.year}"

def add_month_label_pl(df, date_col="rok_miesiąc", label_col="etykieta_miesiąca"):
    out = df.copy()
    out[label_col] = out[date_col].apply(format_month_year_pl)
    return out