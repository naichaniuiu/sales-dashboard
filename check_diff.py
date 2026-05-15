import pandas as pd
import json

df_debt = pd.read_excel('C:/Users/wm881/Downloads/业绩 欠款看板.xlsx', sheet_name='欠款数据 ')
df_debt_xb = df_debt[df_debt['一级部门'] == '中西部大区']

with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== 部门欠款对比 ===')
for dept in ['武汉基建制造行业组', '成都站', '西安站', '长沙站', '武汉能源交通行业组', '重庆站', '郑州站', '武汉金融行业组', '其他']:
    # Excel原始
    excel_sum = round(df_debt_xb[df_debt_xb['三级部门'] == dept]['欠款金额'].sum() / 10000, 4)
    # JSON
    json_sum = round(sum(s['total_debt'] for s in data.get(dept, [])), 4)
    diff = round(excel_sum - json_sum, 4)
    print(f'{dept}: Excel={excel_sum}万, JSON={json_sum}万, 差={diff}万')

print()
print('Excel全部:', round(df_debt_xb['欠款金额'].sum() / 10000, 4), '万')
print('JSON全部:', round(sum(sum(s['total_debt'] for s in lst) for lst in data.values()), 4), '万')
