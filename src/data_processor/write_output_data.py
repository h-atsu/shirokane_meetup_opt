import json
from pathlib import Path

import polars as pl
from xlsxwriter import Workbook

from consts import ROOT
from optimize_dataclass.config_dataclass import ConfigData
from optimize_dataclass.io_dataclass import InputData, OutputData


def write_output_data(
    input_data: InputData,
    config_data: ConfigData,
    output_data: OutputData,
    output_dir: Path,
):
    """
    出力データをエクセルに書き込みで保存する
    """
    pass

    outputs: dict[str, pl.DataFrame] = {}
    # summary
    index = ["配送期間", "費用合計", "残業費用", "外注費用", "合計移動時間"]
    value = [
        f"[{min(input_data.list_delivery_date)}～{max(input_data.list_delivery_date)}]",
        output_data.total_cost,
        output_data.total_overtime_cost,
        output_data.total_outsourcing_cost,
        output_data.total_move_time,
    ]
    df = pl.DataFrame({"指標": index, "値": value}, strict=False)
    outputs["summary"] = df.clone()

    # daily_info
    data = []
    for d in input_data.list_delivery_date:
        daily_data = output_data.date2daily_data[d]
        route_str = "→".join([s.name for s in daily_data.list_delivery_route])
        data.append(
            {
                "日付": d,
                "配送ルート": route_str,
                "配送重量": daily_data.daily_total_weight,
                "移動時間": daily_data.daily_move_time,
                "残業時間": daily_data.daily_overtime,
                "残業費用": daily_data.daily_overtime_cost,
            }
        )
        df = pl.DataFrame(data)
        outputs["daily_info"] = df.clone()

    # orders_info
    data = []

    for (
        order_name,
        delivery_status_data,
    ) in output_data.order_name2delivery_status_data.items():
        order_data = input_data.order_name2data[order_name]

        data.append(
            {
                "注文名": order_name,
                "配送店舗名": order_data.destination,
                "重量": order_data.weight,
                "配送日": delivery_status_data,
                "外注フラグ": delivery_status_data.outsourced_flag,
                "外注費用": delivery_status_data.outsourcing_cost,
            }
        )
    df = pl.DataFrame(data)
    outputs["orders_info"] = df.clone()

    if not output_dir.exists():
        output_dir.mkdir()

    # output_data.xlsxに書き込み
    with Workbook(ROOT / output_dir / "output_data.xlsx") as wb:
        for sheet_name, df in outputs.items():
            df.write_excel(workbook=wb, worksheet=sheet_name)

    # input_data, output_dataをjsonで保存
    with open(ROOT / output_dir / "input_data.json", "w") as f:
        json.dump(input_data.model_dump(mode="json"), f, ensure_ascii=False, indent=4)

    with open(ROOT / output_dir / "output_data.json", "w") as f:
        json.dump(output_data.model_dump(mode="json"), f, ensure_ascii=False, indent=4)
