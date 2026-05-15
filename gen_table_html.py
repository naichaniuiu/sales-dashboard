# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    sales_data = json.load(f)

# 按部门汇总
dept_summary = {}
for dept, people in sales_data.items():
    d30 = sum(p['d30'] for p in people)
    d30_90 = sum(p['d30_90'] for p in people)
    d90_180 = sum(p['d90_180'] for p in people)
    d180 = sum(p['d180'] for p in people)
    total_debt = sum(p['total_debt'] for p in people)
    perf = sum(p['perf'] for p in people)
    collect = sum(p['collect'] for p in people)
    dept_summary[dept] = {
        'd30': d30, 'd30_90': d30_90, 'd90_180': d90_180, 'd180': d180,
        'total_debt': total_debt, 'perf': perf, 'collect': collect
    }

# 排序
sorted_cycle = sorted(dept_summary.items(), key=lambda x: x[1]['total_debt'], reverse=True)
sorted_debt = sorted(dept_summary.items(), key=lambda x: x[1]['total_debt'], reverse=True)

total_all = sum(d['total_debt'] for d in dept_summary.values())
sum30 = sum(d['d30'] for d in dept_summary.values())
sum90 = sum(d['d30_90'] for d in dept_summary.values())
sum180 = sum(d['d90_180'] for d in dept_summary.values())
sumOver = sum(d['d180'] for d in dept_summary.values())

# 回款周期用欠款加权计算（从deptData中取原始cycle值更准确）
# 从dashboard_final.json获取cycle值（虽然total_debt旧，但cycle值应该一致）
try:
    with open('C:/Users/wm881/WorkBuddy/20260513090923/dashboard_final.json', encoding='utf-8') as f:
        old_data = json.load(f)
    cycle_map = {d['dept']: d['cycle'] for d in old_data['dept_data']}
    sorted_cycle = sorted(dept_summary.items(), key=lambda x: cycle_map.get(x[0], 0), reverse=True)
except:
    cycle_map = {}

# 回款周期分析表 - tbody HTML
print('=== 回款周期分析表 - tbody HTML ===')
print('<tbody id="cycleTableBody">')
for dept, d in sorted_cycle:
    cycle = cycle_map.get(dept, 0)
    sc = 'negative' if cycle > 90 else 'warning' if cycle > 60 else 'highlight'
    badge = 'badge-down' if cycle > 90 else 'badge-warning' if cycle > 60 else 'badge-good'
    label = '需关注' if cycle > 90 else '一般' if cycle > 60 else '良好'
    print(f"  <tr onclick=\"showSalesDetail('{dept}')\" style=\"cursor:pointer;\" title=\"点击查看销售员明细\">")
    print(f"    <td>🏢 {dept}</td>")
    print(f"    <td>{d['total_debt']:.2f}</td>")
    print(f"    <td>{d['collect']:.2f}</td>")
    print(f"    <td class=\"{sc}\">{cycle:.1f}</td>")
    print(f"    <td><span class=\"status-badge {badge}\">{label}</span></td>")
    print(f"  </tr>")
print('</tbody>')

# 回款周期分析表 - tfoot HTML
collect_all = sum(d['collect'] for d in dept_summary.values())
print()
print('=== 回款周期分析表 - tfoot HTML ===')
print('<tfoot id="cycleTableFoot">')
if cycle_map:
    weighted_cycle = sum(cycle_map.get(dept, 0) * d['total_debt'] for dept, d in dept_summary.items())
    avg_cycle = weighted_cycle / total_all
else:
    avg_cycle = 0
print(f'  <tr><td>合计</td><td>{total_all:.2f}</td><td>{collect_all:.2f}</td><td>{avg_cycle:.1f}</td><td></td></tr>')
print('</tfoot>')

# 欠款分析表 - tbody HTML
print()
print('=== 欠款分析表 - tbody HTML ===')
print('<tbody id="debtTableBody">')
for dept, d in sorted_debt:
    risky = d['d90_180'] + d['d180']
    badge = 'badge-down' if risky > 50 else 'badge-warning' if risky > 20 else 'badge-good'
    label = '高风险' if risky > 50 else '关注' if risky > 20 else '较好'
    d90cls = 'warning' if d['d90_180'] > 0 else ''
    d180cls = 'negative' if d['d180'] > 0 else ''
    print(f"  <tr onclick=\"showSalesDetail('{dept}')\" style=\"cursor:pointer;\" title=\"点击查看销售员明细\">")
    print(f"    <td>🏢 {dept}</td>")
    print(f"    <td>{d['d30']:.2f}</td>")
    print(f"    <td>{d['d30_90']:.2f}</td>")
    print(f"    <td class=\"{d90cls}\">{d['d90_180']:.2f}</td>")
    print(f"    <td class=\"{d180cls}\">{d['d180']:.2f}</td>")
    print(f"    <td class=\"negative\">{d['total_debt']:.2f}</td>")
    print(f"    <td><span class=\"status-badge {badge}\">{label}</span></td>")
    print(f"  </tr>")
print('</tbody>')

# 欠款分析表 - tfoot HTML
print()
print('=== 欠款分析表 - tfoot HTML ===')
print('<tfoot id="debtTableFoot">')
print(f'  <tr><td>合计</td><td>{sum30:.2f}</td><td>{sum90:.2f}</td><td>{sum180:.2f}</td><td>{sumOver:.2f}</td><td>{total_all:.2f}</td><td></td></tr>')
print('</tfoot>')
