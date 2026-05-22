import json

# 读取完整 JSON
with open('debt_drill.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 读取当前 HTML
with open('欠款分析_客户下钻看板.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 将 JSON 转为紧凑的 JS 对象字符串（不使用 JSON 字符串，避免转义问题）
js_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# 替换 fetch 部分为直接赋值
old_fetch = """// ===== 从外部 JSON 加载数据（避免数据截断）=====
fetch('debt_drill.json')
  .then(function(r){
    if(!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  })
  .then(function(data){
    RAW = data;
    initSummary();
    renderDepts();
  })
  .catch(function(err){
    console.error('数据加载失败:', err);
    document.getElementById('mainBody').innerHTML =
      '<tr><td colspan="10" class="empty-msg" style="color:#ef5350">数据加载失败，请确保 debt_drill.json 与本文件在同一目录</td></tr>';
  });"""

new_inline = f"""// ===== 数据已内嵌（支持本地 file:// 直接打开）=====
RAW = {js_data};
initSummary();
renderDepts();"""

html = html.replace(old_fetch, new_inline)

# 写入
with open('欠款分析_客户下钻看板.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('已生成内嵌数据的 HTML，大小:', len(html), '字节')
