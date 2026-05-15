# -*- coding: utf-8 -*-
import json, re

path = 'C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    sales_data = json.load(f)

# 汇总
dept_summary = {}
for dept, people in sales_data.items():
    dept_summary[dept] = {
        'd30': sum(p['d30'] for p in people),
        'd30_90': sum(p['d30_90'] for p in people),
        'd90_180': sum(p['d90_180'] for p in people),
        'd180': sum(p['d180'] for p in people),
        'total_debt': sum(p['total_debt'] for p in people),
        'collect': sum(p['collect'] for p in people),
    }

# cycle 从 deptData JS变量提取
cycle_map = {}
for line in content.split('\n'):
    m = re.search(r"dept:'([^']+)',[^}]*?cycle:([\d.]+)", line)
    if m:
        cycle_map[m.group(1)] = float(m.group(2))

# 回款周期表 tbody
cycle_sorted = sorted(dept_summary.items(), key=lambda x: cycle_map.get(x[0], 0), reverse=True)
cycle_rows_html = ''
for dept, info in cycle_sorted:
    c = cycle_map.get(dept, 0)
    sc = 'negative' if c > 90 else 'warning' if c > 60 else 'highlight'
    badge = 'badge-down' if c > 90 else 'badge-warning' if c > 60 else 'badge-good'
    label = '需关注' if c > 90 else '一般' if c > 60 else '良好'
    cycle_rows_html += f'<tr onclick="showSalesDetail(\'{dept}\')" style="cursor:pointer;"><td>🏢 {dept}</td><td>{info["total_debt"]:.2f}</td><td>{info["collect"]:.2f}</td><td class="{sc}">{c:.1f}</td><td><span class="status-badge {badge}">{label}</span></td></tr>'

# 回款周期表 tfoot
total_debt_all = sum(v['total_debt'] for v in dept_summary.values())
collect_all = sum(v['collect'] for v in dept_summary.values())
weighted_cycle = sum(cycle_map.get(dept, 0) * v['total_debt'] for dept, v in dept_summary.items())
avg_cycle = weighted_cycle / total_debt_all if total_debt_all else 0

# 欠款表 tbody
debt_sorted = sorted(dept_summary.items(), key=lambda x: x[1]['total_debt'], reverse=True)
debt_rows_html = ''
for dept, info in debt_sorted:
    risky = info['d90_180'] + info['d180']
    badge = 'badge-down' if risky > 50 else 'badge-warning' if risky > 20 else 'badge-good'
    label = '高风险' if risky > 50 else '关注' if risky > 20 else '较好'
    d90cls = 'warning' if info['d90_180'] > 0 else ''
    d180cls = 'negative' if info['d180'] > 0 else ''
    debt_rows_html += f'<tr onclick="showSalesDetail(\'{dept}\')" style="cursor:pointer;"><td>🏢 {dept}</td><td>{info["d30"]:.2f}</td><td>{info["d30_90"]:.2f}</td><td class="{d90cls}">{info["d90_180"]:.2f}</td><td class="{d180cls}">{info["d180"]:.2f}</td><td class="negative">{info["total_debt"]:.2f}</td><td><span class="status-badge {badge}">{label}</span></td></tr>'

# 欠款表 tfoot
sum30 = sum(v['d30'] for v in dept_summary.values())
sum90 = sum(v['d30_90'] for v in dept_summary.values())
sum180 = sum(v['d90_180'] for v in dept_summary.values())
sumOver = sum(v['d180'] for v in dept_summary.values())

# 替换
content = content.replace('<tbody id="cycleTableBody"></tbody>', f'<tbody id="cycleTableBody">{cycle_rows_html}</tbody>')
content = content.replace('<tfoot id="cycleTableFoot"></tfoot>', f'<tfoot id="cycleTableFoot"><tr><td>合计</td><td>{total_debt_all:.2f}</td><td>{collect_all:.2f}</td><td>{avg_cycle:.1f}</td><td></td></tr></tfoot>')
content = content.replace('<tbody id="debtTableBody"></tbody>', f'<tbody id="debtTableBody">{debt_rows_html}</tbody>')
content = content.replace('<tfoot id="debtTableFoot"></tfoot>', f'<tfoot id="debtTableFoot"><tr><td>合计</td><td>{sum30:.2f}</td><td>{sum90:.2f}</td><td>{sum180:.2f}</td><td>{sumOver:.2f}</td><td>{total_debt_all:.2f}</td><td></td></tr></tfoot>')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
print(f"  欠款合计: {total_debt_all:.2f}万")
print(f"  30天内: {sum30:.2f}万, 30-90天: {sum90:.2f}万, 90-180天: {sum180:.2f}万, 180天以上: {sumOver:.2f}万")
