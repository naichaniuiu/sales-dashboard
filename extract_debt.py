# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
import json

path = r'C:/Users/wm881/Downloads/业绩 欠款看板.xlsx'
REGION = '中西部大区'

df_debt = pd.read_excel(path, sheet_name='欠款数据 ')
df_debt_r = df_debt[df_debt['一级部门'] == REGION].copy()

# 只取欠款金额 > 0 的记录
df_pos = df_debt_r[pd.to_numeric(df_debt_r['欠款金额'],errors='coerce') > 0].copy()
df_pos['欠款金额'] = pd.to_numeric(df_pos['欠款金额'], errors='coerce')
days = pd.to_numeric(df_pos['天数'], errors='coerce')
df_pos['账龄区间'] = pd.cut(days, bins=[0,30,90,180,9999],
                            labels=['30天内','30-90天','90-180天','180天以上'])

# 按部门+账龄汇总
pivot = df_pos.pivot_table(index='三级部门', columns='账龄区间', 
                            values='欠款金额', aggfunc='sum', fill_value=0) / 10000
pivot['合计'] = pivot.sum(axis=1)
pivot = pivot.sort_values('合计', ascending=False)

print("=== 各部门分账龄欠款（万元）===")
print(pivot.to_string())

print()
print("=== 高风险客户（90天以上，前15名）===")
risky = df_pos[days > 90].groupby('客户名称')['欠款金额'].sum() / 10000
risky = risky.sort_values(ascending=False).head(15)
for c, v in risky.items():
    row = df_pos[df_pos['客户名称']==c].iloc[0]
    print(f"  {c}（{row['三级部门']}）: {v:.2f}万")

# 回款周期（用天数字段，欠款金额加权）
print()
print("=== 各部门加权回款周期 ===")
cycle_dict = {}
for dept, grp in df_pos.groupby('三级部门'):
    total_amt = grp['欠款金额'].sum()
    weighted = (grp['欠款金额'] * pd.to_numeric(grp['天数'],errors='coerce')).sum()
    cycle = weighted / total_amt if total_amt > 0 else 0
    cycle_dict[dept] = round(cycle, 1)
    print(f"  {dept}: {cycle:.1f}天（加权）")

# 认款数据
df_receipt = pd.read_excel(path, sheet_name='26财年Q1认款数据')
df_receipt_r = df_receipt[df_receipt['一级部门'] == REGION].copy()
receipt_by_dept = df_receipt_r.groupby('三级部门')['认款协同金额'].sum() / 10000
print()
print("=== 各部门认款金额（万元）===")
for d, v in receipt_by_dept.sort_values(ascending=False).items():
    print(f"  {d}: {v:.2f}万")

# 保存所有数据
ages = ['30天内','30-90天','90-180天','180天以上']
dept_debt_age = {}
for dept in pivot.index:
    dept_debt_age[dept] = {}
    for ag in ages:
        dept_debt_age[dept][ag] = round(float(pivot.loc[dept, ag]) if ag in pivot.columns else 0, 2)
    dept_debt_age[dept]['合计'] = round(float(pivot.loc[dept, '合计']), 2)

result = {
    'dept_debt_age': dept_debt_age,
    'age_dist': {ag: round(float(df_pos[df_pos['账龄区间']==ag]['欠款金额'].sum()/10000), 2) for ag in ages},
    'cycle': cycle_dict,
    'receipt': {d: round(float(v),2) for d,v in receipt_by_dept.items()},
    'risky_clients': [
        {'name': c, 'amount': round(float(v),2), 
         'dept': df_pos[df_pos['客户名称']==c].iloc[0]['三级部门']}
        for c, v in risky.items()
    ]
}

with open(r'C:/Users/wm881/WorkBuddy/20260513090923/debt_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\n✅ 已保存 debt_data.json")
