import pandas as pd

def format_pln(value, decimals=0):
    if pd.isna(value):
        value = 0
    if decimals == 0:
        return f"PLN {value:,.0f}".replace(",", " ")
    return f"PLN {value:,.2f}".replace(",", " ").replace(".", ",")

def format_delta_pct(value):
    if value is None or pd.isna(value):
        return "brak porównania"
    return f"{value:+.1f}% vs poprzedni miesiąc"

def format_pct_value(value):
    if value is None or pd.isna(value):
        return "brak"
    return f"{value:+.1f}%"