# -*- coding: utf-8 -*-
"""
安全更新看板数据 v2 - 只替换数据变量和静态表格，不重新生成HTML模板
"""
import json, re, openpyxl
from datetime import datetime, timedelta
from collections import defaultdict

WORKDIR   = r'C:\Users\wm881\WorkBuddy\20260513090923'
HTML_FILE = WORKDIR + r'\中西部大区26财年Q1数据看板.html'
FINAL_JSON      = WORKDIR + r'\dashboard_final.json'
SALES_DETAIL_JSON = WORKDIR + r'\sales_detail.json'
DEBT_DRILL_JSON = WORKDIR + r'\debt_drill.json'
EXCEL = r'C:\Users\wm881\Downloads\业绩 欠款看板.xlsx'

print("=== 安全更新看板数据 v2 ===")

with open(FINAL_JSON, encoding='utf-8') as f:
    final = json.load(f)
with open(SALES_DETAIL_JSON, encoding='utf-8') as f:
    sales_detail = json.load(f)
with open(DEBT_DRILL_JSON, encoding='utf-8') as f:
    debt_drill = json.load(f)

total    = final['total']
dept_data = final['dept_data']   # list
age_dist = final['age_dist']
cycle    = final['cycle']

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

# ===== 1. 更新 deptData JS数组 =====
new_dept_lines = []
for d in dept_data:
    line = (
        "    {dept:'" + d['dept'] + "',v26:" + str(d['v26']) +
        ",v25:" + str(d['v25']) +
        ",yoy:" + str(d['yoy']) +
        ",target:" + str(d.get('target', 0)) +
        ",completion:" + str(d.get('completion', 0)) +
        ",sales:" + str(d.get('sales', 0)) +
        ",d30:" + str(d.get('d30', 0)) +
        ",d30_90:" + str(d.get('d30_90', 0)) +
        ",d90_180:" + str(d.get('d90_180', 0)) +
        ",d180:" + str(d.get('d180', 0)) +
        ",total_debt:" + str(d.get('total_debt', 0)) +
        ",collect:" + str(d.get('collect', 0)) +
        ",cycle:" + str(d.get('cycle', 0)) +
        "}"
    )
    new_dept_lines.append(line)

new_dept_js = "const deptData = [\n" + ",\n".join(new_dept_lines) + "\n];"
html = re.sub(r'const deptData\s*=\s*\[[\s\S]*?\];', new_dept_js, html, count=1)
print("✓ deptData JS数组已更新")

# ===== 2. 更新 salesDetailData =====
sales_json = json.dumps(sales_detail, ensure_ascii=False, separators=(',', ':'))
html = re.sub(r'let salesDetailData\s*=\s*\{[\s\S]*?\};', 'let salesDetailData = ' + sales_json + ';', html, count=1)
print("✓ salesDetailData 已更新")

# ===== 3. 更新 deptCustData =====
dept_sales = debt_drill.get('dept_sales', {})
debt_cust_json = json.dumps(dept_sales, ensure_ascii=False, separators=(',', ':'))
html = re.sub(r'let deptCustData\s*=\s*\{[\s\S]*?\};', 'let deptCustData = ' + debt_cust_json + ';', html, count=1)
print("✓ deptCustData 已更新")

# ===== 4. 更新 deptCustPerfData =====
wb = openpyxl.load_workbook(EXCEL, data_only=True)
ws = wb['26财年Q1业绩']
perf_map = {}
for r in range(2, ws.max_row + 1):
    dept  = ws.cell(r, 31).value
    sales = ws.cell(r, 27).value
    cust  = ws.cell(r, 14).value
    perf  = ws.cell(r, 20).value or 0
    coll  = ws.cell(r, 21).value or 0
    debt  = ws.cell(r, 22).value or 0
    ratio = ws.cell(r, 43).value or 1
    if not dept or not sales or not cust:
        continue
    if not isinstance(perf, (int, float)): perf = 0
    if not isinstance(coll, (int, float)): coll = 0
    if not isinstance(debt, (int, float)): debt = 0
    if not isinstance(ratio, (int, float)): ratio = 1
    perf_map.setdefault(dept, {}).setdefault(sales, {}).setdefault(cust, {'perf':0.0,'collect':0.0,'debt':0.0,'orders':0})
    e = perf_map[dept][sales][cust]
    e['perf']    += perf * ratio
    e['collect'] += coll * ratio
    e['debt']    += debt * ratio
    e['orders']  += 1

