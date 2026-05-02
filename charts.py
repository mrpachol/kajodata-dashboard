import pandas as pd
import plotly.express as px

from config import COLORS


def plotly_dark_layout(fig, title, yaxis_title, xaxis_title):
    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"], size=14),
        title=dict(
            text=title,
            font=dict(size=20, color=COLORS["text"]),
            x=0.0,
            xanchor="left",
        ),
        margin=dict(t=90, l=60, r=20, b=60),
        xaxis=dict(
            title=xaxis_title,
            title_font=dict(color=COLORS["text"], size=14),
            tickfont=dict(color=COLORS["muted"], size=11),
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            linecolor=COLORS["axis"],
        ),
        yaxis=dict(
            title=yaxis_title,
            title_font=dict(color=COLORS["text"], size=14),
            tickfont=dict(color=COLORS["muted"], size=12),
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            linecolor=COLORS["axis"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(color=COLORS["text"]),
        ),
        legend_title_text="",
    )
    return fig


# =========================
# OVERVIEW
# =========================

def build_active_clients_chart(monthly_active):
    fig = px.line(
        monthly_active,
        x="etykieta_miesiąca",
        y="aktywni_klienci",
        markers=True,
        title="Aktywni klienci miesiąc do miesiąca",
        color_discrete_sequence=[COLORS["aktywni"]],
    )
    fig.update_traces(
        line=dict(width=3, color=COLORS["aktywni"]),
        marker=dict(size=7, color=COLORS["aktywni"])
    )
    return plotly_dark_layout(
        fig,
        "Aktywni klienci miesiąc do miesiąca",
        "Liczba klientów",
        "Miesiąc",
    )


def build_revenue_chart(monthly_rev):
    fig = px.bar(
        monthly_rev,
        x="etykieta_miesiąca",
        y="przychod",
        title="Przychód miesiąc do miesiąca",
        color_discrete_sequence=[COLORS["przychod"]],
    )
    fig.update_traces(
        marker_color=COLORS["przychod"],
        marker_line_color=COLORS["primary"],
        marker_line_width=0.6,
        opacity=0.9
    )
    return plotly_dark_layout(
        fig,
        "Przychód miesiąc do miesiąca",
        "Przychód [PLN]",
        "Miesiąc",
    )


def build_activity_heatmap(df_filt):
    dni_map = {
        "Monday": "Pon",
        "Tuesday": "Wt",
        "Wednesday": "Śr",
        "Thursday": "Czw",
        "Friday": "Pt",
        "Saturday": "Sob",
        "Sunday": "Nd"
    }
    kolejnosc_dni = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]

    df_heat = df_filt.dropna(subset=["Data transakcji", "Klient"]).copy()
    df_heat["Godzina"] = df_heat["Data transakcji"].dt.hour
    df_heat["Dzień_tyg"] = df_heat["Data transakcji"].dt.day_name().map(dni_map)
    df_heat["Dzień_tyg"] = pd.Categorical(
        df_heat["Dzień_tyg"],
        categories=kolejnosc_dni,
        ordered=True
    )

    heatmap_df = (
        df_heat.groupby(["Dzień_tyg", "Godzina"])["Klient"]
        .nunique()
        .reset_index(name="Unikalni_klienci")
    )

    heatmap_matrix = (
        heatmap_df.pivot(
            index="Dzień_tyg",
            columns="Godzina",
            values="Unikalni_klienci"
        )
        .fillna(0)
        .reindex(index=kolejnosc_dni, columns=range(24), fill_value=0)
    )

    fig = px.imshow(
        heatmap_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="YlOrRd",
        labels=dict(x="Godzina", y="Dzień tygodnia", color="Unikalni klienci"),
        title="Heatmapa aktywności klientów: dzień tygodnia × godzina"
    )

    fig.update_layout(
        xaxis_title="Godzina",
        yaxis_title="Dzień tygodnia",
        coloraxis_colorbar_title="Unikalni klienci",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    fig.update_xaxes(side="bottom")
    return fig


# =========================
# PRICING
# =========================

def build_pricing_retention_chart(segment_summary):
    fig = px.bar(
        segment_summary,
        x="segment_cenowy",
        y="odsetek_powracajacych_pct",
        title="Odsetek klientów powracających wg ceny wejścia",
        color="segment_cenowy",
        color_discrete_map={
            "Niższa cena wejścia": COLORS["akcent"],
            "Cena standardowa": COLORS["aktywni"],
            "Wyższa cena wejścia": COLORS["przychod"],
        }
    )
    return plotly_dark_layout(
        fig,
        "Odsetek klientów powracających wg ceny wejścia",
        "Powracający klienci [%]",
        "Segment cenowy",
    )


def build_pricing_ltv_chart(segment_summary):
    fig = px.bar(
        segment_summary,
        x="segment_cenowy",
        y="sredni_przychod_na_klienta",
        title="Średni przychód na klienta wg ceny wejścia",
        color="segment_cenowy",
        color_discrete_map={
            "Niższa cena wejścia": COLORS["akcent"],
            "Cena standardowa": COLORS["aktywni"],
            "Wyższa cena wejścia": COLORS["przychod"],
        }
    )
    return plotly_dark_layout(
        fig,
        "Średni przychód na klienta wg ceny wejścia",
        "Przychód na klienta [PLN]",
        "Segment cenowy",
    )


# =========================
# RETENTION
# =========================

def build_repeat_rate_chart(monthly_ret):
    fig = px.line(
        monthly_ret,
        x="etykieta_miesiąca",
        y="repeat_rate_pct",
        markers=True,
        title="Repeat rate miesiąc do miesiąca",
        color_discrete_sequence=[COLORS["aktywni"]],
    )
    fig.update_traces(
        line=dict(width=3, color=COLORS["aktywni"]),
        marker=dict(size=7, color=COLORS["aktywni"])
    )
    return plotly_dark_layout(
        fig,
        "Repeat rate miesiąc do miesiąca",
        "Repeat rate [%]",
        "Miesiąc",
    )


def build_cohort_heatmap(retention_matrix_display):
    fig = px.imshow(
        retention_matrix_display,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Macierz retencji kohortowej [%]"
    )
    fig.update_layout(
        xaxis_title="Miesiące od pierwszego zakupu",
        yaxis_title="Kohorta"
    )
    return plotly_dark_layout(
        fig,
        "Macierz retencji kohortowej",
        "Kohorta",
        "Miesiące od zakupu"
    )