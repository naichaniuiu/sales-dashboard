# -*- coding: utf-8 -*-
"""
根据最新JSON数据重新生成HTML看板
"""
import json
from datetime import datetime

def load_data():
    """加载数据文件"""
    with open('C:/Users/wm881/WorkBuddy/20260513090923/dashboard_final.json', encoding='utf-8') as f:
        return json.load(f)

def generate_main_dashboard(data):
    """生成主看板HTML"""
    today = datetime.now().strftime('%Y-%m-%d')
    dept_data = data['dept_data']
    total = data['total']
    risk = data['risk_customers'][:5]
    cycle_data = data['cycle']['data']
    
    # 部门表格行
    dept_rows = ''
    for d in dept_data:
        yoy_cls = 'trend-down' if d['yoy'] < 0 else 'trend-up'
        yoy_sign = '' if d['yoy'] == 0 else ('↓' if d['yoy'] < 0 else '↑')
        comp_cls = 'negative' if d['completion'] < 50 else 'warning' if d['completion'] < 80 else 'highlight'
        dept_rows += f'''<tr onclick="showSalesDetail('{d['dept']}')" style="cursor:pointer;">
            <td>🏢 {d['dept']}</td>
            <td>{d['v26']:.2f}</td>
            <td>{d['v25']:.2f}</td>
            <td class="{yoy_cls}">{yoy_sign}{abs(d['yoy'])}%</td>
            <td>{d['target']:.1f}</td>
            <td class="{comp_cls}">{d['completion']:.1f}%</td>
            <td>{d['sales']}</td>
            <td>{d['total_debt']:.2f}</td>
            <td>{d['collect']:.2f}</td>
        </tr>'''
    
    # 高风险客户
    risk_rows = ''
    for name, amt in risk:
        risk_rows += f'<li class="risk-item"><span class="risk-name">{name}</span><span class="risk-amount negative">{amt}万</span></li>'
    
    # 回款周期排序
    cycle_sorted = sorted(cycle_data, key=lambda x: x[1], reverse=True)
    cycle_rows = ''
    for dept, cyc in cycle_sorted[:9]:
        cyc_cls = 'negative' if cyc > 90 else 'warning' if cyc > 60 else 'highlight'
        badge = 'badge-down' if cyc > 90 else 'badge-warning' if cyc > 60 else 'badge-good'
        label = '需关注' if cyc > 90 else '一般' if cyc > 60 else '良好'
        cycle_rows += f'''<tr>
            <td>🏢 {dept}</td>
            <td class="{cyc_cls}">{cyc:.1f}天</td>
            <td><span class="status-badge {badge}">{label}</span></td>
        </tr>'''
    
    # JS数据
    js_labels = json.dumps([d['dept'] for d in dept_data])
    js_perf26 = json.dumps([d['v26'] for d in dept_data])
    js_perf25 = json.dumps([d['v25'] for d in dept_data])
    js_completion = json.dumps([d['completion'] for d in dept_data])
    
    comp_cls_total = 'negative' if total['completion'] < 50 else 'warning' if total['completion'] < 80 else 'highlight'
    yoy_cls_total = 'trend-down' if total['yoy'] < 0 else 'trend-up'
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中西部大区 26财年Q1 数据看板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #0a0e27; color: #fff; line-height: 1.6; min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ font-size: 2.2em; background: linear-gradient(135deg, #00d4ff 0%, #7b2ff7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 10px; }}
        .header p {{ color: #8892b0; font-size: 1.1em; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .kpi-card {{ background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%); border-radius: 16px; padding: 24px; text-align: center; border: 1px solid rgba(255,255,255,0.1); transition: transform 0.3s, box-shadow 0.3s; }}
        .kpi-card:hover {{ transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,212,255,0.15); }}
        .kpi-icon {{ font-size: 2.5em; margin-bottom: 10px; }}
        .kpi-card h3 {{ color: #8892b0; font-size: 0.9em; font-weight: 500; margin-bottom: 8px; }}
        .kpi-card .value {{ font-size: 2.2em; font-weight: 700; color: #00d4ff; }}
        .kpi-card .sub {{ font-size: 0.85em; color: #8892b0; margin-top: 5px; }}
        .highlight {{ color: #00ff88 !important; }}
        .negative {{ color: #ff4757 !important; }}
        .warning {{ color: #ffa502 !important; }}
        .module {{ background: rgba(255,255,255,0.05); border-radius: 20px; padding: 30px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 25px; }}
        .module-title {{ font-size: 1.3em; margin-bottom: 10px; color: #00d4ff; display: flex; align-items: center; gap: 10px; }}
        .charts-section {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 30px; }}
        .chart-box {{ background: rgba(255,255,255,0.03); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.08); }}
        .chart-box h3 {{ color: #00d4ff; margin-bottom: 15px; font-size: 1.1em; text-align: center; }}
        .chart-container {{ position: relative; height: 320px; }}
        .dept-table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        .dept-table thead th {{ background: rgba(0,212,255,0.1); color: #00d4ff; padding: 12px 8px; text-align: center; font-weight: 500; border-bottom: 1px solid rgba(0,212,255,0.2); white-space: nowrap; }}
        .dept-table tbody tr {{ border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s; cursor: pointer; }}
        .dept-table tbody tr:hover {{ background: rgba(255,255,255,0.05); }}
        .dept-table tbody td {{ padding: 11px 8px; text-align: center; color: #ccd6f6; }}
        .dept-table tbody td:first-child {{ text-align: left; padding-left: 12px; }}
        .dept-table tfoot tr {{ background: rgba(0,212,255,0.08); border-top: 2px solid rgba(0,212,255,0.3); }}
        .dept-table tfoot td {{ padding: 12px 8px; text-align: center; color: #00d4ff; font-weight: 600; }}
        .dept-table tfoot td:first-child {{ text-align: left; padding-left: 12px; }}
        .trend-down {{ color: #ff4757; font-weight: 600; }}
        .trend-up {{ color: #00ff88; font-weight: 600; }}
        .status-badge {{ padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
        .badge-down {{ background: rgba(255,71,87,0.2); color: #ff4757; border: 1px solid rgba(255,71,87,0.3); }}
        .badge-warning {{ background: rgba(255,165,2,0.2); color: #ffa502; border: 1px solid rgba(255,165,2,0.3); }}
        .badge-good {{ background: rgba(0,212,255,0.2); color: #00d4ff; border: 1px solid rgba(0,212,255,0.3); }}
        .risk-list {{ list-style: none; padding: 0; }}
        .risk-item {{ display: flex; justify-content: space-between; padding: 12px 15px; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #ff4757; }}
        .risk-name {{ color: #ccd6f6; }}
        .risk-amount {{ font-weight: 600; }}
        .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; }}
        .modal-overlay.active {{ display: flex; align-items: center; justify-content: center; }}
        .modal {{ background: #1a2040; border-radius: 20px; padding: 30px; max-width: 900px; width: 90%; max-height: 80vh; overflow-y: auto; border: 1px solid rgba(0,212,255,0.3); }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .modal-title {{ color: #00d4ff; font-size: 1.2em; font-weight: 600; }}
        .modal-close {{ background: rgba(255,255,255,0.1); border: none; color: #fff; width: 30px; height: 30px; border-radius: 50%; cursor: pointer; font-size: 1.2em; display: flex; align-items: center; justify-content: center; }}
        .modal-close:hover {{ background: rgba(255,71,87,0.3); }}
        .modal-table {{ width: 100%; border-collapse: collapse; font-size: 0.85em; }}
        .modal-table th {{ background: rgba(0,212,255,0.1); color: #00d4ff; padding: 10px 8px; text-align: center; }}
        .modal-table td {{ padding: 8px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        @media (max-width: 768px) {{ .charts-section {{ grid-template-columns: 1fr; }} .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} .dept-table {{ font-size: 0.8em; }} }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>中西部大区 26财年Q1 数据看板</h1>
        <p>数据更新时间：{today} &nbsp;|&nbsp; 数据来源：业绩 欠款看板.xlsx</p>
    </div>

    <!-- 核心KPI -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">💰</div>
            <h3>26Q1 实际业绩</h3>
            <div class="value">{total['v26']:.2f}<span style="font-size:0.5em;">万</span></div>
            <div class="sub">目标：{total['target']:.1f}万</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🎯</div>
            <h3>Q1目标完成率</h3>
            <div class="value {comp_cls_total}">{total['completion']:.1f}%</div>
            <div class="sub">同比 {yoy_cls_total} {abs(total['yoy']):.1f}%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <h3>总欠款金额</h3>
            <div class="value negative">{total['debt']:.2f}<span style="font-size:0.5em;">万</span></div>
            <div class="sub">认款：{total['collect']:.2f}万</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <h3>在职销售员</h3>
            <div class="value">{total['sales']}</div>
            <div class="sub">人</div>
        </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
        <div class="chart-box">
            <h3>📈 26Q1 vs 25Q1 业绩对比</h3>
            <div class="chart-container"><canvas id="perfChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3>📊 26Q1 目标完成率</h3>
            <div class="chart-container"><canvas id="targetChart"></canvas></div>
        </div>
    </div>

    <!-- 部门明细表 -->
    <div class="module">
        <div class="module-title">📋 部门业绩明细</div>
        <table class="dept-table">
            <thead>
                <tr>
                    <th>部门</th>
                    <th>26Q1业绩</th>
                    <th>25Q1业绩</th>
                    <th>同比</th>
                    <th>目标</th>
                    <th>完成率</th>
                    <th>销售员</th>
                    <th>欠款</th>
                    <th>认款</th>
                </tr>
            </thead>
            <tbody>
                {dept_rows}
            </tbody>
            <tfoot>
                <tr>
                    <td>合计</td>
                    <td>{total['v26']:.2f}</td>
                    <td>{total['v25']:.2f}</td>
                    <td class="{yoy_cls_total}">{total['yoy']:.1f}%</td>
                    <td>{total['target']:.1f}</td>
                    <td>{total['completion']:.1f}%</td>
                    <td>{total['sales']}</td>
                    <td>{total['debt']:.2f}</td>
                    <td>{total['collect']:.2f}</td>
                </tr>
            </tfoot>
        </table>
    </div>

    <!-- 回款周期分析 -->
    <div class="module">
        <div class="module-title">⏱️ 部门回款周期分析</div>
        <table class="dept-table">
            <thead>
                <tr><th>部门</th><th>平均回款周期</th><th>状态</th></tr>
            </thead>
            <tbody>{cycle_rows}</tbody>
        </table>
    </div>

    <!-- 高风险客户 -->
    <div class="module">
        <div class="module-title">⚠️ 高风险客户（90天以上欠款）</div>
        <ul class="risk-list">
            {risk_rows}
        </ul>
    </div>
</div>

<!-- 销售员明细弹窗 -->
<div class="modal-overlay" id="salesModal">
    <div class="modal">
        <div class="modal-header">
            <div class="modal-title" id="modalTitle">销售员明细</div>
            <button class="modal-close" onclick="closeModal()">×</button>
        </div>
        <div id="modalContent"></div>
    </div>
</div>

<script>
// 图表数据
const deptLabels = {js_labels};
const perf26Data = {js_perf26};
const perf25Data = {js_perf25};
const completionData = {js_completion};

// 业绩对比图
new Chart(document.getElementById('perfChart'), {{
    type: 'bar',
    data: {{
        labels: deptLabels,
        datasets: [
            {{ label: '26Q1', data: perf26Data, backgroundColor: 'rgba(0,212,255,0.8)' }},
            {{ label: '25Q1', data: perf25Data, backgroundColor: 'rgba(123,47,247,0.6)' }}
        ]
    }},
    options: {{ responsive: true, plugins: {{ legend: {{ position: 'top' }} }} }}
}});

// 目标完成率图
new Chart(document.getElementById('targetChart'), {{
    type: 'bar',
    data: {{
        labels: deptLabels,
        datasets: [{{ label: '完成率%', data: completionData, backgroundColor: completionData.map(v => v >= 80 ? 'rgba(0,255,136,0.8)' : v >= 50 ? 'rgba(255,165,2,0.8)' : 'rgba(255,71,87,0.8)') }}]
    }},
    options: {{ responsive: true, indexAxis: 'y', plugins: {{ legend: {{ display: false }} }} }}
}});

// 销售员明细（从sales_detail.json加载）
let salesData = {{}};
fetch('sales_detail.json')
    .then(r => r.json())
    .then(d => {{ salesData = d; }});

function showSalesDetail(dept) {{
    document.getElementById('modalTitle').textContent = dept + ' 销售员明细';
    const people = salesData[dept] || [];
    let html = '<table class="modal-table"><thead><tr><th>姓名</th><th>状态</th><th>26Q1业绩</th><th>欠款合计</th></tr></thead><tbody>';
    for (const p of people) {{
        html += `<tr><td>${{p.name}}</td><td>${{p.status}}</td><td>${{p.perf.toFixed(2)}}</td><td class="${{p.total_debt > 0 ? 'negative' : ''}}">${{p.total_debt.toFixed(2)}}</td></tr>`;
    }}
    html += '</tbody></table>';
    document.getElementById('modalContent').innerHTML = html;
    document.getElementById('salesModal').classList.add('active');
}}
function closeModal() {{ document.getElementById('salesModal').classList.remove('active'); }}
document.getElementById('salesModal').addEventListener('click', e => {{ if(e.target.id === 'salesModal') closeModal(); }});
</script>
</body>
</html>'''
    return html

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("正在生成HTML看板...")
    data = load_data()
    
    # 生成主看板
    html = generate_main_dashboard(data)
    output_path = 'C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 主看板已更新: {output_path}")
    
    print("\n🎉 HTML看板生成完成！")

if __name__ == '__main__':
    main()
