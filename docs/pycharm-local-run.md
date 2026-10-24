# 在 PyCharm 运行网站

打开项目根目录，也就是同时包含 `run.py`、`requirements.txt` 和 `src/` 的文件夹。
网站的 FastAPI 应用定义在 `src/main.py`；启动服务器请运行根目录的 `run.py`。

## 1. 更新 GitHub 代码

这版整合代码在 `codex/blue-tech-homepage` 分支，已包含最新 `main` 的功能与新的科技风格。

如果你已在 PyCharm 克隆了这个仓库，先 **Git → Fetch**，再在 Git 分支菜单选择 **Remote → origin/codex/blue-tech-homepage → Checkout**，然后选择 **Git → Pull**。
如果提示有未提交的本地修改，先 **Commit** 或 **Shelve** 保存修改，再 Pull；出现合并冲突时保留并处理本地工作。

首次使用时，选择 **Get from Version Control**，填入仓库地址：

```text
https://github.com/Yuhang08/Future-Skill-AI-Model.git
```

首次克隆后，也切换到上面的 `codex/blue-tech-homepage` 分支再运行。

## 2. 配置 Python

在 **Settings → Project → Python Interpreter** 中，为这个项目创建或选择 Python **3.12** 的虚拟环境。
Windows、macOS 和 Linux 均使用项目自己的 Python 环境。

打开 PyCharm 的 **Terminal**，确认使用已选的虚拟环境，然后安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 3. 点击 Run

在项目文件列表中右键根目录的 **`run.py` → Run 'run'**。
看到 `Uvicorn running on http://127.0.0.1:5000` 后，在浏览器打开：

```text
http://127.0.0.1:5000/
```

| 页面 | 地址 |
| --- | --- |
| 首页与职业问卷 | `http://127.0.0.1:5000/` |
| 学习路径 | `http://127.0.0.1:5000/reskilling` |
| AI 趋势 | `http://127.0.0.1:5000/ai-trend` |
| Uncertainty Lab | `http://127.0.0.1:5000/uncertainty` |
| SDG Mapping | `http://127.0.0.1:5000/sdg-impact` |
| 面试练习 | `http://127.0.0.1:5000/interview-practice/` |

点击网页右上角 **Settings → Appearance**，选择 **Light / Dark**，检查首页和背景效果。
查看最新 UI 前，使用 **Ctrl + F5**（macOS 可用 **⌘ + Shift + R**）刷新浏览器缓存。
结束测试时，点击 PyCharm 的红色 **Stop** 按钮；修改 Python 代码后重新运行 `run.py`。

## 端口被占用时

在 **Run → Edit Configurations → Environment variables** 中添加：

```text
FUTURESKILL_PORT=5001
```

重新运行，再打开 `http://127.0.0.1:5001/`。
你也可以在项目根目录创建本地 `.env` 文件，写入上面这一行；`run.py` 会在加载应用前读取它，已有的环境变量优先。
`.env` 是可选的，已由 Git 忽略。

## 可选 AI 功能与本地数据

测试网页 UI、职业问卷、规则学习路径和 SDG 页面无需 API key。
生成 AI 面试问题或请求 AI 技能差距解释时，需要受支持的服务端 AI 配置。
本地可使用 `OPENAI_API_KEY`；Replit 托管配置使用配套的 `AI_INTEGRATIONS_OPENAI_BASE_URL` 和 `AI_INTEGRATIONS_OPENAI_API_KEY`。
请在 PyCharm 的环境变量或本地 `.env` 中设置实际凭据。

学习记录、会话信息、上传文件及面试问题历史默认保存在 `src/instance/`。
该目录已由 Git 忽略。可用 `FUTURESKILL_DATA_DIR` 指定其他可写目录。

## 使用 Terminal 启动

在项目根目录运行以下命令，效果与 Run 按钮相同：

```bash
python run.py
```

如果使用已有的 Uvicorn 运行配置，可继续用：

```bash
python -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 5000
```

根目录 `.env` 的自动读取由 `run.py` 提供；直接运行 Uvicorn 时，可在 PyCharm 的 Environment variables 中配置所需变量。
