# -*- coding: utf-8 -*-
"""
将欠款和业绩的二级下钻功能注入到 generate_html.py 生成的HTML中
步骤：
1. 插入 deptCustDebtData 和 deptCustPerfData 数据变量
2. 替换 renderSalesDebt（增加销售员→客户下钻）
3. 替换 renderSalesPerf（增加销售员→客户下钻）
4. 新增 renderCustDebt, backToSalesDebt, renderCustPerf, backToSalesPerf
5. 更新 closeSalesModal 重置所有 _back 变量
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json

HTML_FILE = '中西部大区26财年Q1数据看板.html'

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

# 读取数据
with open('debt_drill.json', 'r', encoding='utf-8') as f:
    debt_drill = f.read()

with open('perf_drill.json', 'r', encoding='utf-8') as f:
    perf_drill = f.read()

# ========== 1. 插入数据变量 ==========
# 找到 salesCycleData 声明位置之后插入（update_cycle_drill.py 已经插入了 salesCycleData）
# 我们在 custCycleData 之后插入
marker = 'let custCycleData = '
idx = html.find(marker)
if idx == -1:
    # 如果没有回款周期数据（不太可能），在 salesDetailData 之后插入
    marker2 = 'let salesDetailData = '
    idx = html.find(marker2)
    if idx == -1:
        print('ERROR: Cannot find data insertion point')
        sys.exit(1)
    # 找到 salesDetailData 赋值结束
    brace_start = html.find('{', idx)
    depth = 0
    pos = brace_start
    while pos < len(html):
        if html[pos] == '{': depth += 1
        elif html[pos] == '}':
            depth -= 1
            if depth == 0:
                pos += 1
                break
        pos += 1
    semi_pos = html.find(';', pos)
    insert_pos = semi_pos + 1
else:
    # 找到 custCycleData 赋值结束
    brace_start = html.find('{', idx)
    depth = 0
    pos = brace_start
    while pos < len(html):
        if html[pos] == '{': depth += 1
        elif html[pos] == '}':
            depth -= 1
            if depth == 0:
                pos += 1
                break
        pos += 1
    semi_pos = html.find(';', pos)
    insert_pos = semi_pos + 1

new_data = f"""

// ===== 欠款下钻数据（部门→销售员→客户）=====
let deptCustDebtData = {debt_drill};

// ===== 业绩下钻数据（部门→销售员→客户）=====
let deptCustPerfData = {perf_drill};

