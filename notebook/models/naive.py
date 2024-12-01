# %%
from datetime import timedelta

import matplotlib.pyplot as plt
import polars as pl
from ortools.math_opt.python import mathopt

from consts import ROOT

# %%
# DATA_DIR = ROOT / "data" / "small_dataset"
DATA_DIR = ROOT / "data" / "raw_data_from_book" / "small_dataset"

df_locations = pl.read_csv(DATA_DIR / "locations.csv")
print(len(df_locations))
df_locations.head()

# %%


fig = plt.subplot()
fig.set_aspect("equal")
for row in df_locations.to_pandas().itertuples():
    if row.depo_flag:
        fig.scatter(row.x, row.y, marker="o")
    else:
        fig.scatter(row.x, row.y, marker="x")
    fig.annotate(row.k, (row.x, row.y + 0.1))
plt.show()

# %%
df_distances = pl.read_csv(DATA_DIR / "distances.csv")
print(len(df_distances))
df_distances.head()

# %%
df_orders = pl.read_csv(DATA_DIR / "orders.csv")
print(len(df_orders))
df_orders.head()

# %% [markdown]
# ### ③素朴な数理モデルの実装と確認（小規模データ）

# %%
# 配送日のリスト
D = list(range(df_orders["b"].min(), df_orders["e"].max() + 1))

# 配送センター
p = df_locations.filter(pl.col("depo_flag") == 1)["k"].to_list()[0]

# お店のリスト
S = df_locations.filter(pl.col("depo_flag") == 0)["k"].to_list()

# 地点のリスト
K = [p] + S

# 荷物のリスト
R = df_orders["r"].to_list()

# %%
# 荷物に紐づける配送先のお店
R2S = dict(df_orders.select(["r", "s"]).iter_rows())

# 荷物に紐づける重量
R2W = dict(df_orders.select(["r", "w"]).iter_rows())

# 荷物に紐づける指定配送期間の開始日
R2B = dict(df_orders.select(["r", "b"]).iter_rows())

# 荷物に紐づける指定配送期間の終了日
R2E = dict(df_orders.select(["r", "e"]).iter_rows())

# 地点間の移動時間
KK2T = {(k1, k2): t for k1, k2, t in df_distances.select(["k1", "k2", "t"]).iter_rows()}

# %%

print("R2S:", R2S)
print("R2W:", R2W)
print("R2B:", R2B)
print("R2E:", R2E)
print("KK2T:", KK2T)

# %% [markdown]
# ### ☆「素朴な数理モデル」の実装

# %%

model = mathopt.Model(name="VRP")

# %%


def add_variable(
    model: mathopt.Model, constraints: mathopt.LinearExpression, name: str
) -> mathopt.Variable:
    """
    中間変数を定義するために変数を宣言して制約条件として追加するための関数
    """
    ret = model.add_variable(name=name)
    model.add_linear_constraint(ret == constraints)
    return ret


# x = pulp.LpVariable.dicts("x", DKK, cat="Binary")
# u = pulp.LpVariable.dicts("u", DK, cat="Integer", lowBound=0)
# y = pulp.LpVariable.dicts("y", DR, cat="Binary")
# h = pulp.LpVariable.dicts("h", D, cat="Continuous", lowBound=0)


x = {}
u = {}
y = {}
h = {}

for d in D:
    for k1 in K:
        for k2 in K:
            x[d, k1, k2] = model.add_binary_variable(name=f"x_{d}_{k1}_{k2}")

for d in D:
    for k in K:
        u[d, k] = model.add_integer_variable(lb=0, name=f"u_{d}_{k}")

for d in D:
    for r in R:
        y[d, r] = model.add_binary_variable(name=f"y_{d}_{r}")


for d in D:
    h[d] = model.add_variable(name=f"h_{d}", lb=0)

# %%
for d in D:
    for k1 in K:
        model.add_linear_constraint(
            sum(x[d, k1, k2] for k2 in K) == sum(x[d, k2, k1] for k2 in K)
        )

    # (A-2) 各配送日について、地点に訪問する数は高々1回まで
    model.add_linear_constraint(sum([x[d, k2, k1] for k2 in K]) <= 1)

