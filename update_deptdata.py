import re

path = 'C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 正确的部门欠款数据（包含离职人员，与欠款表一致）
corrections = {
    '武汉基建制造行业组': {'d30': 232.60, 'd30_90': 56.12, 'd90_180': 39.31, 'd180': 1.49, 'total_debt': 329.52},
    '成都站':              {'d30': 98.68,  'd30_90': -33.70, 'd90_180': 102.95, 'd180': 28.16, 'total_debt': 196.09},
    '西安站':              {'d30': 76.40,  'd30_90': 75.03,  'd90_180': 172.35, 'd180': 15.86, 'total_debt': 339.64},
    '长沙站':              {'d30': 43.23,  'd30_90': 16.10,  'd90_180': 5.95,   'd180': 1.13,  'total_debt': 66.41},
    '武汉能源交通行业组':   {'d30': 52.86,  'd30_90': 13.88,  'd90_180': 80.51,  'd180': 0.07,  'total_debt': 147.32},
    '重庆站':              {'d30': 35.76,  'd30_90': 13.94,  'd90_180': 51.98,  'd180': 11.75, 'total_debt': 113.43},
    '郑州站':              {'d30': 25.20,  'd30_90': 49.79,  'd90_180': 79.18,  'd180': 1.68,  'total_debt': 155.85},
    '武汉金融行业组':       {'d30': 19.09,  'd30_90': 51.30,  'd90_180': 122.13, 'd180': 58.08, 'total_debt': 250.60},
    '其他':                {'d30': 16.58,  'd30_90': 3.42,   'd90_180': 2.51,   'd180': 0.30,  'total_debt': 22.81},
}

for dept, vals in corrections.items():
    # 构建正则：匹配该部门行中的各字段
    # dept:'xxx', ... d30:旧值, d30_90:旧值, d90_180:旧值, d180:旧值, total_debt:旧值
    pattern = (
        r"(dept:'" + re.escape(dept) + r"',[^}]*?)"
        r"d30:([-\d.]+),([^}]*?)"
        r"d30_90:([-\d.]+),([^}]*?)"
        r"d90_180:([-\d.]+),([^}]*?)"
        r"d180:([-\d.]+),([^}]*?)"
        r"total_debt:([\d.]+)"
    )
    
    def replacer(m):
        return (
            m.group(1) +
            f"d30:{vals['d30']}," +
            m.group(3) +
            f"d30_90:{vals['d30_90']}," +
            m.group(5) +
            f"d90_180:{vals['d90_180']}," +
            m.group(7) +
            f"d180:{vals['d180']}," +
            m.group(9) +
            f"total_debt:{vals['total_debt']}"
        )
    
    new_content, n = re.subn(pattern, replacer, content)
    if n > 0:
        content = new_content
        print(f"Updated {dept}")
    else:
        print(f"WARNING: Could not find {dept}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
