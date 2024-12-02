from typing import Literal

from pydantic import BaseModel, Field, fields


class ObjectiveData(BaseModel):
    """
    目的関数データ
    """

    priority: int = Field(ge=1)  # 優先度
    direction: Literal["minimize", "maximize"]  # 最小化か最大化か
    is_applied: bool = True  # 適用するかどうかn


class ConstraintData(BaseModel):
    """
    制約条件データ
    """

    is_applied: bool = True  # 適用するかどうか


class ConfigData(BaseModel):
    dataset_name: str  # データセット名
    # 計算設定
    solver_model_type: str = "naive_model"  # 最適化モデルの種類
    time_limit: int  # 計算時間（秒）
    threads: int  # 計算スレッド数

    # 入力データ
    standartd_work_time: float  # 定時の勤務時間（時間）
    max_overtime: float  # 最大残業時間（時間）
    overtime_cost_per_hour: float  # 残業時間コスト（円/時間）
    outsourcing_cost_per_weight: float  # 外注費用（円/kg）
    truck_capacity: float  # トラックの積載量（kg）

    # 目的関数
    total_move_time_objective: ObjectiveData  # 移動時間の総和
    total_cost_objective: ObjectiveData  # 総費用

    # 制約条件
    max_overtime_constraint: ConstraintData  # 最大残業時間制約
    truck_capacity_constraint: ConstraintData  # トラックの積載量制約

    def get_list_objective(self) -> list[ObjectiveData]:
        return [
            getattr(self, f.name) for f in fields(self) if f.name.endswith("objective")
        ]

    def get_list_constraint(self) -> list[ConstraintData]:
        return [
            getattr(self, f.name) for f in fields(self) if f.name.endswith("constraint")
        ]
