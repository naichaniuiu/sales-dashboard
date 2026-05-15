# -*- coding: utf-8 -*-
"""
读取 业绩 欠款看板.xlsx 的所有工作表名称和结构
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd

path = r'C:/Users/wm881/Downloads/业绩 欠款看板.xlsx'

xl = pd.ExcelFile(path)
print("所有工作表:")
for name in xl.sheet_names:
    print(f"  - {name}")

print()
for name in xl.sheet_names:
    df = pd.read_excel(path, sheet_name=name, nrows=3)
    print(f"【{name}】 shape={df.shape}")
    print(f"  列名: {list(df.columns)}")
    print()