deptCustPerfData = {}
for dept, sm in perf_map.items():
    sl = []
    for sn, cm in sm.items():
        custs = []
        tp = tc = td = 0
        for cn, v in cm.items():
            p = round(v['perf']/10000, 2)
            c = round(v['collect']/10000, 2)
            d = round(v['debt']/10000, 2)
            tp += p; tc += c; td += d
            custs.append({'name':cn,'perf':p,'collect':c,'debt':d,'orders':v['orders']})
        custs.sort(key=lambda x: x['perf'], reverse=True)
        sl.append({'name':sn,'total':round(tp,2),'collect':round(tc,2),'debt':round(td,2),'cust_count':len(custs),'custs':custs})
    sl.sort(key=lambda x: x['total'], reverse=True)
    deptCustPerfData[dept] = sl

perf_cust_json = json.dumps(deptCustPerfData, ensure_ascii=False, separators=(',', ':'))
html = re.sub(r'let deptCustPerfData\s*=\s*\{[\s\S]*?\};', 'let deptCustPerfData = ' + perf_cust_json + ';', html, count=1)
print("✓ deptCustPerfData 已更新")

# ===== 5. 更新 KPI 指标卡 =====
v26 = total['v26']
target = total.get('target', 5586.0)
completion = total.get('completion', 0)
gap = round(target - v26, 2)
yoy = total.get('yoy', 0)
v25 = total.get('v25', 0)
sales_cnt = total.get('sales', 68)
debt = total.get('debt', 0)
d90_up = round(total.get('d90_180', 0) + total.get('d180', 0), 2)

# KPI 1: 实际业绩
html = re.sub(
    r'(<div class="value">)\d+\.?\d*(<span style="font-size:0.5em;">万</span></div>\s*<div class="sub">目标：)',
    lambda m: m.group(1) + str(v26) + m.group(2),
    html, count=1
)
html = re.sub(
    r'(目标：5586\.0万</div>)',
    '目标：' + str(target) + '万</div>',
    html, count=1
)

# KPI 2: 目标完成率
html = re.sub(
    r'(<div class="value negative">)\d+\.?\d*(%</div>\s*<div class="sub">距目标还差 )',
    lambda m: m.group(1) + str(completion) + m.group(2),
    html, count=1
)
html = re.sub(
    r'(距目标还差 )\d+\.?\d*(万</div>)',
    lambda m: m.group(1) + str(gap) + m.group(2),
    html, count=1
)

# KPI 3: 同比
html = re.sub(
    r'(<div class="value negative">)-\d+\.?\d*(%</div>\s*<div class="sub">25Q1：)',
    lambda m: m.group(1) + str(yoy) + '%</div>\n            <div class="sub">25Q1：',
    html, count=1
)
html = re.sub(
    r'(25Q1：)\d+\.?\d*(万</div>)',
    lambda m: m.group(1) + str(v25) + m.group(2),
    html, count=1
)

# KPI 4: 销售员数
html = re.sub(
    r'(<div class="value" style="color:#ffa502;">)\d+(</div>\s*<div class="sub">人</div>)',
    lambda m: m.group(1) + str(sales_cnt) + m.group(2),
    html, count=1
)

# KPI 5: 逾期欠款总额
html = re.sub(
    r'(<div class="value negative">)\d+\.?\d*(<span style="font-size:0.5em;">万</span></div>\s*<div class="sub">90天以上：)',
    lambda m: m.group(1) + str(debt) + m.group(2),
    html, count=1
)
html = re.sub(
    r'(90天以上：)\d+\.?\d*(万</div>)',
    lambda m: m.group(1) + str(d90_up) + m.group(2),
    html, count=1
)
print("✓ KPI 指标卡已更新")

# ===== 6. 更新业绩表格行 =====
perf_rows = ''
for d in dept_data:
    dept_name = d['dept']
    v26_d = d['v26']
    target_d = d.get('target', 0)
    comp_d = d.get('completion', 0)
    v25_d = d['v25']
    yoy_d = d['yoy']
    sales_d = d.get('sales', 0)

    if yoy_d >= 0:
        yoy_str = f'▲ +{yoy_d}%'
        yoy_cls = 'trend-up'
    else:
        yoy_str = f'▼ {yoy_d}%'
        yoy_cls = 'trend-down'

    if yoy_d > -30:
        badge = '<span class="status-badge badge-up">稳定增长</span>'
    elif yoy_d > -60:
        badge = '<span class="status-badge badge-warn">同比下滑</span>'
    else:
        badge = '<span class="status-badge badge-down">严重下滑</span>'

    target_str = str(target_d) if target_d else '—'
    comp_str = f'{comp_d}%' if target_d else '—'

    perf_rows += (
        f'\n                    <tr onclick="showSalesDetail(\'{dept_name}\',\'perf\')" style="cursor:pointer;" title="点击查看销售员业绩明细">'
        f'\n                        <td>🏢 {dept_name}</td>'
        f'\n                        <td class="highlight">{v26_d}</td>'
        f'<td>{target_str}</td>'
        f'<td>{comp_str}</td>'
        f'<td>{v25_d}</td>'
        f'\n                        <td class="{yoy_cls}">{yoy_str}</td>'
        f'<td>{sales_d}</td>'
        f'\n                        <td>{badge}</td>'
        f'\n                    </tr>'
    )

