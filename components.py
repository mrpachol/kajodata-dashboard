from datetime import date
import streamlit as st


def render_global_styles():
    st.markdown(
        """
        <style>
        .st-key-kpi_top [data-testid="stMetricValue"] {
            font-size: 1.95rem !important;
            font-weight: 700 !important;
        }

        .st-key-kpi_top [data-testid="stMetricLabel"] {
            font-size: 0.98rem !important;
            font-weight: 600 !important;
        }

        .st-key-kpi_bottom [data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
        }

        .st-key-kpi_bottom [data-testid="stMetricLabel"] {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
        }

        div[data-testid="stMetric"] {
            min-height: 120px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(page_options):
    st.logo(
        image="data/tp_data_logo.png",
        icon_image="data/tp_data_icon.png",
    )

    with st.sidebar:
        page = st.radio("Sekcja", page_options)
        st.image("data/logo_acolyte.webp", width=140)
        st.caption("Data Acolyte")
        st.image("data/Logo_KajoData_.webp", width=140)
        st.caption("KajoDataSpace")

    return page


def _safe_month_shift(max_date, months_back=12):
    year = max_date.year
    month = max_date.month - months_back

    while month <= 0:
        month += 12
        year -= 1

    return date(year, month, 1)


def render_date_range_selector(
    min_date,
    max_date,
    key_prefix,
    label="Zakres analizy",
    default_preset="Pełny zakres",
):
    preset_options = [
        "Pełny zakres",
        "Ostatnie 12 miesięcy",
        "2025",
        "2026 YTD",
        "Własny zakres",
    ]

    default_index = (
        preset_options.index(default_preset)
        if default_preset in preset_options
        else 0
    )

    st.markdown("#### Zakres analizy")

    preset = st.radio(
        "Szybki wybór zakresu",
        preset_options,
        index=default_index,
        horizontal=True,
        key=f"{key_prefix}_preset",
        help="Wybierz gotowy zakres albo przełącz się na własny zakres dat."
    )

    if preset == "Pełny zakres":
        selected = (min_date, max_date)

    elif preset == "Ostatnie 12 miesięcy":
        start = _safe_month_shift(max_date, months_back=12)
        selected = (max(min_date, start), max_date)

    elif preset == "2025":
        start_2025 = date(2025, 1, 1)
        end_2025 = date(2025, 12, 31)
        selected = (max(min_date, start_2025), min(max_date, end_2025))

    elif preset == "2026 YTD":
        start_2026 = date(2026, 1, 1)
        selected = (max(min_date, start_2026), max_date)

    else:
        selected = st.date_input(
            label,
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_custom_range",
            help="Wybierz datę początkową i końcową analizy.",
        )

    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        start_date, end_date = selected

        st.caption(
            f"Wybrany zakres: **{start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}**"
        )

        return selected

    st.info("Wybierz pełny zakres: datę początkową i końcową.")
    return None