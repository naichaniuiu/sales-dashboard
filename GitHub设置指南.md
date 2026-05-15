# GitHub 设置指南

## 仓库信息
- **仓库地址**: https://github.com/naichaniuiu/sales-dashboard
- **看板地址**: https://naichaniuiu.github.io/sales-dashboard
- **用户名**: naichaniuiu（注意是两个"i"）

## 首次设置（只需一次）

### 1. 启用 Secret Scanning（解锁Token）

访问以下链接，点击 "Unblock secret"：
https://github.com/naichaniuiu/sales-dashboard/security/secret-scanning/unblock-secret/3DlMfX0Ds3gh4xTtXBSt3aoWPOw

### 2. 重新生成 Personal Access Token（推荐）

由于Token已暴露，建议重新生成：

1. 打开 https://github.com/settings/tokens
2. 找到旧的Token，点击 "Delete" 撤销
3. 点击 "Generate new token (classic)"
4. 配置：
   - Note: dashboard-push
   - Expiration: 90 Days
   - Select scopes: ✅ repo（全选）
5. 点击 "Generate token"
6. **立即复制保存新Token**

### 3. 更新批处理文件中的Token

编辑 `一键更新.bat`，将第11行的Token替换为新Token：
```
set /p GH_TOKEN=  → 输入新Token
```

## 每日使用

### 一键更新流程

1. 双击运行 `一键更新.bat`
2. 首次运行时会要求输入 GitHub Token
3. 脚本自动：
   - 提取最新Excel数据
   - 生成销售员明细
   - 更新看板HTML
   - 推送到GitHub
4. 等待1-2分钟，刷新看板页面即可看到最新数据

### 看板访问

所有管理者访问同一地址：
```
https://naichaniuiu.github.io/sales-dashboard/
```

## 共享给其他管理者

只需告诉他们上面的看板地址即可，无需额外设置。

## 注意事项

- Token 建议每90天更新一次
- 保持Token安全，不要随意分享
- 如果推送失败，可能是Token过期，重新生成即可
