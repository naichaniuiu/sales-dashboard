import pandas as pd
import json

df_debt = pd.read_excel('C:/Users/wm881/Downloads/业绩 欠款看板.xlsx', sheet_name='欠款数据 ')
df_debt_xb = df_debt[df_debt['一级部门'] == '中西部大区']
df26 = pd.read_excel('C:/Users/wm881/Downloads/业绩 欠款看板.xlsx', sheet_name='26财年Q1业绩')
df26_active = df26[(df26['一级部门'] == '中西部大区') & (df26['销售员状态'] == '在职')]

all_names = set(df_debt_xb['销售员名称'].unique())
active_names = set(df26_active['销售员名称'].unique())

with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    data = json.load(f)
json_names = set()
for lst in data.values():
    for s in lst:
        json_names.add(s['name'])

missing = all_names - json_names
print('欠款表中有但JSON中没有的销售员:', missing)
print('人数:', len(missing))

for name in missing:
    d = df_debt_xb[df_debt_xb['销售员名称'] == name]
    dept = d['三级部门'].unique().tolist()
    amt = round(d['欠款金额'].sum() / 10000, 2)
    print(f'  {name}: {len(d)}行, 欠款={amt}万, 部门={dept}')
