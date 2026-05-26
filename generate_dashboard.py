#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据最新Excel数据生成中西部大区26财年Q1数据看板
"""
import pandas as pd
import json

EXCEL = "C:/Users/wm881/Downloads/业绩 欠款看板.xlsx"

# ===================== 读取所有工作表 =====================
df25 = pd.read_excel(EXCEL, sheet_name="25财年Q1业绩")
df26 = pd.read_excel(EXCEL, sheet_name="26财年Q1业绩")
df_target = pd.read_excel(EXCEL, sheet_name="26财年业绩目标季度拆分")
df_debt_all = pd.read_excel(EXCEL, sheet_name="欠款数据 ")
df_collect_all = pd.read_excel(EXCEL, sheet_name="26财年Q1认款数据")

# ===================== 过滤中西部大区 =====================
df25_xb = df25[df25["一级部门"] == "中西部大区"].copy()
df26_xb = df26[df26["一级部门"] == "中西部大区"].copy()
df_debt = df_debt_all[df_debt_all["一级部门"] == "中西部大区"].copy()
df_collect = df_collect_all[df_collect_all["一级部门"] == "中西部大区"].copy()

# ===================== 业绩汇总 =====================
sum25 = df25_xb.groupby("三级部门")["业绩总金额"].sum() / 10000
sum26 = df26_xb.groupby("三级部门")["业绩总金额"].sum() / 10000
# 剔除离职销售员，只统计在职人数
df26_active = df26_xb[df26_xb["销售员状态"] == "在职"]
sales_count = df26_active.groupby("三级部门")["销售员名称"].nunique()

# ===================== 目标数据（单位已是万元，不需要再除以10000）=====================
targets = {}
for _, row in df_target.iterrows():
    dept = str(row["区域"]).strip()
    val = row.get("26财年Q1", 0)
    if pd.notna(val) and val > 0:
        targets[dept] = float(val)  # 已是万元

# ===================== 欠款数据处理 =====================
# 账龄分类（含全部正负欠款）—— 用于四个账龄桶汇总
df_debt_aged = df_debt.copy()
df_debt_aged["欠款天数"] = pd.to_numeric(df_debt_aged["欠款天数"], errors="coerce").fillna(0)

def classify_days(days):
    if days <= 30:
        return "30天内"
    elif days <= 90:
        return "30-90天"
    elif days <= 180:
        return "90-180天"
    else:
        return "180天以上"

df_debt_aged["账龄分类"] = df_debt_aged["欠款天数"].apply(classify_days)

# 按部门+账龄汇总（含正负）
debt_pivot = df_debt_aged.pivot_table(
    values="欠款金额", index="三级部门", columns="账龄分类",
    aggfunc="sum", fill_value=0
) / 10000

# 确保四个账龄列都存在
for col in ["30天内","30-90天","90-180天","180天以上"]:
    if col not in debt_pivot.columns:
        debt_pivot[col] = 0

# 账龄总分布（含正负）
age_dist = df_debt_aged.groupby("账龄分类")["欠款金额"].sum() / 10000

# 仅正数欠款 —— 用于加权天数计算和风险客户
df_debt_pos = df_debt[df_debt["欠款金额"] > 0].copy()
df_debt_pos["欠款天数"] = pd.to_numeric(df_debt_pos["欠款天数"], errors="coerce").fillna(0)
df_debt_pos["账龄分类"] = df_debt_pos["欠款天数"].apply(classify_days)

# 全部欠款（正负相抵）按部门汇总 —— 用于KPI和回款周期
debt_net_by_dept = df_debt.groupby("三级部门")["欠款金额"].sum() / 10000

# ===================== 认款数据 =====================
collect_by_dept = df_collect.groupby("三级部门")["认款协同金额"].sum() / 10000

# ===================== 回款加权天数（认款端） =====================
from datetime import datetime

df_collect_w = df_collect.copy()
df_collect_w["业绩日期"] = pd.to_datetime(df_collect_w["业绩日期"], errors="coerce")
df_collect_w["认款时间"] = pd.to_datetime(df_collect_w["认款时间"], errors="coerce")
df_collect_w["认款天数"] = df_collect_w.apply(
    lambda row: max(0, (row["认款时间"] - row["业绩日期"]).days)
    if pd.notna(row["业绩日期"]) and pd.notna(row["认款时间"]) else 0,
    axis=1
)
df_collect_w["rec_weighted"] = df_collect_w["认款协同金额"] * df_collect_w["认款天数"]
rec_weighted_by_dept = df_collect_w.groupby("三级部门")["rec_weighted"].sum()  # 单位：元·天

# ===================== 欠款加权天数（欠款端） =====================
debt_weighted_by_dept = df_debt_pos.groupby("三级部门").apply(
    lambda g: (g["欠款金额"] * g["欠款天数"]).sum(), include_groups=False
)  # 单位：元·天

# ===================== 加权回款周期 =====================
# 公式: 回款周期 = (欠款加权天数 + 回款加权天数) / (欠款总额 + 认款协同金额)
def calc_cycle(dept):
    # 欠款端（单位：元）
    debt_w = float(debt_weighted_by_dept.get(dept, 0))
    debt_total = float(df_debt[df_debt["三级部门"] == dept]["欠款金额"].sum())

    # 认款端（单位：元）
    rec_w = float(rec_weighted_by_dept.get(dept, 0))
    rec_total = float(df_collect_w[df_collect_w["三级部门"] == dept]["认款协同金额"].sum())

    total_w = debt_w + rec_w
    total_a = debt_total + rec_total

    if total_a == 0:
        return 0
    return round(total_w / total_a, 1)

# ===================== 汇总部门数据 =====================
all_depts = sorted(set(list(sum26.index) + list(sum25.index)))
exclude_keywords = ["中西部", "合计", "大区"]
all_depts = [d for d in all_depts if not any(k in str(d) for k in exclude_keywords)]

dept_data = []
for dept in all_depts:
    v26 = round(float(sum26.get(dept, 0)), 2)
    v25 = round(float(sum25.get(dept, 0)), 2)
    yoy = round((v26 - v25) / v25 * 100, 1) if v25 > 0 else 0

    # 目标匹配
    tgt = targets.get(dept, 0)
    if tgt == 0:
        for k, v in targets.items():
            if dept in k or k in dept:
                tgt = v
                break

    completion = round(v26 / tgt * 100, 1) if tgt > 0 else 0
    sales = int(sales_count.get(dept, 0))

    # 欠款账龄
    if dept in debt_pivot.index:
        row = debt_pivot.loc[dept]
        d30     = round(float(row.get("30天内", 0)), 2)
        d30_90  = round(float(row.get("30-90天", 0)), 2)
        d90_180 = round(float(row.get("90-180天", 0)), 2)
        d180    = round(float(row.get("180天以上", 0)), 2)
    else:
        d30 = d30_90 = d90_180 = d180 = 0

    total_debt = round(float(debt_net_by_dept.get(dept, 0)), 2)
    collect = round(float(collect_by_dept.get(dept, 0)), 2)
    cycle = calc_cycle(dept)

    dept_data.append({
        "dept": dept,
        "v26": v26, "v25": v25, "yoy": yoy,
        "target": round(tgt, 1), "completion": completion, "sales": sales,
        "d30": d30, "d30_90": d30_90, "d90_180": d90_180, "d180": d180,
        "total_debt": total_debt, "collect": collect, "cycle": cycle
    })

dept_data.sort(key=lambda x: x["v26"], reverse=True)

# ===================== 整体合计 =====================
total_26 = round(sum(d["v26"] for d in dept_data), 2)
total_25 = round(sum(d["v25"] for d in dept_data), 2)
total_yoy = round((total_26 - total_25) / total_25 * 100, 1) if total_25 > 0 else 0
total_target = round(float(targets.get("中西部大区", sum(d["target"] for d in dept_data if d["target"] > 0))), 1)
total_completion = round(total_26 / total_target * 100, 1) if total_target > 0 else 0
total_sales = df26_active[df26_active["一级部门"] == "中西部大区"]["销售员名称"].nunique()
total_d30     = round(sum(d["d30"]     for d in dept_data), 2)
total_d30_90  = round(sum(d["d30_90"]  for d in dept_data), 2)
total_d90_180 = round(sum(d["d90_180"] for d in dept_data), 2)
total_d180    = round(sum(d["d180"]    for d in dept_data), 2)
total_debt    = round(float(debt_net_by_dept.sum()), 2)
total_collect = round(sum(d["collect"] for d in dept_data), 2)

# ===================== 回款周期 =====================
cycle_data = [(d["dept"], d["cycle"]) for d in dept_data if d["cycle"] > 0]
avg_cycle   = round(sum(c for _, c in cycle_data) / len(cycle_data), 1) if cycle_data else 0
max_cycle   = max((c for _, c in cycle_data), default=0)
min_cycle   = min((c for _, c in cycle_data), default=0)
max_dept    = next((d for d, c in cycle_data if c == max_cycle), "")
min_dept    = next((d for d, c in reversed(cycle_data) if c == min_cycle), "")
over90_count = sum(1 for _, c in cycle_data if c > 90)

# ===================== 高风险客户 =====================
df_risk = df_debt_pos[df_debt_pos["账龄分类"].isin(["90-180天","180天以上"])]
risk_list = []
if "客户名称" in df_risk.columns:
    risk_agg = df_risk.groupby(["客户名称","三级部门"])["欠款金额"].sum().sort_values(ascending=False).head(15)
    risk_list = [(f"{nm}（{dept}）", round(amt/10000, 2)) for (nm, dept), amt in risk_agg.items()]

# ===================== 打印核查 =====================
print("=== 业绩数据 ===")
for d in dept_data:
    print(f"  {d['dept']}: 26Q1={d['v26']}万, 25Q1={d['v25']}万, 同比={d['yoy']}%, 目标={d['target']}万, 完成率={d['completion']}%, 销售员={d['sales']}")
print(f"  合计: 26Q1={total_26}, 25Q1={total_25}, 目标={total_target}, 完成率={total_completion}%")

print("\n=== 欠款账龄 ===")
print(f"  30天内:{total_d30}  30-90天:{total_d30_90}  90-180天:{total_d90_180}  180天以上:{total_d180}  合计:{total_debt}")
print(f"  认款合计:{total_collect}")

print("\n=== 回款周期 ===")
for d, c in sorted(cycle_data, key=lambda x: x[1], reverse=True):
    print(f"  {d}: {c}天")

print("\n=== 高风险客户 ===")
for name, amt in risk_list[:5]:
    print(f"  {name}: {amt}万")

# 保存JSON
with open("C:/Users/wm881/WorkBuddy/20260513090923/dashboard_final.json", "w", encoding="utf-8") as f:
    json.dump({
        "dept_data": dept_data,
        "total": {
            "v26": total_26, "v25": total_25, "yoy": total_yoy,
            "target": total_target, "completion": total_completion,
            "sales": total_sales, "debt": total_debt, "collect": total_collect,
            "d30": total_d30, "d30_90": total_d30_90, "d90_180": total_d90_180, "d180": total_d180
        },
        "risk_customers": risk_list,
        "cycle": {
            "avg": avg_cycle, "max": max_cycle, "min": min_cycle,
            "max_dept": max_dept, "min_dept": min_dept, "over90": over90_count,
            "data": sorted(cycle_data, key=lambda x: x[1], reverse=True)
        },
        "age_dist": {k: round(float(v), 2) for k, v in age_dist.items()}
    }, f, ensure_ascii=False, indent=2)

print("\n[OK] 数据整理完成，已保存到 dashboard_final.json")
