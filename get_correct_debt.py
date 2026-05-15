import json

with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    data = json.load(f)

dept_order = ['武汉基建制造行业组', '成都站', '西安站', '长沙站', '武汉能源交通行业组', '重庆站', '郑州站', '武汉金融行业组', '其他']
for dept in dept_order:
    lst = data[dept]
    td = sum(s['total_debt'] for s in lst)
    d30 = sum(s['d30'] for s in lst)
    d30_90 = sum(s['d30_90'] for s in lst)
    d90_180 = sum(s['d90_180'] for s in lst)
    d180 = sum(s['d180'] for s in lst)
    print(f"'{dept}': total_debt={td:.2f}, d30={d30:.2f}, d30_90={d30_90:.2f}, d90_180={d90_180:.2f}, d180={d180:.2f}")

print()
print('全部欠款:', sum(sum(s['total_debt'] for s in lst) for lst in data.values()))
