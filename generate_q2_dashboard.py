# -*- coding: utf-8 -*-
"""
26财年Q2数据看板一键生成脚本
从 D:/业绩 欠款看板 Q2.xlsx 提取数据，生成完整看板（含三级下钻）
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

# ===================== 配置 =====================
EXCEL = 'D:/业绩 欠款看板 Q2.xlsx'
OUT_DIR = 'C:/Users/wm881/WorkBuddy/20260513090923'
REGION = '中西部大区'
QUARTER = 'Q2'
Q_LABEL = '26Q2'
Q_PREV = '25Q2'
HTML_OUT = f'{OUT_DIR}/中西部大区26财年Q2数据看板.html'
TODAY = datetime.now()
TODAY_STR = TODAY.strftime('%Y-%m-%d')
YESTERDAY_STR = (TODAY - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"=== 26财年Q2数据看板生成 ===")
print(f"Excel: {EXCEL}")
print(f"日期: {TODAY_STR}")
print()

# ===================== 读取Excel =====================
df25 = pd.read_excel(EXCEL, sheet_name="25财年Q2业绩")
df26 = pd.read_excel(EXCEL, sheet_name="26财年Q2业绩")
df_target = pd.read_excel(EXCEL, sheet_name="26财年业绩目标季度拆分")
df_debt_all = pd.read_excel(EXCEL, sheet_name="欠款数据 ")
df_collect_all = pd.read_excel(EXCEL, sheet_name="认款数据")

# 过滤中西部大区
df25_xb = df25[df25["一级部门"] == REGION].copy()
df26_xb = df26[df26["一级部门"] == REGION].copy()
df_debt = df_debt_all[df_debt_all["一级部门"] == REGION].copy()
df_collect = df_collect_all[df_collect_all["一级部门"] == REGION].copy()
df_staff_raw = pd.read_excel(EXCEL, sheet_name="在职销售人数")

# 强制转换数值列，防止Excel中混入日期等类型
df_debt["欠款金额"] = pd.to_numeric(df_debt["欠款金额"], errors="coerce").fillna(0)
df_collect["认款协同金额"] = pd.to_numeric(df_collect["认款协同金额"], errors="coerce").fillna(0)

# ===================== 在职销售人数（从Excel表格读取）=====================
staff_count_from_excel = {}
for _, row in df_staff_raw.iterrows():
    dept = str(row.iloc[0]).strip()
    count = int(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
    if "合计" in dept or "大区" in dept:
        continue
    staff_count_from_excel[dept] = count

total_staff_from_excel = sum(staff_count_from_excel.values())
print(f"在职销售人数（来自Excel）: {staff_count_from_excel}，合计={total_staff_from_excel}")
print()

# ===================== 计算欠款天数（Q2 Excel无此列，需手动计算）=====================
df_debt["业绩日期"] = pd.to_datetime(df_debt["业绩日期"], errors="coerce")
df_debt["欠款天数"] = df_debt["业绩日期"].apply(
    lambda d: max(0, (TODAY - d.to_pydatetime()).days) if pd.notna(d) else 0
)

# ===================== 业绩汇总 =====================
sum25 = df25_xb.groupby("三级部门")["业绩总金额"].sum() / 10000
df26_active = df26_xb[df26_xb["销售员状态"] == "在职"]
sum26 = df26_active.groupby("三级部门")["业绩总金额"].sum() / 10000
# 使用Excel表格中的在职销售人数，不再从业绩数据统计
sales_count = staff_count_from_excel

# ===================== 目标数据（Q2列）=====================
targets = {}
for _, row in df_target.iterrows():
    dept = str(row["区域"]).strip()
    val = row.get("26财年Q2", 0)
    if pd.notna(val) and val > 0:
        targets[dept] = float(val)

# ===================== 欠款数据处理 =====================
df_debt_aged = df_debt.copy()
df_debt_aged["欠款天数"] = pd.to_numeric(df_debt_aged["欠款天数"], errors="coerce").fillna(0)

def classify_days(days):
    if days <= 30: return "30天内"
    elif days <= 90: return "30-90天"
    elif days <= 180: return "90-180天"
    else: return "180天以上"

df_debt_aged["账龄分类"] = df_debt_aged["欠款天数"].apply(classify_days)

debt_pivot = df_debt_aged.pivot_table(
    values="欠款金额", index="三级部门", columns="账龄分类",
    aggfunc="sum", fill_value=0
) / 10000

for col in ["30天内","30-90天","90-180天","180天以上"]:
    if col not in debt_pivot.columns:
        debt_pivot[col] = 0

age_dist = df_debt_aged.groupby("账龄分类")["欠款金额"].sum() / 10000

df_debt_pos = df_debt[df_debt["欠款金额"] > 0].copy()
df_debt_pos["欠款天数"] = pd.to_numeric(df_debt_pos["欠款天数"], errors="coerce").fillna(0)
df_debt_pos["账龄分类"] = df_debt_pos["欠款天数"].apply(classify_days)

debt_net_by_dept = df_debt.groupby("三级部门")["欠款金额"].sum() / 10000

# ===================== 认款数据 =====================
collect_by_dept = df_collect.groupby("三级部门")["认款协同金额"].sum() / 10000

# ===================== 回款加权天数 =====================
df_collect_w = df_collect.copy()
df_collect_w["业绩日期"] = pd.to_datetime(df_collect_w["业绩日期"], errors="coerce")
df_collect_w["认款时间"] = pd.to_datetime(df_collect_w["认款时间"], errors="coerce")
df_collect_w["认款天数"] = df_collect_w.apply(
    lambda row: max(0, (row["认款时间"] - row["业绩日期"]).days)
    if pd.notna(row["业绩日期"]) and pd.notna(row["认款时间"]) else 0,
    axis=1
)
df_collect_w["rec_weighted"] = df_collect_w["认款协同金额"] * df_collect_w["认款天数"]
rec_weighted_by_dept = df_collect_w.groupby("三级部门")["rec_weighted"].sum()

debt_weighted_by_dept = df_debt_pos.groupby("三级部门").apply(
    lambda g: (g["欠款金额"] * g["欠款天数"]).sum(), include_groups=False
)

def calc_cycle(dept):
    debt_w = float(debt_weighted_by_dept.get(dept, 0))
    debt_total = float(df_debt[df_debt["三级部门"] == dept]["欠款金额"].sum())
    rec_w = float(rec_weighted_by_dept.get(dept, 0))
    rec_total = float(df_collect_w[df_collect_w["三级部门"] == dept]["认款协同金额"].sum())
    total_w = debt_w + rec_w
    total_a = debt_total + rec_total
    if total_a == 0: return 0
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
    tgt = targets.get(dept, 0)
    if tgt == 0:
        for k, v in targets.items():
            if dept in k or k in dept:
                tgt = v
                break
    completion = round(v26 / tgt * 100, 1) if tgt > 0 else 0
    sales = int(sales_count.get(dept, 0))
    if dept in debt_pivot.index:
        row = debt_pivot.loc[dept]
        d30 = round(float(row.get("30天内", 0)), 2)
        d30_90 = round(float(row.get("30-90天", 0)), 2)
        d90_180 = round(float(row.get("90-180天", 0)), 2)
        d180 = round(float(row.get("180天以上", 0)), 2)
    else:
        d30 = d30_90 = d90_180 = d180 = 0
    total_debt = round(float(debt_net_by_dept.get(dept, 0)), 2)
    collect = round(float(collect_by_dept.get(dept, 0)), 2)
    cycle = calc_cycle(dept)
    dept_data.append({
        "dept": dept, "v26": v26, "v25": v25, "yoy": yoy,
        "target": round(tgt, 1), "completion": completion, "sales": sales,
        "d30": d30, "d30_90": d30_90, "d90_180": d90_180, "d180": d180,
        "total_debt": total_debt, "collect": collect, "cycle": cycle
    })

dept_data.sort(key=lambda x: x["v26"], reverse=True)

total_26 = round(sum(d["v26"] for d in dept_data), 2)
total_25 = round(sum(d["v25"] for d in dept_data), 2)
total_yoy = round((total_26 - total_25) / total_25 * 100, 1) if total_25 > 0 else 0
total_target = round(float(targets.get("中西部大区", sum(d["target"] for d in dept_data if d["target"] > 0))), 1)
total_completion = round(total_26 / total_target * 100, 1) if total_target > 0 else 0
total_sales = total_staff_from_excel
total_d30 = round(sum(d["d30"] for d in dept_data), 2)
total_d30_90 = round(sum(d["d30_90"] for d in dept_data), 2)
total_d90_180 = round(sum(d["d90_180"] for d in dept_data), 2)
total_d180 = round(sum(d["d180"] for d in dept_data), 2)
total_debt = round(float(debt_net_by_dept.sum()), 2)
total_collect = round(sum(d["collect"] for d in dept_data), 2)

cycle_data = [(d["dept"], d["cycle"]) for d in dept_data if d["cycle"] > 0]
avg_cycle = round(sum(c for _, c in cycle_data) / len(cycle_data), 1) if cycle_data else 0
max_cycle = max((c for _, c in cycle_data), default=0)
min_cycle = min((c for _, c in cycle_data), default=0)
max_dept = next((d for d, c in cycle_data if c == max_cycle), "")
min_dept = next((d for d, c in reversed(cycle_data) if c == min_cycle), "")
over90_count = sum(1 for _, c in cycle_data if c > 90)

# 高风险客户
df_risk = df_debt_pos[df_debt_pos["账龄分类"].isin(["90-180天","180天以上"])]
risk_list = []
if "客户名称" in df_risk.columns:
    risk_agg = df_risk.groupby(["客户名称","三级部门"])["欠款金额"].sum().sort_values(ascending=False).head(15)
    risk_list = [(f"{nm}（{dept}）", round(amt/10000, 2)) for (nm, dept), amt in risk_agg.items()]

print("=== 业绩数据 ===")
for d in dept_data:
    print(f"  {d['dept']}: 26Q2={d['v26']}万, 25Q2={d['v25']}万, 同比={d['yoy']}%, 目标={d['target']}万, 完成率={d['completion']}%, 销售员={d['sales']}")
print(f"  合计: 26Q2={total_26}, 25Q2={total_25}, 目标={total_target}, 完成率={total_completion}%")
print(f"\n=== 欠款账龄 ===")
print(f"  30天内:{total_d30}  30-90天:{total_d30_90}  90-180天:{total_d90_180}  180天以上:{total_d180}  合计:{total_debt}")
print(f"  认款合计:{total_collect}")

# 保存 dashboard_final.json
dashboard_data = {
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
}
with open(f"{OUT_DIR}/dashboard_q2.json", "w", encoding="utf-8") as f:
    json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
print(f"\n[OK] dashboard_q2.json 已保存")

# ===================== 生成 sales_detail.json (Q2) =====================
print("\n=== 生成销售员明细 ===")
df26_active_sd = df26_xb[df26_xb["销售员状态"] == "在职"].copy()
active_sales_names = set(df26_active_sd["销售员名称"].dropna().astype(str).str.strip().unique())
perf = df26_active_sd.groupby(["三级部门", "销售员名称"]).agg(
    业绩=("业绩总金额", "sum"), 回款=("回款金额", "sum"), 单数=("业绩单号", "count")
).reset_index()
perf["业绩"] = (perf["业绩"] / 10000).round(2)
perf["回款"] = (perf["回款"] / 10000).round(2)

# 过滤欠款/认款数据，仅保留在职销售员
df_debt_all_sd = df_debt[df_debt["销售员名称"].fillna("").astype(str).str.strip().isin(active_sales_names)].copy()
df_debt_all_sd["欠款天数"] = pd.to_numeric(df_debt_all_sd["欠款天数"], errors="coerce").fillna(0)
df_debt_all_sd["账龄"] = df_debt_all_sd["欠款天数"].apply(classify_days)
debt_age = df_debt_all_sd.groupby(["三级部门", "销售员名称", "账龄"])["欠款金额"].sum().reset_index()
debt_age["欠款金额"] = (debt_age["欠款金额"] / 10000).round(2)
debt_pivot_sd = debt_age.pivot_table(
    index=["三级部门", "销售员名称"], columns="账龄", values="欠款金额", fill_value=0
).reset_index()
for col in ["30天内", "30-90天", "90-180天", "180天以上"]:
    if col not in debt_pivot_sd.columns:
        debt_pivot_sd[col] = 0.0

collect_sd = df_collect[df_collect["销售员名称"].fillna("").astype(str).str.strip().isin(active_sales_names)].groupby(["三级部门", "销售员名称"])["认款协同金额"].sum().reset_index()
collect_sd["认款协同金额"] = (collect_sd["认款协同金额"] / 10000).round(2)

result = {}
for _, row in debt_pivot_sd.iterrows():
    dept = row["三级部门"]
    name = row["销售员名称"]
    if dept not in result: result[dept] = {}
    d30 = round(row.get("30天内", 0), 2)
    d30_90 = round(row.get("30-90天", 0), 2)
    d90_180 = round(row.get("90-180天", 0), 2)
    d180 = round(row.get("180天以上", 0), 2)
    total_debt_sd = round(d30 + d30_90 + d90_180 + d180, 2)
    c_row = collect_sd[(collect_sd["三级部门"] == dept) & (collect_sd["销售员名称"] == name)]
    c_amt = round(float(c_row["认款协同金额"].values[0]), 2) if len(c_row) > 0 else 0.0
    result[dept][name] = {
        "name": name, "perf": 0.0, "collect": 0.0, "debt": total_debt_sd,
        "orders": 0, "d30": d30, "d30_90": d30_90, "d90_180": d90_180, "d180": d180,
        "total_debt": total_debt_sd, "collect_amt": c_amt
    }

for _, row in perf.iterrows():
    dept = row["三级部门"]
    name = row["销售员名称"]
    if dept not in result: result[dept] = {}
    if name in result[dept]:
        result[dept][name]["perf"] = float(row["业绩"])
        result[dept][name]["collect"] = float(row["回款"])
        result[dept][name]["orders"] = int(row["单数"])
    else:
        c_row = collect_sd[(collect_sd["三级部门"] == dept) & (collect_sd["销售员名称"] == name)]
        c_amt = round(float(c_row["认款协同金额"].values[0]), 2) if len(c_row) > 0 else 0.0
        result[dept][name] = {
            "name": name, "perf": float(row["业绩"]), "collect": float(row["回款"]),
            "debt": 0.0, "orders": int(row["单数"]),
            "d30": 0.0, "d30_90": 0.0, "d90_180": 0.0, "d180": 0.0,
            "total_debt": 0.0, "collect_amt": c_amt
        }

sales_detail = {dept: list(people.values()) for dept, people in result.items()}
with open(f"{OUT_DIR}/sales_detail_q2.json", "w", encoding="utf-8") as f:
    json.dump(sales_detail, f, ensure_ascii=False, indent=2)
print(f"[OK] sales_detail_q2.json ({sum(len(v) for v in sales_detail.values())}人)")

# ===================== 生成周期下钻数据 =====================
print("\n=== 生成回款周期下钻 ===")
df_debt_cyc = df_debt[df_debt["销售员名称"].fillna("").astype(str).str.strip().isin(active_sales_names)].copy()
df_debt_cyc["欠款天数"] = pd.to_numeric(df_debt_cyc["欠款天数"], errors="coerce").fillna(0)
df_debt_cyc["欠款金额_abs"] = df_debt_cyc["欠款金额"].abs()
df_debt_cyc["客户名称"] = df_debt_cyc["客户名称"].fillna("未知客户").astype(str).str.strip()
df_debt_cyc["销售员名称"] = df_debt_cyc["销售员名称"].fillna("").astype(str).str.strip()
df_debt_cyc = df_debt_cyc[df_debt_cyc["销售员名称"] != ""]

debt_map = defaultdict(lambda: defaultdict(lambda: {
    'weighted_days': 0.0, 'total_amt': 0.0, 'client_map': defaultdict(lambda: {
        'weighted_days': 0.0, 'total_amt': 0.0
    })
}))
for _, row in df_debt_cyc.iterrows():
    dept = row['三级部门']; sales = row['销售员名称']; client = row['客户名称']
    days = row['欠款天数']; amt = row['欠款金额_abs']
    debt_map[dept][sales]['weighted_days'] += amt * days
    debt_map[dept][sales]['total_amt'] += amt
    debt_map[dept][sales]['client_map'][client]['weighted_days'] += amt * days
    debt_map[dept][sales]['client_map'][client]['total_amt'] += amt

df_rec = df_collect[df_collect["销售员名称"].fillna("").astype(str).str.strip().isin(active_sales_names)].copy()
df_rec["认款协同金额"] = pd.to_numeric(df_rec["认款协同金额"], errors="coerce").fillna(0)
df_rec["回款客户名称"] = df_rec["回款客户名称"].fillna("未知客户").astype(str).str.strip()
df_rec["销售员名称"] = df_rec["销售员名称"].fillna("").astype(str).str.strip()
df_rec = df_rec[df_rec["销售员名称"] != ""]

rec_map = defaultdict(lambda: defaultdict(lambda: {
    'weighted_days': 0.0, 'total_amt': 0.0, 'client_map': defaultdict(lambda: {
        'weighted_days': 0.0, 'total_amt': 0.0
    })
}))
for _, row in df_rec.iterrows():
    dept = row['三级部门']; sales = row['销售员名称']; client = row['回款客户名称']
    amt = row['认款协同金额']
    perf_date = row.get('业绩日期'); rec_time = row.get('认款时间')
    if isinstance(perf_date, datetime) and isinstance(rec_time, datetime):
        rec_days = max(0, (rec_time - perf_date).days)
    else:
        rec_days = 0
    rec_map[dept][sales]['weighted_days'] += amt * rec_days
    rec_map[dept][sales]['total_amt'] += amt
    rec_map[dept][sales]['client_map'][client]['weighted_days'] += amt * rec_days
    rec_map[dept][sales]['client_map'][client]['total_amt'] += amt

all_depts_cyc = sorted(set(str(k) for k in list(debt_map.keys()) + list(rec_map.keys()) if pd.notna(k)))

sales_cycle_data = {}
for dept in all_depts_cyc:
    all_sales = sorted(set(str(k) for k in list(debt_map[dept].keys()) + list(rec_map[dept].keys()) if pd.notna(k)))
    dept_list = []
    for sales_name in all_sales:
        d = debt_map[dept][sales_name]; rc = rec_map[dept][sales_name]
        total_w = d['weighted_days'] + rc['weighted_days']
        total_a = d['total_amt'] + rc['total_amt']
        cycle = round(total_w / total_a, 1) if total_a > 0 else 0
        dept_list.append({
            'name': sales_name, 'debt_amt': round(d['total_amt'], 2),
            'rec_amt': round(rc['total_amt'], 2), 'cycle': cycle,
            'debt_weighted': round(d['weighted_days'], 2), 'rec_weighted': round(rc['weighted_days'], 2)
        })
    dept_list.sort(key=lambda x: x['cycle'], reverse=True)
    sales_cycle_data[dept] = dept_list

cust_cycle_data = {}
for dept in all_depts_cyc:
    all_sales = sorted(set(str(k) for k in list(debt_map[dept].keys()) + list(rec_map[dept].keys()) if pd.notna(k)))
    dept_cust = {}
    for sales_name in all_sales:
        d_clients = debt_map[dept][sales_name]['client_map']
        r_clients = rec_map[dept][sales_name]['client_map']
        all_clients = sorted(set(list(d_clients.keys()) + list(r_clients.keys())))
        cust_list = []
        for cname in all_clients:
            dc = d_clients[cname]; rc = r_clients[cname]
            total_w = dc['weighted_days'] + rc['weighted_days']
            total_a = dc['total_amt'] + rc['total_amt']
            cycle = round(total_w / total_a, 1) if total_a > 0 else 0
            cust_list.append({'name': cname, 'debt_amt': round(dc['total_amt'], 2), 'rec_amt': round(rc['total_amt'], 2), 'cycle': cycle})
        cust_list.sort(key=lambda x: x['cycle'], reverse=True)
        dept_cust[sales_name] = cust_list
    cust_cycle_data[dept] = dept_cust

total_cust_cyc = sum(sum(len(clients) for clients in sales.values()) for sales in cust_cycle_data.values())
print(f"[OK] sales_cycle_data ({len(sales_cycle_data)}部门), cust_cycle_data ({total_cust_cyc}客户)")

# ===================== 生成欠款/业绩下钻数据 =====================
print("\n=== 生成欠款/业绩下钻 ===")
# 欠款下钻
df_debt_drill = df_debt[df_debt["销售员名称"].fillna("").astype(str).str.strip().isin(active_sales_names)].copy()
df_debt_drill["欠款天数"] = pd.to_numeric(df_debt_drill["欠款天数"], errors="coerce").fillna(0)
df_debt_drill["欠款金额"] = pd.to_numeric(df_debt_drill["欠款金额"], errors="coerce").fillna(0)
df_debt_drill["客户名称"] = df_debt_drill["客户名称"].fillna("未知客户").astype(str).str.strip()
df_debt_drill["销售员名称"] = df_debt_drill["销售员名称"].fillna("").astype(str).str.strip()
df_debt_drill = df_debt_drill[df_debt_drill["销售员名称"] != ""]

def classify_drill(days):
    if days <= 30: return 'd30'
    elif days <= 90: return 'd30_90'
    elif days <= 180: return 'd90_180'
    else: return 'd180'

debt_drill_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
    'd30': 0.0, 'd30_90': 0.0, 'd90_180': 0.0, 'd180': 0.0, 'max_days': 0
})))
for _, row in df_debt_drill.iterrows():
    dept = row['三级部门']; sales = row['销售员名称']; client = row['客户名称']
    days = row['欠款天数']; amt = row['欠款金额'] / 10000
    bucket = classify_drill(days)
    entry = debt_drill_map[dept][sales][client]
    entry[bucket] += amt
    entry['max_days'] = max(entry['max_days'], days)

debt_drill = {}
for dept in sorted(str(k) for k in debt_drill_map.keys() if pd.notna(k)):
    sales_list = []
    for sales_name in sorted(str(k) for k in debt_drill_map[dept].keys() if pd.notna(k)):
        cust_list = []; s_d30 = s_d30_90 = s_d90_180 = s_d180 = 0.0
        for client_name in sorted(str(k) for k in debt_drill_map[dept][sales_name].keys() if pd.notna(k)):
            c = debt_drill_map[dept][sales_name][client_name]
            c_total = round(c['d30'] + c['d30_90'] + c['d90_180'] + c['d180'], 2)
            s_d30 += c['d30']; s_d30_90 += c['d30_90']; s_d90_180 += c['d90_180']; s_d180 += c['d180']
            cust_list.append({'name': client_name, 'd30': round(c['d30'],2), 'd30_90': round(c['d30_90'],2),
                'd90_180': round(c['d90_180'],2), 'd180': round(c['d180'],2), 'total': c_total, 'max_days': int(c['max_days'])})
        cust_list.sort(key=lambda x: x['total'], reverse=True)
        s_total = round(s_d30 + s_d30_90 + s_d90_180 + s_d180, 2)
        sales_list.append({'name': sales_name, 'd30': round(s_d30,2), 'd30_90': round(s_d30_90,2),
            'd90_180': round(s_d90_180,2), 'd180': round(s_d180,2), 'total': s_total, 'cust_count': len(cust_list), 'custs': cust_list})
    sales_list.sort(key=lambda x: x['total'], reverse=True)
    debt_drill[dept] = sales_list

# 业绩下钻
df_perf_drill = df26_active.copy()
df_perf_drill["客户名称"] = df_perf_drill["客户名称"].fillna("未知客户").astype(str).str.strip()
df_perf_drill["销售员名称"] = df_perf_drill["销售员名称"].fillna("").astype(str).str.strip()
df_perf_drill = df_perf_drill[df_perf_drill["销售员名称"] != ""]
df_perf_drill["业绩总金额"] = pd.to_numeric(df_perf_drill["业绩总金额"], errors="coerce").fillna(0)
df_perf_drill["回款金额"] = pd.to_numeric(df_perf_drill["回款金额"], errors="coerce").fillna(0)

perf_drill_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'perf': 0.0, 'collect': 0.0, 'orders': 0})))
for _, row in df_perf_drill.iterrows():
    dept = row['三级部门']; sales = row['销售员名称']; client = row['客户名称']
    perf_amt = float(row['业绩总金额']) / 10000; coll_amt = float(row['回款金额']) / 10000
    entry = perf_drill_map[dept][sales][client]
    entry['perf'] += perf_amt; entry['collect'] += coll_amt; entry['orders'] += 1

perf_drill = {}
for dept in sorted(str(k) for k in perf_drill_map.keys() if pd.notna(k)):
    sales_list = []
    for sales_name in sorted(str(k) for k in perf_drill_map[dept].keys() if pd.notna(k)):
        cust_list = []; s_perf = s_coll = 0
        for client_name in sorted(str(k) for k in perf_drill_map[dept][sales_name].keys() if pd.notna(k)):
            c = perf_drill_map[dept][sales_name][client_name]
            cust_list.append({'name': client_name, 'perf': round(c['perf'],2), 'collect': round(c['collect'],2), 'orders': c['orders']})
            s_perf += c['perf']; s_coll += c['collect']
        cust_list.sort(key=lambda x: x['perf'], reverse=True)
        sales_list.append({'name': sales_name, 'total': round(s_perf,2), 'collect': round(s_coll,2),
            'cust_count': len(cust_list), 'custs': cust_list})
    sales_list.sort(key=lambda x: x['total'], reverse=True)
    perf_drill[dept] = sales_list

print(f"[OK] debt_drill ({len(debt_drill)}部门), perf_drill ({len(perf_drill)}部门)")

# ===================== 生成HTML =====================
print("\n=== 生成HTML看板 ===")

dept_js = []
for d in dept_data:
    dept_js.append(f"{{dept:'{d['dept']}',v26:{d['v26']},v25:{d['v25']},yoy:{d['yoy']},target:{d['target']},completion:{d['completion']},sales:{d['sales']},d30:{d['d30']},d30_90:{d['d30_90']},d90_180:{d['d90_180']},d180:{d['d180']},total_debt:{d['total_debt']},collect:{d['collect']},cycle:{d['cycle']}}}")
dept_js_str = ",\n    ".join(dept_js)

sales_js_parts = []
for dept, people in sales_detail.items():
    person_js = []
    for p in people:
        person_js.append(f'{{"name":"{p["name"]}","perf":{p["perf"]},"collect":{p["collect"]},"debt":{p["total_debt"]},"orders":0,"d30":{p["d30"]},"d30_90":{p["d30_90"]},"d90_180":{p["d90_180"]},"d180":{p["d180"]},"total_debt":{p["total_debt"]},"collect_amt":{p["collect_amt"]}}}')
    sales_js_parts.append(f'"{dept}":[{",".join(person_js)}]')
sales_js_str = "{" + ",".join(sales_js_parts) + "}"

v26_total = total_26; target_total = total_target; completion = total_completion
v25_total = total_25; yoy = total_yoy; debt_total = total_debt
d90_total = total_d90_180 + total_d180; sales_count_total = total_sales
d30_total = total_d30; d30_90_total = total_d30_90; d90_180_total = total_d90_180
d180_total = total_d180; collect_total = total_collect
target_gap = target_total - v26_total; kpi_gap = f"{target_gap:.2f}"

dept_by_debt = sorted(dept_data, key=lambda x: x['total_debt'], reverse=True)
dept_by_cycle = sorted([(d['dept'], d['cycle']) for d in dept_data if d['cycle'] > 0], key=lambda x: x[1], reverse=True)

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
perf_foot = f'''<tr><td>合计</td><td>{v26_total:.2f}</td><td>{target_total:.1f}</td><td>{completion:.1f}%</td>
                        <td>{v25_total:.2f}</td><td class="trend-down">▼ {yoy:.1f}%</td><td>{sales_count_total}</td><td></td></tr>'''

debt_rows = ""
for d in dept_by_debt:
    risky = d['d90_180'] + d['d180']
    badge = "badge-down" if risky > 50 else "badge-warning" if risky > 20 else "badge-good"
    status = "高风险" if risky > 50 else "关注" if risky > 20 else "较好"
    d90_cls = "warning" if d['d90_180'] > 0 else ""
    d180_cls = "negative" if d['d180'] > 0 else ""
    debt_rows += f'''<tr onclick="showSalesDetail('{d['dept']}','debt')" style="cursor:pointer;"><td>🏢 {d['dept']}</td><td>{d['d30']:.2f}</td><td>{d['d30_90']:.2f}</td><td class="{d90_cls}">{d['d90_180']:.2f}</td><td class="{d180_cls}">{d['d180']:.2f}</td><td class="negative">{d['total_debt']:.2f}</td><td><span class="status-badge {badge}">{status}</span></td></tr>'''
debt_foot = f'''<tr><td>合计</td><td>{d30_total:.2f}</td><td>{d30_90_total:.2f}</td><td>{d90_180_total:.2f}</td><td>{d180_total:.2f}</td><td>{debt_total:.2f}</td><td></td></tr>'''

risk_rows = ""
for i, (name, amt) in enumerate(risk_list[:15], 1):
    risk_level = "极高风险" if amt > 80 else "高风险" if amt > 40 else "关注"
    risk_badge = "badge-down" if amt > 40 else "badge-warning"
    risk_cls = "negative" if amt > 40 else "warning"
    risk_rows += f'<tr><td>{i}</td><td style="text-align:left;">{name}</td><td class="{risk_cls}">{amt:.2f}</td><td><span class="status-badge {risk_badge}">{risk_level}</span></td></tr>'

cycle_rows = ""
for dept, cyc in dept_by_cycle:
    d = next(x for x in dept_data if x['dept'] == dept)
    badge = "badge-down" if cyc > 90 else "badge-warning" if cyc > 60 else "badge-good"
    status = "需关注" if cyc > 90 else "一般" if cyc > 60 else "良好"
    cyc_cls = "negative" if cyc > 90 else "warning" if cyc > 60 else "highlight"
    cycle_rows += f'<tr onclick="showSalesDetail(\'{dept}\',\'cycle\')" style="cursor:pointer;"><td>🏢 {dept}</td><td>{d["total_debt"]:.2f}</td><td>{d["collect"]:.2f}</td><td class="{cyc_cls}">{cyc:.1f}</td><td><span class="status-badge {badge}">{status}</span></td></tr>'
cycle_foot = f'<tr><td>合计</td><td>{debt_total:.2f}</td><td>{collect_total:.2f}</td><td>{avg_cycle:.1f}</td><td></td></tr>'
debt_pie_data = f'[{d30_total:.2f}, {d30_90_total:.2f}, {d90_180_total:.2f}, {d180_total:.2f}]'

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中西部大区 26财年Q2 数据看板</title>
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
        <h1>中西部大区 26财年Q2 数据看板</h1>
        <p>数据截止：{YESTERDAY_STR} &nbsp;|&nbsp; 统计基日：{TODAY_STR} &nbsp;|&nbsp; 生成于：{TODAY_STR}</p>
    </div>
    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-icon">💰</div><h3>26Q2 实际业绩</h3><div class="value">{v26_total:.2f}<span style="font-size:0.5em;">万</span></div><div class="sub">目标：{target_total:.1f}万</div></div>
        <div class="kpi-card"><div class="kpi-icon">🎯</div><h3>Q2目标完成率</h3><div class="value {'negative' if completion < 50 else ''}">{completion:.1f}%</div><div class="sub">距目标还差 {kpi_gap}万</div></div>
        <div class="kpi-card"><div class="kpi-icon">📉</div><h3>同比25Q2</h3><div class="value negative">{yoy:.1f}%</div><div class="sub">25Q2：{v25_total:.2f}万</div></div>
        <div class="kpi-card"><div class="kpi-icon">👥</div><h3>在职销售员总数</h3><div class="value" style="color:#ffa502;">{sales_count_total}</div><div class="sub">人</div></div>
        <div class="kpi-card"><div class="kpi-icon">⚠️</div><h3>逾期欠款总额</h3><div class="value negative">{debt_total:.2f}<span style="font-size:0.5em;">万</span></div><div class="sub">90天以上：{d90_total:.2f}万</div></div>
    </div>
    <div class="tab-nav">
        <button class="tab-btn active" onclick="switchTab('performance', this)"><span class="tab-icon">📊</span>业绩分析</button>
        <button class="tab-btn" onclick="switchTab('debt', this)"><span class="tab-icon">💳</span>欠款分析</button>
        <button class="tab-btn" onclick="switchTab('collection', this)"><span class="tab-icon">⏱️</span>平均回款周期分析</button>
    </div>
    <div id="tab-performance" class="tab-content active">
        <div class="module">
            <h2 class="module-title">📊 26财年Q2 部门业绩总览</h2>
            <div class="charts-section">
                <div class="chart-box"><h3>25Q2 vs 26Q2 部门业绩对比（万元）</h3><div class="chart-container"><canvas id="perfBarChart"></canvas></div></div>
                <div class="chart-box"><h3>26Q2 部门业绩占比分布</h3><div class="chart-container"><canvas id="perfPieChart"></canvas></div></div>
            </div>
            <p class="module-desc" style="color:#00d4ff;font-weight:600;">🔽 点击任意部门行 → 查看该部门销售员明细</p>
            <table class="dept-table"><thead><tr><th>部门</th><th>26Q2业绩(万)</th><th>Q2目标(万)</th><th>目标完成率</th><th>25Q2同期(万)</th><th>同比%</th><th>销售员数</th><th>状态</th></tr></thead><tbody>{perf_rows}</tbody><tfoot>{perf_foot}</tfoot></table>
        </div>
    </div>
    <div id="tab-debt" class="tab-content">
        <div class="module">
            <h2 class="module-title">💳 欠款分析总览</h2>
            <div class="kpi-grid" style="margin-bottom:25px;">
                <div class="kpi-card"><div class="kpi-icon">📋</div><h3>欠款总额</h3><div class="value negative">{debt_total:.2f}<span style="font-size:0.5em;">万</span></div><div class="sub">全大区逾期欠款合计</div></div>
                <div class="kpi-card"><div class="kpi-icon">🟢</div><h3>30天内</h3><div class="value highlight">{d30_total:.2f}<span style="font-size:0.5em;">万</span></div><div class="sub">占比 {d30_total/debt_total*100:.1f}%</div></div>
                <div class="kpi-card"><div class="kpi-icon">🟡</div><h3>30-90天</h3><div class="value warning">{d30_90_total:.2f}<span style="font-size:0.5em;">万</span></div><div class="sub">占比 {d30_90_total/debt_total*100:.1f}%</div></div>
                <div class="kpi-card"><div class="kpi-icon">🔴</div><h3>90天以上</h3><div class="value negative">{d90_total:.2f}<span style="font-size:0.5em;">万</span></div><div class="sub">90-180天：{d90_180_total:.2f}万 | 180天+：{d180_total:.2f}万</div></div>
            </div>
            <div class="charts-section">
                <div class="chart-box"><h3>逾期欠款金额占比分布</h3><div class="chart-container"><canvas id="debtPieChart"></canvas></div></div>
                <div class="chart-box"><h3>各部门欠款总额排名（万元）</h3><div class="chart-container"><canvas id="debtBarChart"></canvas></div></div>
            </div>
            <h3 style="color:#00d4ff;margin-bottom:15px;font-size:1.1em;">各部门分账龄欠款明细 <span style="color:#8892b0;font-size:0.8em;font-weight:normal;">（点击部门查看销售员明细）</span></h3>
            <table class="dept-table"><thead><tr><th>部门（点击查看明细）</th><th>30天内(万)</th><th>30-90天(万)</th><th>90-180天(万)</th><th>180天以上(万)</th><th>合计(万)</th><th>状态</th></tr></thead><tbody id="debtTableBody">{debt_rows}</tbody><tfoot id="debtTableFoot">{debt_foot}</tfoot></table>
            <h3 style="color:#ff4757;margin:25px 0 15px;font-size:1.1em;">🚨 高风险客户（90天以上欠款，前15名）</h3>
            <table class="dept-table"><thead><tr><th>排名</th><th>客户名称（所属部门）</th><th>欠款金额(万)</th><th>风险等级</th></tr></thead><tbody>{risk_rows}</tbody></table>
        </div>
    </div>
    <div id="tab-collection" class="tab-content">
        <div class="module">
            <h2 class="module-title">⏱️ 平均回款周期分析</h2>
            <div class="kpi-grid" style="margin-bottom:25px;">
                <div class="kpi-card"><div class="kpi-icon">📊</div><h3>全大区平均回款周期</h3><div class="value warning">{avg_cycle:.1f}</div><div class="sub">天（欠款+回款加权综合）</div></div>
                <div class="kpi-card"><div class="kpi-icon">🔴</div><h3>最长部门回款周期</h3><div class="value negative">{max_cycle:.1f}</div><div class="sub">{max_dept}</div></div>
                <div class="kpi-card"><div class="kpi-icon">🟢</div><h3>最短部门回款周期</h3><div class="value highlight">{min_cycle:.1f}</div><div class="sub">{min_dept}</div></div>
                <div class="kpi-card" onclick="showOver90Depts()" style="cursor:pointer;" title="点击查看回款周期大于90天的部门"><div class="kpi-icon">⚠️</div><h3>超90天部门数</h3><div class="value negative">{over90_count}</div><div class="sub">回款周期大于90天的部门（点击查看）</div></div>
            </div>
            <div style="background:rgba(255, 255, 255, 0.03);border-radius:12px;padding:15px 20px;margin-bottom:20px;border:1px solid rgba(255, 255, 255, 0.08);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="font-weight:600;color:#00d4ff;">部门平均回款周期（天）</span><span style="color:#8892b0;font-size:0.9em;">| 回款周期计算 =（欠款加权天数 + 回款加权天数）÷（欠款总额 + 认款协同金额）</span></div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;">
                    <div style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:50%;background:#00ff88;display:inline-block;"></span><span style="color:#ccd6f6;font-size:0.9em;">≤60天（良好）</span></div>
                    <div style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:50%;background:#ffa502;display:inline-block;"></span><span style="color:#ccd6f6;font-size:0.9em;">61-90天（一般）</span></div>
                    <div style="display:flex;align-items:center;gap:6px;"><span style="width:10px;height:10px;border-radius:50%;background:#ff4757;display:inline-block;"></span><span style="color:#ccd6f6;font-size:0.9em;">&gt;90天（需关注）</span></div>
                </div>
            </div>
            <div class="chart-box" style="margin-bottom:25px;"><h3>📊 部门平均回款周期排名</h3><div class="chart-container" style="height:380px;"><canvas id="cycleChart"></canvas></div></div>
            <table class="dept-table"><thead><tr><th>部门（点击查看明细）</th><th>欠款总额(万)</th><th>回款金额(万)</th><th>回款周期(天)</th><th>状态</th></tr></thead><tbody id="cycleTableBody">{cycle_rows}</tbody><tfoot id="cycleTableFoot">{cycle_foot}</tfoot></table>
        </div>
    </div>
</div>
<div class="modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()"><div class="modal"><div class="modal-header"><div class="modal-title" id="modalTitle">部门详情</div><button class="modal-close" onclick="closeModal()">✕</button></div><div id="modalContent"></div></div></div>
<div class="modal-overlay" id="salesModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0, 0, 0, 0.8);z-index:1001;align-items:center;justify-content:center;">
    <div style="background:#1a2040;border-radius:20px;padding:30px;max-width:1100px;width:95%;max-height:85vh;overflow-y:auto;border:1px solid rgba(0,212,255,0.3);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;"><div class="modal-title" id="salesModalTitle">销售员明细</div><button class="modal-close" onclick="closeSalesModal()">✕</button></div>
        <div id="salesTableContainer"></div>
    </div>
</div>
<script>
const deptData = [
    {dept_js_str}
];
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
let salesDetailData = {sales_js_str};
let salesCycleData = {json.dumps(sales_cycle_data, ensure_ascii=False)};
let custCycleData = {json.dumps(cust_cycle_data, ensure_ascii=False)};
let deptCustDebtData = {json.dumps(debt_drill, ensure_ascii=False)};
let deptCustPerfData = {json.dumps(perf_drill, ensure_ascii=False)};

function showDeptDetail(dept) {{
    const d = deptData.find(x => x.dept === dept);
    if (!d) return;
    document.getElementById('modalTitle').textContent = dept + ' — 部门概览';
    const risky = d.d90_180 + d.d180;
    document.getElementById('modalContent').innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
            <div style="background:rgba(0,212,255,0.1);border-radius:12px;padding:14px;text-align:center;"><div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">26Q2业绩</div><div style="color:#00ff88;font-size:1.5em;font-weight:700;">${{d.v26}}万</div></div>
            <div style="background:rgba(0,212,255,0.1);border-radius:12px;padding:14px;text-align:center;"><div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">完成率</div><div style="color:#ffa502;font-size:1.5em;font-weight:700;">${{d.completion}}%</div></div>
            <div style="background:rgba(255,71,87,0.1);border-radius:12px;padding:14px;text-align:center;"><div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">同比25Q2</div><div style="color:#ff4757;font-size:1.5em;font-weight:700;">${{d.yoy}}%</div></div>
            <div style="background:rgba(0,212,255,0.1);border-radius:12px;padding:14px;text-align:center;"><div style="color:#8892b0;font-size:0.8em;margin-bottom:4px;">欠款总额</div><div style="color:#ff4757;font-size:1.5em;font-weight:700;">${{d.total_debt}}万</div></div>
        </div>
        <div style="text-align:center;margin-top:10px;"><button onclick="showSalesDetail('${{dept}}', getCurrentTab())" style="background:linear-gradient(135deg,#00d4ff,#7b2ff7);color:#fff;border:none;border-radius:8px;padding:10px 28px;font-size:1em;cursor:pointer;">📋 查看销售员明细</button></div>`;
    document.getElementById('modalOverlay').classList.add('active');
}}
function closeModal() {{ document.getElementById('modalOverlay').classList.remove('active'); }}
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
        const hasCust = deptCustPerfData[dept] && deptCustPerfData[dept].find(x => x.name === s.name);
        const nameStyle = hasCust ? 'color:#00d4ff;cursor:pointer;text-decoration:underline;' : 'color:#ccd6f6;';
        const nameClick = hasCust ? `onclick="renderCustPerf('${{dept}}','${{s.name}}')"` : '';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:7px 5px;${{nameStyle}}" ${{nameClick}}>${{s.name}}${{hasCust ? ' 📂' : ''}}</td><td style="padding:7px 5px;color:${{color}};text-align:right;font-weight:600;">${{s.perf.toFixed(2)}}</td><td style="padding:7px 5px;color:#00ff88;text-align:right;">${{s.collect.toFixed(2)}}</td><td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{status}}</td></tr>`;
    }}).join('');
    const tp = list.reduce((s, v) => s + v.perf, 0).toFixed(2);
    const tc = list.reduce((s, v) => s + v.collect, 0).toFixed(2);
    document.getElementById('salesModalTitle').innerHTML = `📊 ${{dept}} - 销售员业绩明细 <span style="font-size:0.7em;color:#8892b0;">（点击销售员名查看客户明细）</span>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.85em;"><thead><tr style="background:rgba(0,212,255,0.12);"><th style="padding:8px 6px;color:#00d4ff;">销售员</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">26Q2业绩(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th></tr></thead><tbody>${{rows}}<tr style="background:rgba(0,212,255,0.08);font-weight:600;"><td style="padding:8px 6px;color:#00d4ff;">合计（${{list.length}}人）</td><td style="padding:8px 6px;color:#00ff88;text-align:right;">${{tp}}</td><td style="padding:8px 6px;color:#00ff88;text-align:right;">${{tc}}</td><td></td></tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}}
function renderSalesDebt(dept) {{
    const list = [...(salesDetailData[dept] || [])];
    list.sort((a, b) => b.total_debt - a.total_debt);
    const rows = list.map(s => {{
        const dc = s.total_debt > 50 ? '#ff4757' : s.total_debt > 20 ? '#ffa502' : '#00ff88';
        const status = s.total_debt > 50 ? '🔴 高风险' : s.total_debt > 20 ? '🟡 关注' : '🟢 较好';
        const hasCust = deptCustDebtData[dept] && deptCustDebtData[dept].find(x => x.name === s.name);
        const nameStyle = hasCust ? 'color:#00d4ff;cursor:pointer;text-decoration:underline;' : 'color:#ccd6f6;';
        const nameClick = hasCust ? `onclick="renderCustDebt('${{dept}}','${{s.name}}')"` : '';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:7px 5px;${{nameStyle}}" ${{nameClick}}>${{s.name}}${{hasCust ? ' 📂' : ''}}</td><td style="padding:7px 5px;color:${{dc}};text-align:right;font-weight:600;">${{s.total_debt.toFixed(2)}}</td><td style="padding:7px 5px;color:#00ff88;text-align:right;">${{s.d30.toFixed(2)}}</td><td style="padding:7px 5px;color:#ffa502;text-align:right;">${{s.d30_90.toFixed(2)}}</td><td style="padding:7px 5px;color:${{s.d90_180>0?'#ff4757':'#8892b0'}};text-align:right;">${{s.d90_180.toFixed(2)}}</td><td style="padding:7px 5px;color:${{s.d180>0?'#ff4757':'#8892b0'}};text-align:right;">${{s.d180.toFixed(2)}}</td><td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{status}}</td></tr>`;
    }}).join('');
    const td = list.reduce((s, v) => s + v.total_debt, 0).toFixed(2);
    document.getElementById('salesModalTitle').innerHTML = `💰 ${{dept}} - 销售员欠款明细 <span style="font-size:0.7em;color:#8892b0;">（点击销售员名查看客户明细）</span>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.82em;"><thead><tr style="background:rgba(0,212,255,0.12);"><th style="padding:8px 6px;color:#00d4ff;">销售员</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">合计欠款(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">30天内</th><th style="padding:8px 6px;color:#ffa502;text-align:right;">30-90天</th><th style="padding:8px 6px;color:#ff4757;text-align:right;">90-180天</th><th style="padding:8px 6px;color:#ff4757;text-align:right;">180天以上</th><th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th></tr></thead><tbody>${{rows}}<tr style="background:rgba(0,212,255,0.08);font-weight:600;"><td style="padding:8px 6px;color:#00d4ff;">合计（${{list.length}}人）</td><td style="padding:8px 6px;color:#ff4757;text-align:right;">${{td}}</td><td colspan="4"></td><td></td></tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}}
function renderSalesCycle(dept) {{
    const list = [...(salesCycleData[dept] || [])];
    list.sort((a, b) => b.cycle - a.cycle);
    const rows = list.map(s => {{
        const cycle = s.cycle;
        const cycleStr = cycle > 0 ? cycle.toFixed(1) : '-';
        const cc = cycle <= 0 ? '#8892b0' : cycle > 90 ? '#ff4757' : cycle > 60 ? '#ffa502' : '#00ff88';
        const status = cycle <= 0 ? '⚪ 无数据' : cycle > 90 ? '🔴 需关注' : cycle > 60 ? '🟡 偏高' : '🟢 正常';
        const hasCust = custCycleData[dept] && custCycleData[dept][s.name];
        const nameStyle = hasCust ? 'color:#00d4ff;cursor:pointer;text-decoration:underline;' : 'color:#ccd6f6;';
        const nameClick = hasCust ? `onclick="renderCustCycle('${{dept}}','${{s.name}}')"` : '';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:7px 5px;${{nameStyle}}" ${{nameClick}}>${{s.name}}${{hasCust ? ' 📂' : ''}}</td><td style="padding:7px 5px;color:#00ff88;text-align:right;">${{(s.rec_amt/10000).toFixed(2)}}</td><td style="padding:7px 5px;color:#ffa502;text-align:right;">${{(s.debt_amt/10000).toFixed(2)}}</td><td style="padding:7px 5px;color:${{cc}};text-align:right;font-weight:600;">${{cycleStr}}</td><td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{status}}</td></tr>`;
    }}).join('');
    const tc = list.reduce((s, v) => s + v.rec_amt, 0);
    const td = list.reduce((s, v) => s + v.debt_amt, 0);
    document.getElementById('salesModalTitle').innerHTML = `⏱️ ${{dept}} - 销售员回款周期明细 <span style="font-size:0.7em;color:#8892b0;">(点击销售员名查看客户明细)</span>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.85em;"><thead><tr style="background:rgba(0,212,255,0.12);"><th style="padding:8px 6px;color:#00d4ff;">销售员</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">认款金额(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">欠款金额(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款周期(天)</th><th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th></tr></thead><tbody>${{rows}}<tr style="background:rgba(0,212,255,0.08);font-weight:600;"><td style="padding:8px 6px;color:#00d4ff;">合计（${{list.length}}人）</td><td style="padding:8px 6px;color:#00ff88;text-align:right;">${{(tc/10000).toFixed(2)}}</td><td style="padding:8px 6px;color:#ffa502;text-align:right;">${{(td/10000).toFixed(2)}}</td><td colspan="2"></td></tr></tbody></table>`;
    document.getElementById('salesModal').style.display = 'flex';
}}
function renderCustCycle(dept, salesName) {{
    window._salesCycleBack = document.getElementById('salesTableContainer').innerHTML;
    window._salesCycleTitle = document.getElementById('salesModalTitle').innerHTML;
    const custList = custCycleData[dept] && custCycleData[dept][salesName] ? custCycleData[dept][salesName] : [];
    if (!custList.length) return;
    const rows = custList.map(c => {{
        const cycle = c.cycle;
        const cycleStr = cycle > 0 ? cycle.toFixed(1) : '-';
        const cc = cycle <= 0 ? '#8892b0' : cycle > 90 ? '#ff4757' : cycle > 60 ? '#ffa502' : '#00ff88';
        const status = cycle <= 0 ? '⚪ 无数据' : cycle > 90 ? '🔴 需关注' : cycle > 60 ? '🟡 偏高' : '🟢 正常';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:7px 5px;color:#ccd6f6;max-width:300px;word-break:break-all;">${{c.name}}</td><td style="padding:7px 5px;color:#00ff88;text-align:right;">${{(c.rec_amt/10000).toFixed(2)}}</td><td style="padding:7px 5px;color:#ffa502;text-align:right;">${{(c.debt_amt/10000).toFixed(2)}}</td><td style="padding:7px 5px;color:${{cc}};text-align:right;font-weight:600;">${{cycleStr}}</td><td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{status}}</td></tr>`;
    }}).join('');
    const tc = custList.reduce((s, c) => s + c.rec_amt, 0);
    const td = custList.reduce((s, c) => s + c.debt_amt, 0);
    document.getElementById('salesModalTitle').innerHTML = `⏱️ ${{salesName}} - 客户回款周期明细 <span style="font-size:0.75em;color:#8892b0;">(${{dept}})</span> <button onclick="backToSalesCycle()" style="margin-left:12px;background:rgba(0,212,255,0.2);border:1px solid rgba(0,212,255,0.4);color:#00d4ff;border-radius:6px;padding:3px 12px;font-size:0.85em;cursor:pointer;">← 返回销售员</button>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.8em;"><thead><tr style="background:rgba(0,212,255,0.12);"><th style="padding:8px 6px;color:#00d4ff;text-align:left;">客户名称</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">认款金额(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">欠款金额(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款周期(天)</th><th style="padding:8px 6px;color:#00d4ff;text-align:center;">状态</th></tr></thead><tbody>${{rows}}<tr style="background:rgba(0,212,255,0.08);font-weight:600;"><td style="padding:8px 6px;color:#00d4ff;">合计（${{custList.length}}个客户）</td><td style="padding:8px 6px;color:#00ff88;text-align:right;">${{(tc/10000).toFixed(2)}}</td><td style="padding:8px 6px;color:#ffa502;text-align:right;">${{(td/10000).toFixed(2)}}</td><td colspan="2"></td></tr></tbody></table>`;
}}
function backToSalesCycle() {{ if (window._salesCycleBack) {{ document.getElementById('salesTableContainer').innerHTML = window._salesCycleBack; document.getElementById('salesModalTitle').innerHTML = window._salesCycleTitle; window._salesCycleBack = null; }} }}
function renderCustDebt(dept, salesName) {{
    window._salesDebtBack = document.getElementById('salesTableContainer').innerHTML;
    window._salesDebtTitle = document.getElementById('salesModalTitle').innerHTML;
    const salesList = deptCustDebtData[dept] || [];
    const sales = salesList.find(s => s.name === salesName);
    const custs = sales ? (sales.custs || []) : [];
    if (!custs.length) return;
    const rows = custs.map(c => {{
        const total_yuan = (c.total * 10000).toLocaleString('zh-CN', {{minimumFractionDigits:2, maximumFractionDigits:2}});
        const d30_yuan = (c.d30 * 10000).toLocaleString('zh-CN', {{minimumFractionDigits:2, maximumFractionDigits:2}});
        const d30_90_yuan = (c.d30_90 * 10000).toLocaleString('zh-CN', {{minimumFractionDigits:2, maximumFractionDigits:2}});
        const d90_180_yuan = (c.d90_180 * 10000).toLocaleString('zh-CN', {{minimumFractionDigits:2, maximumFractionDigits:2}});
        const d180_yuan = (c.d180 * 10000).toLocaleString('zh-CN', {{minimumFractionDigits:2, maximumFractionDigits:2}});
        const statusColor = c.max_days <= 30 ? '#00ff88' : c.max_days <= 90 ? '#ffa502' : c.max_days <= 180 ? '#ff6b6b' : '#ff4757';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:7px 5px;color:#ccd6f6;max-width:280px;word-break:break-all;">${{c.name}}</td><td style="padding:7px 5px;color:#00ff88;text-align:right;">${{d30_yuan}}</td><td style="padding:7px 5px;color:#ffa502;text-align:right;">${{d30_90_yuan}}</td><td style="padding:7px 5px;color:${{c.d90_180>0?'#ff4757':'#8892b0'}};text-align:right;">${{d90_180_yuan}}</td><td style="padding:7px 5px;color:${{c.d180>0?'#ff4757':'#8892b0'}};text-align:right;">${{d180_yuan}}</td><td style="padding:7px 5px;color:#fff;text-align:right;font-weight:600;">${{total_yuan}}</td><td style="padding:7px 5px;color:${{statusColor}};text-align:center;font-weight:600;">${{c.max_days}}天</td></tr>`;
    }}).join('');
    const tc = custs.reduce((s, c) => s + c.total, 0);
    const tc_yuan = (tc * 10000).toLocaleString('zh-CN', {{minimumFractionDigits:2, maximumFractionDigits:2}});
    document.getElementById('salesModalTitle').innerHTML = `💰 ${{salesName}} - 客户欠款明细 <span style="font-size:0.75em;color:#8892b0;">（${{dept}}）</span> <button onclick="backToSalesDebt()" style="margin-left:12px;background:rgba(0,212,255,0.2);border:1px solid rgba(0,212,255,0.4);color:#00d4ff;border-radius:6px;padding:3px 12px;font-size:0.85em;cursor:pointer;">← 返回销售员</button>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.8em;"><thead><tr style="background:rgba(0,212,255,0.12);"><th style="padding:8px 6px;color:#00d4ff;text-align:left;">客户名称</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">30天内(元)</th><th style="padding:8px 6px;color:#ffa502;text-align:right;">30-90天(元)</th><th style="padding:8px 6px;color:#ff4757;text-align:right;">90-180天(元)</th><th style="padding:8px 6px;color:#ff4757;text-align:right;">180天+(元)</th><th style="padding:8px 6px;color:#fff;text-align:right;">合计(元)</th><th style="padding:8px 6px;color:#00d4ff;text-align:center;">最长账龄</th></tr></thead><tbody>${{rows}}<tr style="background:rgba(0,212,255,0.08);font-weight:600;"><td style="padding:8px 6px;color:#00d4ff;">合计（${{custs.length}}个客户）</td><td colspan="4"></td><td style="padding:8px 6px;color:#fff;text-align:right;">${{tc_yuan}}</td><td></td></tr></tbody></table>`;
}}
function backToSalesDebt() {{ if (window._salesDebtBack) {{ document.getElementById('salesTableContainer').innerHTML = window._salesDebtBack; document.getElementById('salesModalTitle').innerHTML = window._salesDebtTitle; window._salesDebtBack = null; }} }}
function renderCustPerf(dept, salesName) {{
    window._salesPerfBack = document.getElementById('salesTableContainer').innerHTML;
    window._salesPerfTitle = document.getElementById('salesModalTitle').innerHTML;
    const salesList = deptCustPerfData[dept] || [];
    const sales = salesList.find(s => s.name === salesName);
    const custs = sales ? (sales.custs || []) : [];
    if (!custs.length) return;
    const rows = custs.map(c => {{
        const color = c.perf < 0 ? '#ff4757' : c.perf < 1 ? '#ffa502' : '#00ff88';
        return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:7px 5px;color:#ccd6f6;max-width:280px;word-break:break-all;">${{c.name}}</td><td style="padding:7px 5px;color:${{color}};text-align:right;font-weight:600;">${{c.perf.toFixed(2)}}</td><td style="padding:7px 5px;color:#00ff88;text-align:right;">${{c.collect.toFixed(2)}}</td><td style="padding:7px 5px;color:#ccd6f6;text-align:center;">${{c.orders}}</td></tr>`;
    }}).join('');
    const tp = custs.reduce((s, c) => s + c.perf, 0).toFixed(2);
    const tc = custs.reduce((s, c) => s + c.collect, 0).toFixed(2);
    document.getElementById('salesModalTitle').innerHTML = `📊 ${{salesName}} - 客户业绩明细 <span style="font-size:0.75em;color:#8892b0;">（${{dept}}）</span> <button onclick="backToSalesPerf()" style="margin-left:12px;background:rgba(0,212,255,0.2);border:1px solid rgba(0,212,255,0.4);color:#00d4ff;border-radius:6px;padding:3px 12px;font-size:0.85em;cursor:pointer;">← 返回销售员</button>`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.8em;"><thead><tr style="background:rgba(0,212,255,0.12);"><th style="padding:8px 6px;color:#00d4ff;text-align:left;">客户名称</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">业绩(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:right;">回款(万)</th><th style="padding:8px 6px;color:#00d4ff;text-align:center;">订单数</th></tr></thead><tbody>${{rows}}<tr style="background:rgba(0,212,255,0.08);font-weight:600;"><td style="padding:8px 6px;color:#00d4ff;">合计（${{custs.length}}个客户）</td><td style="padding:8px 6px;color:#00ff88;text-align:right;">${{tp}}</td><td style="padding:8px 6px;color:#00ff88;text-align:right;">${{tc}}</td><td></td></tr></tbody></table>`;
}}
function backToSalesPerf() {{ if (window._salesPerfBack) {{ document.getElementById('salesTableContainer').innerHTML = window._salesPerfBack; document.getElementById('salesModalTitle').innerHTML = window._salesPerfTitle; window._salesPerfBack = null; }} }}
function closeSalesModal() {{ document.getElementById('salesModal').style.display = 'none'; window._salesDebtBack = null; window._salesPerfBack = null; window._salesCycleBack = null; }}
function showOver90Depts() {{
    const over90 = deptData.filter(d => d.cycle > 90).sort((a, b) => b.cycle - a.cycle);
    const rows = over90.map(d => {{ const risky = d.d90_180 + d.d180; return `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);cursor:pointer;" onclick="showSalesDetail('${{d.dept}}','cycle')"><td style="padding:10px 8px;color:#ccd6f6;font-weight:600;">🏢 ${{d.dept}}</td><td style="padding:10px 8px;color:#ff4757;text-align:right;font-weight:700;">${{d.cycle.toFixed(1)}}天</td><td style="padding:10px 8px;color:#ff4757;text-align:right;">${{d.total_debt.toFixed(2)}}万</td><td style="padding:10px 8px;color:#ffa502;text-align:right;">${{risky.toFixed(2)}}万</td><td style="padding:10px 8px;text-align:center;"><span class="status-badge badge-down">需关注</span></td></tr>`; }}).join('');
    const totalDebt = over90.reduce((s, d) => s + d.total_debt, 0);
    const totalRisky = over90.reduce((s, d) => s + d.d90_180 + d.d180, 0);
    const avgCycle = over90.length > 0 ? over90.reduce((s, d) => s + d.cycle, 0) / over90.length : 0;
    document.getElementById('salesModalTitle').textContent = `⚠️ 回款周期超90天部门（共${{over90.length}}个）`;
    document.getElementById('salesTableContainer').innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:0.9em;"><thead><tr style="background:rgba(255,71,87,0.15);"><th style="padding:10px 8px;color:#ff4757;text-align:left;">部门（点击下钻）</th><th style="padding:10px 8px;color:#ff4757;text-align:right;">回款周期</th><th style="padding:10px 8px;color:#ff4757;text-align:right;">欠款总额</th><th style="padding:10px 8px;color:#ff4757;text-align:right;">高风险欠款(90天+)</th><th style="padding:10px 8px;color:#ff4757;text-align:center;">状态</th></tr></thead><tbody>${{rows}}</tbody><tfoot><tr style="background:rgba(255,71,87,0.08);font-weight:600;"><td style="padding:10px 8px;color:#ff4757;">合计（${{over90.length}}个部门）</td><td style="padding:10px 8px;color:#ff4757;text-align:right;">平均 ${{avgCycle.toFixed(1)}}天</td><td style="padding:10px 8px;color:#ff4757;text-align:right;">${{totalDebt.toFixed(2)}}万</td><td style="padding:10px 8px;color:#ff4757;text-align:right;">${{totalRisky.toFixed(2)}}万</td><td></td></tr></tfoot></table><div style="margin-top:15px;color:#8892b0;font-size:0.85em;text-align:center;">💡 点击部门名称可查看该部门销售员回款周期明细</div>`;
    document.getElementById('salesModal').style.display = 'flex';
}}
function renderCycleTable() {{
    const tbody = document.getElementById('cycleTableBody');
    if (!tbody) return;
    const sorted = [...deptData].filter(d => d.cycle > 0).sort((a, b) => b.cycle - a.cycle);
    tbody.innerHTML = sorted.map(d => {{
        const sc = d.cycle > 90 ? 'negative' : d.cycle > 60 ? 'warning' : 'highlight';
        const badge = d.cycle > 90 ? 'badge-down' : d.cycle > 60 ? 'badge-warning' : 'badge-good';
        const label = d.cycle > 90 ? '需关注' : d.cycle > 60 ? '一般' : '良好';
        return `<tr onclick="showSalesDetail('${{d.dept}}','cycle')" style="cursor:pointer;"><td>🏢 ${{d.dept}}</td><td>${{d.total_debt.toFixed(2)}}</td><td>${{d.collect.toFixed(2)}}</td><td class="${{sc}}">${{d.cycle.toFixed(1)}}</td><td><span class="status-badge ${{badge}}">${{label}}</span></td></tr>`;
    }}).join('');
}}
Chart.register(ChartDataLabels);
function initCharts() {{
    const depts = deptData.map(d => d.dept);
    const v26 = deptData.map(d => d.v26);
    const v25 = deptData.map(d => d.v25);
    const COLORS = ['#00d4ff','#7b2ff7','#00ff88','#ffa502','#ff6b9d','#4ecdc4','#45b7d1','#f7dc6f','#82e0aa'];
    new Chart(document.getElementById('perfBarChart'), {{
        type: 'bar',
        data: {{ labels: depts, datasets: [{{ label: '25Q2(万)', data: v25, backgroundColor: 'rgba(0,212,255,0.5)', borderColor: '#00d4ff', borderWidth: 1 }}, {{ label: '26Q2(万)', data: v26, backgroundColor: 'rgba(123,47,247,0.7)', borderColor: '#7b2ff7', borderWidth: 1 }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#ccd6f6' }} }}, datalabels: {{ display: false }} }}, scales: {{ x: {{ ticks: {{ color: '#8892b0', maxRotation: 30, font: {{ size: 10 }} }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, y: {{ ticks: {{ color: '#8892b0' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }} }} }}
    }});
    new Chart(document.getElementById('perfPieChart'), {{
        type: 'doughnut',
        data: {{ labels: depts, datasets: [{{ data: v26, backgroundColor: COLORS, borderColor: '#0a0e27', borderWidth: 2 }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#ccd6f6', font: {{ size: 11 }}, padding: 10 }} }}, datalabels: {{ color: '#fff', font: {{ size: 10, weight: 'bold' }}, formatter: (val, ctx) => {{ const total = ctx.dataset.data.reduce((a, b) => a + b, 0); const pct = (val / total * 100).toFixed(1); return pct > 3 ? pct + '%' : ''; }} }} }} }}
    }});
    const cycleItems = deptData.filter(d => d.cycle > 0).sort((a, b) => b.cycle - a.cycle);
    const cycleColors = cycleItems.map(d => d.cycle > 90 ? '#ff4757' : d.cycle > 60 ? '#ffa502' : '#00ff88');
    new Chart(document.getElementById('cycleChart'), {{
        type: 'bar',
        data: {{ labels: cycleItems.map(d => d.dept), datasets: [{{ label: '回款周期(天)', data: cycleItems.map(d => d.cycle), backgroundColor: cycleColors, borderRadius: 6 }}] }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }}, datalabels: {{ color: '#fff', anchor: 'end', align: 'right', font: {{ size: 12, weight: 'bold' }}, formatter: val => val + '天' }} }}, scales: {{ x: {{ ticks: {{ color: '#8892b0' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }}, max: 150 }}, y: {{ ticks: {{ color: '#ccd6f6', font: {{ size: 12 }} }}, grid: {{ display: false }} }} }} }}
    }});
    new Chart(document.getElementById('debtPieChart'), {{
        type: 'doughnut',
        data: {{ labels: ['30天内', '30-90天', '90-180天', '180天以上'], datasets: [{{ data: {debt_pie_data}, backgroundColor: ['#00ff88', '#ffa502', '#ff6b6b', '#ff4757'], borderColor: '#0a0e27', borderWidth: 3 }}] }},
        options: {{ responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#ccd6f6', padding: 15 }} }}, datalabels: {{ color: '#fff', font: {{ size: 11, weight: 'bold' }}, formatter: (val, ctx) => {{ const total = ctx.dataset.data.reduce((a, b) => a + b, 0); const pct = (val / total * 100).toFixed(1); return pct + '%'; }} }} }} }}
    }});
    const debtSorted = [...deptData].sort((a, b) => b.total_debt - a.total_debt);
    new Chart(document.getElementById('debtBarChart'), {{
        type: 'bar',
        data: {{ labels: debtSorted.map(d => d.dept), datasets: [{{ label: '欠款(万)', data: debtSorted.map(d => d.total_debt), backgroundColor: 'rgba(255,71,87,0.7)', borderColor: '#ff4757', borderWidth: 1, borderRadius: 4 }}] }},
        options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }}, datalabels: {{ color: '#fff', anchor: 'end', align: 'right', font: {{ size: 11, weight: 'bold' }}, formatter: val => val.toFixed(1) }} }}, scales: {{ x: {{ ticks: {{ color: '#8892b0' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}, y: {{ ticks: {{ color: '#ccd6f6', font: {{ size: 11 }} }}, grid: {{ display: false }} }} }} }}
    }});
}}
window.addEventListener('load', initCharts);
window.addEventListener('load', function() {{ renderCycleTable(); }});
</script>
</body>
</html>'''

with open(HTML_OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n[OK] HTML看板已生成: {HTML_OUT}")
print(f"  HTML大小: {len(html)} chars")
print(f"\n🎉 26财年Q2数据看板生成完成！")
