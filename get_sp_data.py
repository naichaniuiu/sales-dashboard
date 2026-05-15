# -*- coding: utf-8 -*-
"""
查看各工作表中一级部门/区域的分布情况
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np

path = r'C:/Users/wm881/Downloads/业绩 欠款看板.xlsx'

# 1. 查看26财年Q1业绩中的一级部门
df26 = pd.read_excel(path, sheet_name='26财年Q1业绩')
print("=== 26财年Q1业绩 - 一级部门分布 ===")
depts = df26['一级部门'].value_counts()
for dept, cnt in depts.items():
    amt = df26[df26['一级部门']==dept]['业绩总金额'].sum() / 10000
    print(f"  {dept}: {cnt}条记录, 业绩{amt:.2f}万")

print()

# 2. 查看25财年Q1业绩中的一级部门
df25 = pd.read_excel(path, sheet_name='25财年Q1业绩')
print("=== 25财年Q1业绩 - 一级部门分布 ===")
depts25 = df25['一级部门'].value_counts()
for dept, cnt in depts25.items():
    amt = df25[df25['一级部门']==dept]['业绩总金额'].sum() / 10000
    print(f"  {dept}: {cnt}条记录, 业绩{amt:.2f}万")

print()

# 3. 查看欠款数据中的一级部门
df_debt = pd.read_excel(path, sheet_name='欠款数据 ')
print("=== 欠款数据 - 一级部门分布 ===")
depts_debt = df_debt['一级部门'].value_counts()
for dept, cnt in depts_debt.items():
    amt = df_debt[df_debt['一级部门']==dept]['欠款金额'].sum() / 10000
    print(f"  {dept}: {cnt}条记录, 欠款{amt:.2f}万")

print()

# 4. 查看业绩目标中的区域
df_target = pd.read_excel(path, sheet_name='26财年业绩目标季度拆分')
print("=== 26财年业绩目标 - 区域分布 ===")
print(df_target[['区域','26财年Q1']].to_string(index=False))
