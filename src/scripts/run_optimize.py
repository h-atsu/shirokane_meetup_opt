from datetime import datetime

from consts import ROOT
from data_processor.make_input_data import make_input_data
from data_processor.write_output_data import write_output_data
from execute_model import execute_model
from optimize_dataclass.config_dataclass import (
    ConfigData,
    ConstraintData,
    ObjectiveData,
)


def main(config_data: ConfigData):
    # output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = ROOT / "data" / "outputs" / f"{timestamp}"

    # 入力データの読み込み
    input_data = make_input_data(config_data.dataset_name)

    # 入力データ→最適化モデル→出力データ
    output_data = execute_model(input_data, config_data)

    # 出力データをエクセルに書き込み
    write_output_data(input_data, config_data, output_data, output_dir)


if __name__ == "__main__":
    config_data = ConfigData(
        dataset_name="small_dataset",
        time_limit=10,
        threads=4,
        standartd_work_time=8.0,
        max_overtime=3.0,
        overtime_cost_per_hour=3000.0,
        outsourcing_cost_per_weight=46.0,
        truck_capacity=4000.0,
        total_move_time_objective=ObjectiveData(
            priority=1,
            direction="minimize",
            is_applied=True,
        ),
        total_cost_objective=ObjectiveData(
            priority=2,
            direction="minimize",
            is_applied=True,
        ),
        max_overtime_constraint=ConstraintData(
            is_applied=True,
        ),
        truck_capacity_constraint=ConstraintData(
            is_applied=True,
        ),
    )
    main(config_data)
