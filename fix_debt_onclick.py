with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', encoding='utf-8') as f:
    content = f.read()

# Fix cycle table rows: onclick="showSalesDetail('xxx')" -> onclick="showSalesDetail('xxx','cycle')"
# Find cycleTableBody
tb_start = content.find('<tbody id="cycleTableBody">')
tb_end = content.find('</tbody>', tb_start) + len('</tbody>')
cycle_section = content[tb_start:tb_end]

def add_cycle(s):
    # Replace showSalesDetail('xxx')" with showSalesDetail('xxx','cycle')"
    import re
    def replacer(m):
        inner = m.group(1)
        return "showSalesDetail('" + inner + "','cycle')\""
    return re.sub(r"showSalesDetail\('([^']+)'\)\"", replacer, s)

new_cycle_section = add_cycle(cycle_section)
content = content[:tb_start] + new_cycle_section + content[tb_end:]

with open('C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html', 'w', encoding='utf-8') as f:
    f.write(content)

count = cycle_section.count("showSalesDetail")
print(f'Done. Fixed {count} handlers in cycleTableBody')
