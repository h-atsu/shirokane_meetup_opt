# %%
from datetime import timedelta
from itertools import combinations

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
def add_variable(
    model: mathopt.Model, constraints: mathopt.LinearExpression, name: str
) -> mathopt.Variable:
    """
    中間変数を定義するために変数を宣言して制約条件として追加するための関数
    """
    ret = model.add_variable(name=name)
    model.add_linear_constraint(ret == constraints)
    return ret


def tsp(p_, S_, KK2T_):
    K = [p_] + S_
    model = mathopt.Model(name="TSP")
    x = {}
    u = {}

    for k1 in K:
        for k2 in K:
            x[k1, k2] = model.add_binary_variable(name=f"x_{k1}_{k2}")

    for k in K:
        u[k] = model.add_integer_variable(lb=0, ub=len(K) - 1, name=f"u_{k}")
    # x = pulp.LpVariable.dicts("x", KK, cat="Binary")
    # u = pulp.LpVariable.dicts("u", K, cat="Integer", lowBound=0)

    # 各地点に必ず1回訪問する
    for k1 in K:
        model.add_linear_constraint(
            sum([x[k1, k2] for k2 in K]) == 1,
        )
        model.add_linear_constraint(
            sum([x[k2, k1] for k2 in K]) == 1,
        )

    # (B-1)
    model.add_linear_constraint(u[p_] == 0)

    # (B-3)
    for s1 in S_:
        for s2 in S_:
            model.add_linear_constraint(
                u[s1] + 1 <= u[s2] + (len(K) - 1) * (1 - x[s1, s2]),
            )

    # 移動時間は11時間以内
    model.add_linear_constraint(
        sum([KK2T_[k1, k2] * x[k1, k2] for k1 in K for k2 in K]) <= 11,
    )

    # 目的関数は移動時間の最小化
    total_time = add_variable(
        model, sum([KK2T_[k1, k2] * x[k1, k2] for k1 in K for k2 in K]), "total_time"
    )
    model.minimize(
        total_time,
    )

    params = mathopt.SolveParameters(
        time_limit=timedelta(seconds=60),
        enable_output=False,
        threads=4,
    )
    result = mathopt.solve(model, mathopt.SolverType.GSCIP, params=params)

    if result.termination.reason == mathopt.TerminationReason.OPTIMAL:
        X = [(k1, k2) for k1 in K for k2 in K if result.variable_values(x[k1, k2]) == 1]
        objective_value = result.objective_value()

    else:
        X = []
        total_time = -1
        objective_value = -1
    return result.termination.reason, X, objective_value


# %%
testS = ["s1", "s2", "s3"]
status, X, time = tsp(p, testS, KK2T)
print("x:", X)
print("移動時間:", time)

Stp2Pat = {}
for n in range(len(S) + 1):
    # お店の集合Sからn個選ぶ組合せを列挙
    count = 0
    for Stp in combinations(S, n):  # 辞書式で列挙される
        # 配送センターpとn個のお店(Stp)の巡回セールスマン問題を解く
        status, X, time = tsp(p, list(Stp), KK2T)

        # 解が存在するときのみ配送ルートとして採用
        if status == mathopt.TerminationReason.OPTIMAL:
            Stp2Pat[Stp] = (X, time)
            count += 1
    print(f"訪問するお店の数:{n} 配送ルート数:{count}")
print("要件(ⅰ)(ⅱ)を満たす配送ルート数:", len(Stp2Pat))

# %%
for i, (Stp, Pat) in enumerate(Stp2Pat.items()):
    if i > 3:
        break
    print("---お店の組合せ:", Stp)
    print("配送ルート:", Pat)

# %% [markdown]
# ### （2）ステップ２　効率的な配送パターンの列挙

# %%
# 配送日に対して配送可能な荷物のリストを紐づける辞書
D2R = {d: [] for d in D}
for r in R:
    for d in range(R2B[r], R2E[r] + 1):
        D2R[d].append(r)

# 各配送日に配送可能な荷物のリスト
for d in D:
    print("配送日:", d, D2R[d])

# %%
# 各配送日に紐づける効率的な配送パターンのリスト
D2Pat = {d: [] for d in D}
for d in D:
    # 配送日dに配送可能な荷物のリストを作成
    dayR = D2R[d]

    # 荷物のリストの部分集合を列挙
    for n in range(len(dayR) + 1):
        for tarR in combinations(dayR, n):
            # 要件(iii):荷物の重量の確認
            w = sum([R2W[r] for r in tarR])
            if w > 4000:
                continue

            # 荷物の配送先のお店を抽出
            tarS = set([R2S[r] for r in tarR])
            tarStp = tuple(sorted(tarS))

            # 要件(iv):実行可能な配送ルートとの照合
            if tarStp in Stp2Pat:
                X, time = Stp2Pat[tarStp]
                pat = (X, time, list(tarR))
                D2Pat[d].append(pat)
            else:
                continue
    print(f"配送日:{d} 配送パターン数:{len(D2Pat[d])}")

