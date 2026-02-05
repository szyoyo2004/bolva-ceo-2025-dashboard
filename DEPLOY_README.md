# BOLVA CEO Dashboard - Deployment Guide

## 🖥️ 1. 本地运行 (Local Run)

已为您生成一键启动脚本，无需命令行操作。

### 步骤：
1. **直接双击** 文件夹中的 `run_local.bat`。
2. 系统会自动启动浏览器并打开看板 (默认地址 `http://localhost:8501`)。

### 前置要求：
- 您的电脑已安装 Python。
- 若是首次运行，可能需要安装依赖包。请在文件夹空白处 右键 -> "Open in Terminal" (或打开 CMD)，运行：
  ```bash
  pip install -r requirements.txt
  ```

---

## ☁️ 2. 在线发布 (Online / Streamlit Cloud)

如果您希望生成在线链接分享给 CFO 或投资人，建议使用 **Streamlit Community Cloud** (免费、安全)。

### 步骤：
1. **上传代码到 GitHub**
   - 将当前文件夹 (`CEO_2025_年度经营看板 3`) 初始化为 Git 仓库并推送到您的 GitHub。
   - 确保 `requirements.txt` 在根目录下 (已为您准备好)。

2. **登录 Streamlit Cloud**
   - 访问 [share.streamlit.io](https://share.streamlit.io/)
   - 使用 GitHub 账号登录。

3. **创建 App**
   - 点击 **"New app"**。
   - 选择您刚才上传的 GitHub 仓库。
   - **Main file path** 填写：`app3.py`
   - 点击 **"Deploy"**。

### 云端数据源注意事项：
- **Excel 文件**：由于云端无法访问您的 `D:\` 盘，您需要在看板侧边栏选择 **"上传 Excel 数据源"**，将 `2025年全年.xlsx` 上传即可。
- 或者，您可以将 Excel 文件放入 GitHub 仓库同级目录，并修改代码中的默认路径为相对路径 (不推荐，数据保密性考虑)。**推荐使用侧边栏上传功能。**

---

## 🛠️ 文件说明
- `app3.py`: 看板主程序。
- `requirements.txt`: 在线部署所需的依赖列表。
- `run_local.bat`: 本地一键启动脚本。
