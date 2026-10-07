import pandas as pd
import pytest

from zielona_polska.pipeline import COLUMNS, transform


def sample_frame():
    return pd.DataFrame([
        {"country": "Poland", "year": 2020, "electricity_generation_twh": 100,
         "hydro_electricity_twh": 2, "wind_electricity_twh": 10,
         "solar_electricity_twh": 3,
         "other_renewables_including_bioenergy_electricity_twh": 5,
         "fossil_fuels_electricity_twh": 80,
         "electricity_carbon_intensity_gco2eq_per_kwh": 700},
        {"country": "Germany", "year": 2020, "electricity_generation_twh": 500,
         "hydro_electricity_twh": 1, "wind_electricity_twh": 1,
         "solar_electricity_twh": 1,
         "other_renewables_including_bioenergy_electricity_twh": 1,
         "fossil_fuels_electricity_twh": 1,
         "electricity_carbon_intensity_gco2eq_per_kwh": 1},
    ])


def test_transform_filters_country_and_calculates_share():
    result = transform(sample_frame())
    assert len(result) == 1
    assert result.iloc[0].renewables_twh == 20
    assert result.iloc[0].renewables_share_pct == 20


def test_transform_rejects_schema_drift():
    with pytest.raises(ValueError, match="wymaganych kolumn"):
        transform(sample_frame().drop(columns=[COLUMNS[-1]]))


def test_transform_keeps_share_missing_when_component_missing():
    raw = sample_frame().iloc[[0]].copy()
    raw.loc[:, "solar_electricity_twh"] = float("nan")
    result = transform(raw)
    assert pd.isna(result.iloc[0].renewables_share_pct)
