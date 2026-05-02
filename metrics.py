import pandas as pd

def pct_change(current, previous):
    if current is None or previous in [None, 0] or pd.isna(previous):
        return None
    return ((current - previous) / previous) * 100

def abs_change(current, previous):
    if current is None or previous is None or pd.isna(previous):
        return None
    return current - previous

def compute_change(current, previous):
    if current is None or previous in [None, 0] or pd.isna(previous):
        return None, None
    abs_delta = current - previous
    pct_delta = (abs_delta / previous) * 100
    return abs_delta, pct_delta

def get_last_and_prev_month(df_filtered):
    if df_filtered.empty:
        return None, None
    months = sorted(df_filtered["rok_miesiąc"].dropna().unique())
    last_month = months[-1] if months else None
    prev_month = months[-2] if len(months) > 1 else None
    return last_month, prev_month

def get_best_and_worst_month(monthly_df, value_col):
    if monthly_df.empty or value_col not in monthly_df.columns:
        return None, None

    best_idx = monthly_df[value_col].idxmax()
    worst_idx = monthly_df[value_col].idxmin()

    return monthly_df.loc[best_idx], monthly_df.loc[worst_idx]

def compute_ytd_values(df_filtered):
    if df_filtered.empty:
        return None, None, None

    current_year = int(df_filtered["Rok"].max())
    current_month = int(df_filtered.loc[df_filtered["Rok"] == current_year, "Miesiąc"].max())
    prev_year = current_year - 1

    ytd_current = df_filtered[
        (df_filtered["Rok"] == current_year) &
        (df_filtered["Miesiąc"] <= current_month)
    ]["Kwota"].sum()

    ytd_prev = df_filtered[
        (df_filtered["Rok"] == prev_year) &
        (df_filtered["Miesiąc"] <= current_month)
    ]["Kwota"].sum()

    if ytd_prev == 0:
        return ytd_current, ytd_prev, None

    ytd_change = ((ytd_current - ytd_prev) / ytd_prev) * 100
    return ytd_current, ytd_prev, ytd_change