for d in D:
    # (B-1) 各配送日について、配送センターは出発地点(0番目に訪問)
    model.add_linear_constraint(u[d, p] == 0)

    # (B-3) 各配送日について、お店間だけのサイクルを禁止
    for s1 in S:
        for s2 in S:
            model.add_linear_constraint(
                u[d, s1] + 1 <= u[d, s2] + (len(K) - 1) * (1 - x[d, s1, s2])
            )

# (C) 各荷物は、自社配送するなら期間内で高々1回まで
for r in R:
    model.add_linear_constraint(sum([y[d, r] for d in D]) <= 1)

# (D) 各配送日について、荷物を自社配送するなら、配送先のお店に訪問
for d in D:
    for r in R:
        tar_s = R2S[r]
        model.add_linear_constraint(y[d, r] <= sum(x[d, k, tar_s] for k in K))

# (E) 各配送日について、荷物の重量は4,000[kg]以下
for d in D:
    model.add_linear_constraint(sum([y[d, r] * R2W[r] for r in R]) <= 4000)

# (F) 各配送日について、ドライバーの残業時間は所定労働時間の8時間を差し引いた労働時間
for d in D:
    model.add_linear_constraint(
        sum([KK2T[k1, k2] * x[d, k1, k2] for k1 in K for k2 in K]) - 8 <= h[d]
    )

# (G) 各配送日について、ドライバーの残業時間は3時間以内
for d in D:
    model.add_linear_constraint(h[d] <= 3)

# (H) 各荷物は指定配送期間外の配送を禁止
for r in R:
    for d in D:
        if d < R2B[r]:
            model.add_linear_constraint(y[d, r] == 0)
        if R2E[r] < d:
            model.add_linear_constraint(y[d, r] == 0)

# (I) 配送費用（残業費用+外注費用）を最小化する
zangyo = add_variable(model, sum([3000 * h[d] for d in D]), "zangyo")
gaityu = add_variable(
    model, sum([46 * R2W[r] * (1 - sum(y[d, r] for d in D)) for r in R]), "gaityu"
)
model.minimize(zangyo + gaityu)

# %%
# 求解（明示的にCBCソルバーを指定する）
params = mathopt.SolveParameters(
    time_limit=timedelta(seconds=60),
    enable_output=True,
    threads=4,
)
result = mathopt.solve(model, mathopt.SolverType.GSCIP, params=params)


# %%$
# 結果の表示
print(f"残業費用:{result.variable_values(zangyo):.0f}[円]")
print(f"外注費用:{result.variable_values(gaityu):.0f}[円]")
print(
    f"費用合計:{result.variable_values(zangyo) + result.variable_values(gaityu):.0f}[円]"
)

# %%
for d in D:
    X = [(k1, k2) for k1 in K for k2 in K if result.variable_values(x[d, k1, k2]) == 1]

    time = sum([KK2T[k1, k2] for k1, k2 in X])
    print(f"---配送日:{d}日目---")
    print(f"配送重量:{sum([result.variable_values(y[d,r]) * R2W[r] for r in R])}[kg]")
    print(f"移動時間:{time:.2f}[h]")
    print(f"残業時間:{result.variable_values(h[d]):.2f}[h]")
    print("x:", X)

    # 移動する地点の順番のリストを作成
    tar = p
    Route = [p]
    while len(X) >= 1:
        for k1, k2 in X:
            if k1 == tar:
                tar = k2
                Route.append(k2)
                X.remove((k1, k2))

    print("u:", [result.variable_values(u[d, k]) for k in Route])
    print("配送ルート:", "->".join(Route))

# %%
for r in R:
    # 自社トラックで配送したかどうかのフラグ
    owned_truck_flag = sum([result.variable_values(y[d, r]) for d in D])
    if owned_truck_flag:
        # 配送日の取得
        tar_d = [d for d in D if result.variable_values(y[d, r]) == 1][0]
        text = f"荷物{r}(お店{R2S[r]},{R2W[r]}[kg])-配送日:{tar_d}日目"
    else:
        # 外注費用の取得
        gc = 46 * R2W[r]
        text = f"荷物{r}(お店{R2S[r]},{R2W[r]}[kg])-外注費用:{gc}[円]"
    print(text)
# %%
