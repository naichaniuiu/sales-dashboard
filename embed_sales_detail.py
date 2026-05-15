"""将 sales_detail.json 数据嵌入 HTML，移除 fetch 依赖"""
import json, re

# 读取数据
with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
    data = json.load(f)

# 序列化为紧凑 JSON（避免换行导致 HTML 格式问题）
embedded_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# 读取 HTML
with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', encoding='utf-8') as f:
    html = f.read()

# 1. 替换变量声明 + loadSalesDetail 函数
old_block = """let salesDetailLoaded = false;
let salesDetailData = {};

function loadSalesDetail() {
    if (salesDetailLoaded) return Promise.resolve();
    return fetch('sales_detail.json').then(r => r.json()).then(d => {
        salesDetailData = d;
        salesDetailLoaded = true;
    }).catch(e => console.error('加载销售员明细失败', e));
}"""

new_block = f"""let salesDetailLoaded = true; // 数据已内嵌，无需 fetch
let salesDetailData = {embedded_json};

function loadSalesDetail() {{
    // 数据已通过内嵌 JSON 提供，此函数仅做兼容保留
}}"""

html = html.replace(old_block, new_block)

# 2. 简化 showSalesDetail：移除 fetch 逻辑
old_show = """function showSalesDetail(dept) {
    if (!salesDetailLoaded) {
        document.getElementById('salesTableContainer').innerHTML = '<div style="color:#8892b0;text-align:center;padding:40px;">加载中...</div>';
        document.getElementById('salesModal').style.display = 'flex';
        fetch('sales_detail.json').then(r=>r.json()).then(d=>{
            salesDetailData = d;
            salesDetailLoaded = true;
            renderSalesTable(dept);
        });
        return;
    }
    renderSalesTable(dept);
}"""

new_show = """function showSalesDetail(dept) {
    renderSalesTable(dept);
}"""

html = html.replace(old_show, new_show)

# 保存
with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Done! 数据已嵌入，fetch 已移除。')
print(f'JSON 大小: {len(embedded_json)} 字符')