# 替换业绩表格tbody
html = re.sub(
    r'(<table class="dept-table">\s*<thead>\s*<tr>\s*<th>三级部门</th>[\s\S]*?</thead>\s*<tbody>)([\s\S]*?)(<tr[^>]*class="total-row"[\s\S]*?</table>)',
    lambda m: m.group(1) + perf_rows + '\n                ' + m.group(3),
    html, count=1
)
print("✓ 业绩表格行已更新")

# ===== 7. 更新欠款表格行 =====
# 按欠款总额排序
dept_by_debt = sorted(dept_data, key=lambda x: x.get('total_debt', 0), reverse=True)
debt_rows = ''
for d in dept_by_debt:
    dept_name = d['dept']
    d30   = d.get('d30', 0)
    d30_90 = d.get('d30_90', 0)
    d90_180 = d.get('d90_180', 0)
    d180  = d.get('d180', 0)
    tot   = d.get('total_debt', 0)

    if tot > 200:
        status = '<span class="status-badge badge-down">🔴 高风险</span>'
    elif tot > 100:
        status = '<span class="status-badge badge-warn">🟡 关注</span>'
    else:
        status = '<span class="status-badge badge-up">🟢 较好</span>'

    # 进度条宽度
    max_tot = max(x.get('total_debt', 0) for x in dept_data) or 1
    bar_w = round(tot / max_tot * 100)

    debt_rows += (
        f'\n                    <tr onclick="showSalesDetail(\'{dept_name}\',\'debt\')" style="cursor:pointer;">'
        f'\n                        <td style="font-weight:600;">{dept_name}'
        f'<div style="height:4px;background:rgba(255,255,255,0.1);border-radius:2px;margin-top:4px;">'
        f'<div style="height:4px;width:{bar_w}%;background:linear-gradient(90deg,#00d4ff,#ff4757);border-radius:2px;"></div></div></td>'
        f'\n                        <td style="color:#00ff88;text-align:right;">{d30}</td>'
        f'\n                        <td style="color:#ffa502;text-align:right;">{d30_90}</td>'
        f'\n                        <td style="color:#ff6b6b;text-align:right;">{d90_180}</td>'
        f'\n                        <td style="color:#ff4757;text-align:right;">{d180}</td>'
        f'\n                        <td style="color:#fff;text-align:right;font-weight:600;">{tot}</td>'
        f'\n                        <td>{status}</td>'
        f'\n                    </tr>'
    )

html = re.sub(
    r'(<table class="dept-table">\s*<thead>\s*<tr>\s*<th>三级部门</th>\s*<th>30天内\(万\)</th>[\s\S]*?</thead>\s*<tbody>)([\s\S]*?)(<tr[^>]*class="total-row"[\s\S]*?</table>)',
    lambda m: m.group(1) + debt_rows + '\n                ' + m.group(3),
    html, count=1
)
print("✓ 欠款表格行已更新")

# ===== 8. 更新页脚日期 =====
today     = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
html = re.sub(
    r'数据截止：\d{4}-\d{2}-\d{2} &nbsp;\|&nbsp; 统计基准日：\d{4}-\d{2}-\d{2} &nbsp;\|&nbsp; 生成于：\d{4}-\d{2}-\d{2}',
    f'数据截止：{yesterday} &nbsp;|&nbsp; 统计基准日：{today} &nbsp;|&nbsp; 生成于：{today}',
    html, count=1
)
print(f"✓ 日期已更新 → 数据截止:{yesterday}, 生成于:{today}")

# ===== 9. 保存 =====
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

# ===== 10. JS语法验证 =====
import subprocess, sys
result = subprocess.run(
    [r'C:\Users\wm881\.workbuddy\binaries\node\versions\22.12.0\node.exe', '-e',
     '''const fs=require('fs');const h=fs.readFileSync(String.raw`''' + HTML_FILE.replace('\\', '\\\\') + '''`,'utf8');
        const m=h.match(/<script[^>]*>([\\s\\S]*?)<\\/script>/g)||[];let ok=true;
        m.forEach((t,i)=>{const c=t.replace(/<\\/?script[^>]*>/g,'');try{new Function(c);}catch(e){console.log('ERR script '+(i+1)+': '+e.message);ok=false;}});
        if(ok)console.log('JS syntax OK');else process.exit(1);'''],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("✓ JS语法验证通过")
else:
    print("✗ JS语法错误:", result.stdout, result.stderr)
    sys.exit(1)

print(f"\n✅ 看板更新完成！总业绩:{v26}万, 欠款:{debt}万")
