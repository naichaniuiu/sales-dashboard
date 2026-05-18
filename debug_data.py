import json
with open('dashboard_final.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
print('=== dept_data ===')
for item in d['dept_data']:
    print(f"{item['dept']}: cycle={item.get('cycle', 'N/A')}, total_debt={item.get('total_debt', 'N/A')}")
print('\n=== cycle ===')
print(d.get('cycle', {}))
