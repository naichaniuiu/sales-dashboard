import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if 'tab-content' in stripped or 'deptTableBody' in stripped or 'cycleTableBody' in stripped:
        print(f'{i}: {stripped[:120]}')
