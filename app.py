"""Interaktywny dashboard monitorujący miks energii elektrycznej Polski."""

import pandas as pd
import plotly.express as px
import streamlit as st

from zielona_polska.model import forecast_share, temporal_mae
from zielona_polska.pipeline import load_data

st.set_page_config(page_title="Zielona Polska", page_icon="🌱", layout="wide")
st.title("🌱 Zielona Polska")
st.caption("Tani prąd, czyste powietrze — panel obserwacji transformacji elektroenergetycznej")

with st.sidebar:
    st.header("Ustawienia")
    horizon = st.slider("Horyzont scenariusza trendu (lata)", 1, 5, 3)
    refresh = st.button("Odśwież dane z OWID")

try:
    data = load_data(refresh=refresh)
except Exception as exc:  # Surface actionable failures while preserving a useful app shell.
    st.error(f"Nie udało się wczytać danych: {exc}")
    st.info("Sprawdź połączenie z internetem albo ustaw DATA_PATH na lokalny plik CSV.")
    st.stop()

valid = data.dropna(subset=["renewables_share_pct"])
if valid.empty:
    st.error("Brak kompletnych danych o udziale OZE.")
    st.stop()
latest = valid.iloc[-1]
previous = valid.iloc[-2] if len(valid) > 1 else latest
change = latest.renewables_share_pct - previous.renewables_share_pct
a, b, c = st.columns(3)
a.metric("Udział OZE", f"{latest.renewables_share_pct:.1f}%", f"{change:+.1f} p.p. r/r")
b.metric("Generacja ogółem", f"{latest.generation_twh:,.1f} TWh", f"rok {int(latest.year)}")
if pd.notna(latest.carbon_intensity_gco2e_kwh):
    c.metric("Intensywność emisji", f"{latest.carbon_intensity_gco2e_kwh:,.0f} gCO₂e/kWh")
else:
    c.metric("Intensywność emisji", "brak danych")

st.subheader("Jak zmienia się udział OZE?")
forecast = forecast_share(valid, horizon)
observed = valid[["year", "renewables_share_pct"]].copy()
observed["typ"] = "Dane historyczne"
future = forecast.rename(columns={"type": "typ"})
plot_df = pd.concat([observed, future[["year", "renewables_share_pct", "typ"]]], ignore_index=True)
fig = px.line(plot_df, x="year", y="renewables_share_pct", color="typ", markers=True,
              labels={"year": "Rok", "renewables_share_pct": "Udział OZE (%)", "typ": ""},
              color_discrete_map={"Dane historyczne": "#15803d", "scenariusz": "#f59e0b"})
fig.update_layout(legend_title_text="", yaxis_range=[0, 100], hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)
st.caption("Przerysowany trend jest prostą ekstrapolacją historyczną, nie prognozą operacyjną ani celem polityki publicznej.")

left, right = st.columns(2)
with left:
    st.subheader("Składniki miksu (TWh)")
    components = ["hydro_twh", "wind_twh", "solar_twh", "other_renewables_twh", "fossil_twh"]
    labels = {"hydro_twh": "Woda", "wind_twh": "Wiatr", "solar_twh": "Słońce",
              "other_renewables_twh": "Pozostałe OZE", "fossil_twh": "Paliwa kopalne"}
    mix = data.melt(id_vars="year", value_vars=components, var_name="źródło", value_name="TWh")
    mix["źródło"] = mix["źródło"].map(labels)
    st.plotly_chart(px.area(mix, x="year", y="TWh", color="źródło",
                            color_discrete_sequence=["#38bdf8", "#16a34a", "#facc15", "#84cc16", "#64748b"]),
                    use_container_width=True)
with right:
    st.subheader("Walidacja chronologiczna")
    try:
        model_mae, baseline_mae = temporal_mae(valid)
        st.write(f"MAE modelu trendu: **{model_mae:.2f} p.p.**")
        st.write(f"MAE baseline'u ostatniej wartości: **{baseline_mae:.2f} p.p.**")
        st.caption("Test obejmuje trzy ostatnie obserwacje; wyniki nie gwarantują jakości przyszłej prognozy.")
    except ValueError as exc:
        st.warning(str(exc))
    st.subheader("Dane źródłowe")
    st.dataframe(data.tail(10).sort_values("year", ascending=False), use_container_width=True, hide_index=True)

with st.expander("Interpretacja i ograniczenia"):
    st.markdown("""Dane opisują roczną produkcję energii elektrycznej. Nie zawierają cen rachunków, finansowania KPO ani danych o lokalnym stężeniu zanieczyszczeń. Współwystępowanie wzrostu OZE i spadku intensywności emisji nie dowodzi związku przyczynowego. Źródło i metodologia: [OWID Energy dataset](https://catalog.ourworldindata.org/energy/owid_energy/).""")
