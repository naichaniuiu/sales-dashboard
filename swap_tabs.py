with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', encoding='utf-8') as f:
    content = f.read()

# Find tab-collection (回款周期分析) div
col_start = content.find('<div id="tab-collection"')
# Find tab-debt (欠款分析) div  
debt_start = content.find('<div id="tab-debt"')

if col_start == -1 or debt_start == -1:
    print(f'Not found: collection={col_start}, debt={debt_start}')
    exit()

# Find end of tab-debt: it's the </div> that closes the tab-content div
# The tab-debt div ends with </div> and then <!-- 弹窗 --> comes after
marker = '<!-- 弹窗 -->'
marker_pos = content.find(marker, debt_start)
debt_end = marker_pos  # tab-debt content ends right before <!-- 弹窗 -->

# tab-collection ends at debt_start (where tab-debt begins)
col_end = debt_start

col_section = content[col_start:col_end]
debt_section = content[debt_start:debt_end]

print(f'collection section: {col_start} to {col_end} ({len(col_section)} chars)')
print(f'debt section: {debt_start} to {debt_end} ({len(debt_section)} chars)')

# Swap: put debt before collection
new_content = content[:col_start] + debt_section + col_section + content[debt_end:]

with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done. Tab order swapped.')
