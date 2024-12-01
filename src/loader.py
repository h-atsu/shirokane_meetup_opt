from pathlib import Path

import pandera.polars as pa
import polars as pl
from pandera.typing import DataFrame

from schema import DistanceSchema, LocationsSchema, OrdersSchema


@pa.check_types
def load_locations_mst(filepath: Path) -> DataFrame[LocationsSchema]:
    df = pl.read_excel(filepath, sheet_name="locations_mst").with_columns(
        pl.col("x_cord").cast(pl.Float64),
        pl.col("y_cord").cast(pl.Float64),
    )
    return df


@pa.check_types
def load_distances_mst(filepath: Path) -> DataFrame[DistanceSchema]:
    df = pl.read_excel(filepath, sheet_name="distances_mst").with_columns(
        pl.col("time_to_move").cast(pl.Float64)
    )
    return df


@pa.check_types
def load_orders(filepath: Path) -> DataFrame[OrdersSchema]:
    df = pl.read_excel(filepath, sheet_name="orders").with_columns(
        pl.col("weight").cast(pl.Float64)
    )
    return df
