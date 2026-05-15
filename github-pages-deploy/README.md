# 中西部大区数据看板

## 访问地址

👉 **https://[你的用户名].github.io/workbuddy-dashboard**

## 每日更新说明

### 更新数据文件

1. 修改 `data/performance.json` 中的业绩数据
2. 修改 `data/debt.json` 中的欠款数据
3. 提交并推送到GitHub

```bash
git add .
git commit -m "更新 2026-05-13 数据"
git push origin main
```

### 注意事项

- `lastUpdate` 字段会显示在看板顶部，请同步更新
- 数据格式必须与JSON Schema一致
- 推送后约1-2分钟GitHub Pages自动更新

## 本地预览

直接在浏览器打开 `index.html` 即可预览
