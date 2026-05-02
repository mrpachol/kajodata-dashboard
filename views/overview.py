import pandas as pd
import streamlit as st

from charts import build_active_clients_chart, build_revenue_chart
from formatters import format_pln, format_delta_pct, format_pct_value
from components import render_date_range_selector
from metrics import (
    compute_change,
    get_last_and_prev_month,
    get_best_and_worst_month,
    compute_ytd_values,
)
from transforms import filter_data_by_date_range, add_month_label_pl, format_month_year_pl


def render_overview(df, df_customers_full):
    st.markdown("# 📊 Jak zmienia się liczba klientów?")
    st.markdown("**Przegląd sprzedaży kursów i subskrypcji KajoDataSpace.**")
    st.caption("Analiza obejmuje transakcje od listopada 2023 do marca 2026.")

    min_date = df["Data transakcji"].min().date()
    max_date = df["Data transakcji"].max().date()

    date_range = render_date_range_selector(
        min_date=min_date,
        max_date=max_date,
        key_prefix="overview",
        label="Własny zakres dat dla przeglądu",
    )

    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
        st.info("Wybierz pełny zakres dat: datę początkową i końcową.")
        return

    df_filt = filter_data_by_date_range(df_customers_full, date_range)
    if df_filt.empty:
        st.warning("Brak danych dla wybranego zakresu dat.")
        return

    last_month, prev_month = get_last_and_prev_month(df_filt)

    df_last = (
        df_filt[df_filt["rok_miesiąc"] == last_month].copy()
        if last_month is not None
        else pd.DataFrame()
    )
    df_prev = (
        df_filt[df_filt["rok_miesiąc"] == prev_month].copy()
        if prev_month is not None
        else pd.DataFrame()
    )

    nowi = df_last.loc[df_last["typ_klienta"] == "nowy", "Klient"].nunique()
    aktywni = df_last["Klient"].nunique()
    przychod = df_last["Kwota"].sum()

    prev_nowi = df_prev.loc[df_prev["typ_klienta"] == "nowy", "Klient"].nunique() if not df_prev.empty else None
    prev_aktywni = df_prev["Klient"].nunique() if not df_prev.empty else None
    prev_przychod = df_prev["Kwota"].sum() if not df_prev.empty else None

    delta_nowi_abs, delta_nowi_pct = compute_change(nowi, prev_nowi)
    delta_aktywni_abs, delta_aktywni_pct = compute_change(aktywni, prev_aktywni)
    delta_przychod_abs, delta_przychod_pct = compute_change(przychod, prev_przychod)

    ytd_current, ytd_prev, ytd_change = compute_ytd_values(df_filt)

    arpu = przychod / aktywni if aktywni > 0 else 0
    udzial_nowych = (nowi / aktywni * 100) if aktywni > 0 else 0

    st.caption("KPI za wybrany okres (agregacja miesięczna).")

    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        st.metric(
            "Nowi klienci",
            nowi,
            format_delta_pct(delta_nowi_pct),
            border=True,
        )

    with kpi2:
        st.metric(
            "Aktywni klienci",
            aktywni,
            format_delta_pct(delta_aktywni_pct),
            border=True,
        )

    with kpi3:
        st.metric(
            "Przychód",
            format_pln(przychod),
            format_delta_pct(delta_przychod_pct),
            border=True,
        )

    st.caption("Wskaźniki wspierające")

    kpi4, kpi5, kpi6 = st.columns(3)

    with kpi4:
        st.metric(
            "Przychód YTD",
            format_pln(ytd_current) if ytd_current is not None else "brak",
            format_pct_value(ytd_change) if ytd_change is not None else None,
            delta_color="normal",
            border=True,
        )

    with kpi5:
        st.metric("ARPU", format_pln(arpu), border=True)

    with kpi6:
        st.metric("Udział nowych klientów", f"{udzial_nowych:.1f}%", border=True)

    monthly_active = (
        df_filt.groupby("rok_miesiąc")["Klient"]
        .nunique()
        .reset_index(name="aktywni_klienci")
        .sort_values("rok_miesiąc")
    )
    monthly_active = add_month_label_pl(monthly_active, "rok_miesiąc", "etykieta_miesiąca")

    monthly_rev = (
        df_filt.groupby("rok_miesiąc")["Kwota"]
        .sum()
        .reset_index(name="przychod")
        .sort_values("rok_miesiąc")
    )
    monthly_rev = add_month_label_pl(monthly_rev, "rok_miesiąc", "etykieta_miesiąca")

    wyk1, wyk2 = st.columns(2)

    with wyk1:
        st.plotly_chart(build_active_clients_chart(monthly_active), use_container_width=True)

    with wyk2:
        st.plotly_chart(build_revenue_chart(monthly_rev), use_container_width=True)

    best_rev_month, worst_rev_month = get_best_and_worst_month(monthly_rev, "przychod")
    best_active_month, worst_active_month = get_best_and_worst_month(monthly_active, "aktywni_klienci")

    st.markdown("### Kluczowe obserwacje")

    if best_rev_month is not None and worst_rev_month is not None:
        st.write(
            f"- **Największy przychód:** {format_month_year_pl(best_rev_month['rok_miesiąc'])} "
            f"– **{format_pln(best_rev_month['przychod'])}**."
        )

    if best_active_month is not None and worst_active_month is not None:
        st.write(
            f"- **Najwięcej klientów:** {format_month_year_pl(best_active_month['rok_miesiąc'])} "
            f"– **{int(best_active_month['aktywni_klienci'])} klientów**."
        )

    if (
        delta_przychod_abs is not None
        and delta_aktywni_abs is not None
        and prev_przychod not in (None, 0)
        and prev_aktywni not in (None, 0)
    ):
        st.write(
            f"- **Trend m/m:** przychód zmienił się o {format_pln(delta_przychod_abs)} "
            f"({delta_przychod_pct:+.1f}%), a liczba aktywnych klientów o "
            f"{int(round(delta_aktywni_abs))} osób ({delta_aktywni_pct:+.1f}%)."
        )
    else:
        st.write("- **Trend m/m:** brak pełnych danych do porównania z poprzednim miesiącem.")

    if delta_przychod_abs is None or delta_aktywni_abs is None:
        st.info("- **Wniosek:** Za mało danych do pełnej oceny trendu miesiąc do miesiąca.")
    elif delta_przychod_abs > 0 and delta_aktywni_abs > 0:
        st.success("- **Wniosek:** Zdrowy wzrost obu metryk → strategia działa.")
    elif delta_przychod_abs < 0 and delta_aktywni_abs < 0:
        st.error("- **Wniosek:** Podwójny spadek → pilna analiza cen i retencji.")
    elif delta_przychod_abs > 0:
        st.info("- **Wniosek:** Przychód rośnie, ale klientów ubywa → sprawdź wpływ cen i churn.")
    else:
        st.warning("- **Wniosek:** Klientów przybywa, ale przychód spada → sprawdź promocje i ARPU.")