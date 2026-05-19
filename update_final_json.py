import json

with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('dashboard_final.json', 'r', encoding='utf-8') as f:
    final = json.load(f)

depts = data['depts']
dept_debt = data['dept_debt']
debt_by_age = data['debt_by_dept_age']
debt_cycle = data['debt_cycle']
receipt = data['receipt']
perf26 = data.get('perf26', {})
perf25 = data.get('perf25', {})
target = data.get('target', {})
sales_count = data.get('sales_count', {})

# 总业绩
total_v26 = round(sum(perf26.values()), 2)
total_v25 = round(sum(perf25.values()), 2)
yoy = round((total_v26 - total_v25) / total_v25 * 100, 1) if total_v25 else 0

# 大区目标（按区域名）
region_target = 0
for k, v in target.items():
    if '中西部' in k:
        region_target = v
        break

completion = round(total_v26 / region_target * 100, 1) if region_target else 0
total_sales = sum(sales_count.values())

# 更新 total
final['total']['v26'] = total_v26
final['total']['v25'] = total_v25
final['total']['yoy'] = yoy
final['total']['target'] = region_target
final['total']['completion'] = completion
final['total']['sales'] = total_sales

# 更新各部门数据（业绩 + 欠款）
for d in final['dept_data']:
    dept = d['dept']
    v26 = perf26.get(dept, 0)
    v25 = perf25.get(dept, 0)
    dept_target = target.get(dept, 0)
    d['v26'] = round(v26, 2)
    d['v25'] = round(v25, 2)
    d['yoy'] = round((v26 - v25) / v25 * 100, 1) if v25 else 0
    d['target'] = round(dept_target, 2)
    d['completion'] = round(v26 / dept_target * 100, 1) if dept_target else 0
    d['sales'] = int(sales_count.get(dept, 0))
    d['total_debt'] = round(dept_debt.get(dept, 0), 2)
    d['d30'] = round(debt_by_age.get(dept, {}).get('30天内', 0), 2)
    d['d30_90'] = round(debt_by_age.get(dept, {}).get('30-90天', 0), 2)
    d['d90_180'] = round(debt_by_age.get(dept, {}).get('90-180天', 0), 2)
    d['d180'] = round(debt_by_age.get(dept, {}).get('180天以上', 0), 2)
    d['cycle'] = round(debt_cycle.get(dept, 0), 1)
    d['collect'] = round(receipt.get(dept, 0), 2)

final['total']['debt'] = round(sum(dept_debt.values()), 2)
final['total']['d30'] = round(data['age_dist']['30天内'], 2)
final['total']['d30_90'] = round(data['age_dist']['30-90天'], 2)
final['total']['d90_180'] = round(data['age_dist']['90-180天'], 2)
final['total']['d180'] = round(data['age_dist']['180天以上'], 2)
final['total']['collect'] = round(sum(receipt.values()), 2)

with open('dashboard_final.json', 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print('dashboard_final.json updated')
print(f'26Q1总业绩: {final["total"]["v26"]}万 (目标达成率: {final["total"]["completion"]}%)')
print(f'欠款合计: {final["total"]["debt"]}万')
