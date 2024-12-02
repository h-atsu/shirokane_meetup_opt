import polars as pl

from consts import ROOT
from loader import load_distances_mst, load_locations_mst, load_orders
from optimize_dataclass.io_dataclass import InputData, OrderData, StoreData


def make_input_data(dataset_name: str) -> InputData:
    dataset_dir = ROOT / "data" / "raw" / f'{dataset_name + ".xlsx"}'
    df_locations = load_locations_mst(dataset_dir)
    df_distances = load_distances_mst(dataset_dir)
    df_orders = load_orders(dataset_dir)

    list_delivery_date = list(
        range(
            df_orders["time_window_start"].min(), df_orders["time_window_end"].max() + 1
        )
    )

    list_order_name = df_orders["order"].to_list()
    order_name_2data = {}
    for row in df_orders.iter_rows(named=True):
        order_name_2data[row["order"]] = OrderData(
            name=row["order"],
            destination=row["store"],
            weight=row["weight"],
            time_window_start=row["time_window_start"],
            time_window_end=row["time_window_end"],
        )

    list_store_name = df_locations.filter(pl.col("is_depot") == 0)["location"].to_list()
    depot_data = None
    store_name2data = {}
    for row in df_locations.iter_rows(named=True):
        if row["is_depot"]:
            depot_data = StoreData(
                name=row["location"], x_cord=row["x_cord"], y_cord=row["y_cord"]
            )
        else:
            store_name2data[row["location"]] = StoreData(
                name=row["location"], x_cord=row["x_cord"], y_cord=row["y_cord"]
            )
    list_store_and_depot_data = list(store_name2data.values()) + [depot_data]
    move_time_matrix = {
        (row["location1"], row["location2"]): row["time_to_move"]
        for row in df_distances.iter_rows(named=True)
    }
    return InputData(
        list_delivery_date=list_delivery_date,
        list_order_name=list_order_name,
        order_name2data=order_name_2data,
        list_store_name=list_store_name,
        store_name2data=store_name2data,
        depot_data=depot_data,
        list_store_and_depot_data=list_store_and_depot_data,
        move_time_matrix=move_time_matrix,
    )
