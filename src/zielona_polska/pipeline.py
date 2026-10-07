"""Pobiera, sprawdza i zapisuje publiczny wyciąg danych energetycznych OWID."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests

DATA_URL = "https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv"
COLUMNS = [
    "country", "year", "electricity_generation_twh", "hydro_electricity_twh",
    "wind_electricity_twh", "solar_electricity_twh",
    "other_renewables_including_bioenergy_electricity_twh",
    "fossil_fuels_electricity_twh", "electricity_carbon_intensity_gco2eq_per_kwh",
]
RENAME = {
    "electricity_generation_twh": "generation_twh",
    "hydro_electricity_twh": "hydro_twh",
    "wind_electricity_twh": "wind_twh",
    "solar_electricity_twh": "solar_twh",
    "other_renewables_including_bioenergy_electricity_twh": "other_renewables_twh",
    "fossil_fuels_electricity_twh": "fossil_twh",
    "electricity_carbon_intensity_gco2eq_per_kwh": "carbon_intensity_gco2e_kwh",
}


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    """Select Poland and derive the renewable share without imputing missing inputs."""
    missing = set(COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Źródło nie zawiera wymaganych kolumn: {sorted(missing)}")
    data = raw.loc[raw["country"].eq("Poland"), COLUMNS].copy()
    data = data.rename(columns=RENAME)
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    for col in data.columns.difference(["country", "year"]):
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["year", "generation_twh"]).sort_values("year")
    data = data.loc[data["year"] >= 1990].drop_duplicates("year", keep="last")
    renewables = ["hydro_twh", "wind_twh", "solar_twh", "other_renewables_twh"]
    data["renewables_twh"] = data[renewables].sum(axis=1, min_count=len(renewables))
    valid = data["generation_twh"].gt(0) & data["renewables_twh"].notna()
    data["renewables_share_pct"] = pd.NA
    data.loc[valid, "renewables_share_pct"] = (
        100 * data.loc[valid, "renewables_twh"] / data.loc[valid, "generation_twh"]
    )
    return data.reset_index(drop=True)


def load_data(path: str | Path | None = None, refresh: bool = False) -> pd.DataFrame:
    """Load cached data; fetch from OWID on cache miss or explicit refresh."""
    target = Path(path or os.getenv("DATA_PATH", "data/processed/poland_energy.csv"))
    if target.exists() and not refresh:
        return pd.read_csv(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(DATA_URL, timeout=(10, 90), headers={"User-Agent": "zielona-polska/0.1"})
    response.raise_for_status()
    from io import BytesIO

    result = transform(pd.read_csv(BytesIO(response.content), usecols=lambda name: name in COLUMNS))
    if result.empty:
        raise ValueError("OWID nie zwrócił rekordów dla Polski")
    result.to_csv(target, index=False)
    return result


if __name__ == "__main__":
    frame = load_data(refresh=True)
    print(f"Zapisano {len(frame)} rekordów: {frame.year.min():.0f}–{frame.year.max():.0f}")
