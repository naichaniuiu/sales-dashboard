# -*- coding: utf-8 -*-
"""
根据最新JSON数据重新生成HTML看板（保留旧模板样式）
"""
import json
from datetime import datetime

def load_data():
    """加载数据文件"""
    with open('C:/Users/wm881/WorkBuddy/20260513090923/dashboard_final.json', encoding='utf-8') as f:
        return json.load(f)

def load_sales_detail():
    """加载销售员明细"""
    with open('C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json', encoding='utf-8') as f:
        return json.load(f)

def generate_html(data, sales_detail):
    """生成HTML"""
    today = datetime.now().strftime('%Y-%m-%d')
    dept_data = data['dept_data']
    total = data['total']
    risk = data['risk_customers']
    cycle_data = data['cycle']
    
    # 构建 deptData JS 数组
    dept_js = []
    for d in dept_data:
        dept_js.append(f"{{dept:'{d['dept']}',v26:{d['v26']},v25:{d['v25']},yoy:{d['yoy']},target:{d['target']},completion:{d['completion']},sales:{d['sales']},d30:{d['d30']},d30_90:{d['d30_90']},d90_180:{d['d90_180']},d180:{d['d180']},total_debt:{d['total_debt']},collect:{d['collect']},cycle:{d['cycle']}}}")
    dept_js_str = ",\n    ".join(dept_js)
    
    # 构建 salesDetailData JS 对象
    sales_js_parts = []
    for dept, people in sales_detail.items():
        person_js = []
        for p in people:
            person_js.append(f'{{"name":"{p["name"]}","perf":{p["perf"]},"collect":{p["collect"]},"debt":{p["total_debt"]},"orders":0,"d30":{p["d30"]},"d30_90":{p["d30_90"]},"d90_180":{p["d90_180"]},"d180":{p["d180"]},"total_debt":{p["total_debt"]},"collect_amt":{p["collect"]}}}')
        sales_js_parts.append(f'"{dept}":[{",".join(person_js)}]')
    sales_js_str = "{" + ",".join(sales_js_parts) + "}"
    
    # 计算 KPI
    v26_total = total['v26']
    target_total = total['target']
    completion = total['completion']
    v25_total = total['v25']
    yoy = total['yoy']
    debt_total = total['debt']
    d90_total = total['d90_180'] + total['d180']
    sales_count = total['sales']
    
    # 欠款账龄分布
    d30_total = total['d30']
    d30_90_total = total['d30_90']
    d90_180_total = total['d90_180']
    d180_total = total['d180']
    collect_total = total['collect']
    
    # 回款周期
    avg_cycle = cycle_data['avg']
    max_cycle = cycle_data['max']
    max_dept = cycle_data['max_dept']
    over90_count = cycle_data['over90']
    
    # 计算最短周期
    min_cycle = cycle_data['min']
    min_dept = cycle_data['min_dept']
    
    # 排序部门（按欠款降序）
    dept_by_debt = sorted(dept_data, key=lambda x: x['total_debt'], reverse=True)
    
    # 排序部门（按回款周期降序）
    dept_by_cycle = sorted([(d['dept'], d['cycle']) for d in dept_data if d['cycle'] > 0], key=lambda x: x[1], reverse=True)
    
    # 生成部门表格行（业绩分析Tab）
    perf_rows = ""
    for d in dept_data:
        status = "严重下滑" if d['yoy'] < -50 else "待关注"
        badge = "badge-down" if d['yoy'] < -50 else "badge-warning"
        target_str = f"{d['target']:.1f}" if d['target'] > 0 else "-"
        perf_rows += f'''<tr onclick="showSalesDetail('{d['dept']}','perf')" style="cursor:pointer;" title="点击查看销售员业绩明细">
                        <td>🏢 {d['dept']}</td>
                        <td class="highlight">{d['v26']:.2f}</td><td>{target_str}</td><td>{d['completion']:.1f}%</td><td>{d['v25']:.2f}</td>
                        <td class="trend-down">▼ {d['yoy']:.1f}%</td><td>{d['sales']}</td>
                        <td><span class="status-badge {badge}">{status}</span></td>
                    </tr>'''
    
    # 生成合计行
    perf_foot = f'''<tr>
                        <td>合计</td><td>{v26_total:.2f}</td><td>{target_total:.1f}</td><td>{completion:.1f}%</td>
                        <td>{v25_total:.2f}</td><td class="trend-down">▼ {yoy:.1f}%</td><td>{sales_count}</td><td></td>
                    </tr>'''
    
    # 生成欠款分析表格
    debt_rows = ""
    for d in dept_by_debt:
        risky = d['d90_180'] + d['d180']
        badge = "badge-down" if risky > 50 else "badge-warning" if risky > 20 else "badge-good"
        status = "高风险" if risky > 50 else "关注" if risky > 20 else "较好"
        d90_cls = "warning" if d['d90_180'] > 0 else ""
        d180_cls = "negative" if d['d180'] > 0 else ""
        debt_rows += f'''<tr onclick="showSalesDetail('{d['dept']}','debt')" style="cursor:pointer;"><td>🏢 {d['dept']}</td><td>{d['d30']:.2f}</td><td>{d['d30_90']:.2f}</td><td class="{d90_cls}">{d['d90_180']:.2f}</td><td class="{d180_cls}">{d['d180']:.2f}</td><td class="negative">{d['total_debt']:.2f}</td><td><span class="status-badge {badge}">{status}</span></td></tr>'''
    
    debt_foot = f'''<tr><td>合计</td><td>{d30_total:.2f}</td><td>{d30_90_total:.2f}</td><td>{d90_180_total:.2f}</td><td>{d180_total:.2f}</td><td>{debt_total:.2f}</td><td></td></tr>'''
    
    # 生成高风险客户
    risk_rows = ""
    for i, (name, amt) in enumerate(risk[:15], 1):
        risk_level = "极高风险" if amt > 80 else "高风险" if amt > 40 else "关注"
        risk_badge = "badge-down" if amt > 40 else "badge-warning"
        risk_cls = "negative" if amt > 40 else "warning"
        risk_rows += f'<tr><td>{i}</td><td style="text-align:left;">{name}</td><td class="{risk_cls}">{amt:.2f}</td><td><span class="status-badge {risk_badge}">{risk_level}</span></td></tr>'
    
    # 生成回款周期表格
    cycle_rows = ""
    for dept, cyc in dept_by_cycle:
        d = next(x for x in dept_data if x['dept'] == dept)
        badge = "badge-down" if cyc > 90 else "badge-warning" if cyc > 60 else "badge-good"
        status = "需关注" if cyc > 90 else "一般" if cyc > 60 else "良好"
        cyc_cls = "negative" if cyc > 90 else "warning" if cyc > 60 else "highlight"
        cycle_rows += f'<tr onclick="showSalesDetail(\'{dept}\',\'cycle\')" style="cursor:pointer;"><td>🏢 {dept}</td><td>{d["total_debt"]:.2f}</td><td>{d["collect"]:.2f}</td><td class="{cyc_cls}">{cyc:.1f}</td><td><span class="status-badge {badge}">{status}</span></td></tr>'
    
    cycle_foot = f'<tr><td>合计</td><td>{debt_total:.2f}</td><td>{collect_total:.2f}</td><td>{avg_cycle:.1f}</td><td></td></tr>'
    
    # 欠款饼图数据
    debt_pie_data = f'[{d30_total:.2f}, {d30_90_total:.2f}, {d90_180_total:.2f}, {d180_total:.2f}]'
    
    # KPI副标题
    target_gap = target_total - v26_total
    kpi_gap = f"{target_gap:.2f}"
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中西部大区 26财年Q1 数据看板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
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

        .tab-nav {{ display: flex; gap: 10px; margin-bottom: 25px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); overflow-x: auto; scrollbar-width: none; }}
        .tab-nav::-webkit-scrollbar {{ display: none; }}
        .tab-btn {{ display: flex; align-items: center; gap: 8px; padding: 12px 24px; background: transparent; border: none; border-radius: 8px; color: #8892b0; font-size: 0.95em; font-weight: 500; cursor: pointer; transition: all 0.3s; white-space: nowrap; }}
        .tab-btn:hover {{ background: rgba(255,255,255,0.05); color: #ccd6f6; }}
        .tab-btn.active {{ background: linear-gradient(135deg, #00d4ff 0%, #7b2ff7 100%); color: #fff; box-shadow: 0 4px 15px rgba(0,212,255,0.3); }}

        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; animation: fadeIn 0.3s ease; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        .module {{ background: rgba(255,255,255,0.05); border-radius: 20px; padding: 30px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 25px; }}
        .module-title {{ font-size: 1.3em; margin-bottom: 10px; color: #00d4ff; display: flex; align-items: center; gap: 10px; }}
        .module-desc {{ color: #8892b0; margin-bottom: 20px; font-size: 0.9em; }}

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
        .trend-neutral {{ color: #ffa502; }}
        .status-badge {{ padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
        .badge-down {{ background: rgba(255,71,87,0.2); color: #ff4757; border: 1px solid rgba(255,71,87,0.3); }}
        .badge-warning {{ background: rgba(255,165,2,0.2); color: #ffa502; border: 1px solid rgba(255,165,2,0.3); }}
        .badge-new {{ background: rgba(0,255,136,0.2); color: #00ff88; border: 1px solid rgba(0,255,136,0.3); }}
        .badge-good {{ background: rgba(0,212,255,0.2); color: #00d4ff; border: 1px solid rgba(0,212,255,0.3); }}

        /* 下钻弹窗 */
        .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; }}
        .modal-overlay.active {{ display: flex; align-items: center; justify-content: center; }}
        .modal {{ background: #1a2040; border-radius: 20px; padding: 30px; max-width: 900px; width: 90%; max-height: 80vh; overflow-y: auto; border: 1px solid rgba(0,212,255,0.3); }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .modal-title {{ color: #00d4ff; font-size: 1.2em; font-weight: 600; }}
        .modal-close {{ background: rgba(255,255,255,0.1); border: none; color: #fff; width: 30px; height: 30px; border-radius: 50%; cursor: pointer; font-size: 1.2em; display: flex; align-items: center; justify-content: center; }}
        .modal-close:hover {{ background: rgba(255,71,87,0.3); }}

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
            <div class="value">{v26_total:.2f}<span style="font-size:0.5em;">万</span></div>
            <div class="sub">目标：{target_total:.1f}万</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🎯</div>
            <h3>Q1目标完成率</h3>
            <div class="value {'negative' if completion < 50 else ''}">{completion:.1f}%</div>
            <div class="sub">距目标还差 {kpi_gap}万</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📉</div>
            <h3>同比25Q1</h3>
            <div class="value negative">{yoy:.1f}%</div>
            <div class="sub">25Q1：{v25_total:.2f}万</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <h3>在职销售员总数</h3>
            <div class="value" style="color:#ffa502;">{sales_count}</div>
            <div class="sub">人</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">⚠️</div>
            <h3>逾期欠款总额</h3>
            <div class="value negative">{debt_total:.2f}<span style="font-size:0.5em;">万</span></div>
            <div class="sub">90天以上：{d90_total:.2f}万</div>
        </div>
    </div>

    <!-- Tab导航 -->
    <div class="tab-nav">
        <button class="tab-btn active" onclick="switchTab('performance', this)"><span class="tab-icon">📊</span>业绩分析</button>
        <button class="tab-btn" onclick="switchTab('debt', this)"><span class="tab-icon">💳</span>欠款分析</button>
        <button class="tab-btn" onclick="switchTab('collection', this)"><span class="tab-icon">⏱️</span>平均回款周期分析</button>
    </div>

    <!-- ===== 业绩分析 Tab ===== -->
    <div id="tab-performance" class="tab-content active">
        <div class="module">
            <h2 class="module-title">📊 26财年Q1 部门业绩总览</h2>
            <div class="charts-section">
                <div class="chart-box">
                    <h3>25Q1 vs 26Q1 部门业绩对比（万元）</h3>
                    <div class="chart-container"><canvas id="perfBarChart"></canvas></div>
                </div>
                <div class="chart-box">
                    <h3>26Q1 部门业绩占比分布</h3>
                    <div class="chart-container"><canvas id="perfPieChart"></canvas></div>
                </div>
            </div>
            <p class="module-desc" style="color:#00d4ff;font-weight:600;">🔽 点击任意部门行 → 查看该部门销售员明细</p>
            <table class="dept-table">
                <thead>
                    <tr>
                        <th>部门</th>
                        <th>26Q1业绩(万)</th>
                        <th>Q1目标(万)</th>
                        <th>目标完成率</th>
                        <th>25Q1同期(万)</th>
                        <th>同比%</th>
                        <th>销售员数</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {perf_rows}
                </tbody>
                <tfoot>
                    {perf_foot}
                </tfoot>
            </table>
        </div>
    </div>

    <!-- ===== 欠款分析 Tab ===== -->
    <div id="tab-debt" class="tab-content">
        <div class="module">
            <h2 class="module-title">💳 欠款分析总览</h2>

            <!-- 欠款KPI -->
            <div class="kpi-grid" style="margin-bottom:25px;">
                <div class="kpi-card">
                    <div class="kpi-icon">📋</div>
                    <h3>欠款总额</h3>
                    <div class="value negative">{debt_total:.2f}<span style="font-size:0.5em;">万</span></div>
                    <div class="sub">全大区逾期欠款合计</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">🟢</div>
                    <h3>30天内</h3>
                    <div class="value highlight">{d30_total:.2f}<span style="font-size:0.5em;">万</span></div>
                    <div class="sub">占比 {d30_total/debt_total*100:.1f}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">🟡</div>
                    <h3>30-90天</h3>
                    <div class="value warning">{d30_90_total:.2f}<span style="font-size:0.5em;">万</span></div>
                    <div class="sub">占比 {d30_90_total/debt_total*100:.1f}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">🔴</div>
                    <h3>90天以上</h3>
                    <div class="value negative">{d90_total:.2f}<span style="font-size:0.5em;">万</span></div>
                    <div class="sub">90-180天：{d90_180_total:.2f}万 | 180天+：{d180_total:.2f}万</div>
                </div>
            </div>

            <!-- 图表 -->
            <div class="charts-section">
                <div class="chart-box">
                    <h3>逾期欠款金额占比分布</h3>
                    <div class="chart-container"><canvas id="debtPieChart"></canvas></div>
                </div>
                <div class="chart-box">
                    <h3>各部门欠款总额排名（万元）</h3>
                    <div class="chart-container"><canvas id="debtBarChart"></canvas></div>
                </div>
            </div>

            <!-- 欠款明细表 -->
            <h3 style="color:#00d4ff;margin-bottom:15px;font-size:1.1em;">各部门分账龄欠款明细 <span style="color:#8892b0;font-size:0.8em;font-weight:normal;">（点击部门查看销售员明细）</span></h3>
            <table class="dept-table">
                <thead>
                    <tr>
                        <th>部门（点击查看明细）</th>
                        <th>30天内(万)</th>
                        <th>30-90天(万)</th>
                        <th>90-180天(万)</th>
                        <th>180天以上(万)</th>
                        <th>合计(万)</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody id="debtTableBody">{debt_rows}</tbody>
                <tfoot id="debtTableFoot">{debt_foot}</tfoot>
            </table>

            <!-- 高风险客户 -->
            <h3 style="color:#ff4757;margin:25px 0 15px;font-size:1.1em;">🚨 高风险客户（90天以上欠款，前15名）</h3>
            <table class="dept-table">
                <thead>
                    <tr><th>排名</th><th>客户名称（所属部门）</th><th>欠款金额(万)</th><th>风险等级</th></tr>
                </thead>
                <tbody>
                    {risk_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- ===== 平均回款周期分析 Tab ===== -->
    <div id="tab-collection" class="tab-content">
        <div class="module">
            <h2 class="module-title">⏱️ 平均回款周期分析</h2>
            <div class="kpi-grid" style="margin-bottom:25px;">
                <div class="kpi-card">
                    <div class="kpi-icon">📊</div>
                    <h3>全大区平均回款周期</h3>
                    <div class="value warning">{avg_cycle:.1f}</div>
                    <div class="sub">天（欠款加权综合）</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">🔴</div>
                    <h3>最长部门回款周期</h3>
                    <div class="value negative">{max_cycle:.1f}</div>
                    <div class="sub">{max_dept}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">🟢</div>
                    <h3>最短部门回款周期</h3>
                    <div class="value highlight">{min_cycle:.1f}</div>
                    <div class="sub">{min_dept}</div>
                </div>
                <div class="kpi-card" onclick="showOver90Depts()" style="cursor:pointer;" title="点击查看回款周期大于90天的部门">
                    <div class="kpi-icon">⚠️</div>
                    <h3>超90天部门数</h3>
                    <div class="value negative">{over90_count}</div>
                    <div class="sub">回款周期大于90天的部门（点击查看）</div>
                </div>
            </div>

            <!-- 图例 -->
            <div style="background:rgba(255, 255, 255, 0.03);border-radius:12px;padding:15px 20px;margin-bottom:20px;border:1px solid rgba(255, 255, 255, 0.08);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                    <span style="font-weight:600;color:#00d4ff;">部门平均回款周期（天）</span>
                    <span style="color:#8892b0;font-size:0.9em;">| 基于欠款账龄中点加权计算</span>
                </div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;">
                    <div style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:50%;background:#00ff88;display:inline-block;"></span><span style="color:#ccd6f6;font-size:0.9em;">≤60天（良好）</span></div>
                    <div style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:50%;background:#ffa502;display:inline-block;"></span><span style="color:#ccd6f6;font-size:0.9em;">61-90天（一般）</span></div>
                    <div style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:50%;background:#ff4757;display:inline-block;"></span><span style="color:#ccd6f6;font-size:0.9em;">&gt;90天（需关注）</span></div>
                </div>
            </div>

            <div class="chart-box" style="margin-bottom:25px;">
                <h3>📊 部门平均回款周期排名</h3>
                <div class="chart-container" style="height:380px;"><canvas id="cycleChart"></canvas></div>
            </div>

            <!-- 回款周期表格 -->
            <table class="dept-table">
                <thead>
                    <tr>
                        <th>部门（点击查看明细）</th>
                        <th>欠款总额(万)</th>
                        <th>回款金额(万)</th>
                        <th>回款周期(天)</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody id="cycleTableBody">{cycle_rows}</tbody>
                <tfoot id="cycleTableFoot">{cycle_foot}</tfoot>
            </table>
        </div>
    </div>
</div>

<!-- 弹窗 -->
<div class="modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()">
    <div class="modal">
        <div class="modal-header">
            <div class="modal-title" id="modalTitle">部门详情</div>
            <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div id="modalContent"></div>
    </div>
</div>

<!-- 销售员明细弹窗 -->
<div class="modal-overlay" id="salesModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0, 0, 0, 0.8);z-index:1001;align-items:center;justify-content:center;">
    <div style="background:#1a2040;border-radius:20px;padding:30px;max-width:1100px;width:95%;max-height:85vh;overflow-y:auto;border:1px solid rgba(0,212,255,0.3);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
            <div class="modal-title" id="salesModalTitle">销售员明细</div>
            <button class="modal-close" onclick="closeSalesModal()">✕</button>
        </div>
        <div id="salesTableContainer"></div>
    </div>
</div>

<script>
// ===== 数据 =====
const deptData = [
    {dept_js_str}
];

// ===== Tab切换 =====
let currentTabType = 'perf';
function switchTab(id, btn) {{
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + id).classList.add('active');
    btn.classList.add('active');
    if (id === 'performance') currentTabType = 'perf';
    else if (id === 'debt') currentTabType = 'debt';
    else if (id === 'collection') currentTabType = 'cycle';
}}
function getCurrentTab() {{ return currentTabType; }}

// ===== 销售员明细数据 =====
let salesDetailData = {sales_js_str};

// ===== 部门弹窗 =====
function showDeptDetail(dept) {{
    const d = deptData.find(x => x.dept === dept);
    if (!d) return;
    document.getElementById('modalTitle').textContent = dept + ' — 部门概览';
    const risky = d.d90_180 + d.d180;
    document.getElementById('modalContent').innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
            <div style="background:rgba(0,212,255,0.1);border-radius:12px;padding:14px;text-align:center;">
                <div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">26Q1业绩</div>
                <div style="color:#00ff88;font-size:1.5em;font-weight:700;">${{d.v26}}万</div>
            </div>
            <div style="background:rgba(0,212,255,0.1);border-radius:12px;padding:14px;text-align:center;">
                <div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">完成率</div>
                <div style="color:#ffa502;font-size:1.5em;font-weight:700;">${{d.completion}}%</div>
            </div>
            <div style="background:rgba(255,71,87,0.1);border-radius:12px;padding:14px;text-align:center;">
                <div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">同比25Q1</div>
                <div style="color:#ff4757;font-size:1.5em;font-weight:700;">${{d.yoy}}%</div>
            </div>
            <div style="background:rgba(0,212,255,0.1);border-radius:12px;padding:14px;text-align:center;">
                <div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">欠款总额</div>
                <div style="color:#ff4757;font-size:1.5em;font-weight:700;">${{d.total_debt}}万</div>
            </div>
        </div>
        <div style="text-align:center;margin-top:10px;">
            <button onclick="showSalesDetail('${{dept}}', getCurrentTab())" style="background:linear-gradient(135deg,#00d4ff,#7b2ff7);color:#fff;border:none;border-radius:8px;padding:10px 28px;font-size:1em;cursor:pointer;">📋 查看销售员明细</button>
        </div>`;
    document.getElementById('modalOverlay').classList.add('active');
}}
function closeModal() {{
    document.getElementById('modalOverlay').classList.remove('active');
}}

// ===== 销售员明细弹窗 =====
function showSalesDetail(dept, type) {{
    if (type === 'perf') renderSalesPerf(dept);
    else if (type === 'debt') renderSalesDebt(dept);
    else if (type === 'cycle') renderSalesCycle(dept);
    else renderSalesPerf(dept);
}}

function renderSalesPerf(dept) {{
    const list = [...(salesDetailData[dept] || [])];
    list.sort((a, b) => b.perf - a.perf);
    const rows = list.map(s => {{
        const color = s.perf < 0 ? '#ff4757' : s.perf < 5 ? '#ffa502' : '#00ff88';
        const status = s.perf < 0 ? '🔴 无业绩' : s.perf < 5 ? '🟡 待提升' : '🟢 正常';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;color:#ccd6f6;">${{s.name}}</td>
            <td style="padding:7px 5px;color:${{color}};text-align:right;font-weight:600;">${{s.perf.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${{s.collect.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{status}}</td>
        </tr>`;
    }}).join('');
    const tp = list.reduce((s, v) => s + v.perf, 0).toFixed(2);
    const tc = list.reduce((s, v) => s + v.collect, 0).toFixed(2);
    document.getElementById('salesModalTitle').textContent = `📊 ${{dept}} - 销售员业绩明细`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.85em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;">销售员</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">26Q1业绩(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th>
        </tr></thead>
        <tbody>${{rows}}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">合计（${{list.length}}人）</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${{tp}}</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${{tc}}</td>
            <td></td>
        </tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}}

function renderSalesDebt(dept) {{
    const list = [...(salesDetailData[dept] || [])];
    list.sort((a, b) => b.total_debt - a.total_debt);
    const rows = list.map(s => {{
        const dc = s.total_debt > 50 ? '#ff4757' : s.total_debt > 20 ? '#ffa502' : '#00ff88';
        const status = s.total_debt > 50 ? '🔴 高风险' : s.total_debt > 20 ? '🟡 关注' : '🟢 较好';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;color:#ccd6f6;">${{s.name}}</td>
            <td style="padding:7px 5px;color:${{dc}};text-align:right;font-weight:600;">${{s.total_debt.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${{s.d30.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:#ffa502;text-align:right;">${{s.d30_90.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:${{s.d90_180>0?'#ff4757':'#8892b0'}};text-align:right;">${{s.d90_180.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:${{s.d180>0?'#ff4757':'#8892b0'}};text-align:right;">${{s.d180.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{status}}</td>
        </tr>`;
    }}).join('');
    const td = list.reduce((s, v) => s + v.total_debt, 0).toFixed(2);
    document.getElementById('salesModalTitle').textContent = `💰 ${{dept}} - 销售员欠款明细`;
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
        <tbody>${{rows}}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">合计（${{list.length}}人）</td>
            <td style="padding:8px 6px;color:#ff4757;text-align:right;">${{td}}</td>
            <td colspan="4"></td>
            <td></td>
        </tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}}

function renderSalesCycle(dept) {{
    const list = [...(salesDetailData[dept] || [])];
    list.forEach(s => {{
        s.cycle = (s.collect > 0) ? (s.total_debt / s.collect * 90) : null;
    }});
    list.sort((a, b) => {{
        if (a.cycle === null && b.cycle === null) return 0;
        if (a.cycle === null) return 1;
        if (b.cycle === null) return -1;
        return b.cycle - a.cycle;
    }});
    const rows = list.map(s => {{
        const cycle = s.cycle;
        const cycleStr = cycle !== null ? cycle.toFixed(1) : '-';
        const cc = cycle === null ? '#8892b0' : cycle > 90 ? '#ff4757' : cycle > 60 ? '#ffa502' : '#00ff88';
        const status = cycle === null ? '⚪ 无回款' : cycle > 90 ? '🔴 需关注' : cycle > 60 ? '🟡 偏高' : '🟢 正常';
        const dc = s.total_debt > 50 ? '#ff4757' : s.total_debt > 20 ? '#ffa502' : '#00ff88';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
            <td style="padding:7px 5px;color:#ccd6f6;">${{s.name}}</td>
            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${{s.collect.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:${{dc}};text-align:right;">${{s.total_debt.toFixed(2)}}</td>
            <td style="padding:7px 5px;color:${{cc}};text-align:right;font-weight:600;">${{cycleStr}}</td>
            <td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{status}}</td>
        </tr>`;
    }}).join('');
    const tc = list.reduce((s, v) => s + v.collect, 0).toFixed(2);
    const td = list.reduce((s, v) => s + v.total_debt, 0).toFixed(2);
    document.getElementById('salesModalTitle').textContent = `⏱️ ${{dept}} - 销售员回款周期明细`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.85em;">
        <thead><tr style="background:rgba(0,212,255,0.12);">
            <th style="padding:8px 6px;color:#00d4ff;">销售员</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款金额(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">欠款金额(万)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款周期(天)</th>
            <th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th>
        </tr></thead>
        <tbody>${{rows}}
        <tr style="background:rgba(0,212,255,0.08);font-weight:600;">
            <td style="padding:8px 6px;color:#00d4ff;">合计（${{list.length}}人）</td>
            <td style="padding:8px 6px;color:#00ff88;text-align:right;">${{tc}}</td>
            <td style="padding:8px 6px;color:#ff4757;text-align:right;">${{td}}</td>
            <td colspan="2"></td>
        </tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}}

function closeSalesModal() {{
    document.getElementById('salesModal').style.display = 'none';
}}

function showOver90Depts() {{
    const over90 = deptData.filter(d => d.cycle > 90).sort((a, b) => b.cycle - a.cycle);
    const rows = over90.map(d => {{
        const risky = d.d90_180 + d.d180;
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);cursor:pointer;" onclick="showSalesDetail('${{d.dept}}','cycle')">
            <td style="padding:10px 8px;color:#ccd6f6;font-weight:600;">🏢 ${{d.dept}}</td>
            <td style="padding:10px 8px;color:#ff4757;text-align:right;font-weight:700;">${{d.cycle.toFixed(1)}}天</td>
            <td style="padding:10px 8px;color:#ff4757;text-align:right;">${{d.total_debt.toFixed(2)}}万</td>
            <td style="padding:10px 8px;color:#ffa502;text-align:right;">${{risky.toFixed(2)}}万</td>
            <td style="padding:10px 8px;text-align:center;"><span class="status-badge badge-down">需关注</span></td>
        </tr>`;
    }}).join('');
    
    const totalDebt = over90.reduce((s, d) => s + d.total_debt, 0);
    const totalRisky = over90.reduce((s, d) => s + d.d90_180 + d.d180, 0);
    const avgCycle = over90.length > 0 ? over90.reduce((s, d) => s + d.cycle, 0) / over90.length : 0;
    
    document.getElementById('salesModalTitle').textContent = `⚠️ 回款周期超90天部门（共${{over90.length}}个）`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.9em;">
        <thead><tr style="background:rgba(255,71,87,0.15);">
            <th style="padding:10px 8px;color:#ff4757;text-align:left;">部门（点击下钻）</th>
            <th style="padding:10px 8px;color:#ff4757;text-align:right;">回款周期</th>
            <th style="padding:10px 8px;color:#ff4757;text-align:right;">欠款总额</th>
            <th style="padding:10px 8px;color:#ff4757;text-align:right;">高风险欠款(90天+)</th>
            <th style="padding:10px 8px;color:#ff4757;text-align:center;">状态</th>
        </tr></thead>
        <tbody>${{rows}}</tbody>
        <tfoot><tr style="background:rgba(255,71,87,0.08);font-weight:600;">
            <td style="padding:10px 8px;color:#ff4757;">合计（${{over90.length}}个部门）</td>
            <td style="padding:10px 8px;color:#ff4757;text-align:right;">平均 ${{avgCycle.toFixed(1)}}天</td>
            <td style="padding:10px 8px;color:#ff4757;text-align:right;">${{totalDebt.toFixed(2)}}万</td>
            <td style="padding:10px 8px;color:#ff4757;text-align:right;">${{totalRisky.toFixed(2)}}万</td>
            <td></td>
        </tr></tfoot></table>
        <div style="margin-top:15px;color:#8892b0;font-size:0.85em;text-align:center;">💡 点击部门名称可查看该部门销售员回款周期明细</div>`;
    document.getElementById('salesModal').style.display = 'flex';
}}

// ===== 平均回款周期分析表格 =====
function renderCycleTable() {{
    const tbody = document.getElementById('cycleTableBody');
    if (!tbody) return;
    const sorted = [...deptData].filter(d => d.cycle > 0).sort((a, b) => b.cycle - a.cycle);
    tbody.innerHTML = sorted.map(d => {{
        const sc = d.cycle > 90 ? 'negative' : d.cycle > 60 ? 'warning' : 'highlight';
        const badge = d.cycle > 90 ? 'badge-down' : d.cycle > 60 ? 'badge-warning' : 'badge-good';
        const label = d.cycle > 90 ? '需关注' : d.cycle > 60 ? '一般' : '良好';
        return `<tr onclick="showSalesDetail('${{d.dept}}','cycle')" style="cursor:pointer;">
            <td>🏢 ${{d.dept}}</td>
            <td>${{d.total_debt.toFixed(2)}}</td>
            <td>${{d.collect.toFixed(2)}}</td>
            <td class="${{sc}}">${{d.cycle.toFixed(1)}}</td>
            <td><span class="status-badge ${{badge}}">${{label}}</span></td>
        </tr>`;
    }}).join('');
}}

// ===== 图表 =====
Chart.register(ChartDataLabels);

function initCharts() {{
    const depts = deptData.map(d => d.dept);
    const v26 = deptData.map(d => d.v26);
    const v25 = deptData.map(d => d.v25);
    const COLORS = ['#00d4ff','#7b2ff7','#00ff88','#ffa502','#ff6b9d','#4ecdc4','#45b7d1','#f7dc6f','#82e0aa'];

    // 业绩对比柱状图
    new Chart(document.getElementById('perfBarChart'), {{
        type: 'bar',
        data: {{
            labels: depts,
            datasets: [
                {{ label: '25Q1(万)', data: v25, backgroundColor: 'rgba(0,212,255,0.5)', borderColor: '#00d4ff', borderWidth: 1 }},
                {{ label: '26Q1(万)', data: v26, backgroundColor: 'rgba(123,47,247,0.7)', borderColor: '#7b2ff7', borderWidth: 1 }}
            ]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ labels: {{ color: '#ccd6f6' }} }}, datalabels: {{ display: false }} }},
            scales: {{
                x: {{ ticks: {{ color: '#8892b0', maxRotation: 30, font: {{ size: 10 }} }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                y: {{ ticks: {{ color: '#8892b0' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
            }}
        }}
    }});

    // 业绩占比甜甜圈
    new Chart(document.getElementById('perfPieChart'), {{
        type: 'doughnut',
        data: {{
            labels: depts,
            datasets: [{{ data: v26, backgroundColor: COLORS, borderColor: '#0a0e27', borderWidth: 2 }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'right', labels: {{ color: '#ccd6f6', font: {{ size: 11 }}, padding: 10 }} }},
                datalabels: {{
                    color: '#fff', font: {{ size: 10, weight: 'bold' }},
                    formatter: (val, ctx) => {{
                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                        const pct = (val / total * 100).toFixed(1);
                        return pct > 3 ? pct + '%' : '';
                    }}
                }}
            }}
        }}
    }});

    // 回款周期柱状图
    const cycleItems = deptData.filter(d => d.cycle > 0).sort((a, b) => b.cycle - a.cycle);
    const cycleColors = cycleItems.map(d => d.cycle > 90 ? '#ff4757' : d.cycle > 60 ? '#ffa502' : '#00ff88');
    new Chart(document.getElementById('cycleChart'), {{
        type: 'bar',
        data: {{
            labels: cycleItems.map(d => d.dept),
            datasets: [{{ label: '回款周期(天)', data: cycleItems.map(d => d.cycle), backgroundColor: cycleColors, borderRadius: 6 }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true, maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                datalabels: {{
                    color: '#fff', anchor: 'end', align: 'right', font: {{ size: 12, weight: 'bold' }},
                    formatter: val => val + '天'
                }}
            }},
            scales: {{
                x: {{ ticks: {{ color: '#8892b0' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, max: 150 }},
                y: {{ ticks: {{ color: '#ccd6f6', font: {{ size: 12 }} }}, grid: {{ display: false }} }}
            }}
        }}
    }});

    // 欠款账龄甜甜圈
    new Chart(document.getElementById('debtPieChart'), {{
        type: 'doughnut',
        data: {{
            labels: ['30天内', '30-90天', '90-180天', '180天以上'],
            datasets: [{{
                data: {debt_pie_data},
                backgroundColor: ['#00ff88', '#ffa502', '#ff6b6b', '#ff4757'],
                borderColor: '#0a0e27', borderWidth: 3
            }}]
        }},
        options: {{
            responsive: true, maintainAspectRatio: false,
            cutout: '55%',
            plugins: {{
                legend: {{ position: 'bottom', labels: {{ color: '#ccd6f6', padding: 15 }} }},
                datalabels: {{
                    color: '#fff', font: {{ size: 11, weight: 'bold' }},
                    formatter: (val, ctx) => {{
                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                        const pct = (val / total * 100).toFixed(1);
                        return pct + '%';
                    }}
                }}
            }}
        }}
    }});

    // 部门欠款排名横向柱状图
    const debtSorted = [...deptData].sort((a, b) => b.total_debt - a.total_debt);
    new Chart(document.getElementById('debtBarChart'), {{
        type: 'bar',
        data: {{
            labels: debtSorted.map(d => d.dept),
            datasets: [{{ label: '欠款(万)', data: debtSorted.map(d => d.total_debt), backgroundColor: 'rgba(255,71,87,0.7)', borderColor: '#ff4757', borderWidth: 1, borderRadius: 4 }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true, maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                datalabels: {{
                    color: '#fff', anchor: 'end', align: 'right', font: {{ size: 11, weight: 'bold' }},
                    formatter: val => val.toFixed(1)
                }}
            }},
            scales: {{
                x: {{ ticks: {{ color: '#8892b0' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                y: {{ ticks: {{ color: '#ccd6f6', font: {{ size: 11 }} }}, grid: {{ display: false }} }}
            }}
        }}
    }});
}}

window.addEventListener('load', initCharts);
window.addEventListener('load', function() {{
    renderCycleTable();
}});
</script>
</body>
</html>'''
    return html

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("正在生成HTML看板（保留旧模板样式）...")
    data = load_data()
    sales_detail = load_sales_detail()
    
    html = generate_html(data, sales_detail)
    output_path = 'C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 主看板已更新: {output_path}")
    
    print("\n🎉 HTML看板生成完成！")

if __name__ == '__main__':
    main()
