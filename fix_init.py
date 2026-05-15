#!/usr/bin/env python
p = "C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html"
with open(p, "r", encoding="utf-8") as f:
    content = f.read()
old = "window.addEventListener('load', initCharts);\n</script>"
new = "window.addEventListener('load', initCharts);\nwindow.addEventListener('load', loadSalesDetail);\n</script>"
if old in content:
    content = content.replace(old, new, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK: preloading added")
else:
    print("NOT FOUND")
