# -*- coding: utf-8 -*-
"""独立复核 Q3 看板 KPI（按 gen_q3_dashboard.py 口径）"""
import openpyxl
from datetime import datetime, date

DATA_FILE = 'D:/业绩 欠款看板 Q3.xlsx'
TODAY = datetime(2026, 11, 25)
Q3_START, Q3_END = datetime(2026, 10, 1), datetime(2026, 12, 31)
Q3_START_25, Q3_END_25 = datetime(2025, 10, 1), datetime(2025, 12, 31)
SELLER_EXCLUDE = {'石红银'}
DEPT_MAP = {'中西部大区','中西大区','华中大区','华中大区（已封存）','西南大区','西南大区（已封存）'}

wb = openpyxl.load_workbook(DATA_FILE, data_only=True, read_only=True)
print('SHEETS:', wb.sheetnames)

def sheet_by_kw(kw):
    for n in wb.sheetnames:
        if kw in n:
            return n
    return None

def to_wan(v):
    try:
        return float(v) / 10000.0
    except (TypeError, ValueError):
        return 0.0

def parse_date(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    s = str(v).strip()
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s[:19], fmt)
        except ValueError:
            pass
    return None

def rows(sheetname):
    ws = wb[sheetname]
    it = ws.iter_rows(values_only=True)
    headers = None
    for row in it:
        if headers is None:
            headers = [str(h).strip() if h is not None else '' for h in row]
            continue
        yield dict(zip(headers, row))

def in_dept(r):
    return str(r.get('一级部门') or '').strip().replace('\t', '') in DEPT_MAP

def excluded_seller_dept(r):
    seller = str(r.get('销售员名称') or '').strip().replace('\t', '')
    dept2 = str(r.get('二级部门') or '').strip().replace('\t', '')
    sub = str(r.get('三级部门') or '').strip().replace('\t', '')
    return (seller in SELLER_EXCLUDE) or dept2 == '武汉仓' or sub == '武汉仓'

# 26Q3 业绩（B端过滤）
name26 = wb.worksheets[1].title
t26, c26 = 0.0, 0
for r in rows(name26):
    if not in_dept(r):
        continue
    d = parse_date(r.get('业绩日期'))
    if not d or not (Q3_START <= d <= Q3_END):
        continue
    if str(r.get('是否核算B端业绩') or '').strip() != '是':
        continue
    if excluded_seller_dept(r):
        continue
    t26 += to_wan(r.get('业绩总金额'))
    c26 += 1
print(f'26Q3 actual (B端, filtered): {t26:.2f} wan  ({c26} rows)')

# 25Q3 业绩
name25 = wb.worksheets[0].title
t25, c25 = 0.0, 0
for r in rows(name25):
    if not in_dept(r):
        continue
    d = parse_date(r.get('业绩日期'))
    if not d or not (Q3_START_25 <= d <= Q3_END_25):
        continue
    if excluded_seller_dept(r):
        continue
    t25 += to_wan(r.get('业绩总金额'))
    c25 += 1
print(f'25Q3 (filtered): {t25:.2f} wan  ({c25} rows)')

# 欠款
name_debt = sheet_by_kw('欠款')
total, overdue, d90 = 0.0, 0.0, 0.0
buckets = [0.0, 0.0, 0.0, 0.0]
cnt = 0
for r in rows(name_debt):
    if excluded_seller_dept(r):
        continue
    d = parse_date(r.get('业绩日期'))
    days = (TODAY - d).days if d else 0
    if days < 0:
        days = 0
    v = to_wan(r.get('欠款金额'))
    total += v
    if days > 30:
        overdue += v
    if days > 90:
        d90 += v
    if days <= 30:
        buckets[0] += v
    elif days <= 90:
        buckets[1] += v
    elif days <= 180:
        buckets[2] += v
    else:
        buckets[3] += v
    cnt += 1
print(f'Total debt: {total:.2f} wan  ({cnt} rows)')
print(f'  buckets <=30 / 31-90 / 91-180 / 180+: {buckets[0]:.2f} / {buckets[1]:.2f} / {buckets[2]:.2f} / {buckets[3]:.2f}  sum={sum(buckets):.2f}')
print(f'Overdue (>30d): {overdue:.2f} wan')
print(f'90d+ debt: {d90:.2f} wan')
print(f'Completion (actual/4040): {t26/4040*100:.1f}%')
wb.close()