"""

html = html[:insert_pos] + new_data + html[insert_pos:]
print(f'Inserted data: deptCustDebtData({len(debt_drill)} chars), deptCustPerfData({len(perf_drill)} chars)')

# ========== 2. 替换 renderSalesDebt ==========
func_start = html.find('function renderSalesDebt(dept) {')
if func_start == -1:
    # 可能是模板函数的Python格式 {{...}}，已经被展开成单大括号
    func_start = html.find('function renderSalesDebt(dept) {')
if func_start == -1:
    print('ERROR: renderSalesDebt not found')
    sys.exit(1)

brace_count = 0
func_end = -1
for i in range(func_start, len(html)):
    if html[i] == '{': brace_count += 1
    elif html[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            func_end = i + 1
            break

print(f'Old renderSalesDebt: pos {func_start}-{func_end}')

new_debt_func = r"""function renderSalesDebt(dept) {
    const list = [...(salesDetailData[dept] || [])];
    list.sort((a, b) => b.total_debt - a.total_debt);
    const rows = list.map(s => {
        const dc = s.total_debt > 50 ? '#ff4757' : s.total_debt > 20 ? '#ffa502' : '#00ff88';
        const status = s.total_debt > 50 ? '\u{1F534} 高风险' : s.total_debt > 20 ? '\u{1F7E1} 关注' : '\u{1F7E2} 较好';
        const hasCust = deptCustDebtData[dept] && deptCustDebtData[dept].find(x => x.name === s.name);
        const nameStyle = hasCust ? 'color:#00d4ff;cursor:pointer;text-decoration:underline;' : 'color:#ccd6f6;';
        const nameClick = hasCust ? `onclick="renderCustDebt('${dept}','${s.name}')"` : '';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;${nameStyle}" ${nameClick}>${s.name}${hasCust ? ' \u{1F4C2}' : ''}</td>
            <td style="padding:7px 5px;color:${dc};text-align:right;font-weight:600;">${s.total_debt.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${s.d30.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ffa502;text-align:right;">${s.d30_90.toFixed(2)}</td>
            <td style="padding:7px 5px;color:${s.d90_180>0?'#ff4757':'#8892b0'};text-align:right;">${s.d90_180.toFixed(2)}</td>
            <td style="padding:7px 5px;color:${s.d180>0?'#ff4757':'#8892b0'};text-align:right;">${s.d180.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${status}</td>
        </tr>`;
    }).join('');
    const td = list.reduce((s, v) => s + v.total_debt, 0).toFixed(2);
    document.getElementById('salesModalTitle').innerHTML = `\u{1F4B0} ${dept} - 销售员欠款明细 <span style="font-size:0.7em;color:#8892b0;">（点击销售员名查看客户明细）</span>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.82em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;">销售员</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">合计欠款(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">30天内</th>
            <th style="padding:8px 6px;color:#ffa502;text-align:right;">30-90天</th>
            <th style="padding:8px 6px;color:#ff4757;text-align:right;">90-180天</th>
            <th style="padding:8px 6px;color:#ff4757;text-align:right;">180天以上</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th>
        </tr></thead>
        <tbody>${rows}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">合计（${list.length}人）</td>
            <td style="padding:8px 6px;color:#ff4757;text-align:right;">${td}</td>
            <td colspan="4"></td>
            <td></td>
        </tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}"""

html = html[:func_start] + new_debt_func + html[func_end:]
print('Replaced renderSalesDebt')

# ========== 3. 替换 renderSalesPerf ==========
func_start = html.find('function renderSalesPerf(dept) {')
if func_start == -1:
    print('ERROR: renderSalesPerf not found')
    sys.exit(1)

brace_count = 0
func_end = -1
for i in range(func_start, len(html)):
    if html[i] == '{': brace_count += 1
    elif html[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            func_end = i + 1
            break

print(f'Old renderSalesPerf: pos {func_start}-{func_end}')

new_perf_func = r"""function renderSalesPerf(dept) {
    const list = [...(salesDetailData[dept] || [])];
    list.sort((a, b) => b.perf - a.perf);
    const rows = list.map(s => {
        const color = s.perf < 0 ? '#ff4757' : s.perf < 5 ? '#ffa502' : '#00ff88';
        const status = s.perf < 0 ? '\u{1F534} 无业绩' : s.perf < 5 ? '\u{1F7E1} 待提升' : '\u{1F7E2} 正常';
        const hasCust = deptCustPerfData[dept] && deptCustPerfData[dept].find(x => x.name === s.name);
        const nameStyle = hasCust ? 'color:#00d4ff;cursor:pointer;text-decoration:underline;' : 'color:#ccd6f6;';
        const nameClick = hasCust ? `onclick="renderCustPerf('${dept}','${s.name}')"` : '';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;${nameStyle}" ${nameClick}>${s.name}${hasCust ? ' \u{1F4C2}' : ''}</td>
            <td style="padding:7px 5px;color:${color};text-align:right;font-weight:600;">${s.perf.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${s.collect.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${status}</td>
        </tr>`;
    }).join('');
    const tp = list.reduce((s, v) => s + v.perf, 0).toFixed(2);
    const tc = list.reduce((s, v) => s + v.collect, 0).toFixed(2);
    document.getElementById('salesModalTitle').innerHTML = `\u{1F4CA} ${dept} - 销售员业绩明细 <span style="font-size:0.7em;color:#8892b0;">（点击销售员名查看客户明细）</span>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.85em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;">销售员</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">26Q1业绩(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th>
        </tr></thead>
        <tbody>${rows}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">合计（${list.length}人）</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${tp}</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${tc}</td>
            <td></td>
        </tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}"""

html = html[:func_start] + new_perf_func + html[func_end:]
print('Replaced renderSalesPerf')

# ========== 4. 新增客户下钻函数 ==========
# 找到 backToSalesCycle 函数结束位置，在其后插入
insert_marker = 'function backToSalesCycle()'
insert_idx = html.find(insert_marker)
if insert_idx == -1:
    # 如果回款周期下钻没有运行，找 closeSalesModal 结束位置
    insert_marker2 = 'function closeSalesModal()'
    insert_idx = html.find(insert_marker2)
    if insert_idx == -1:
        print('ERROR: Cannot find insertion point for drill functions')
        sys.exit(1)
    brace_count = 0
    for i in range(insert_idx, len(html)):
        if html[i] == '{': brace_count += 1
        elif html[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                insert_idx = i + 1
                break
else:
    brace_count = 0
    for i in range(insert_idx, len(html)):
        if html[i] == '{': brace_count += 1
        elif html[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                insert_idx = i + 1
                break

print(f'Drill functions insertion point: {insert_idx}')

new_drill_funcs = r"""

// ===== 客户欠款明细（欠款分析第二级下钻）=====
function renderCustDebt(dept, salesName) {
    window._salesDebtBack = document.getElementById('salesTableContainer').innerHTML;
    window._salesDebtTitle = document.getElementById('salesModalTitle').innerHTML;

    const salesList = deptCustDebtData[dept] || [];
    const sales = salesList.find(s => s.name === salesName);
    const custs = sales ? (sales.custs || []) : [];
    if (!custs.length) return;

    const rows = custs.map(c => {
        const total_yuan = (c.total * 10000).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
        const d30_yuan = (c.d30 * 10000).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
        const d30_90_yuan = (c.d30_90 * 10000).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
        const d90_180_yuan = (c.d90_180 * 10000).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
        const d180_yuan = (c.d180 * 10000).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
        const statusColor = c.max_days <= 30 ? '#00ff88' : c.max_days <= 90 ? '#ffa502' : c.max_days <= 180 ? '#ff6b6b' : '#ff4757';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;color:#ccd6f6;max-width:280px;word-break:break-all;">${c.name}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${d30_yuan}</td>
            <td style="padding:7px 5px;color:#ffa502;text-align:right;">${d30_90_yuan}</td>
            <td style="padding:7px 5px;color:${c.d90_180>0?'#ff4757':'#8892b0'};text-align:right;">${d90_180_yuan}</td>
            <td style="padding:7px 5px;color:${c.d180>0?'#ff4757':'#8892b0'};text-align:right;">${d180_yuan}</td>
            <td style="padding:7px 5px;color:#fff;text-align:right;font-weight:600;">${total_yuan}</td>
            <td style="padding:7px 5px;color:${statusColor};text-align:center;font-weight:600;">${c.max_days}天</td>
        </tr>`;
    }).join('');

    const tc = custs.reduce((s, c) => s + c.total, 0);
    const tc_yuan = (tc * 10000).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});

    document.getElementById('salesModalTitle').innerHTML = `\u{1F4B0} ${salesName} - 客户欠款明细 <span style="font-size:0.75em;color:#8892b0;">（${dept}）</span> <button onclick="backToSalesDebt()" style="margin-left:12px;background:rgba(0,212,255,0.2);border:1px solid rgba(0,212,255,0.4);color:#00d4ff;border-radius:6px;padding:3px 12px;font-size:0.85em;cursor:pointer;">\u2190 返回销售员</button>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.8em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;text-align:left;">客户名称</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">30天内(元)</th>
            <th style="padding:8px 6px;color:#ffa502;text-align:right;">30-90天(元)</th>
            <th style="padding:8px 6px;color:#ff4757;text-align:right;">90-180天(元)</th>
            <th style="padding:8px 6px;color:#ff4757;text-align:right;">180天+(元)</th>
            <th style="padding:8px 6px;color:#fff;text-align:right;">合计(元)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">最长账龄</th>
        </tr></thead>
        <tbody>${rows}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">合计（${custs.length}个客户）</td>
            <td colspan="4"></td>
            <td style="padding:8px 6px;color:#fff;text-align:right;">${tc_yuan}</td>
            <td></td>
        </tr></tbody></table>`;
}

function backToSalesDebt() {
    if (window._salesDebtBack) {
        document.getElementById('salesTableContainer').innerHTML = window._salesDebtBack;
        document.getElementById('salesModalTitle').innerHTML = window._salesDebtTitle;
        window._salesDebtBack = null;
    }
}

// ===== 客户业绩明细（业绩分析第二级下钻）=====
function renderCustPerf(dept, salesName) {
    window._salesPerfBack = document.getElementById('salesTableContainer').innerHTML;
    window._salesPerfTitle = document.getElementById('salesModalTitle').innerHTML;

    const salesList = deptCustPerfData[dept] || [];
    const sales = salesList.find(s => s.name === salesName);
    const custs = sales ? (sales.custs || []) : [];
    if (!custs.length) return;

    const rows = custs.map(c => {
        const color = c.perf < 0 ? '#ff4757' : c.perf < 1 ? '#ffa502' : '#00ff88';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;color:#ccd6f6;max-width:280px;word-break:break-all;">${c.name}</td>
            <td style="padding:7px 5px;color:${color};text-align:right;font-weight:600;">${c.perf.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${c.collect.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${c.orders}</td>
        </tr>`;
    }).join('');

    const tp = custs.reduce((s, c) => s + c.perf, 0).toFixed(2);
    const tc = custs.reduce((s, c) => s + c.collect, 0).toFixed(2);

    document.getElementById('salesModalTitle').innerHTML = `\u{1F4CA} ${salesName} - 客户业绩明细 <span style="font-size:0.75em;color:#8892b0;">（${dept}）</span> <button onclick="backToSalesPerf()" style="margin-left:12px;background:rgba(0,212,255,0.2);border:1px solid rgba(0,212,255,0.4);color:#00d4ff;border-radius:6px;padding:3px 12px;font-size:0.85em;cursor:pointer;">\u2190 返回销售员</button>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.8em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;text-align:left;">客户名称</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">业绩(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">订单数</th>
        </tr></thead>
        <tbody>${rows}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">合计（${custs.length}个客户）</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${tp}</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${tc}</td>
            <td></td>
        </tr></tbody></table>`;
}

function backToSalesPerf() {
    if (window._salesPerfBack) {
        document.getElementById('salesTableContainer').innerHTML = window._salesPerfBack;
        document.getElementById('salesModalTitle').innerHTML = window._salesPerfTitle;
        window._salesPerfBack = null;
    }
}

"""

html = html[:insert_idx] + new_drill_funcs + html[insert_idx:]
print('Added renderCustDebt, backToSalesDebt, renderCustPerf, backToSalesPerf')

# ========== 5. 更新 closeSalesModal 重置所有 _back 变量 ==========
# 找到 closeSalesModal 函数
close_idx = html.find('function closeSalesModal()')
if close_idx == -1:
    print('ERROR: closeSalesModal not found')
    sys.exit(1)

brace_count = 0
close_end = -1
for i in range(close_idx, len(html)):
    if html[i] == '{': brace_count += 1
    elif html[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            close_end = i + 1
            break

old_close = html[close_idx:close_end]

# 新的 closeSalesModal，重置所有三个 _back 变量
new_close = """function closeSalesModal() {
    document.getElementById('salesModal').style.display = 'none';
    window._salesDebtBack = null;
    window._salesPerfBack = null;
    window._salesCycleBack = null;
}"""

html = html[:close_idx] + new_close + html[close_end:]
print('Updated closeSalesModal (reset all back variables)')

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nDone! HTML updated with debt+perf drill-down successfully.')
print(f'HTML size: {len(html)} chars')
