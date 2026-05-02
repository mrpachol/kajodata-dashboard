import streamlit as st

from config import PAGE_OPTIONS
from data_loader import load_data, load_customer_data
from components import render_global_styles, render_sidebar
from views.overview import render_overview
from views.pricing import render_pricing
from views.retention import render_retention

st.set_page_config(
    page_title="Konkurs Data Acolyte x KajoDataSpace",
    page_icon="data/tp_data_icon.png",
    layout="wide",
)

render_global_styles()

df = load_data()
df_customers_full = load_customer_data(df)

page = render_sidebar(PAGE_OPTIONS)

if page == "Przegląd":
    render_overview(df, df_customers_full)
elif page == "Wpływ zmian cen":
    render_pricing(df, df_customers_full)
elif page == "Retencja klientów":
    render_retention(df, df_customers_full)