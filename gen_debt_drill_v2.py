import json

with open('debt_drill.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

js_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# 用字符串拼接避免 f-string 花括号问题
css = """*{margin:0;padding:0;box-sizing:border-box;}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  background:#0a0e1a;color:#d0d4dc;min-height:100vh;
}
.header{padding:24px 32px 8px;}
.header-title{font-size:20px;font-weight:700;color:#fff;margin-bottom:6px;}
.header-sub{font-size:13px;color:#6b7280;}
.header-sub a{color:#3b82f6;text-decoration:none;}
.header-sub a:hover{text-decoration:underline;}
.back-bar{padding:12px 32px;}
.back-btn{
  display:inline-flex;align-items:center;gap:6px;
  padding:8px 16px;border-radius:8px;
  border:1px solid rgba(255,255,255,.12);
  background:rgba(255,255,255,.05);color:#9ca3af;font-size:13px;
  cursor:pointer;transition:all .2s;
}
.back-btn:hover{background:rgba(255,255,255,.1);color:#fff;}
.page-title{padding:0 32px 8px;}
.page-title h2{font-size:18px;font-weight:700;color:#fff;margin-bottom:4px;}
.page-title .subtitle{font-size:12px;color:#6b7280;}
.dept-list{padding:12px 32px 32px;max-width:600px;}
.dept-item{
  display:block;padding:14px 18px;border-radius:10px;margin-bottom:8px;
  background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);
  color:#3b82f6;font-size:15px;font-weight:500;cursor:pointer;
  transition:all .2s;
}
.dept-item:hover{background:rgba(59,130,246,.08);border-color:rgba(59,130,246,.2);}
.table-wrap{padding:12px 32px 32px;}
table{width:100%;border-collapse:collapse;font-size:13px;}
thead th{
  text-align:left;padding:12px 14px;
  background:rgba(255,255,255,.04);color:#9ca3af;font-weight:500;font-size:12px;
  border-bottom:1px solid rgba(255,255,255,.08);white-space:nowrap;
}
thead th.right{text-align:right;}
tbody td{padding:14px;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:middle;}
tbody td.right{text-align:right;font-variant-numeric:tabular-nums;}
tbody tr:hover{background:rgba(255,255,255,.02);}
.td-link{color:#3b82f6;cursor:pointer;font-weight:500;}
.td-link:hover{text-decoration:underline;}
.amt-zero{color:#6b7280;}
.amt-total{color:#fff;font-weight:600;}
.empty-msg{padding:60px 20px;text-align:center;color:#6b7280;font-size:14px;}
.hidden{display:none !important;}
@media(max-width:768px){
  .header,.back-bar,.page-title,.table-wrap,.dept-list{padding-left:16px;padding-right:16px;}
  table{font-size:12px;}
  tbody td{padding:10px 8px;}
}"""

js = r"""let RAW = null;
let currentLevel = 1;
let currentDept = '';
let currentSales = '';

function fmtY(v){
  var n = (parseFloat(v)||0) * 10000;
  return n.toLocaleString('zh-CN', {minimumFractionDigits:2,maximumFractionDigits:2});
}

function show(id){ document.getElementById(id).classList.remove('hidden'); }
function hide(id){ document.getElementById(id).classList.add('hidden'); }

function renderLevel1(){
  currentLevel = 1;
  hide('backBar'); hide('pageTitle'); hide('lv2-table'); hide('lv3-table');
  show('lv1-header'); show('lv1-list');
  var list = document.getElementById('lv1-list');
  list.innerHTML = '';
  RAW.depts.forEach(function(d){
    var div = document.createElement('div');
    div.className = 'dept-item';
    div.textContent = d.dept;
    div.addEventListener('click', function(e){
      e.preventDefault();
      enterDept(d.dept);
    });
    list.appendChild(div);
  });
}

function enterDept(dept){
  currentLevel = 2;
  currentDept = dept;
  hide('lv1-header'); hide('lv1-list'); hide('lv3-table');
  show('backBar'); show('pageTitle'); show('lv2-table');
  document.getElementById('pageTitleText').textContent = dept + ' \u00B7 \u9500\u552E\u5458\u6B20\u6B3E\u660E\u7EC6';
  document.getElementById('pageSubtitle').textContent = '\u70B9\u51FB\u9500\u552E\u5458\u59D3\u540D\u53EF\u67E5\u770B\u8BE5\u9500\u552E\u5458\u5BA2\u6237\u6B20\u6B3E\u660E\u7EC6\uFF08\u6B63\u8D1F\u5408\u8BA1\uFF0C\u5355\u4F4D\uFF1A\u5143\uFF09';
  var salesList = RAW.dept_sales[dept] || [];
  var tbody = document.getElementById('lv2-body');
  tbody.innerHTML = '';
  if(!salesList.length){
    tbody.innerHTML = '<tr><td colspan="6" class="empty-msg">\u6682\u65E0\u6570\u636E</td></tr>';
    return;
  }
  salesList.forEach(function(s){
    var tr = document.createElement('tr');
    var td = document.createElement('td');
    td.className = 'td-link';
    td.textContent = s.name;
    td.addEventListener('click', function(e){
      e.preventDefault();
      enterSales(dept, s.name);
    });
    tr.appendChild(td);
    [['right', fmtY(s.d30)], ['right', fmtY(s.d30_90)], ['right', fmtY(s.d90_180)], ['right', fmtY(s.d180)], ['right amt-total', fmtY(s.total)]].forEach(function(col){
      var c = document.createElement('td');
      c.className = col[0];
      c.textContent = col[1];
      tr.appendChild(c);
    });
    tbody.appendChild(tr);
  });
}

function enterSales(dept, salesName){
  currentLevel = 3;
  currentSales = salesName;
  hide('lv2-table'); show('lv3-table');
  document.getElementById('pageTitleText').textContent = salesName + ' \u00B7 \u5BA2\u6237\u6B20\u6B3E\u660E\u7EC6';
  document.getElementById('pageSubtitle').textContent = '\u5404\u5BA2\u6237\u6B20\u6B3E \u00D7 \u903E\u671F\u5206\u6BB5\uFF08\u6B63\u8D1F\u5408\u8BA1\uFF0C\u5355\u4F4D\uFF1A\u5143\uFF09';
  var salesList = RAW.dept_sales[dept] || [];
  var sales = salesList.find(function(s){ return s.name === salesName; });
  var custs = sales ? (sales.custs || []) : [];
  var tbody = document.getElementById('lv3-body');
  tbody.innerHTML = '';
  if(!custs.length){
    tbody.innerHTML = '<tr><td colspan="6" class="empty-msg">\u6682\u65E0\u6570\u636E</td></tr>';
    return;
  }
  custs.forEach(function(c){
    var tr = document.createElement('tr');
    var cols = [
      ['', c.name],
      ['right', fmtY(c.d30)],
      ['right', fmtY(c.d30_90)],
      ['right', fmtY(c.d90_180)],
      ['right', fmtY(c.d180)],
      ['right amt-total', fmtY(c.total)]
    ];
    cols.forEach(function(col){
      var td = document.createElement('td');
      td.className = col[0];
      td.textContent = col[1];
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function goBack(){
  if(currentLevel === 3){ enterDept(currentDept); }
  else if(currentLevel === 2){ renderLevel1(); }
}
"""

html_body = """
<div class="header" id="lv1-header">
  <div class="header-title">各部门欠款明细（编分）</div>
  <div class="header-sub">单位：元 | 正负合计 | <a href="#">点击部门展开</a></div>
</div>
<div class="back-bar hidden" id="backBar">
  <button class="back-btn" onclick="goBack()">← 返回欠款分析</button>
</div>
<div class="page-title hidden" id="pageTitle">
  <h2 id="pageTitleText"></h2>
  <div class="subtitle" id="pageSubtitle"></div>
</div>
<div class="dept-list" id="lv1-list"></div>
<div class="table-wrap hidden" id="lv2-table">
  <table>
    <thead><tr>
      <th>销售员</th>
      <th class="right">30天内</th>
      <th class="right">30-90天</th>
      <th class="right">90-180天</th>
      <th class="right">180天以上</th>
      <th class="right">合计</th>
    </tr></thead>
    <tbody id="lv2-body"></tbody>
  </table>
</div>
<div class="table-wrap hidden" id="lv3-table">
  <table>
    <thead><tr>
      <th>客户名称</th>
      <th class="right">30天内</th>
      <th class="right">30-90天</th>
      <th class="right">90-180天</th>
      <th class="right">180天以上</th>
      <th class="right">合计</th>
    </tr></thead>
    <tbody id="lv3-body"></tbody>
  </table>
</div>
"""

# 组装最终 HTML
parts = []
parts.append('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>')
parts.append('<meta charset="UTF-8">')
parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
parts.append('<title>各部门欠款明细</title>')
parts.append('<style>\n' + css + '\n</style>')
parts.append('</head>\n<body>\n')
parts.append(html_body)
parts.append('<script>\n' + js)
parts.append('\nRAW = ' + js_data + ';\n')
parts.append('renderLevel1();\n')
parts.append('</script>\n</body>\n</html>\n')

final_html = '\n'.join(parts)

with open('欠款分析_客户下钻看板.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print('已生成，大小:', len(final_html), '字节')
