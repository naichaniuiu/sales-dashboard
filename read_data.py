# -*- coding: utf-8 -*-
import pandas as pd
import os

base = r'C:/Users/wm881/Downloads'
files = os.listdir(base)
# 找包含业绩和25或26的文件
target_files = [f for f in files if ('业绩' in f or '看板' in f) and ('25' in f or '26' in f) and f.endswith('.xlsx')]
print('Target files:')
for f in target_files[:15]:
    print(f'  {f}')

# 读取 业绩 欠款看板.xlsx
print('\n读取业绩 欠款看板.xlsx...')
df = pd.read_excel(os.path.join(base, '业绩 欠款看板.xlsx'), sheet_name=None)
print('工作表:', list(df.keys())[:5])
for name in list(df.keys())[:2]:
    print(f'\n{name} 前5行:')
    print(df[name].head(5).to_string())
