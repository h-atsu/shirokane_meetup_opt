from datetime import timedelta
from typing import Literal

from ortools.math_opt.python import mathopt

from models.base_model import BaseModel
from optimize_dataclass.io_dataclass import DailyData, DeliveryStatusData, OutputData


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

        # 中間変数
        self.total_overtime = None  # 計画期間全体の残業時間
        self.total_overtime_cost = None  # 計画期間全体の残業時間コスト
        self.total_outsourcing_cost = None  # 計画期間全体の外注費用
        self.total_cost = None  # 計画期間全体のコスト（残業費用+外注費用）
        self.total_move_time = None  # 計画期間全体の移動時間

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
        """
        決定変数の追加
        """
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
                if k.name == self.data.depot_data.name:
                    self.u[d, k.name] = self.model.add_integer_variable(
                        lb=0, ub=0, name=f"u_{d}_{k.name}"
                    )
                else:
                    self.u[d, k.name] = self.model.add_integer_variable(
                        lb=1,
                        ub=len(self.data.list_store_and_depot_data) - 1,
                        name=f"u_{d}_{k.name}",
                    )

        # y
        for d in self.data.list_delivery_date:
            for r in self.data.list_order_name:
                self.y[d, r] = self.model.add_binary_variable(name=f"y_{d}_{r}")

        # h
        for d in self.data.list_delivery_date:
            self.h[d] = self.model.add_variable(name=f"h_{d}", lb=0)

        # total_overtime
        self.total_overtime = self._add_intermediate_variable(
            sum([self.h[d] for d in self.data.list_delivery_date]), "total_overtime"
        )
        # total_overtime_cost
        self.total_overtime_cost = self._add_intermediate_variable(
            self.config.overtime_cost_per_hour * self.total_overtime,
            "total_overtime_cost",
        )

        # total_outsourcing_cost
        self.total_outsourcing_cost = self._add_intermediate_variable(
            sum(
                [
                    self.config.outsourcing_cost_per_weight
                    * self.data.order_name2data[r].weight
                    * (1 - sum([self.y[d, r] for d in self.data.list_delivery_date]))
                    for r in self.data.list_order_name
                ]
            ),
            "outsourcing_cost",
        )

        # total_cost
        self.total_cost = self._add_intermediate_variable(
            self.total_overtime_cost + self.total_outsourcing_cost, "total_cost"
        )

        # total_move_time
        self.total_move_time = self._add_intermediate_variable(
            sum(
                [
                    self.data.move_time_matrix[k1.name, k2.name]
                    * self.x[d, k1.name, k2.name]
                    for d in self.data.list_delivery_date
                    for k1 in self.data.list_store_and_depot_data
                    for k2 in self.data.list_store_and_depot_data
                ]
            ),
            "total_move_time",
        )

        return self

    def add_constraints(self):
        """
        制約条件の追加
        """
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
                - self.config.standartd_work_time
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
        各配送日について、荷物の重量は所定の値以下に抑える制約条件
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
        """
        残業時間を所定の値以下に抑える制約条件
        """
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
        """
        最適化の実行
        """

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
        """
        OutputDataへの整形
        """

        date2daily_data = {}

        for d in self.data.list_delivery_date:
            list_adjacent = [
                (k1.name, k2.name)
                for k1 in self.data.list_store_and_depot_data
                for k2 in self.data.list_store_and_depot_data
                if self.result.variable_values(self.x[d, k1.name, k2.name]) > 0.5
            ]
            # 移動する地点の順番のリストを作成
            tar = self.data.depot_data.name
            route = [tar]
            tmp_list = list_adjacent.copy()
            while len(tmp_list) >= 1:
                for k1, k2 in tmp_list:
                    if k1 == tar:
                        tar = k2
                        route.append(k2)
                        tmp_list.remove((k1, k2))

            list_derivery_route = (
                [self.data.depot_data]
                + [self.data.store_name2data[k] for k in route[1:-1]]
                + [self.data.depot_data]
            )

            daily_move_time = sum(
                [self.data.move_time_matrix[k1, k2] for k1, k2 in list_adjacent]
            )
            daily_total_weight = sum(
                [
                    self.result.variable_values(self.y[d, r])
                    * self.data.order_name2data[r].weight
                    for r in self.data.list_order_name
                ]
            )
            daily_overtime = self.result.variable_values(self.h[d])
            daily_overtime_cost = self.config.overtime_cost_per_hour * daily_overtime

            date2daily_data[d] = DailyData(
                list_delivery_route=list_derivery_route,
                daily_total_weight=daily_total_weight,
                daily_overtime=daily_overtime,
                daily_overtime_cost=daily_overtime_cost,
                daily_move_time=daily_move_time,
            )

        order_name2delivery_status_data = {}
        for r in self.data.list_order_name:
            delivered_date = [
                d
                for d in self.data.list_delivery_date
                if self.result.variable_values(self.y[d, r]) > 0.5
            ]
            if len(delivered_date) > 0:
                order_name2delivery_status_data[r] = DeliveryStatusData(
                    delivered_date=delivered_date[0],
                    outsourced_flag=False,
                    outsourcing_cost=None,
                )

            else:
                outsourcing_cost = (
                    self.config.outsourcing_cost_per_weight
                    * self.data.order_name2data[r].weight
                )
                order_name2delivery_status_data[r] = DeliveryStatusData(
                    delivered_date=None,
                    outsourced_flag=True,
                    outsourcing_cost=outsourcing_cost,
                )

        return OutputData(
            date2daily_data=date2daily_data,
            order_name2delivery_status_data=order_name2delivery_status_data,
            total_cost=self.result.variable_values(self.total_cost),
            total_overtime=self.result.variable_values(self.total_overtime),
            total_overtime_cost=self.result.variable_values(self.total_overtime_cost),
            total_outsourcing_cost=self.result.variable_values(
                self.total_outsourcing_cost
            ),
            total_move_time=self.result.variable_values(self.total_move_time),
        )
