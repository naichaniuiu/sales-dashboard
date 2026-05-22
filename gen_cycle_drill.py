# -*- coding: utf-8 -*-
"""
生成回款周期二级下钻数据
- sales_cycle_data.json: 按部门->销售员的回款周期
- cust_cycle_data.json:  按部门->销售员->客户的回款周期

公式: 回款周期 = (欠款加权天数 + 回款加权天数) / (|欠款总额| + 认款协同金额)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import pandas as pd
from datetime import datetime
from collections import defaultdict

REGION = '中西部大区'
EXCEL = r'C:\Users\wm881\Downloads\业绩 欠款看板.xlsx'
OUT_DIR = r'C:\Users\wm881\WorkBuddy\20260513090923'

# ========== 1. 读取欠款数据 ==========
df_debt = pd.read_excel(EXCEL, sheet_name='欠款数据 ')
df_debt = df_debt[df_debt['一级部门'] == REGION].copy()
df_debt['欠款天数'] = pd.to_numeric(df_debt['欠款天数'], errors='coerce').fillna(0)
df_debt['欠款金额_abs'] = df_debt['欠款金额'].abs()
df_debt['客户名称'] = df_debt['客户名称'].fillna('未知客户').astype(str).str.strip()
df_debt['销售员名称'] = df_debt['销售员名称'].fillna('').astype(str).str.strip()
df_debt = df_debt[df_debt['销售员名称'] != '']

# 按部门->销售员->客户 汇总欠款
debt_map = defaultdict(lambda: defaultdict(lambda: {
    'weighted_days': 0.0, 'total_amt': 0.0, 'client_map': defaultdict(lambda: {
        'weighted_days': 0.0, 'total_amt': 0.0
    })
}))

for _, row in df_debt.iterrows():
    dept = row['三级部门']
    sales = row['销售员名称']
    client = row['客户名称']
    days = row['欠款天数']
    amt = row['欠款金额_abs']

    debt_map[dept][sales]['weighted_days'] += amt * days
    debt_map[dept][sales]['total_amt'] += amt
    debt_map[dept][sales]['client_map'][client]['weighted_days'] += amt * days
    debt_map[dept][sales]['client_map'][client]['total_amt'] += amt

sales_debt_count = sum(len(v) for v in debt_map.values())
print(f"[欠款] 已读取 {sales_debt_count} 个销售员的欠款数据")

# ========== 2. 读取认款数据 ==========
df_rec = pd.read_excel(EXCEL, sheet_name='26财年Q1认款数据')
df_rec = df_rec[df_rec['一级部门'] == REGION].copy()
df_rec['认款协同金额'] = pd.to_numeric(df_rec['认款协同金额'], errors='coerce').fillna(0)
df_rec['回款客户名称'] = df_rec['回款客户名称'].fillna('未知客户').astype(str).str.strip()
df_rec['销售员名称'] = df_rec['销售员名称'].fillna('').astype(str).str.strip()
df_rec = df_rec[df_rec['销售员名称'] != '']

rec_map = defaultdict(lambda: defaultdict(lambda: {
    'weighted_days': 0.0, 'total_amt': 0.0, 'client_map': defaultdict(lambda: {
        'weighted_days': 0.0, 'total_amt': 0.0
    })
}))

for _, row in df_rec.iterrows():
    dept = row['三级部门']
    sales = row['销售员名称']
    client = row['回款客户名称']
    amt = row['认款协同金额']

    perf_date = row.get('业绩日期')
    rec_time = row.get('认款时间')

    if isinstance(perf_date, datetime) and isinstance(rec_time, datetime):
        rec_days = max(0, (rec_time - perf_date).days)
    else:
        rec_days = 0

    rec_map[dept][sales]['weighted_days'] += amt * rec_days
    rec_map[dept][sales]['total_amt'] += amt
    rec_map[dept][sales]['client_map'][client]['weighted_days'] += amt * rec_days
    rec_map[dept][sales]['client_map'][client]['total_amt'] += amt

sales_rec_count = sum(len(v) for v in rec_map.values())
print(f"[认款] 已读取 {sales_rec_count} 个销售员的认款数据")

# ========== 3. 合并计算销售员级回款周期 ==========
all_depts = sorted(set(list(debt_map.keys()) + list(rec_map.keys())))
sales_cycle_data = {}

for dept in all_depts:
    all_sales = sorted(set(list(debt_map[dept].keys()) + list(rec_map[dept].keys())))
    dept_list = []

    for sales_name in all_sales:
        d = debt_map[dept][sales_name]
        rc = rec_map[dept][sales_name]

        debt_w = d['weighted_days']
        debt_a = d['total_amt']
        rec_w = rc['weighted_days']
        rec_a = rc['total_amt']

        total_w = debt_w + rec_w
        total_a = debt_a + rec_a

        cycle = round(total_w / total_a, 1) if total_a > 0 else 0

        dept_list.append({
            'name': sales_name,
            'debt_amt': round(debt_a, 2),
            'rec_amt': round(rec_a, 2),
            'cycle': cycle,
            'debt_weighted': round(debt_w, 2),
            'rec_weighted': round(rec_w, 2)
        })

    dept_list.sort(key=lambda x: x['cycle'], reverse=True)
    sales_cycle_data[dept] = dept_list

with open(f'{OUT_DIR}/sales_cycle_data.json', 'w', encoding='utf-8') as f:
    json.dump(sales_cycle_data, f, ensure_ascii=False, indent=2)

print(f"\n[OK] sales_cycle_data.json ({len(sales_cycle_data)} 个部门)")

# ========== 4. 合并计算客户级回款周期 ==========
cust_cycle_data = {}

for dept in all_depts:
    all_sales = sorted(set(list(debt_map[dept].keys()) + list(rec_map[dept].keys())))
    dept_cust = {}

    for sales_name in all_sales:
        d_clients = debt_map[dept][sales_name]['client_map']
        r_clients = rec_map[dept][sales_name]['client_map']
        all_clients = sorted(set(list(d_clients.keys()) + list(r_clients.keys())))

        cust_list = []
        for cname in all_clients:
            dc = d_clients[cname]
            rc = r_clients[cname]

            debt_w = dc['weighted_days']
            debt_a = dc['total_amt']
            rec_w = rc['weighted_days']
            rec_a = rc['total_amt']

            total_w = debt_w + rec_w
            total_a = debt_a + rec_a

            if total_a > 0:
                cycle = round(total_w / total_a, 1)
            else:
                cycle = 0

            cust_list.append({
                'name': cname,
                'debt_amt': round(debt_a, 2),
                'rec_amt': round(rec_a, 2),
                'cycle': cycle
            })

        cust_list.sort(key=lambda x: x['cycle'], reverse=True)
        dept_cust[sales_name] = cust_list

    cust_cycle_data[dept] = dept_cust

with open(f'{OUT_DIR}/cust_cycle_data.json', 'w', encoding='utf-8') as f:
    json.dump(cust_cycle_data, f, ensure_ascii=False, indent=2)

total_cust = sum(
    sum(len(clients) for clients in sales.values())
    for sales in cust_cycle_data.values()
)
print(f"[OK] cust_cycle_data.json ({total_cust} 条客户记录)")

# ========== 5. 打印验证 ==========
print("\n=== 销售员级回款周期（前5部门）===")
for dept in all_depts[:5]:
    print(f"\n  {dept}:")
    for s in sales_cycle_data[dept][:3]:
        print(f"    {s['name']}: 欠款{s['debt_amt']:.0f}, 认款{s['rec_amt']:.0f}, 周期{s['cycle']}天")
