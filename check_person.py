import pandas as pd

df26 = pd.read_excel('C:/Users/wm881/Downloads/业绩 欠款看板.xlsx', sheet_name='26财年Q1业绩')
df26_xb = df26[df26['一级部门'] == '中西部大区']

for name in ['刘美希', '危昶']:
    d = df26_xb[df26_xb['销售员名称'] == name]
    if len(d) == 0:
        print(f'{name}: 不在26Q1业绩表中')
    else:
        status = d['销售员状态'].unique().tolist()
        dept = d['三级部门'].unique().tolist()
        print(f'{name}: 在表中, 状态={status}, 部门={dept}')
