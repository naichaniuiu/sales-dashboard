#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中西部大区数据看板 - 数据自动提取脚本
每天运行此脚本，自动从Excel提取最新数据并生成JSON文件

使用方法：
    python update_data.py

运行后：
1. 从 业绩 欠款看板.xlsx 提取数据
2. 生成 github-pages-deploy/data/performance.json
3. 生成 github-pages-deploy/data/debt.json
4. 提交到GitHub（如果配置了git）
"""

import pandas as pd
import json
import os
from datetime import datetime

# ============ 配置区域 ============
# 数据源文件路径
DATA_SOURCE = r'C:/Users/wm881/Downloads/业绩 欠款看板.xlsx'

# 输出目录
OUTPUT_DIR = r'C:/Users/wm881/WorkBuddy/20260513090923/github-pages-deploy/data'

# Git提交配置（可选）
GIT_COMMIT = True  # 设置为False可跳过Git提交


def load_excel_data():
    """从Excel加载数据"""
    print("📂 正在读取Excel数据...")
    
    # 读取业绩数据
    df_perf25 = pd.read_excel(DATA_SOURCE, sheet_name='25财年Q1业绩')
    df_perf26 = pd.read_excel(DATA_SOURCE, sheet_name='26财年Q1业绩')
    df_debt = pd.read_excel(DATA_SOURCE, sheet_name='逾期欠款明细')
    
    return df_perf25, df_perf26, df_debt


def process_performance_data(df_25, df_26):
    """处理业绩对比数据"""
    print("📊 正在处理业绩数据...")
    
    # 筛选中西部大区数据
    df_25_cn = df_25[df_25['一级部门'] == '中西部大区'].copy()
    df_26_cn = df_26[df_26['一级部门'] == '中西部大区'].copy()
    
    # 按三级部门汇总
    perf_25 = df_25_cn.groupby('三级部门')['Q1业绩(万元)'].sum().reset_index()
    perf_26 = df_26_cn.groupby('三级部门')['Q1业绩(万元)'].sum().reset_index()
    
    # 构建输出数据
    data = {
        "lastUpdate": datetime.now().strftime("%Y-%m-%d"),
        "region": "中西部大区",
        "fiscal25": {
            "total": round(perf_25['Q1业绩(万元)'].sum(), 2),
            "departments": [
                {"name": row['三级部门'], "value": round(row['Q1业绩(万元)'], 2)}
                for _, row in perf_25.iterrows()
            ]
        },
        "fiscal26": {
            "total": round(perf_26['Q1业绩(万元)'].sum(), 2),
            "departments": [
                {"name": row['三级部门'], "value": round(row['Q1业绩(万元)'], 2)}
                for _, row in perf_26.iterrows()
            ]
        }
    }
    
    return data


def process_debt_data(df_debt):
    """处理欠款数据"""
    print("💰 正在处理欠款数据...")
    
    # 筛选中西部大区数据
    df_cn = df_debt[df_debt['大区'] == '中西部大区'].copy()
    
    # 按账龄区间统计
    debt_by_period = {
        "30天内": df_cn[df_cn['账龄区间'] == '30天内']['欠款金额(万元)'].sum(),
        "30-90天": df_cn[df_cn['账龄区间'] == '30-90天']['欠款金额(万元)'].sum(),
        "90-180天": df_cn[df_cn['账龄区间'] == '90-180天']['欠款金额(万元)'].sum(),
        "180天以上": df_cn[df_cn['账龄区间'] == '180天以上']['欠款金额(万元)'].sum()
    }
    
    # 按部门汇总
    dept_debt = df_cn.groupby('部门')['欠款金额(万元)'].sum().reset_index()
    dept_debt = dept_debt.sort_values('欠款金额(万元)', ascending=False)
    
    data = {
        "lastUpdate": datetime.now().strftime("%Y-%m-%d"),
        "region": "中西部大区",
        "totalDebt": round(df_cn['欠款金额(万元)'].sum(), 2),
        "periodBreakdown": {
            "labels": list(debt_by_period.keys()),
            "values": [round(v, 2) for v in debt_by_period.values()],
            "colors": ["#00ff88", "#00d4ff", "#ffa502", "#ff4757"]
        },
        "departments": [
            {"name": row['部门'], "total": round(row['欠款金额(万元)'], 2)}
            for _, row in dept_debt.iterrows()
        ]
    }
    
    return data


def save_json(data, filename):
    """保存JSON文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ 已保存: {filepath}")


def git_commit_push():
    """提交并推送到GitHub"""
    if not GIT_COMMIT:
        return
    
    print("\n🔄 正在提交到GitHub...")
    
    import subprocess
    
    os.chdir(r'C:/Users/wm881/WorkBuddy/20260513090923/github-pages-deploy')
    
    # 添加所有更改
    subprocess.run(['git', 'add', '.'], check=True)
    
    # 提交
    commit_msg = f"数据更新 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Git提交成功: {commit_msg}")
        
        # 推送到GitHub
        result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Git推送成功！GitHub Pages将在2分钟内自动更新")
        else:
            print(f"⚠️ Git推送失败: {result.stderr}")
    else:
        print(f"⚠️ 没有需要提交的内容或提交失败")


def main():
    print("=" * 50)
    print("🔄 中西部大区数据看板 - 数据更新脚本")
    print("=" * 50)
    print()
    
    try:
        # 1. 加载数据
        df_perf25, df_perf26, df_debt = load_excel_data()
        
        # 2. 处理业绩数据
        perf_data = process_performance_data(df_perf25, df_perf26)
        save_json(perf_data, 'performance.json')
        
        # 3. 处理欠款数据
        debt_data = process_debt_data(df_debt)
        save_json(debt_data, 'debt.json')
        
        # 4. Git提交推送
        git_commit_push()
        
        print()
        print("=" * 50)
        print("🎉 数据更新完成！")
        print(f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🌐 访问地址: https://liuchuanfeng.github.io/workbuddy-dashboard")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        raise


if __name__ == '__main__':
    main()
