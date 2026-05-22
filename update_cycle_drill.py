# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('中西部大区26财年Q1数据看板.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Read data files
with open('sales_cycle_data.json', 'r', encoding='utf-8') as f:
    sales_cycle = f.read()

with open('cust_cycle_data.json', 'r', encoding='utf-8') as f:
    cust_cycle = f.read()

# 2. Insert data variables before '// ===== 部门弹窗 ====='
marker = '// ===== \u90E8\u95E8\u5F39\u7A97 ====='
marker_pos = html.find(marker)
if marker_pos == -1:
    print('ERROR: marker not found')
    sys.exit(1)

new_data = f"""
let salesCycleData = {sales_cycle};
let custCycleData = {cust_cycle};

"""
html = html[:marker_pos] + new_data + html[marker_pos:]
print(f'Inserted data: salesCycleData({len(sales_cycle)} chars), custCycleData({len(cust_cycle)} chars)')

# 3. Replace renderSalesCycle function
func_start = html.find('function renderSalesCycle(dept) {')
if func_start == -1:
    print('ERROR: renderSalesCycle not found')
    sys.exit(1)

brace_count = 0
func_end = -1
for i in range(func_start, len(html)):
    if html[i] == '{':
        brace_count += 1
    elif html[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            func_end = i + 1
            break

print(f'Old renderSalesCycle: pos {func_start}-{func_end}')

new_func = r"""function renderSalesCycle(dept) {
    const list = [...(salesCycleData[dept] || [])];
    list.sort((a, b) => b.cycle - a.cycle);
    const rows = list.map(s => {
        const cycle = s.cycle;
        const cycleStr = cycle > 0 ? cycle.toFixed(1) : '-';
        const cc = cycle <= 0 ? '#8892b0' : cycle > 90 ? '#ff4757' : cycle > 60 ? '#ffa502' : '#00ff88';
        const status = cycle <= 0 ? '\u26AA \u65E0\u6570\u636E' : cycle > 90 ? '\u{1F534} \u9700\u5173\u6CE8' : cycle > 60 ? '\u{1F7E1} \u504F\u9AD8' : '\u{1F7E2} \u6B63\u5E38';
        const hasCust = custCycleData[dept] && custCycleData[dept][s.name];
        const nameStyle = hasCust ? 'color:#00d4ff;cursor:pointer;text-decoration:underline;' : 'color:#ccd6f6;';
        const nameClick = hasCust ? `onclick="renderCustCycle('${dept}','${s.name}')"` : '';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;${nameStyle}" ${nameClick}>${s.name}${hasCust ? ' \u{1F4C2}' : ''}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${(s.rec_amt/10000).toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ffa502;text-align:right;">${(s.debt_amt/10000).toFixed(2)}</td>
            <td style="padding:7px 5px;color:${cc};text-align:right;font-weight:600;">${cycleStr}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${status}</td>
        </tr>`;
    }).join('');
    const tc = list.reduce((s, v) => s + v.rec_amt, 0);
    const td = list.reduce((s, v) => s + v.debt_amt, 0);
    document.getElementById('salesModalTitle').innerHTML = `\u23F1\uFE0F ${dept} - \u9500\u552E\u5458\u56DE\u6B3E\u5468\u671F\u660E\u7EC6 <span style="font-size:0.7em;color:#8892b0;">(\u70B9\u51FB\u9500\u552E\u5458\u540D\u67E5\u770B\u5BA2\u6237\u660E\u7EC6)</span>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.85em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;">\u9500\u552E\u5458</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">\u8BA4\u6B3E\u91D1\u989D(\u4E07)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">\u6B20\u6B3E\u91D1\u989D(\u4E07)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">\u56DE\u6B3E\u5468\u671F(\u5929)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">\u72B6\u6001</th>
        </tr></thead>
        <tbody>${rows}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">\u5408\u8BA1\uFF08${list.length}\u4EBA\uFF09</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${(tc/10000).toFixed(2)}</td>
            <td style="padding:8px 6px;color:#ffa502;text-align:right;">${(td/10000).toFixed(2)}</td>
            <td colspan="2"></td>
        </tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}"""

html = html[:func_start] + new_func + html[func_end:]
print('Replaced renderSalesCycle')

# 4. Add renderCustCycle and backToSalesCycle after backToSalesDebt function
back_start = html.find('function backToSalesDebt() {')
if back_start == -1:
    print('ERROR: backToSalesDebt not found')
    sys.exit(1)

brace_count = 0
back_end = -1
for i in range(back_start, len(html)):
    if html[i] == '{':
        brace_count += 1
    elif html[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            back_end = i + 1
            break

print(f'backToSalesDebt ends at: {back_end}')

new_funcs = r"""

// ===== 客户回款周期明细（第二级下钻）=====
function renderCustCycle(dept, salesName) {
    window._salesCycleBack = document.getElementById('salesTableContainer').innerHTML;
    window._salesCycleTitle = document.getElementById('salesModalTitle').innerHTML;

    const custList = custCycleData[dept] && custCycleData[dept][salesName] ? custCycleData[dept][salesName] : [];
    if (!custList.length) return;

    const rows = custList.map(c => {
        const cycle = c.cycle;
        const cycleStr = cycle > 0 ? cycle.toFixed(1) : '-';
        const cc = cycle <= 0 ? '#8892b0' : cycle > 90 ? '#ff4757' : cycle > 60 ? '#ffa502' : '#00ff88';
        const status = cycle <= 0 ? '\u26AA \u65E0\u6570\u636E' : cycle > 90 ? '\u{1F534} \u9700\u5173\u6CE8' : cycle > 60 ? '\u{1F7E1} \u504F\u9AD8' : '\u{1F7E2} \u6B63\u5E38';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;color:#ccd6f6;max-width:300px;word-break:break-all;">${c.name}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${(c.rec_amt/10000).toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ffa502;text-align:right;">${(c.debt_amt/10000).toFixed(2)}</td>
            <td style="padding:7px 5px;color:${cc};text-align:right;font-weight:600;">${cycleStr}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${status}</td>
        </tr>`;
    }).join('');

    const tc = custList.reduce((s, c) => s + c.rec_amt, 0);
    const td = custList.reduce((s, c) => s + c.debt_amt, 0);

    document.getElementById('salesModalTitle').innerHTML = `\u23F1\uFE0F ${salesName} - \u5BA2\u6237\u56DE\u6B3E\u5468\u671F\u660E\u7EC6 <span style="font-size:0.75em;color:#8892b0;">(${dept})</span> <button onclick="backToSalesCycle()" style="margin-left:12px;background:rgba(0,212,255,0.2);border:1px solid rgba(0,212,255,0.4);color:#00d4ff;border-radius:6px;padding:3px 12px;font-size:0.85em;cursor:pointer;">\u2190 \u8FD4\u56DE\u9500\u552E\u5458</button>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.8em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;text-align:left;">\u5BA2\u6237\u540D\u79F0</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">\u8BA4\u6B3E\u91D1\u989D(\u4E07)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">\u6B20\u6B3E\u91D1\u989D(\u4E07)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">\u56DE\u6B3E\u5468\u671F(\u5929)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">\u72B6\u6001</th>
        </tr></thead>
        <tbody>${rows}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">\u5408\u8BA1\uFF08${custList.length}\u4E2A\u5BA2\u6237\uFF09</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${(tc/10000).toFixed(2)}</td>
            <td style="padding:8px 6px;color:#ffa502;text-align:right;">${(td/10000).toFixed(2)}</td>
            <td colspan="2"></td>
        </tr></tbody></table>`;
}

function backToSalesCycle() {
    if (window._salesCycleBack) {
        document.getElementById('salesTableContainer').innerHTML = window._salesCycleBack;
        document.getElementById('salesModalTitle').innerHTML = window._salesCycleTitle;
        window._salesCycleBack = null;
    }
}

"""

html = html[:back_end] + new_funcs + html[back_end:]
print('Added renderCustCycle and backToSalesCycle')

# 5. Update closeSalesModal to reset cycle back state
old_close = "    window._salesDebtBack = null;\n    window._salesPerfBack = null;\n}"
new_close = "    window._salesDebtBack = null;\n    window._salesPerfBack = null;\n    window._salesCycleBack = null;\n}"
if old_close in html:
    html = html.replace(old_close, new_close)
    print('Updated closeSalesModal')
else:
    print('WARNING: closeSalesModal pattern not found, trying alternative')
    # Try to find and fix it
    idx = html.find('function closeSalesModal()')
    if idx != -1:
        # Just add a line before the closing of the function
        pass

with open('中西部大区26财年Q1数据看板.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('\nDone! HTML updated successfully.')
