from datetime import datetime

from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import IntParameter, IStrategy



class basic_unicorn(IStrategy):
    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "1d"
    minimal_roi = {}
    stoploss = -1.0

    fastMA = IntParameter(low=5, high=20, default=10, space="buy",load=False)
    slowMA = IntParameter(low=20, high=40, default=30, space="buy",load=False)
    leverage_parameter = IntParameter(low=4, high=4, default=3, space="buy",load=False)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        heikin_ashi = qtpylib.heikinashi(dataframe)
        dataframe["ha_open"] = heikin_ashi["open"]
        dataframe["ha_close"] = heikin_ashi["close"]
        dataframe["ha_positive_switch"] = (
            (dataframe["ha_close"].shift(1) < dataframe["ha_open"].shift(1))
            & (dataframe["ha_close"] > dataframe["ha_open"])
        ).astype(int)
        dataframe["ha_negative_switch"] = (
            (dataframe["ha_close"].shift(1) > dataframe["ha_open"].shift(1))
            & (dataframe["ha_close"] < dataframe["ha_open"])
        ).astype(int)

        fast_length = self.fastMA.value
        slow_length = max(self.slowMA.value, fast_length + 1)
        dataframe["fastMA"] = dataframe["ha_close"].rolling(fast_length).mean()
        dataframe["slowMA"] = dataframe["ha_close"].rolling(slow_length).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["ha_positive_switch"] == 1)
            & (dataframe["fastMA"] > dataframe["slowMA"]),
            "enter_long",
        ] = 1
        dataframe.loc[
            (dataframe["ha_negative_switch"] == 1)
            & (dataframe["fastMA"] < dataframe["slowMA"]),
            "enter_short",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["ha_negative_switch"] == 1, "exit_long"] = 1
        dataframe.loc[dataframe["ha_positive_switch"] == 1, "exit_short"] = 1
        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: float | None,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        return max_stake

    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        return min(float(self.leverage_parameter.value), max_leverage)
