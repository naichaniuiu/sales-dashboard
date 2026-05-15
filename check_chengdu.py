import pandas as pd
import json

df_debt = pd.read_excel('C:/Users/wm881/Downloads/业绩 欠款看板.xlsx', sheet_name='欠款数据 ')
df_debt_cd = df_debt[(df_debt['一级部门'] == '中西部大区') & (df_debt['三级部门'] == '成都站')]

df26 = pd.read_excel('C:/Users/wm881/Downloads/业绩 欠款看板.xlsx', sheet_name='26财年Q1业绩')
df26_active = df26[(df26['一级部门'] == '中西部大区') & (df26['销售员状态'] == '在职')]

with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== 成都站欠款明细对比 ===')
print('Excel按人汇总:')
excel_by_person = df_debt_cd.groupby('销售员名称')['欠款金额'].sum().apply(lambda x: round(x/10000, 2))
for name, amt in excel_by_person.items():
    print(f'  {name}: {amt}万')

print(f'\nExcel合计: {round(df_debt_cd["欠款金额"].sum()/10000, 4)}万')

print('\nJSON中的人:')
json_people = {s['name']: s['total_debt'] for s in data.get('成都站', [])}
for name, amt in json_people.items():
    print(f'  {name}: {amt}万')

print(f'\nJSON合计: {sum(json_people.values())}万')

print('\nExcel有但JSON没有的人:')
for name in excel_by_person.index:
    if name not in json_people:
        print(f'  {name}: {excel_by_person[name]}万')

print('\nJSON有但Excel没有的人:')
for name in json_people:
    if name not in excel_by_person.index:
        print(f'  {name}: {json_people[name]}万')
