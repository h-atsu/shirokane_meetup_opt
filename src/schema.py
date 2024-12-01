import pandera.polars as pa


class LocationsSchema(pa.DataFrameModel):
    """
    店舗データ
    """

    location: str
    x_cord: float
    y_cord: float
    is_depot: int = pa.Field(isin=[0, 1])

    class Config:
        unique = ["location"]


class DistanceSchema(pa.DataFrameModel):
    """
    店舗間距離データ
    """

    location1: str
    location2: str
    time_to_move: float

    class Config:
        unique = ["location1", "location2"]


class OrdersSchema(pa.DataFrameModel):
    """
    配送注文データ
    """

    order_name: str
    store_name: str
    weight: float
    time_window_start: int
    time_window_end: int

    class Config:
        unique = ["order_name"]
