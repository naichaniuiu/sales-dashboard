#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成销售员明细数据，用于部门下钻

规则：
- 业绩/回款/单数：只统计在职销售员（68人），部门以业绩表为准
- 欠款/账龄：包含全部人员（在职+离职，共80人），部门以欠款表为准
  （处理跨部门调动：同一人可能在业绩表和欠款表中属于不同部门）
- 认款：按实际认款记录
"""
import pandas as pd
import json

EXCEL = "C:/Users/wm881/Downloads/业绩 欠款看板.xlsx"
OUT   = "C:/Users/wm881/WorkBuddy/20260513090923/sales_detail.json"

# ========== 读取 ==========
df26     = pd.read_excel(EXCEL, sheet_name="26财年Q1业绩")
df_debt  = pd.read_excel(EXCEL, sheet_name="欠款数据 ")
df_collect = pd.read_excel(EXCEL, sheet_name="26财年Q1认款数据")

df26_xb      = df26[df26["一级部门"] == "中西部大区"].copy()
df_debt_xb   = df_debt[df_debt["一级部门"] == "中西部大区"].copy()
df_collect_xb= df_collect[df_collect["一级部门"] == "中西部大区"].copy()

# 在职销售员名单（用于业绩统计）
df26_active = df26_xb[df26_xb["销售员状态"] == "在职"].copy()
active_names = set(df26_active["销售员名称"].unique())

# ========== 1. 业绩 / 回款 / 单数（仅在职，部门以业绩表为准）==========
perf = (
    df26_active
    .groupby(["三级部门", "销售员名称"])
    .agg(
        业绩=("业绩总金额", "sum"),
        回款=("回款金额",   "sum"),
        单数=("业绩单号",   "count"),
    )
    .reset_index()
)
perf["业绩"] = (perf["业绩"] / 10000).round(2)
perf["回款"] = (perf["回款"] / 10000).round(2)

# ========== 2. 欠款账龄（全部人员，部门以欠款表为准）==========
df_debt_all = df_debt_xb.copy()
df_debt_all["欠款天数"] = pd.to_numeric(df_debt_all["欠款天数"], errors="coerce").fillna(0)

def classify(d):
    if d <= 30:   return "30天内"
    elif d <= 90:  return "30-90天"
    elif d <= 180: return "90-180天"
    else:           return "180天以上"

df_debt_all["账龄"] = df_debt_all["欠款天数"].apply(classify)

debt_age = (
    df_debt_all
    .groupby(["三级部门", "销售员名称", "账龄"])["欠款金额"]
    .sum()
    .reset_index()
)
debt_age["欠款金额"] = (debt_age["欠款金额"] / 10000).round(2)

debt_pivot = debt_age.pivot_table(
    index=["三级部门", "销售员名称"],
    columns="账龄",
    values="欠款金额",
    fill_value=0,
).reset_index()

for col in ["30天内", "30-90天", "90-180天", "180天以上"]:
    if col not in debt_pivot.columns:
        debt_pivot[col] = 0.0

# ========== 3. 认款金额（全部人员，部门以认款表为准）==========
collect = (
    df_collect_xb
    .groupby(["三级部门", "销售员名称"])["认款协同金额"]
    .sum()
    .reset_index()
)
collect["认款协同金额"] = (collect["认款协同金额"] / 10000).round(2)

# ========== 4. 构建结果：以欠款表的部门+人员为基准 ==========
# 这样即使跨部门调动，欠款也能正确归属到欠款表中的部门

result = {}

# 先处理所有有欠款的人员（包括在职和离职）
for _, row in debt_pivot.iterrows():
    dept = row["三级部门"]
    name = row["销售员名称"]
    
    if dept not in result:
        result[dept] = {}
    
    d30 = round(row.get("30天内", 0), 2)
    d30_90 = round(row.get("30-90天", 0), 2)
    d90_180 = round(row.get("90-180天", 0), 2)
    d180 = round(row.get("180天以上", 0), 2)
    total_debt = round(d30 + d30_90 + d90_180 + d180, 2)
    
    # 查找认款
    c_row = collect[(collect["三级部门"] == dept) & (collect["销售员名称"] == name)]
    c_amt = round(float(c_row["认款协同金额"].values[0]), 2) if len(c_row) > 0 else 0.0
    
    result[dept][name] = {
        "name": name,
        "perf": 0.0,  # 默认业绩为0（离职或跨部门）
        "collect": 0.0,
        "debt": total_debt,
        "orders": 0,
        "d30": d30,
        "d30_90": d30_90,
        "d90_180": d90_180,
        "d180": d180,
        "total_debt": total_debt,
        "collect_amt": c_amt,
    }

# 再叠加上在职人员的业绩数据（部门以业绩表为准）
for _, row in perf.iterrows():
    dept = row["三级部门"]
    name = row["销售员名称"]
    
    if dept not in result:
        result[dept] = {}
    
    if name in result[dept]:
        # 该部门已有此人的欠款数据，叠加业绩
        result[dept][name]["perf"] = float(row["业绩"])
        result[dept][name]["collect"] = float(row["回款"])
        result[dept][name]["orders"] = int(row["单数"])
    else:
        # 该部门没有此人的欠款数据（可能无欠款），新建记录
        c_row = collect[(collect["三级部门"] == dept) & (collect["销售员名称"] == name)]
        c_amt = round(float(c_row["认款协同金额"].values[0]), 2) if len(c_row) > 0 else 0.0
        
        result[dept][name] = {
            "name": name,
            "perf": float(row["业绩"]),
            "collect": float(row["回款"]),
            "debt": 0.0,
            "orders": int(row["单数"]),
            "d30": 0.0,
            "d30_90": 0.0,
            "d90_180": 0.0,
            "d180": 0.0,
            "total_debt": 0.0,
            "collect_amt": c_amt,
        }

# 转换为列表格式
final_result = {}
for dept, people in result.items():
    final_result[dept] = list(people.values())

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

# 验证
total_debt_all = sum(sum(s["total_debt"] for s in lst) for lst in final_result.values())
print(f"[OK] sales_detail.json 已生成")
print(f"  部门数: {len(final_result)}")
total_people = sum(len(v) for v in final_result.values())
print(f"  总人数: {total_people}")
print(f"  欠款合计: {total_debt_all:.4f} 万")

for dept, lst in final_result.items():
    active_count = sum(1 for s in lst if s["perf"] > 0)
    left_count = sum(1 for s in lst if s["perf"] == 0 and s["total_debt"] != 0)
    no_debt = sum(1 for s in lst if s["perf"] > 0 and s["total_debt"] == 0)
    dept_debt = sum(s["total_debt"] for s in lst)
    print(f"  {dept}: {len(lst)}人(在职有业绩{active_count}/离职欠款{left_count}/在职无欠款{no_debt}), 欠款{dept_debt:.2f}万")
