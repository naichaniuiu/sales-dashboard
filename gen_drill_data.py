# -*- coding: utf-8 -*-
"""
生成欠款和业绩的二级下钻数据
- debt_drill.json:  按部门->销售员->客户的欠款账龄分布
- perf_drill.json:  按部门->销售员->客户的业绩明细
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import pandas as pd
from collections import defaultdict

REGION = '中西部大区'
EXCEL = r'C:\Users\wm881\Downloads\业绩 欠款看板.xlsx'
OUT_DIR = r'C:\Users\wm881\WorkBuddy\20260513090923'

# ========== 1. 欠款下钻数据 ==========
print("=== 生成欠款下钻数据 ===")
df_debt = pd.read_excel(EXCEL, sheet_name='欠款数据 ')
df_debt = df_debt[df_debt['一级部门'] == REGION].copy()

# 确保数值字段
df_debt['欠款天数'] = pd.to_numeric(df_debt['欠款天数'], errors='coerce').fillna(0)
df_debt['欠款金额'] = pd.to_numeric(df_debt['欠款金额'], errors='coerce').fillna(0)
df_debt['客户名称'] = df_debt['客户名称'].fillna('未知客户').astype(str).str.strip()
df_debt['销售员名称'] = df_debt['销售员名称'].fillna('').astype(str).str.strip()
df_debt = df_debt[df_debt['销售员名称'] != '']

# 账龄分类
def classify(days):
    if days <= 30: return 'd30'
    elif days <= 90: return 'd30_90'
    elif days <= 180: return 'd90_180'
    else: return 'd180'

# 按部门→销售员→客户→账龄 汇总（万元）
debt_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
    'd30': 0.0, 'd30_90': 0.0, 'd90_180': 0.0, 'd180': 0.0, 'max_days': 0
})))

for _, row in df_debt.iterrows():
    dept = row['三级部门']
    sales = row['销售员名称']
    client = row['客户名称']
    days = row['欠款天数']
    amt = row['欠款金额'] / 10000  # 元→万元

    bucket = classify(days)
    entry = debt_map[dept][sales][client]
    entry[bucket] += amt
    entry['max_days'] = max(entry['max_days'], days)

# 组装 debt_drill.json
debt_drill = {}
total_debt = 0
total_custs = 0

for dept in sorted(str(k) for k in debt_map.keys() if pd.notna(k)):
    sales_list = []
    for sales_name in sorted(str(k) for k in debt_map[dept].keys() if pd.notna(k)):
        cust_list = []
        s_d30 = s_d30_90 = s_d90_180 = s_d180 = 0.0

        for client_name in sorted(str(k) for k in debt_map[dept][sales_name].keys() if pd.notna(k)):
            c = debt_map[dept][sales_name][client_name]
            c_total = round(c['d30'] + c['d30_90'] + c['d90_180'] + c['d180'], 2)
            s_d30 += c['d30']
            s_d30_90 += c['d30_90']
            s_d90_180 += c['d90_180']
            s_d180 += c['d180']
            cust_list.append({
                'name': client_name,
                'd30': round(c['d30'], 2),
                'd30_90': round(c['d30_90'], 2),
                'd90_180': round(c['d90_180'], 2),
                'd180': round(c['d180'], 2),
                'total': c_total,
                'max_days': int(c['max_days'])
            })

        # 按欠款总额降序
        cust_list.sort(key=lambda x: x['total'], reverse=True)
        s_total = round(s_d30 + s_d30_90 + s_d90_180 + s_d180, 2)
        sales_list.append({
            'name': sales_name,
            'd30': round(s_d30, 2),
            'd30_90': round(s_d30_90, 2),
            'd90_180': round(s_d90_180, 2),
            'd180': round(s_d180, 2),
            'total': s_total,
            'cust_count': len(cust_list),
            'custs': cust_list
        })
        total_custs += len(cust_list)

    # 按销售员欠款降序
    sales_list.sort(key=lambda x: x['total'], reverse=True)
    debt_drill[dept] = sales_list
    total_debt += sum(s['total'] for s in sales_list)

with open(f'{OUT_DIR}/debt_drill.json', 'w', encoding='utf-8') as f:
    json.dump(debt_drill, f, ensure_ascii=False, indent=2)

dept_count = len(debt_drill)
sales_count = sum(len(v) for v in debt_drill.values())
print(f"[OK] debt_drill.json ({dept_count}个部门, {sales_count}个销售员, {total_custs}个客户)")
print(f"  欠款合计: {total_debt:.2f}万")

# ========== 2. 业绩下钻数据 ==========
print("\n=== 生成业绩下钻数据 ===")
df_perf = pd.read_excel(EXCEL, sheet_name='26财年Q1业绩')
df_perf = df_perf[df_perf['一级部门'] == REGION].copy()

# 只统计在职销售员
df_perf_active = df_perf[df_perf['销售员状态'] == '在职'].copy()
df_perf_active['客户名称'] = df_perf_active['客户名称'].fillna('未知客户').astype(str).str.strip()
df_perf_active['销售员名称'] = df_perf_active['销售员名称'].fillna('').astype(str).str.strip()
df_perf_active = df_perf_active[df_perf_active['销售员名称'] != '']

# 确保数值字段
df_perf_active['业绩总金额'] = pd.to_numeric(df_perf_active['业绩总金额'], errors='coerce').fillna(0)
df_perf_active['回款金额'] = pd.to_numeric(df_perf_active['回款金额'], errors='coerce').fillna(0)

perf_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
    'perf': 0.0, 'collect': 0.0, 'orders': 0
})))

for _, row in df_perf_active.iterrows():
    dept = row['三级部门']
    sales = row['销售员名称']
    client = row['客户名称']
    perf_amt = float(row['业绩总金额']) / 10000  # 元→万元
    coll_amt = float(row['回款金额']) / 10000
    orders = 1

    entry = perf_map[dept][sales][client]
    entry['perf'] += perf_amt
    entry['collect'] += coll_amt
    entry['orders'] += orders

# 组装 perf_drill.json
perf_drill = {}
total_perf = 0
total_custs_perf = 0

for dept in sorted(str(k) for k in perf_map.keys() if pd.notna(k)):
    sales_list = []
    for sales_name in sorted(str(k) for k in perf_map[dept].keys() if pd.notna(k)):
        cust_list = []
        s_perf = s_coll = 0

        for client_name in sorted(str(k) for k in perf_map[dept][sales_name].keys() if pd.notna(k)):
            c = perf_map[dept][sales_name][client_name]
            cust_list.append({
                'name': client_name,
                'perf': round(c['perf'], 2),
                'collect': round(c['collect'], 2),
                'orders': c['orders']
            })
            s_perf += c['perf']
            s_coll += c['collect']

        cust_list.sort(key=lambda x: x['perf'], reverse=True)
        sales_list.append({
            'name': sales_name,
            'total': round(s_perf, 2),
            'collect': round(s_coll, 2),
            'cust_count': len(cust_list),
            'custs': cust_list
        })
        total_custs_perf += len(cust_list)

    sales_list.sort(key=lambda x: x['total'], reverse=True)
    perf_drill[dept] = sales_list
    total_perf += sum(s['total'] for s in sales_list)

with open(f'{OUT_DIR}/perf_drill.json', 'w', encoding='utf-8') as f:
    json.dump(perf_drill, f, ensure_ascii=False, indent=2)

dept_count_p = len(perf_drill)
sales_count_p = sum(len(v) for v in perf_drill.values())
print(f"[OK] perf_drill.json ({dept_count_p}个部门, {sales_count_p}个销售员, {total_custs_perf}个客户)")
print(f"  业绩合计: {total_perf:.2f}万")
print("\n全部下钻数据生成完成!")
