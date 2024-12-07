from models.naive_model import NaiveModel
from optimize_dataclass.config_dataclass import ConfigData
from optimize_dataclass.io_dataclass import InputData, OutputData

solver_model_name2model_class = {
    "naive_model": NaiveModel,
}


def execute_model(input_data: InputData, config_data: ConfigData) -> OutputData:
    model = solver_model_name2model_class[config_data.solver_model_type](
        input_data, config_data
    )
    model.add_variables().add_constraints().add_objectives()
    status = model.optimize()

    if status in ["Optimal", "Feasible"]:
        output_data = model.get_result()
    else:
        raise Exception(f"最適化が正しく完了しませんでした: {status}")

    return output_data
