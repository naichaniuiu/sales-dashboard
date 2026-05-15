# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

path = r'C:/Users/wm881/Downloads/业绩 欠款看板.xlsx'
REGION = '中西部大区'

df_debt = pd.read_excel(path, sheet_name='欠款数据 ')
df_debt_r = df_debt[df_debt['一级部门'] == REGION].copy()

print(f"欠款数据行数: {len(df_debt_r)}")
print()

# 检查关键字段
cols = ['天数', '回款天数', '欠款金额', '提取正负数欠款', '三级部门', '客户名称']
print("=== 前10行关键字段 ===")
print(df_debt_r[cols].head(10).to_string())
print()

# 各字段统计
print("=== 欠款金额统计 ===")
print(f"  欠款金额 sum: {df_debt_r['欠款金额'].sum()/10000:.2f}万")
print(f"  提取正负数欠款 sum: {df_debt_r['提取正负数欠款'].sum()/10000:.2f}万")
print(f"  欠款金额>0的记录数: {(df_debt_r['欠款金额']>0).sum()}")
print(f"  提取正负数欠款>0的记录数: {(df_debt_r['提取正负数欠款']>0).sum()}")
print()

# 天数分布
print("=== 天数字段分布（前20）===")
print(df_debt_r['天数'].value_counts().head(20))
print()
print(f"  天数 > 0 的记录数: {(pd.to_numeric(df_debt_r['天数'],errors='coerce')>0).sum()}")

# 直接用欠款金额（正值）
df_pos = df_debt_r[pd.to_numeric(df_debt_r['欠款金额'],errors='coerce') > 0].copy()
print(f"\n欠款金额>0的记录: {len(df_pos)}")
print(f"  合计: {df_pos['欠款金额'].sum()/10000:.2f}万")

# 用天数分级
days_col = pd.to_numeric(df_pos['天数'], errors='coerce')
print(f"\n按天数分级（用欠款金额>0的记录）:")
print(f"  30天内: {df_pos[days_col<=30]['欠款金额'].sum()/10000:.2f}万")
print(f"  30-90天: {df_pos[(days_col>30)&(days_col<=90)]['欠款金额'].sum()/10000:.2f}万")
print(f"  90-180天: {df_pos[(days_col>90)&(days_col<=180)]['欠款金额'].sum()/10000:.2f}万")
print(f"  180天以上: {df_pos[days_col>180]['欠款金额'].sum()/10000:.2f}万")

# 各部门欠款
print("\n各部门欠款（欠款金额>0）:")
dept_d = df_pos.groupby('三级部门')['欠款金额'].sum()/10000
for d, v in dept_d.sort_values(ascending=False).items():
    print(f"  {d}: {v:.2f}万")

# 认款数据
df_receipt = pd.read_excel(path, sheet_name='26财年Q1认款数据')
df_receipt_r = df_receipt[df_receipt['一级部门'] == REGION].copy()
print(f"\n认款数据列名: {list(df_receipt_r.columns)}")
print(f"认款数据行数: {len(df_receipt_r)}")

# 检查认款数据中的回款天数
if '审核通过日期' in df_receipt_r.columns and '认款时间' in df_receipt_r.columns:
    print("\n认款数据前5行:")
    print(df_receipt_r[['三级部门','认款协同金额','认款时间','审核通过日期']].head(5).to_string())
