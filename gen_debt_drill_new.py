import json

# 读取数据
with open('debt_drill.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def fmt_yuan(v):
    """万元转元，带千分位"""
    yuan = float(v) * 10000 if v is not None else 0
    return f"{yuan:,.2f}"

def fmt_yuan_plain(v):
    """万元转元，纯数字（用于排序等）"""
    return float(v) * 10000 if v is not None else 0

# 生成 JS 数据
js_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>各部门欠款明细</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  background:#0a0e1a;color:#d0d4dc;min-height:100vh;
}}

/* ===== 顶部标题栏 ===== */
.header{{
  padding:24px 32px 8px;
}}
.header-title{{
  font-size:20px;font-weight:700;color:#fff;margin-bottom:6px;
}}
.header-sub{{
  font-size:13px;color:#6b7280;
}}
.header-sub a{{
  color:#3b82f6;text-decoration:none;
}}
.header-sub a:hover{{
  text-decoration:underline;
}}

/* ===== 返回按钮 ===== */
.back-bar{{
  padding:12px 32px;
}}
.back-btn{{
  display:inline-flex;align-items:center;gap:6px;
  padding:8px 16px;border-radius:8px;
  border:1px solid rgba(255,255,255,.12);
  background:rgba(255,255,255,.05);color:#9ca3af;font-size:13px;
  cursor:pointer;transition:all .2s;
}}
.back-btn:hover{{
  background:rgba(255,255,255,.1);color:#fff;
}}
.back-btn svg{{
  width:14px;height:14px;
}}

/* ===== 页面标题区 ===== */
.page-title{{
  padding:0 32px 8px;
}}
.page-title h2{{
  font-size:18px;font-weight:700;color:#fff;margin-bottom:4px;
}}
.page-title .subtitle{{
  font-size:12px;color:#6b7280;
}}

/* ===== 一级：站点列表 ===== */
.dept-list{{
  padding:12px 32px 32px;
  max-width:600px;
}}
.dept-list a{{
  display:block;padding:14px 18px;
  border-radius:10px;margin-bottom:8px;
  background:rgba(255,255,255,.03);
  border:1px solid rgba(255,255,255,.06);
  color:#3b82f6;font-size:15px;font-weight:500;
  text-decoration:none;cursor:pointer;
  transition:all .2s;
}}
.dept-list a:hover{{
  background:rgba(59,130,246,.08);
  border-color:rgba(59,130,246,.2);
}}

/* ===== 二级/三级：表格 ===== */
.table-wrap{{
  padding:12px 32px 32px;
}}
table{{
  width:100%;border-collapse:collapse;
  font-size:13px;
}}
thead th{{
  text-align:left;padding:12px 14px;
  background:rgba(255,255,255,.04);
  color:#9ca3af;font-weight:500;font-size:12px;
  border-bottom:1px solid rgba(255,255,255,.08);
  white-space:nowrap;
}}
thead th.right{{ text-align:right; }}
tbody td{{
  padding:14px;border-bottom:1px solid rgba(255,255,255,.05);
  vertical-align:middle;
}}
tbody td.right{{
  text-align:right;font-variant-numeric:tabular-nums;
}}
tbody tr:hover{{
  background:rgba(255,255,255,.02);
}}

/* 销售员/客户名称可点击 */
.td-link{{
  color:#3b82f6;cursor:pointer;font-weight:500;
}}
.td-link:hover{{
  text-decoration:underline;
}}

