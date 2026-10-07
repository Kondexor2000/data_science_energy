"""Prosta ekstrapolacja trendu oraz walidacja chronologiczna."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


def forecast_share(data: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """Fit a linear trend on observed years and extrapolate a bounded share."""
    if not 1 <= horizon <= 5:
        raise ValueError("Horyzont prognozy musi wynosić od 1 do 5 lat")
    clean = data.dropna(subset=["year", "renewables_share_pct"]).sort_values("year")
    if len(clean) < 5:
        raise ValueError("Do modelu potrzeba co najmniej 5 obserwacji")
    model = LinearRegression().fit(clean[["year"]], clean["renewables_share_pct"])
    years = np.arange(int(clean.year.max()) + 1, int(clean.year.max()) + horizon + 1)
    values = np.clip(model.predict(years.reshape(-1, 1)), 0, 100)
    return pd.DataFrame({"year": years, "renewables_share_pct": values, "type": "scenariusz"})


def temporal_mae(data: pd.DataFrame, test_size: int = 3) -> tuple[float, float]:
    """Compare linear regression to last-value forecast on the final observations."""
    clean = data.dropna(subset=["year", "renewables_share_pct"]).sort_values("year")
    if len(clean) <= test_size + 2:
        raise ValueError("Za mało danych do walidacji chronologicznej")
    train, test = clean.iloc[:-test_size], clean.iloc[-test_size:]
    model = LinearRegression().fit(train[["year"]], train["renewables_share_pct"])
    predicted = np.clip(model.predict(test[["year"]]), 0, 100)
    baseline = np.repeat(train.renewables_share_pct.iloc[-1], len(test))
    return float(mean_absolute_error(test.renewables_share_pct, predicted)), float(
        mean_absolute_error(test.renewables_share_pct, baseline)
    )
