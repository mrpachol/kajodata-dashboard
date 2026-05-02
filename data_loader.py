import pandas as pd
import streamlit as st

from transforms import prepare_customer_base

@st.cache_data
def load_data():
    df = pd.read_excel("data/KDS Transactions.xlsx")
    df["Data transakcji"] = pd.to_datetime(df["Data transakcji"], errors="coerce")
    df["Kwota"] = pd.to_numeric(df["Kwota"], errors="coerce")
    df = df.dropna(subset=["Data transakcji", "Kwota", "Klient"]).copy()

    df["Rok"] = df["Data transakcji"].dt.year
    df["Miesiąc"] = df["Data transakcji"].dt.month
    df["Dzień"] = df["Data transakcji"].dt.day_name()
    df["Godzina"] = df["Data transakcji"].dt.hour
    df["rok_miesiąc"] = df["Data transakcji"].dt.to_period("M").dt.to_timestamp()

    return df.sort_values("Data transakcji").reset_index(drop=True)

@st.cache_data
def load_customer_data(df):
    return prepare_customer_base(df)