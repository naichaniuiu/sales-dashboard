# 中西部大区数据看板 - GitHub Pages 部署

## 📁 仓库文件结构

```
workbuddy-dashboard/
├── data/                      # 数据文件夹（每日更新）
│   ├── performance.json       # 业绩数据
│   └── debt.json             # 欠款数据
├── assets/                    # 静态资源
│   └── css/
│   └── js/
├── index.html                 # 主看板页面
├── README.md                  # 说明文档
└── .github/
    └── workflows/
        └── daily-update.yml   # GitHub Actions 自动更新脚本
```

## 🔧 部署步骤

### 步骤1: 在GitHub创建仓库

1. 访问 https://github.com 并登录
2. 点击右上角 **+** → **New repository**
3. 填写信息：
   - Repository name: `workbuddy-dashboard`
   - Description: `中西部大区数据看板`
   - 选择 **Public**（公开仓库才能用GitHub Pages）
   - 勾选 **Add a README file**
4. 点击 **Create repository**

### 步骤2: 克隆仓库到本地

```bash
git clone https://github.com/YOUR_USERNAME/workbuddy-dashboard.git
cd workbuddy-dashboard
```

### 步骤3: 启用GitHub Pages

1. 在仓库页面点击 **Settings**
2. 左侧菜单选择 **Pages**
3. Source 下选择 **Deploy from a branch**
4. Branch 选择 **main**，文件夹选择 **/ (root)**
5. 点击 **Save**
6. 等待几分钟后，访问 `https://YOUR_USERNAME.github.io/workbuddy-dashboard`

### 步骤4: 每日更新数据

更新 `data/performance.json` 和 `data/debt.json` 后推送到GitHub：

```bash
git add .
git commit -m "更新 2026-05-13 数据"
git push origin main
```

## 🔄 自动更新方案

### 方案A: 手动更新（简单）

每天运行数据提取脚本，然后推送更新。

### 方案B: GitHub Actions 自动更新（推荐）

配置定时任务自动从数据源拉取最新数据。

---

## 📊 当前看板地址（部署后）

访问地址：`https://YOUR_USERNAME.github.io/workbuddy-dashboard`

---
