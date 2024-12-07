import pandera.polars as pa
from pandera.typing import Series


class LocationsSchema(pa.DataFrameModel):
    """
    店舗データ
    """

    location: Series[str]
    x_cord: Series[float]
    y_cord: Series[float]
    is_depot: int = pa.Field(isin=[0, 1])

    class Config:
        unique = ["location"]


class DistanceSchema(pa.DataFrameModel):
    """
    店舗間距離データ
    """

    location1: Series[str]
    location2: Series[str]
    time_to_move: Series[float]

    class Config:
        unique = ["location1", "location2"]


class OrdersSchema(pa.DataFrameModel):
    """
    配送注文データ
    """

    order: Series[str]
    store: Series[str]
    weight: Series[float]
    time_window_start: int
    time_window_end: int

    class Config:
        unique = ["order"]