# %% [markdown]
# ### ②配送パターンを利用した数理モデルの実装・実験・検証

# %%
# 配送日に、配送可能な配送パターンのリストを紐づける辞書
D2Q = {d: [] for d in D}

# 配送パターンに、配送可能な荷物のリストを紐づける辞書
Q2R = {}

# 配送パターンに、移動時間を紐づける辞書
Q2T = {}

# 配送パターンに、残業時間を紐づける辞書
Q2H = {}

# 配送パターンに、配送ルートを紐づける辞書
Q2X = {}

for d in D:
    for q_no, (X, time, tarR) in enumerate(D2Pat[d]):
        q = f"q_{d}_{q_no}"
        D2Q[d].append(q)
        Q2R[q] = tarR
        Q2T[q] = time
        Q2H[q] = max(time - 8, 0)
        Q2X[q] = X
print("配送日1日目の配送パターン:", D2Q[1])


# %% [markdown]
# ### ★「配送パターンを利用した数理モデル」の実装

# %%

model = mathopt.Model(name="Set Cover")


x = {}
y = {}
for d in D:
    for q in D2Q[d]:
        x[d, q] = model.add_binary_variable(name=f"x_{d}_{q}")
for r in R:
    y[r] = model.add_variable(lb=0, ub=1, name=f"y_{r}")

# (A') 各配送日に1つの配送パターンを選択
for d in D:
    model.add_linear_constraint(
        sum([x[d, q] for q in D2Q[d]]) == 1,
    )

# (B') 各荷物は外注するか自社配送のどちらかを選択
for r in R:
    model.add_linear_constraint(
        y[r] + sum([x[d, q] for d in D for q in D2Q[d] if r in Q2R[q]]) == 1,
    )

# (C') 費用合計と移動時間合計の最小化
zangyo = add_variable(
    model,
    sum([3000 * Q2H[q] * x[d, q] for d in D for q in D2Q[d]]),
    "zangyo",
)
gaityu = add_variable(
    model,
    sum([46 * R2W[r] * y[r] for r in R]),
    "gaityu",
)
total_time = add_variable(
    model,
    sum([x[d, q] * Q2T[q] for d in D for q in D2Q[d]]),
    "total_time",
)
model.minimize(zangyo + gaityu + total_time)

# 求解
params = mathopt.SolveParameters(
    time_limit=timedelta(seconds=60),
    enable_output=True,
    threads=4,
)
result = mathopt.solve(model, mathopt.SolverType.GSCIP, params=params)

# 結果の表示
print(f"残業費用:{result.variable_values(zangyo):.0f}[円]")
print(f"外注費用:{result.variable_values(gaityu):.0f}[円]")
print(
    f"費用合計:{result.variable_values(zangyo) + result.variable_values(gaityu):.0f}[円]"
)
print(f"移動時間:{result.variable_values(total_time):.0f}[時間]")

# %%
resD2Q = {d: q for d in D for q in D2Q[d] if result.variable_values(x[d, q]) > 0.99}
for d in D:
    tar_q = resD2Q[d]

    # 移動する地点の順番のリストを作成
    X = Q2X[tar_q].copy()
    tar = p
    Route = [p]
    while len(X) >= 1:
        for k1, k2 in X:
            if k1 == tar:
                tar = k2
                Route.append(k2)
                X.remove((k1, k2))
    print(f"---配送日:{d} 配送パターン:{tar_q}---")
    print(f"移動時間:{Q2T[tar_q]:.2f}[時間]")
    print(f"残業時間:{Q2H[tar_q]:.2f}[時間]")
    print("配送ルート:", "->".join(Route))
    for r in Q2R[tar_q]:
        print(f"荷物{r}-お店{R2S[r]}")

# %%


# 各地点の座標の取得
K2XY = {row.k: (row.x, row.y) for row in df_locations.to_pandas().itertuples()}

fig = plt.figure(figsize=(12, 20))
for i in range(len(D)):
    d = D[i]
    tar_q = resD2Q[d]
    X = Q2X[tar_q]
    routeK = [k1 for k1, k2 in X]
    time = Q2T[tar_q]
    title_text = f"day:{d}({time:.1f}[h])"

    ax = fig.add_subplot(
        5, 4, i + 1, xlim=(-3.5, 3.5), ylim=(-3.5, 3.5), title=title_text
    )
    ax.set_aspect("equal")

    for row in df_locations.to_pandas().itertuples():
        if row.k in routeK:
            if row.depo_flag:
                ax.scatter(row.x, row.y, marker="o")
            else:
                ax.scatter(row.x, row.y, marker="x")

    for k1, k2 in X:
        (x1, y1) = K2XY[k1]
        (x2, y2) = K2XY[k2]
        ax.arrow(
            x1, y1, (x2 - x1), (y2 - y1), head_width=0.2, length_includes_head=True
        )

# %%
