""" Time Series Finance Client classes """


import datetime as dt
import logging
from typing import Optional, Union

import pandas as pd

from teii.finance import FinanceClient, FinanceClientInvalidData, FinanceClientParamError
# NOTE: FinanceClientParamError is not used in the current implementation. Is an error? Should be removed?


class TimeSeriesFinanceClient(FinanceClient):
    """ Wrapper around the AlphaVantage API for Time Series Weekly Adjusted.

        Source:
            https://www.alphavantage.co/documentation/ (TIME_SERIES_WEEKLY_ADJUSTED)
    """

    _data_field2name_type = {
        "1. open":                  ("open",     "float"),
        "2. high":                  ("high",     "float"),
        "3. low":                   ("low",      "float"),
        "4. close":                 ("close",    "float"),
        "5. adjusted close":        ("aclose",   "float"),
        "6. volume":                ("volume",   "int"),
        "7. dividend amount":       ("dividend", "float")
    }

    def __init__(self, ticker: str,
                 api_key: Optional[str] = None,
                 logging_level: Union[int, str] = logging.WARNING) -> None:
        """ TimeSeriesFinanceClient constructor. """

        super().__init__(ticker, api_key, logging_level)

        self._build_data_frame()

    def _build_data_frame(self) -> None:
        """ Build Panda's DataFrame and format data. """

        try:
            # Build Panda's data frame
            data_frame = pd.DataFrame.from_dict(self._json_data, orient='index', dtype='float')
            # Rename data fields
            data_frame = data_frame.rename(columns={key: name_type[0]
                                                    for key, name_type in self._data_field2name_type.items()})
            # Set data field types
            data_frame = data_frame.astype(dtype={name_type[0]: name_type[1]
                                                  for key, name_type in self._data_field2name_type.items()})
            # Set index type
            data_frame.index = data_frame.index.astype("datetime64[ns]")
            # Sort data
            self._data_frame = data_frame.sort_index(ascending=True)

        except Exception as e:
            raise FinanceClientInvalidData("Error building data frame") from e

    def _build_base_query_url_params(self) -> str:
        """ Return base query URL parameters.

        Parameters are dependent on the query type:
            https://www.alphavantage.co/documentation/
        URL format:
            https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol=TICKER&outputsize=full&apikey=API_KEY&data_type=json
        """

        return f"function=TIME_SERIES_WEEKLY_ADJUSTED&symbol={self._ticker}&outputsize=full&apikey={self._api_key}"

    @classmethod
    def _build_query_data_key(cls) -> str:
        """ Return data query key. """

        return "Weekly Adjusted Time Series"

    def _validate_query_data(self) -> None:
        """ Validate query data. """

        try:
            assert self._json_metadata["2. Symbol"] == self._ticker
        except Exception as e:
            raise FinanceClientInvalidData("Metadata field '2. Symbol' not found") from e
        else:
            self._logger.info(f"Metadata key '2. Symbol' = '{self._ticker}' found")

    def weekly_price(self,
                     from_date: Optional[dt.date] = None,
                     to_date: Optional[dt.date] = None) -> Optional[pd.Series]:
        """ Return weekly close price from 'from_date' to 'to_date'. """

        assert self._data_frame is not None

        series = self._data_frame['aclose']

        # TODO
        #   Comprueba que from_date <= to_date y genera excepción
        #   'FinanceClientParamError' en caso de error

        # FIXME: type hint error
        if from_date is not None and to_date is not None:
            if from_date is not None and to_date is not None:
                try:
                    assert from_date <= to_date
                except Exception as e:
                    raise FinanceClientParamError("from_date tiene que ser menor o igual que to_date") from e

                series = series.loc[from_date:to_date]   # type: ignore

        return series

    def weekly_volume(self,
                      from_date: Optional[dt.date] = None,
                      to_date: Optional[dt.date] = None) -> pd.Series:
        """ Return weekly volume from 'from_date' to 'to_date'. """

        assert self._data_frame is not None

        series = self._data_frame['volume']

        # TODO
        #   Comprueba que from_date <= to_date y genera excepción
        #   'FinanceClientParamError' en caso de error
        #  Comprobacion:
        if from_date is not None and to_date is not None:
            try:
                assert from_date <= to_date
            except Exception as e:
                raise FinanceClientParamError("from_date > to_date") from e

        # FIXME: type hint error
        if from_date is not None and to_date is not None:  # NOTE: Esto no deberia ser necesario, FIXME
            series = series.loc[from_date:to_date]   # type: ignore

        return series

    def highest_weekly_variation(self,
                                 from_date: Optional[dt.date] = None,
                                 to_date: Optional[dt.date] = None) -> tuple:
        """ Return the week with the highest variation in the adjusted close price. """

        assert self._data_frame is not None

        # Filtramos el rango de fechas
        if from_date is not None and to_date is not None:
            self._data_frame = self._data_frame.loc[from_date:to_date]  # type: ignore

        # Calculamos la variación de la cotización
        self._data_frame['variation'] = self._data_frame['high'] - self._data_frame['low']

        # Obtenemos la fecha con la mayor variación
        max_variation = self._data_frame['variation'].idxmax()

        # Obtenemos los valores de high y low para esa fecha
        high = self._data_frame.loc[max_variation]['high']
        low = self._data_frame.loc[max_variation]['low']

        # Devolvemos la tupla
        return (max_variation, high, low, high - low)

    def yearly_dividends(self,
                         from_year: Optional[int] = None,
                         to_year: Optional[int] = None) -> pd.Series:

        assert self._data_frame is not None

        # Convierto los enteros en fechas
        if from_year is not None and to_year is not None:
            from_date = dt.date(year=from_year, month=1, day=1)
            to_date = dt.date(year=to_year, month=12, day=31)
        else:
            from_date = None
            to_date = None

        # Obtenemos los dividendos anuales agrupando los datos anualmente "YS"
        dividendos = self._data_frame.groupby(pd.Grouper(freq='YS'))['dividend'].sum()

        # Filtramos los dividendos por rango de años si se especifican
        if from_year is not None and to_year is not None:
            try:
                assert from_date <= to_date
            except Exception as e:
                raise FinanceClientParamError("from_date > to_date") from e

        dividendos = dividendos.loc[from_date:to_date]
        return dividendos
