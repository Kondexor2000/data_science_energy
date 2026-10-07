import pandas as pd
import pytest

from zielona_polska.model import forecast_share, temporal_mae


def history():
    return pd.DataFrame({"year": range(2010, 2020), "renewables_share_pct": range(10, 20)})


def test_forecast_is_bounded_and_has_requested_horizon():
    result = forecast_share(history(), 3)
    assert result.year.tolist() == [2020, 2021, 2022]
    assert result.renewables_share_pct.between(0, 100).all()


def test_forecast_rejects_long_horizon():
    with pytest.raises(ValueError):
        forecast_share(history(), 6)


def test_temporal_validation_beats_last_value_on_linear_trend():
    model_mae, baseline_mae = temporal_mae(history())
    assert model_mae < baseline_mae
