import numpy as np
import pandas as pd
import streamlit as st

from config import MONTH_MAP
from charts import build_cohort_heatmap, build_repeat_rate_chart
from transforms import filter_data_by_date_range, add_month_label_pl
from components import render_date_range_selector


def render_retention(df, df_customers_full):
    st.markdown("# 🔁 Jaki jest wskaźnik retencji?")
    st.markdown(
        "**Przeanalizuj retencję kohort, tempo odpływu klientów i momenty największego ryzyka churnu.**"
    )
    st.caption(
        "Analiza retencji klientów KajoDataSpace z naciskiem na drugi i trzeci miesiąc od pierwszego zakupu."
    )

    min_date = df["Data transakcji"].min().date()
    max_date = df["Data transakcji"].max().date()

    date_range = render_date_range_selector(
        min_date=min_date,
        max_date=max_date,
        key_prefix="retention",
        label="Własny zakres dat dla retencji",
    )

    if date_range is None:
        return

    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
        st.info("Wybierz datę początkową i końcową albo kliknij „Pełny zakres”.")
        return

    df_filt = filter_data_by_date_range(df_customers_full, date_range)

    if df_filt.empty:
        st.warning("Brak danych dla wybranego zakresu dat.")
        return

    customers_tx = (
        df_filt.groupby("Klient", as_index=False)
        .agg(
            liczba_transakcji=("Kwota", "size"),
            pierwsza_data=("Data transakcji", "min"),
            ostatnia_data=("Data transakcji", "max")
        )
    )

    customers_tx["czy_powracajacy"] = customers_tx["liczba_transakcji"] > 1
    repeat_rate = customers_tx["czy_powracajacy"].mean() * 100 if not customers_tx.empty else 0
    avg_tx = customers_tx["liczba_transakcji"].mean() if not customers_tx.empty else 0

    customers_tx["dni_aktywnosci"] = (
        customers_tx["ostatnia_data"] - customers_tx["pierwsza_data"]
    ).dt.days

    avg_days_active = customers_tx.loc[
        customers_tx["czy_powracajacy"], "dni_aktywnosci"
    ].mean()

    second_purchase_rate = (
        (customers_tx["liczba_transakcji"] >= 2).mean() * 100 if not customers_tx.empty else 0
    )

    st.caption("KPI dla wybranego zakresu dat, liczone na poziomie klienta.")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("Repeat rate", f"{repeat_rate:.1f}%", border=True)

    with kpi2:
        st.metric("Śr. liczba transakcji / klient", f"{avg_tx:.2f}", border=True)

    with kpi3:
        st.metric(
            "Śr. czas aktywności",
            f"{avg_days_active:.0f} dni" if pd.notna(avg_days_active) else "brak",
            border=True
        )

    with kpi4:
        st.metric("Klienci z min. 2 zakupami", f"{second_purchase_rate:.1f}%", border=True)

    cohort_df = df_filt.copy()
    cohort_df["cohort_month"] = cohort_df["pierwszy_miesiąc"]

    cohort_df["cohort_index"] = (
        (cohort_df["rok_miesiąc"].dt.year - cohort_df["cohort_month"].dt.year) * 12 +
        (cohort_df["rok_miesiąc"].dt.month - cohort_df["cohort_month"].dt.month) + 1
    )

    cohort_counts = (
        cohort_df.groupby(["cohort_month", "cohort_index"])["Klient"]
        .nunique()
        .reset_index()
        .pivot(index="cohort_month", columns="cohort_index", values="Klient")
        .sort_index()
    )

    if cohort_counts.empty:
        st.warning("Brak wystarczających danych do analizy kohortowej.")
        return

    cohort_sizes = cohort_counts.iloc[:, 0]
    MIN_COHORT_SIZE = 10

    valid_cohorts = cohort_sizes[cohort_sizes >= MIN_COHORT_SIZE].index
    cohort_counts = cohort_counts.loc[valid_cohorts]
    cohort_sizes = cohort_sizes.loc[valid_cohorts]

    if cohort_counts.empty:
        st.warning(
            f"Brak kohort o minimalnej liczebności {MIN_COHORT_SIZE} klientów. "
            "Poszerz zakres dat lub zmniejsz próg minimalny."
        )
        return

    retention_matrix = cohort_counts.divide(cohort_sizes, axis=0) * 100
    retention_matrix = retention_matrix.round(1)

    retention_matrix_display = retention_matrix.copy()
    retention_matrix_display.index = retention_matrix_display.index.map(
        lambda x: f"{MONTH_MAP.get(x.month, x.month)} {x.year}"
    )

    monthly_total = (
        df_filt.groupby("rok_miesiąc")["Klient"]
        .nunique()
        .reset_index(name="wszyscy_klienci")
    )

    monthly_returning = (
        df_filt[df_filt["typ_klienta"] == "powracający"]
        .groupby("rok_miesiąc")["Klient"]
        .nunique()
        .reset_index(name="powracajacy_klienci")
    )

    monthly_ret = monthly_total.merge(monthly_returning, on="rok_miesiąc", how="left").fillna(0)
    monthly_ret["repeat_rate_pct"] = (
        monthly_ret["powracajacy_klienci"] / monthly_ret["wszyscy_klienci"] * 100
    )
    monthly_ret = add_month_label_pl(monthly_ret, "rok_miesiąc", "etykieta_miesiąca")

    wyk1, wyk2 = st.columns(2)

    with wyk1:
        st.plotly_chart(build_repeat_rate_chart(monthly_ret), use_container_width=True)

    with wyk2:
        st.plotly_chart(build_cohort_heatmap(retention_matrix_display), use_container_width=True)

    st.markdown("### Kluczowe obserwacje")
    st.caption(
        f"Obserwacje oparto na kohortach o liczebności co najmniej {MIN_COHORT_SIZE} klientów. "
        "Wnioski koncentrują się na dojrzałych kohortach, aby ograniczyć wpływ skrajnych wartości i niepełnych okresów obserwacji."
    )

    avg_m2 = retention_matrix[2].mean() if 2 in retention_matrix.columns else np.nan
    avg_m3 = retention_matrix[3].mean() if 3 in retention_matrix.columns else np.nan
    avg_m4 = retention_matrix[4].mean() if 4 in retention_matrix.columns else np.nan

    if pd.notna(avg_m2):
        st.write(
            f"- **Największy odpływ następuje po pierwszym zakupie:** średnia retencja w 2. miesiącu wynosi "
            f"**{avg_m2:.1f}%**, co oznacza, że około **{100 - avg_m2:.1f}%** klientów nie wraca po pierwszej transakcji."
        )

    if pd.notna(avg_m2) and pd.notna(avg_m3):
        delta_2_3 = avg_m3 - avg_m2
        st.write(
            f"- **Odpływ wyraźnie zwalnia po drugim miesiącu:** średnia retencja w 3. miesiącu wynosi "
            f"**{avg_m3:.1f}%**, czyli zmienia się o **{delta_2_3:.1f} p.p.** względem 2. miesiąca."
        )

    if pd.notna(avg_m3) and pd.notna(avg_m4):
        delta_3_4 = avg_m4 - avg_m3
        if delta_3_4 > -5:
            st.write(
                f"- **Kolejne miesiące są stabilniejsze:** zmiana między 3. a 4. miesiącem wynosi "
                f"**{delta_3_4:.1f} p.p.**, co sugeruje bardziej stabilne zachowanie klientów po drugim zakupie."
            )

    if pd.notna(avg_m2):
        st.write(
            "- **Największy potencjał poprawy retencji leży między 1. a 2. zakupem:** "
            "to właśnie ten etap powinien być priorytetem dla działań onboardingowych, follow-upu i ofert kontynuacyjnych."
        )