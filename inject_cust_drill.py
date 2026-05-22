import json

# 读取看板 HTML
with open('中西部大区26财年Q1数据看板.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 读取 debt_drill.json 中的 dept_sales（含客户层级）
with open('debt_drill.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
dept_sales = data['dept_sales']
dept_sales_js = json.dumps(dept_sales, ensure_ascii=False, separators=(',', ':'))

# 1. 在 salesDetailData 声明之后注入 deptCustData
inject_marker = '// ===== 销售员明细数据 =====\nlet salesDetailData'
inject_after = 'let salesDetailData'
idx = html.find(inject_after)
# 找到 salesDetailData 赋值的结束位置（分号后的换行）
# salesDetailData 是一个很长的 JSON 赋值，在独立一行
# 我们需要在它之后插入 deptCustData
# 找到 salesDetailData 那一行的结尾
line_end = html.find('\n', idx)
# 但 salesDetailData 可能跨多行（JSON很长），我们需要找到完整的赋值结束
# 用括号匹配来找到结束
brace_start = html.find('{', idx)
depth = 0
pos = brace_start
while pos < len(html):
    if html[pos] == '{':
        depth += 1
    elif html[pos] == '}':
        depth -= 1
        if depth == 0:
            pos += 1  # 跳过最后的 }
            break
    pos += 1

# 现在找分号
semi_pos = html.find(';', pos)
# 插入 deptCustData
insert_text = '\n\n// ===== 客户下钻数据（部门→销售员→客户）=====\nlet deptCustData = ' + dept_sales_js + ';\n'

html = html[:semi_pos+1] + insert_text + html[semi_pos+1:]

# 2. 替换 renderSalesDebt 函数，增加销售员→客户下钻
old_func_start = 'function renderSalesDebt(dept) {'
old_func_end_idx = html.find(old_func_start)
# 找到函数结束 - 匹配大括号
func_brace_start = html.find('{', old_func_end_idx)
func_depth = 0
func_pos = func_brace_start
while func_pos < len(html):
    if html[func_pos] == '{':
        func_depth += 1
    elif html[func_pos] == '}':
        func_depth -= 1
        if func_depth == 0:
            func_pos += 1
            break
    # 跳过字符串内的花括号
    elif html[func_pos] == "'":
        func_pos += 1
        while func_pos < len(html) and html[func_pos] != "'":
            func_pos += 1
    elif html[func_pos] == '"':
        func_pos += 1
        while func_pos < len(html) and html[func_pos] != '"':
            func_pos += 1
    elif html[func_pos] == '`':
        func_pos += 1
        while func_pos < len(html) and html[func_pos] != '`':
            func_pos += 1
    func_pos += 1

old_func = html[old_func_end_idx:func_pos]

new_func = """function renderSalesDebt(dept) {
    const list = [...(salesDetailData[dept] || [])];
    list.sort((a, b) => b.total_debt - a.total_debt);
    const rows = list.map(s => {
        const dc = s.total_debt > 50 ? '#ff4757' : s.total_debt > 20 ? '#ffa502' : '#00ff88';
        const status = s.total_debt > 50 ? '\\u{1F534} 高风险' : s.total_debt > 20 ? '\\u{1F7E1} 关注' : '\\u{1F7E2} 较好';
        // 检查是否有客户下钻数据
        const hasCust = deptCustData[dept] && deptCustData[dept].find(x => x.name === s.name);
        const nameStyle = hasCust ? 'color:#00d4ff;cursor:pointer;text-decoration:underline;' : 'color:#ccd6f6;';
        const nameClick = hasCust ? `onclick="renderCustDebt('${dept}','${s.name}')"` : '';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;${nameStyle}" ${nameClick}>${s.name}${hasCust ? ' \\u{1F4C2}' : ''}</td>
            <td style="padding:7px 5px;color:${dc};text-align:right;font-weight:600;">${s.total_debt.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${s.d30.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ffa502;text-align:right;">${s.d30_90.toFixed(2)}</td>
            <td style="padding:7px 5px;color:${s.d90_180>0?'#ff4757':'#8892b0'};text-align:right;">${s.d90_180.toFixed(2)}</td>
            <td style="padding:7px 5px;color:${s.d180>0?'#ff4757':'#8892b0'};text-align:right;">${s.d180.toFixed(2)}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${status}</td>
        </tr>`;
    }).join('');
    const td = list.reduce((s, v) => s + v.total_debt, 0).toFixed(2);
    document.getElementById('salesModalTitle').innerHTML = `\\u{1F4B0} ${dept} - 销售员欠款明细 <span style="font-size:0.7em;color:#8892b0;">（点击销售员名查看客户明细）</span>`;
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

html = html.replace(old_func, new_func)

# 3. 在 closeSalesModal 函数之后添加 renderCustDebt 函数
close_func = 'function closeSalesModal() {\n    document.getElementById(\'salesModal\').style.display = \'none\';\n}'

new_close_and_cust = """function closeSalesModal() {
    document.getElementById('salesModal').style.display = 'none';
    window._salesDebtBack = null;
}

// ===== 客户欠款明细（第三级下钻）=====
function renderCustDebt(dept, salesName) {
    // 保存当前销售员表格内容，以便返回
    window._salesDebtBack = document.getElementById('salesTableContainer').innerHTML;
    window._salesDebtTitle = document.getElementById('salesModalTitle').innerHTML;
    
    const salesList = deptCustData[dept] || [];
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
    
    document.getElementById('salesModalTitle').innerHTML = `\\u{1F4B0} ${salesName} - 客户欠款明细 <span style="font-size:0.75em;color:#8892b0;">（${dept}）</span> <button onclick="backToSalesDebt()" style="margin-left:12px;background:rgba(0,212,255,0.2);border:1px solid rgba(0,212,255,0.4);color:#00d4ff;border-radius:6px;padding:3px 12px;font-size:0.85em;cursor:pointer;">\\u2190 返回销售员</button>`;
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
}"""

html = html.replace(close_func, new_close_and_cust)

with open('中西部大区26财年Q1数据看板.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('已注入客户下钻数据到 Q1 数据看板')
print('HTML 大小:', len(html), '字节')
