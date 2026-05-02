import streamlit as st

from charts import build_pricing_ltv_chart, build_pricing_retention_chart, build_activity_heatmap
from formatters import format_pln
from transforms import filter_data_by_date_range
from components import render_date_range_selector


def render_pricing(df, df_customers_full):
    st.markdown("# 🏷️ Czy promocje zwiększają przychód?")
    st.markdown(
        "**Sprawdź, jak różne poziomy ceny wejścia wpływają na liczbę nowych klientów, retencję i wartość kohort.**"
    )

    min_date = df["Data transakcji"].min().date()
    max_date = df["Data transakcji"].max().date()

    date_range = render_date_range_selector(
        min_date=min_date,
        max_date=max_date,
        key_prefix="pricing",
        label="Własny zakres dat dla analizy cen",
    )

    if date_range is None:
        return

    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
        st.info("Wybierz pełny zakres dat: datę początkową i końcową.")
        return

    df_filt = filter_data_by_date_range(df_customers_full, date_range)

    if df_filt.empty:
        st.warning("Brak danych dla wybranego zakresu dat.")
        return

    customer_stats = (
        df_filt.groupby("Klient", as_index=False)
        .agg(
            liczba_transakcji=("Kwota", "size"),
            przychod_klienta=("Kwota", "sum"),
        )
    )

    customer_segments = (
        df_filt[
            ["Klient", "segment_cenowy", "kwota_pierwszej_transakcji"]
        ]
        .drop_duplicates(subset=["Klient"])
        .merge(customer_stats, on="Klient", how="left")
    )

    customer_segments["czy_powracajacy"] = customer_segments["liczba_transakcji"] > 1

    segment_summary = (
        customer_segments.groupby("segment_cenowy", as_index=False)
        .agg(
            liczba_klientow=("Klient", "nunique"),
            srednia_liczba_transakcji=("liczba_transakcji", "mean"),
            sredni_przychod_na_klienta=("przychod_klienta", "mean"),
            odsetek_powracajacych=("czy_powracajacy", "mean"),
            srednia_kwota_wejscia=("kwota_pierwszej_transakcji", "mean"),
        )
    )

    segment_summary["odsetek_powracajacych_pct"] = segment_summary["odsetek_powracajacych"] * 100

    seg_low = segment_summary.loc[segment_summary["segment_cenowy"] == "Niższa cena wejścia"]
    seg_std = segment_summary.loc[segment_summary["segment_cenowy"] == "Cena standardowa"]
    seg_high = segment_summary.loc[segment_summary["segment_cenowy"] == "Wyższa cena wejścia"]

    st.caption("KPI za wybrany okres (agregacja miesięczna).")

    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        if not seg_low.empty:
            st.metric(
                "Niższa cena wejścia",
                f"{int(seg_low['liczba_klientow'].iloc[0])} klientów",
                f"{seg_low['odsetek_powracajacych_pct'].iloc[0]:.1f}% powracających",
                border=True
            )

    with kpi2:
        if not seg_std.empty:
            st.metric(
                "Cena standardowa",
                f"{int(seg_std['liczba_klientow'].iloc[0])} klientów",
                f"{seg_std['odsetek_powracajacych_pct'].iloc[0]:.1f}% powracających",
                border=True
            )

    with kpi3:
        if not seg_high.empty:
            st.metric(
                "Wyższa cena wejścia",
                f"{int(seg_high['liczba_klientow'].iloc[0])} klientów",
                f"{seg_high['odsetek_powracajacych_pct'].iloc[0]:.1f}% powracających",
                border=True
            )

    wyk1, wyk2 = st.columns(2)

    with wyk1:
        st.plotly_chart(build_pricing_retention_chart(segment_summary), use_container_width=True)

    with wyk2:
        st.plotly_chart(build_pricing_ltv_chart(segment_summary), use_container_width=True)

    st.markdown("### Kluczowe obserwacje")

    best_ret = segment_summary.loc[segment_summary["odsetek_powracajacych_pct"].idxmax()]
    best_ltv = segment_summary.loc[segment_summary["sredni_przychod_na_klienta"].idxmax()]
    most_clients = segment_summary.loc[segment_summary["liczba_klientow"].idxmax()]

    st.write(
        f"- **Najwięcej klientów pozyskano w segmencie {most_clients['segment_cenowy']}:** "
        f"**{int(most_clients['liczba_klientow'])} klientów**, co pokazuje, że ten poziom ceny wejścia najlepiej wspiera akwizycję."
    )

    st.write(
        f"- **Najwyższy odsetek powracających klientów ma segment {best_ret['segment_cenowy']}:** "
        f"**{best_ret['odsetek_powracajacych_pct']:.1f}%**, co wskazuje na najwyższą skłonność do ponownych zakupów w tej grupie."
    )

    st.write(
        f"- **Najwyższy średni przychód na klienta generuje segment {best_ltv['segment_cenowy']}:** "
        f"**{format_pln(best_ltv['sredni_przychod_na_klienta'])}**, co oznacza najwyższą wartość klienta w tym wariancie cenowym."
    )

    if (
        most_clients["segment_cenowy"] == best_ret["segment_cenowy"]
        and most_clients["segment_cenowy"] != best_ltv["segment_cenowy"]
    ):
        st.write(
            f"- **Wniosek biznesowy:** segment **{most_clients['segment_cenowy']}** najlepiej łączy skalę pozyskania i skłonność klientów do powrotu, "
            f"natomiast segment **{best_ltv['segment_cenowy']}** lepiej maksymalizuje przychód na klienta. "
            "To wskazuje na kompromis między wzrostem wolumenowym a jakością przychodu."
        )
    elif (
        best_ret["segment_cenowy"] == best_ltv["segment_cenowy"]
        and best_ret["segment_cenowy"] != most_clients["segment_cenowy"]
    ):
        st.write(
            f"- **Wniosek biznesowy:** segment **{best_ret['segment_cenowy']}** daje najlepszą jakość klienta pod względem retencji i przychodu, "
            f"ale nie skaluje akwizycji tak mocno jak segment **{most_clients['segment_cenowy']}**."
        )
    elif best_ret["segment_cenowy"] == best_ltv["segment_cenowy"] == most_clients["segment_cenowy"]:
        st.write(
            f"- **Wniosek biznesowy:** segment **{best_ret['segment_cenowy']}** wygrywa jednocześnie pod względem skali, retencji i przychodu na klienta, "
            "co sugeruje, że jest obecnie najmocniejszym wariantem wejścia cenowego."
        )
    else:
        st.write(
            "- **Wniosek biznesowy:** różne segmenty cenowe wygrywają w różnych wymiarach, "
            "dlatego decyzja cenowa powinna zależeć od priorytetu biznesowego: wzrostu liczby klientów, retencji albo przychodu na klienta."
        )

    st.plotly_chart(build_activity_heatmap(df_filt), use_container_width=True)