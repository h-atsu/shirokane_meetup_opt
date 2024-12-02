from pathlib import Path
from typing import Literal

ROOT = Path(__file__).parent.parent

# 解のステータス
SolutionStatus = Literal["Optimal", "Feasible", "NotSolved", "Unbounded", "Undefined"]
