from datetime import timedelta
from typing import Literal

from ortools.math_opt.python import mathopt

from .base_model import BaseModel


class NaiveModel(BaseModel):
    def __init__(self, optimize_input_data, optimize_config_data):
        super().__init__(optimize_input_data, optimize_config_data)
        self.model = mathopt.Model(name="naive model")
        self.result = None  # 最適化結果格納用

        # 決定変数
        self.x = {}  # 地点移動を表すbinary変数
        self.u = {}  # 訪問順を表す補助変数
        self.y = {}  # 荷物の自社配送を表すbinary変数
        self.h = {}  # 日ごとの残業時間
        self.total_overtime_cost = None  # 計画期間全体の残業時間コスト
        self.total_outsourcing_cost = None  # 計画期間全体の外注費用

    def _add_intermediate_variable(
        self, constraints: mathopt.LinearExpression, name: str
    ) -> mathopt.Variable:
        """
        中間変数を定義するために変数を宣言して制約条件として追加するための関数
        """
        ret = self.model.add_variable(name=name)
        self.model.add_linear_constraint(ret == constraints)
        return ret

    def add_variables(self):
        # x
        for d in self.data.list_delivery_date:
            for k1 in self.data.list_store_and_depot_data:
                for k2 in self.data.list_store_and_depot_data:
                    self.x[d, k1.name, k2.name] = self.model.add_binary_variable(
                        name=f"x_{d}_{k1.name}_{k2.name}"
                    )

        # u
        for d in self.data.list_delivery_date:
            for k in self.data.list_store_and_depot_data:
                self.u[d, k.name] = self.model.add_integer_variable(
                    lb=0, name=f"u_{d}_{k.name}"
                )

        # y
        for d in self.data.list_delivery_date:
            for r in self.data.list_order_name:
                self.y[d, r] = self.model.add_binary_variable(name=f"y_{d}_{r}")

        # h
        for d in self.data.list_delivery_date:
            self.h[d] = self.model.add_variable(name=f"h_{d}", lb=0)

        # total_overtime_cost
        self.total_overtime_cost = self._add_intermediate_variable(
            sum([3000 * self.h[d] for d in self.data.list_delivery_date]), "over_time"
        )
        # total_outsourcing_cost
        self.total_outsourcing_cost = self._add_intermediate_variable(
            sum(
                [
                    self.config.outsourcing_cost_per_weight
                    * self.y[d, r]
                    * self.data.order_name2data[r].weight
                    for d in self.data.list_delivery_date
                    for r in self.data.list_order_name
                ]
            ),
            "outsourcing_cost",
        )

        return self

    def add_constraints(self):
        # 必ず適用する制約条件
        for d in self.data.list_delivery_date:
            for k1 in self.data.list_store_and_depot_data:
                # 各地点の入ってくる数と出ていく数は等しい
                self.model.add_linear_constraint(
                    sum(
                        self.x[d, k1.name, k2.name]
                        for k2 in self.data.list_store_and_depot_data
                    )
                    == sum(
                        self.x[d, k2.name, k1.name]
                        for k2 in self.data.list_store_and_depot_data
                    )
                )
                # 各配送日について、地点に訪問する数は高々1回まで
                self.model.add_linear_constraint(
                    sum(
                        [
                            self.x[d, k2.name, k1.name]
                            for k2 in self.data.list_store_and_depot_data
                        ]
                    )
                    <= 1
                )

        for d in self.data.list_delivery_date:
            depot_data = self.data.depot_data
            #  各配送日について、配送センターは出発地点(0番目に訪問)
            self.model.add_linear_constraint(self.u[d, depot_data.name] == 0)

            # 各配送日について、お店間だけのサイクルを禁止
            for s1 in self.data.list_store_name:
                for s2 in self.data.list_store_name:
                    self.model.add_linear_constraint(
                        self.u[d, s1] + 1
                        <= self.u[d, s2]
                        + (len(self.data.list_store_name) - 1) * (1 - self.x[d, s1, s2])
                    )

        # 各荷物は、自社配送するなら期間内で高々1回まで
        for r in self.data.list_order_name:
            self.model.add_linear_constraint(
                sum([self.y[d, r] for d in self.data.list_delivery_date]) <= 1
            )

        # 各配送日について、荷物を自社配送するなら、配送先のお店に訪問
        for d in self.data.list_delivery_date:
            for r in self.data.list_order_name:
                order_data = self.data.order_name2data[r]
                self.model.add_linear_constraint(
                    self.y[d, r]
                    <= sum(
                        self.x[d, k.name, order_data.destination]
                        for k in self.data.list_store_and_depot_data
                    )
                )

        # 各配送日について、ドライバーの残業時間は所定労働時間の8時間を差し引いた労働時間
        for d in self.data.list_delivery_date:
            self.model.add_linear_constraint(
                sum(
                    [
                        self.data.move_time_matrix[k1.name, k2.name]
                        * self.x[d, k1.name, k2.name]
                        for k1 in self.data.list_store_and_depot_data
                        for k2 in self.data.list_store_and_depot_data
                    ]
                )
                - self.config.max_overtime
                <= self.h[d]
            )

        # 各荷物は指定配送期間外の配送を禁止
        for r in self.data.list_order_name:
            for d in self.data.list_delivery_date:
                order_data = self.data.order_name2data[r]
                if d < order_data.time_window_start:
                    self.model.add_linear_constraint(self.y[d, r] == 0)
                if order_data.time_window_end < d:
                    self.model.add_linear_constraint(self.y[d, r] == 0)

        # ユーザーが指定する制約条件
        if self.config.truck_capacity_constraint.is_applied:
            self._add_truck_capacity_constraint()
        if self.config.max_overtime_constraint.is_applied:
            self._add_max_overtime_constraint()

        return self

    def _add_truck_capacity_constraint(self):
        """
        各配送日について、荷物の重量は所定の値以下
        """
        for d in self.data.list_delivery_date:
            self.model.add_linear_constraint(
                sum(
                    [
                        self.y[d, r] * self.data.order_name2data[r].weight
                        for r in self.data.list_order_name
                    ]
                )
                <= self.config.truck_capacity
            )

    def _add_max_overtime_constraint(self):
        """ """
        for d in self.data.list_delivery_date:
            self.model.add_linear_constraint(self.h[d] <= self.config.max_overtime)

    def add_objectives(self):
        obj_value = 0
        if self.config.total_move_time_objective.is_applied:
            obj_value += self.total_overtime_cost
        if self.config.total_cost_objective.is_applied:
            obj_value += self.total_outsourcing_cost

        self.model.minimize(obj_value)
        return self

    def optimize(
        self,
    ) -> Literal["Optimal", "Feasible", "NotSolved", "Unbounded", "Undefined"]:
        params = mathopt.SolveParameters(
            time_limit=timedelta(seconds=self.config.time_limit),
            enable_output=True,
            threads=self.config.threads,
        )
        self.result = mathopt.solve(self.model, mathopt.SolverType.GSCIP, params=params)

        if self.result.termination.reason == mathopt.TerminationReason.OPTIMAL:
            return "Optimal"
        elif self.result.termination.reason == mathopt.TerminationReason.FEASIBLE:
            return "Feasible"
        elif self.result.termination.reason == mathopt.TerminationReason.NOT_SOLVED:
            return "NotSolved"
        elif self.result.termination.reason == mathopt.TerminationReason.UNBOUNDED:
            return "Unbounded"
        else:
            return "INFEASIBLE"

    def get_result(self):
        return None
