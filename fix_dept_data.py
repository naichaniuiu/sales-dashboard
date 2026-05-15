import json, re

path = 'C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 正确的部门数据（从欠款数据表汇总）
dept_corrections = {
    '武汉基建制造行业组':   {'d30': 244.59, 'd30_90': 55.49,  'd90_180': 39.32, 'd180': 1.49,  'total_debt': 340.89},
    '成都站':              {'d30': 98.75,  'd30_90': 30.72,  'd90_180': 103.56, 'd180': 12.28, 'total_debt': 245.31},
    '西安站':              {'d30': 77.54,  'd30_90': 52.37,  'd90_180': 76.47,  'd180': 8.22,  'total_debt': 214.60},
    '长沙站':              {'d30': 43.52,  'd30_90': 16.10,  'd90_180': 5.95,   'd180': 0.00,  'total_debt': 65.57},
    '武汉能源交通行业组':   {'d30': 53.20,  'd30_90': 13.93,  'd90_180': 80.37,  'd180': 0.07,  'total_debt': 147.57},
    '重庆站':              {'d30': 35.88,  'd30_90': 13.94,  'd90_180': 51.98,  'd180': 11.49, 'total_debt': 113.29},
    '郑州站':              {'d30': 25.61,  'd30_90': 47.26,  'd90_180': 78.86,  'd180': 2.31,  'total_debt': 154.04},
    '武汉金融行业组':       {'d30': 20.34,  'd30_90': 52.59,  'd90_180': 122.35, 'd180': 58.33, 'total_debt': 253.61},
    '其他':                {'d30': 16.13,  'd30_90': 3.42,   'd90_180': 2.92,   'd180': 0.00,  'total_debt': 22.47},
}

# 替换 deptData 数组中的各行
for dept, vals in dept_corrections.items():
    # 匹配形如 {dept:'xxx', ... total_debt:旧值, ...}
    pattern = r"(dept:'" + dept + r"',[^}]*?d30:[^,]+?,[^}]*?d180:[^,]+?,)total_debt:\d+\.\d+([^}]*?\})"
    replacement = r"\1total_debt:" + str(vals['total_debt']) + r"\2"
    new_content, n = re.subn(pattern, replacement, content)
    if n > 0:
        content = new_content
        print(f"Updated total_debt for {dept}")
    else:
        print(f"WARNING: total_debt NOT found for {dept}")

# 替换 d30_90, d90_180, d180, d30
for dept, vals in dept_corrections.items():
    # 更新 d30
    content, n = re.subn(
        r"(dept:'" + dept + r"',[^}]*?)d30:\d+\.\d+",
        lambda m: m.group(1) + f"d30:{vals['d30']}",
        content
    )
    # 更新 d30_90
    content, n2 = re.subn(
        r"(dept:'" + dept + r"',[^}]*?d30:[^,]+?,[^}]*?)d30_90:\d+\.\d+",
        lambda m: m.group(1) + f"d30_90:{vals['d30_90']}",
        content
    )
    # 更新 d90_180
    content, n3 = re.subn(
        r"(dept:'" + dept + r"',[^}]*?d30_90:[^,]+?,[^}]*?)d90_180:\d+\.\d+",
        lambda m: m.group(1) + f"d90_180:{vals['d90_180']}",
        content
    )
    # 更新 d180
    content, n4 = re.subn(
        r"(dept:'" + dept + r"',[^}]*?d90_180:[^,]+?,[^}]*?)d180:\d+\.\d+",
        lambda m: m.group(1) + f"d180:{vals['d180']}",
        content
    )
    print(f"{dept}: d30={n}, d30_90={n2}, d90_180={n3}, d180={n4}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