/* 金额颜色 */
.amt-zero{{ color:#6b7280; }}
.amt-warn{{ color:#f59e0b; }}
.amt-bad{{ color:#ef4444; }}
.amt-crit{{ color:#dc2626; }}
.amt-total{{ color:#fff;font-weight:600; }}

/* 空状态 */
.empty-msg{{
  padding:60px 20px;text-align:center;color:#6b7280;font-size:14px;
}}

/* 隐藏 */
.hidden{{ display:none !important; }}

@media(max-width:768px){{
  .header,.back-bar,.page-title,.table-wrap,.dept-list{{
    padding-left:16px;padding-right:16px;
  }}
  table{{ font-size:12px; }}
  tbody td{{ padding:10px 8px; }}
}}
</style>
</head>
<body>

<!-- 顶部标题 -->
<div class="header" id="lv1-header">
  <div class="header-title">各部门欠款明细（编分）</div>
  <div class="header-sub">单位：元 | 正负合计 | <a href="#">点击部门展开</a></div>
</div>

<!-- 二级/三级：返回按钮 -->
<div class="back-bar hidden" id="backBar">
  <button class="back-btn" onclick="goBack()">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
    返回欠款分析
  </button>
</div>

<!-- 二级/三级：页面标题 -->
<div class="page-title hidden" id="pageTitle">
  <h2 id="pageTitleText"></h2>
  <div class="subtitle" id="pageSubtitle"></div>
</div>

<!-- 一级：站点列表 -->
<div class="dept-list" id="lv1-list"></div>

<!-- 二级：销售员表格 -->
<div class="table-wrap hidden" id="lv2-table">
  <table>
    <thead>
      <tr>
        <th>销售员</th>
        <th class="right">30天内</th>
        <th class="right">30-90天</th>
        <th class="right">90-180天</th>
        <th class="right">180天以上</th>
        <th class="right">合计</th>
      </tr>
    </thead>
    <tbody id="lv2-body"></tbody>
  </table>
</div>

<!-- 三级：客户表格 -->
<div class="table-wrap hidden" id="lv3-table">
  <table>
    <thead>
      <tr>
        <th>客户名称</th>
        <th class="right">30天内</th>
        <th class="right">30-90天</th>
        <th class="right">90-180天</th>
        <th class="right">180天以上</th>
        <th class="right">合计</th>
      </tr>
    </thead>
    <tbody id="lv3-body"></tbody>
  </table>
</div>

<script>
let RAW = null;
let currentLevel = 1;
let currentDept = '';
let currentSales = '';

function fmtY(v){{
  var n = (parseFloat(v)||0) * 10000;
  return n.toLocaleString('zh-CN', {{minimumFractionDigits:2,maximumFractionDigits:2}});
}}

function amtClass(v){{
  var n = parseFloat(v)||0;
  if(n === 0) return 'amt-zero';
  if(n <= 30) return '';
  if(n <= 90) return 'amt-warn';
  if(n <= 180) return 'amt-bad';
  return 'amt-crit';
}}

function amtClassY(v){{
  var n = (parseFloat(v)||0) * 10000;
  if(n === 0) return 'amt-zero';
  return '';
}}

function show(id){{ document.getElementById(id).classList.remove('hidden'); }}
function hide(id){{ document.getElementById(id).classList.add('hidden'); }}

// ===== 一级：站点列表 =====
function renderLevel1(){{
  currentLevel = 1;
  hide('backBar');
  hide('pageTitle');
  hide('lv2-table');
  hide('lv3-table');
  show('lv1-header');
  show('lv1-list');

  var list = document.getElementById('lv1-list');
  list.innerHTML = '';
  RAW.depts.forEach(function(d){{
    var a = document.createElement('a');
    a.textContent = d.dept;
    a.onclick = function(){{ enterDept(d.dept); }};
    list.appendChild(a);
  }});
}}

// ===== 二级：销售员表格 =====
function enterDept(dept){{
  currentLevel = 2;
  currentDept = dept;
  hide('lv1-header');
  hide('lv1-list');
  hide('lv3-table');
  show('backBar');
  show('pageTitle');
  show('lv2-table');

  document.getElementById('pageTitleText').textContent = dept + ' · 销售员欠款明细';
  document.getElementById('pageSubtitle').textContent = '点击销售员姓名可查看该销售员客户欠款明细（正负合计，单位：元）';

  var salesList = RAW.dept_sales[dept] || [];
  var tbody = document.getElementById('lv2-body');
  tbody.innerHTML = '';

  if(!salesList.length){{
    tbody.innerHTML = '<tr><td colspan="6" class="empty-msg">暂无数据</td></tr>';
    return;
  }}

  salesList.forEach(function(s){{
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td class="td-link" onclick="enterSales(\''+dept+'\',\''+s.name+'\')">'+s.name+'</td>' +
      '<td class="right '+amtClassY(s.d30)+'">'+fmtY(s.d30)+'</td>' +
      '<td class="right '+amtClassY(s.d30_90)+'">'+fmtY(s.d30_90)+'</td>' +
      '<td class="right '+amtClassY(s.d90_180)+'">'+fmtY(s.d90_180)+'</td>' +
      '<td class="right '+amtClassY(s.d180)+'">'+fmtY(s.d180)+'</td>' +
      '<td class="right amt-total">'+fmtY(s.total)+'</td>';
    tbody.appendChild(tr);
  }});
}}

// ===== 三级：客户表格 =====
function enterSales(dept, salesName){{
  currentLevel = 3;
  currentSales = salesName;
  hide('lv2-table');
  show('lv3-table');

  document.getElementById('pageTitleText').textContent = salesName + ' · 客户欠款明细';
  document.getElementById('pageSubtitle').textContent = '各客户欠款 × 逾期分段（正负合计，单位：元）';

  var salesList = RAW.dept_sales[dept] || [];
  var sales = salesList.find(function(s){{ return s.name === salesName; }});
  var custs = sales ? (sales.custs || []) : [];

  var tbody = document.getElementById('lv3-body');
  tbody.innerHTML = '';

  if(!custs.length){{
    tbody.innerHTML = '<tr><td colspan="6" class="empty-msg">暂无数据</td></tr>';
    return;
  }}

  custs.forEach(function(c){{
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td>'+c.name+'</td>' +
      '<td class="right '+amtClassY(c.d30)+'">'+fmtY(c.d30)+'</td>' +
      '<td class="right '+amtClassY(c.d30_90)+'">'+fmtY(c.d30_90)+'</td>' +
      '<td class="right '+amtClassY(c.d90_180)+'">'+fmtY(c.d90_180)+'</td>' +
      '<td class="right '+amtClassY(c.d180)+'">'+fmtY(c.d180)+'</td>' +
      '<td class="right amt-total">'+fmtY(c.total)+'</td>';
    tbody.appendChild(tr);
  }});
}}

// ===== 返回 =====
function goBack(){{
  if(currentLevel === 3){{
    enterDept(currentDept);
  }} else if(currentLevel === 2){{
    renderLevel1();
  }}
}}

// ===== 加载数据 =====
RAW = {js_data};
renderLevel1();
</script>
</body>
</html>
'''

with open('欠款分析_客户下钻看板.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('已生成新的欠款分析看板，大小:', len(html), '字节')
