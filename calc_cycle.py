# -*- coding: utf-8 -*-
import json, re

with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    sales_data = json.load(f)

with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 汇总
dept_summary = {}
for dept, people in sales_data.items():
    dept_summary[dept] = {
        'total_debt': sum(p['total_debt'] for p in people),
        'collect': sum(p['collect'] for p in people),
    }

# cycle
cycle_map = {}
for line in html.split('\n'):
    m = re.search(r"dept:'([^']+)',[^}]*?cycle:([\d.]+)", line)
    if m:
        cycle_map[m.group(1)] = float(m.group(2))

# 计算加权平均
total_debt = sum(v['total_debt'] for v in dept_summary.values())
weighted = sum(cycle_map.get(dept, 0) * v['total_debt'] for dept, v in dept_summary.items())
avg_cycle = weighted / total_debt if total_debt else 0

# 超90天部门数
over90 = sum(1 for dept, v in dept_summary.items() if cycle_map.get(dept, 0) > 90)

print(f"加权平均回款周期: {avg_cycle:.1f}天")
print(f"超90天部门数: {over90}")
print(f"最长: {max(cycle_map.items(), key=lambda x: x[1])}")
print(f"最短: {min(cycle_map.items(), key=lambda x: x[1])}")
