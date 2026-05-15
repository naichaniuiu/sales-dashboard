# -*- coding: utf-8 -*-
import pandas as pd
import os

base = r'C:/Users/wm881/Downloads'
df_all = pd.read_excel(os.path.join(base, '业绩 欠款看板.xlsx'), sheet_name=None)

# 读取25财年Q1和26财年Q1数据
df_25 = df_all['25财年Q1业绩']
df_26 = df_all['26财年Q1业绩']

# 筛选中西部大区的数据
df_25_中西部 = df_25[df_25['一级部门'] == '中西部大区'].copy()
df_26_中西部 = df_26[df_26['一级部门'] == '中西部大区'].copy()

print('25财年Q1中西部大区数据行数:', len(df_25_中西部))
print('26财年Q1中西部大区数据行数:', len(df_26_中西部))

# 查看有哪些部门
print('\n25财年Q1 二级部门:')
print(df_25_中西部['二级部门'].unique())
print('\n26财年Q1 二级部门:')
print(df_26_中西部['二级部门'].unique())

# 按二级部门汇总业绩
df_25_汇总 = df_25_中西部.groupby('二级部门')['业绩总金额'].sum().reset_index()
df_25_汇总.columns = ['部门', '25Q1业绩']

df_26_汇总 = df_26_中西部.groupby('二级部门')['业绩总金额'].sum().reset_index()
df_26_汇总.columns = ['部门', '26Q1业绩']

# 合并对比
df_compare = pd.merge(df_25_汇总, df_26_汇总, on='部门', how='outer').fillna(0)
df_compare['同比'] = df_compare['26Q1业绩'] - df_compare['25Q1业绩']
df_compare['同比%'] = ((df_compare['26Q1业绩'] / df_compare['25Q1业绩']) - 1) * 100

print('\n=== 25 vs 26 财年Q1 部门业绩对比 ===')
print(df_compare.to_string(index=False))

# 保存到Excel
output_path = r'C:/Users/wm881/WorkBuddy/20260513090923/中西部25vs26Q1对比.xlsx'
df_compare.to_excel(output_path, index=False)
print(f'\n数据已保存到: {output_path}')
