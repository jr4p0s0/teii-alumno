""" Unit tests for teii.finance.timeseries module """


import datetime as dt

import pytest
from pandas.testing import assert_series_equal

from teii.finance import FinanceClientInvalidAPIKey, TimeSeriesFinanceClient
from teii.finance.exception import FinanceClientInvalidData, FinanceClientParamError


def test_constructor_success(api_key_str,
                             mocked_requests):
    TimeSeriesFinanceClient("IBM", api_key_str)
    TimeSeriesFinanceClient("AAPL", api_key_str)


def test_constructor_env(monkeypatch, mocked_requests):
    monkeypatch.setenv("TEII_FINANCE_API_KEY", "monkeypatched_api_key")
    TimeSeriesFinanceClient("IBM")


def test_constructor_failure_invalid_api_key():
    with pytest.raises(FinanceClientInvalidAPIKey):
        TimeSeriesFinanceClient("IBM")


def test_weekly_price_invalid_dates(api_key_str,
                                    mocked_requests):
    # TODO
    pass


def test_weekly_price_no_dates(api_key_str,
                               mocked_requests,
                               pandas_series_IBM_prices):
    fc = TimeSeriesFinanceClient("IBM", api_key_str)

    ps = fc.weekly_price()

    assert ps.count() == 1276   # 2009-11-12 to 2024-04-15 (1276 business weeks)

    assert ps.count() == pandas_series_IBM_prices.count()

    assert_series_equal(ps, pandas_series_IBM_prices)


def test_weekly_price_dates(api_key_str,
                            mocked_requests,
                            pandas_series_IBM_prices_filtered):
    fc = TimeSeriesFinanceClient("IBM", api_key_str)

    ps = fc.weekly_price(dt.date(year=2021, month=1, day=1),
                         dt.date(year=2023, month=12, day=31))

    assert ps.count() == 156    # 2021-01-01 to 2023-12-31 (156 business weeks)

    assert ps.count() == pandas_series_IBM_prices_filtered.count()

    assert_series_equal(ps, pandas_series_IBM_prices_filtered)


def test_weekly_volume_invalid_dates(api_key_str,
                                     mocked_requests):
    # TODO
    # comprobar que from_date <= to_date y que se generar excepción 'FinanceClientParamError' en caso de error
    fc = TimeSeriesFinanceClient("IBM", api_key_str)
    with pytest.raises(FinanceClientParamError):
        fc.weekly_volume(dt.date(year=2023, month=12, day=31), dt.date(year=2021, month=1, day=1))
    pass


def test_weekly_volume_no_dates(api_key_str,
                                mocked_requests,
                                pandas_series_IBM_volumes):

    fc = TimeSeriesFinanceClient("IBM", api_key_str)

    ps = fc.weekly_volume()

    assert ps.count() == 1276   # 2009-11-12 to 2024-04-15 (1276 business weeks)

    assert ps.count() == pandas_series_IBM_volumes.count()

    assert_series_equal(ps, pandas_series_IBM_volumes)

    pass


def test_weekly_volume_dates(api_key_str,
                             mocked_requests,
                             pandas_series_IBM_volumes_filtered):
    fc = TimeSeriesFinanceClient("IBM", api_key_str)

    ps = fc.weekly_volume(dt.date(year=2010, month=1, day=8), dt.date(year=2023, month=12, day=29))

    assert ps.count() == 730    # 2010-01-08 to 2023-12-29 (730 business weeks)

    assert ps.count() == pandas_series_IBM_volumes_filtered.count()

    assert_series_equal(ps, pandas_series_IBM_volumes_filtered)

    pass


def test_constructor_invalid_data(api_key_str,
                                  mocked_requests):
    with pytest.raises(FinanceClientInvalidData):
        TimeSeriesFinanceClient("NODATA", api_key_str)
