# 配送最適化問題の定式化

## 集合

* $D$ : 配送日の集合
* $p$ : 配送センター（デポ）
* $S$ : お店の集合
* $K = \{p\} \cup S$ : 地点の集合（配送センターとお店）
* $R$ : 荷物の集合

## パラメータ

* $c^{\mathrm{ot}}$ : 1時間あたりの残業コスト
* $c^{\mathrm{out}}$ : 単位重量あたりの外注コスト
* $w_r$ : 荷物 $r$ の重量
* $t_{k_1,k_2}$ : 地点 $k_1$ から地点 $k_2$ への移動時間
* $T^{\mathrm{std}}$ : 標準労働時間（8時間）
* $T^{\mathrm{max}}$ : 最大残業時間
* $W^{\mathrm{max}}$ : トラックの最大積載量
* $[a_r, b_r]$ : 荷物 $r$ の配送可能期間

## 決定変数

* $x_{d,k_1,k_2} \in \{0,1\}$ : 配送日 $d$ に地点 $k_1$ から地点 $k_2$ へ移動する場合1、そうでない場合0
* $u_{d,k} \in \mathbb{Z}_{\geq 0}$ : 配送日 $d$ における地点 $k$ の訪問順序
* $y_{d,r} \in \{0,1\}$ : 配送日 $d$ に荷物 $r$ を自社配送する場合1、そうでない場合0
* $h_d \geq 0$ : 配送日 $d$ の残業時間

## 中間変数

* $H$ : 計画期間全体の残業時間
* $C^{\mathrm{ot}}$ : 計画期間全体の残業コスト
* $C^{\mathrm{out}}$ : 計画期間全体の外注コスト
* $C^{\mathrm{total}}$ : 総コスト（残業コスト + 外注コスト）
* $T^{\mathrm{total}}$ : 計画期間全体の総移動時間

## 目的関数

総コストの最小化：

$$
\begin{align*}
\min \ C^{\mathrm{total}} = C^{\mathrm{ot}} + C^{\mathrm{out}}
\end{align*}
$$

## 制約条件

1. 各地点の入出次数が等しい：

$$
\sum_{k_2 \in K} x_{d,k_1,k_2} = \sum_{k_2 \in K} x_{d,k_2,k_1} \quad \forall d \in D, k_1 \in K
$$

2. 各地点への訪問は1日1回まで：

$$
\sum_{k_2 \in K} x_{d,k_2,k_1} \leq 1 \quad \forall d \in D, k_1 \in K
$$

3. 部分巡回路の禁止（MTZ制約）：

$$
u_{d,s_1} + 1 \leq u_{d,s_2} + (|S|-1)(1-x_{d,s_1,s_2}) \quad \forall d \in D, s_1,s_2 \in S
$$

4. 各荷物の自社配送は期間内で高々1回：

$$
\sum_{d \in D} y_{d,r} \leq 1 \quad \forall r \in R
$$

5. 荷物を自社配送する場合は配送先への訪問が必要：

$$
y_{d,r} \leq \sum_{k \in K} x_{d,k,\mathrm{dest}(r)} \quad \forall d \in D, r \in R
$$

6. 残業時間の定義：

$$
\sum_{k_1 \in K}\sum_{k_2 \in K} t_{k_1,k_2}x_{d,k_1,k_2} - T^{\mathrm{std}} \leq h_d \quad \forall d \in D
$$

7. 配送可能期間の制約：

$$
y_{d,r} = 0 \quad \forall d \not\in [a_r, b_r], r \in R
$$

8. トラック容量制約（オプション）：

$$
\sum_{r \in R} w_r y_{d,r} \leq W^{\mathrm{max}} \quad \forall d \in D
$$

9. 最大残業時間制約（オプション）：

$$
h_d \leq T^{\mathrm{max}} \quad \forall d \in D
$$

## 中間変数の定義

1. 総残業時間：

$$
H = \sum_{d \in D} h_d
$$

2. 総残業コスト：

$$
C^{\mathrm{ot}} = c^{\mathrm{ot}}H
$$

3. 総外注コスト：

$$
C^{\mathrm{out}} = \sum_{r \in R} c^{\mathrm{out}}w_r(1-\sum_{d \in D} y_{d,r})
$$

4. 総移動時間：

$$
T^{\mathrm{total}} = \sum_{d \in D}\sum_{k_1 \in K}\sum_{k_2 \in K} t_{k_1,k_2}x_{d,k_1,k_2}
$$


