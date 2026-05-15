#!/usr/bin/env python
# -*- coding: utf-8 -*-
p = "C:/Users/wm881/WorkBuddy/20260513090923/中西部大区26财年Q1数据看板.html"
with open(p, "r", encoding="utf-8") as f:
    content = f.read()

old = '<td></td><td></td><td></td><td></td>\n            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${tcol}</td>'
new = '<td></td><td></td><td></td><td></td><td></td>\n            <td style="padding:7px 5px;color:#ff4757;text-align:right;">${td}</td>\n            <td style="padding:7px 5px;color:#00ff88;text-align:right;">${tcol}</td>'

if old in content:
    content = content.replace(old, new, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK: total row fixed")
else:
    idx = content.find("合计（")
    print("found at:", idx)
    if idx >= 0:
        print(repr(content[idx:idx+400]))
    else:
        print("合计 not found at all")
