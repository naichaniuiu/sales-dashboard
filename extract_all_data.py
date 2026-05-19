# -*- coding: utf-8 -*-
"""
提取生成新看板所需的所有数据
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
import json
from datetime import datetime

path = r'C:/Users/wm881/Downloads/业绩 欠款看板.xlsx'
REGION = '中西部大区'

# ===== 读取数据 =====
df26 = pd.read_excel(path, sheet_name='26财年Q1业绩')
df25 = pd.read_excel(path, sheet_name='25财年Q1业绩')
df_debt = pd.read_excel(path, sheet_name='欠款数据 ')
df_receipt = pd.read_excel(path, sheet_name='26财年Q1认款数据')
df_target = pd.read_excel(path, sheet_name='26财年业绩目标季度拆分')

# ===== 1. 业绩数据 - 按三级部门 =====
df26_r = df26[df26['一级部门'] == REGION].copy()
df25_r = df25[df25['一级部门'] == REGION].copy()

perf26 = df26_r.groupby('三级部门')['业绩总金额'].sum() / 10000
perf25 = df25_r.groupby('三级部门')['业绩总金额'].sum() / 10000

print("=== 26财年Q1各部门业绩（万元）===")
for dept, val in perf26.sort_values(ascending=False).items():
    p25 = perf25.get(dept, 0)
    yoy = (val - p25) / p25 * 100 if p25 != 0 else float('nan')
    print(f"  {dept}: 26Q1={val:.2f}, 25Q1={p25:.2f}, 同比={yoy:.1f}%")

print(f"  合计: 26Q1={perf26.sum():.2f}, 25Q1={perf25.sum():.2f}")
print()

# ===== 2. 目标达成率 =====
print("=== 26财年Q1业绩目标（万元）===")
df_target_clean = df_target.dropna(subset=['区域'])
target_dict = {}
for _, row in df_target_clean.iterrows():
    if pd.notna(row['区域']) and pd.notna(row['26财年Q1']):
        target_dict[str(row['区域']).strip()] = float(row['26财年Q1'])
        print(f"  {row['区域']}: {row['26财年Q1']:.0f}万")
print()

# ===== 3. 销售员数量 =====
sales_count = df26_r.groupby('三级部门')['销售员名称'].nunique()
print("=== 各部门销售员数量 ===")
for dept, cnt in sales_count.items():
    print(f"  {dept}: {cnt}人")
print()

# ===== 4. 欠款数据 =====
df_debt_r = df_debt[df_debt['一级部门'] == REGION].copy()

# 欠款金额用 欠款金额 字段（带符号相加，正负相抵）
df_debt_r['欠款净额'] = pd.to_numeric(df_debt_r['欠款金额'], errors='coerce').fillna(0)

# 账龄分级（按天数字段）
def classify_age(days):
    try:
        d = float(days)
        if d <= 30: return '30天内'
        elif d <= 90: return '30-90天'
        elif d <= 180: return '90-180天'
        else: return '180天以上'
    except:
        return '未知'

df_debt_r['账龄区间'] = df_debt_r['天数'].apply(classify_age)

# 按部门+账龄汇总
debt_by_dept_age = df_debt_r.groupby(['三级部门', '账龄区间'])['欠款净额'].sum() / 10000

print("=== 各部门欠款（万元）===")
dept_debt = df_debt_r.groupby('三级部门')['欠款净额'].sum() / 10000
for dept, val in dept_debt.sort_values(ascending=False).items():
    print(f"  {dept}: {val:.2f}万")
print(f"  合计: {dept_debt.sum():.2f}万")
print()

# 账龄分布
age_groups = ['30天内', '30-90天', '90-180天', '180天以上']
age_dist = df_debt_r.groupby('账龄区间')['欠款净额'].sum() / 10000
print("=== 欠款账龄分布（万元）===")
for ag in age_groups:
    val = age_dist.get(ag, 0)
    print(f"  {ag}: {val:.2f}万")
print()

# ===== 5. 认款数据（回款）=====
df_receipt_r = df_receipt[df_receipt['一级部门'] == REGION].copy()
receipt_by_dept = df_receipt_r.groupby('三级部门')['认款协同金额'].sum() / 10000
print("=== 各部门认款金额（万元）===")
for dept, val in receipt_by_dept.sort_values(ascending=False).items():
    print(f"  {dept}: {val:.2f}万")
print()

# ===== 6. 回款周期计算 =====
df_debt_r['欠款天数'] = pd.to_numeric(df_debt_r['天数'], errors='coerce').fillna(0)

# 加权回款周期 = (欠款金额*欠款天数 + 认款金额*认款天数) / (欠款金额 + 认款金额)
df_debt_r['欠款绝对值'] = df_debt_r['欠款净额'].abs()

dept_cycle = {}
for dept, grp in df_debt_r.groupby('三级部门'):
    debt_amt = grp['欠款绝对值'].sum()
    debt_days = (grp['欠款绝对值'] * grp['欠款天数']).sum()
    
    # 认款
    receipt_dept = df_receipt_r[df_receipt_r['三级部门'] == dept] if '三级部门' in df_receipt_r.columns else pd.DataFrame()
    receipt_amt = receipt_dept['认款协同金额'].sum() / 10000 if len(receipt_dept) > 0 else 0
    
    total = debt_amt + receipt_amt
    if total > 0:
        cycle = debt_days / total / 10000  # 修正单位
        # 改用简单平均
        cycle = grp['欠款天数'].mean() if debt_amt > 0 else 0
    else:
        cycle = 0
    dept_cycle[dept] = round(cycle, 1)

print("=== 各部门平均回款周期（天）===")
for dept, cycle in sorted(dept_cycle.items(), key=lambda x: -x[1]):
    print(f"  {dept}: {cycle:.1f}天")
print()

# ===== 7. 高风险客户 =====
risky = df_debt_r[df_debt_r['账龄区间'].isin(['90-180天', '180天以上'])].copy()
risky_client = risky.groupby('客户名称')['欠款净额'].sum() / 10000
risky_client = risky_client[risky_client > 0].sort_values(ascending=False).head(10)
print("=== 高风险客户（90天以上欠款）===")
for client, val in risky_client.items():
    print(f"  {client}: {val:.2f}万")
print()

# ===== 8. 整理输出数据供HTML使用 =====
# 部门列表（排序：按26Q1业绩从高到低）
all_depts_26 = list(perf26.sort_values(ascending=False).index)
# 合并25和26都有的部门
all_depts = sorted(set(list(perf26.index) + list(perf25.index)), 
                   key=lambda d: -perf26.get(d, 0))

output = {
    "depts": all_depts_26,
    "perf26": {d: round(perf26.get(d, 0), 2) for d in all_depts_26},
    "perf25": {d: round(perf25.get(d, 0), 2) for d in all_depts_26},
    "target": target_dict,
    "sales_count": {d: int(sales_count.get(d, 0)) for d in all_depts_26},
    "dept_debt": {d: round(float(dept_debt.get(d, 0)), 2) for d in all_depts_26},
    "receipt": {d: round(float(receipt_by_dept.get(d, 0)), 2) for d in all_depts_26},
    "debt_cycle": dept_cycle,
    "age_dist": {ag: round(float(age_dist.get(ag, 0)), 2) for ag in age_groups},
    "debt_by_dept_age": {}
}

for dept in all_depts_26:
    output["debt_by_dept_age"][dept] = {}
    for ag in age_groups:
        try:
            val = float(debt_by_dept_age.get((dept, ag), 0))
        except:
            val = 0
        output["debt_by_dept_age"][dept][ag] = round(val, 2)

# 保存JSON
with open(r'C:/Users/wm881/WorkBuddy/20260513090923/dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("✅ 数据提取完成，已保存到 dashboard_data.json")
