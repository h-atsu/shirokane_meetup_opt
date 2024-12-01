from pydantic import BaseModel


# 入力データクラスの定義
class StoreData(BaseModel):
    """
    店舗データ
    """

    name: str
    x_cord: float
    y_cord: float


class OrderData(BaseModel):
    """
    配送注文データ
    """

    name: str
    destination: str  # 店舗名
    weight: float
    time_window_start: int
    time_window_end: int


class InputData(BaseModel):
    """
    最適化入力クラス
    """

    list_derivery_date: list[int]  # 配送日のリスト
    list_order_name: list[str]  # 配送注文名のリスト
    order_name2data: dict[str, OrderData]  # 配送注文名からデータへの変換
    list_store_name: list[str]  # 店舗名のリスト
    store_name2data: list[StoreData]  # 店舗名から店舗データへの変換
    depot_data = StoreData  # 配送センター(デポ)のデータ
    move_time_matrix: dict[tuple[str, str], float]  # 店舗間の移動時間


# 出力データクラスの定義
class DailyData(BaseModel):
    """
    1日分の配送結果データ
    """

    list_delivery_route: list[StoreData]  # 自社配送のルート
    total_weight: float  # 配送重量
    total_move_time: float  # 移動時間
    over_time: float  # 残業時間
    over_time_cost: float  # 残業時間コスト
    outsourcintg_cost: float  # 外注費用


class OutputData(BaseModel):
    """
    最適化出力クラス
    """

    date2daily_data: dict[int, DailyData]  # 配送日から1日分の配送結果データへの変換
    total_over_time_cost: float  # 総残業時間コスト
    total_outsourcing_cost: float  # 総外注費用
