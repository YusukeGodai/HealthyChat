# HealthyChat

AI 健康监测聊天应用 —— 在自然对话中隐式检测用户的心理与身体健康状况，并在需要时提供专业建议或干预提醒。

## 快速开始（免安装）

从 [Releases](../../releases) 下载 `HealthyChat.exe`，双击运行即可。

1. 双击 `HealthyChat.exe`，等待控制台显示 `Running on http://127.0.0.1:5000`
2. 打开浏览器访问 http://127.0.0.1:5000
3. 点击右上角齿轮图标，选择供应商并填入 API Key，保存设置
4. 开始聊天

> 目标电脑无需安装 Python 或任何依赖。仅支持 Windows。

## 从源码运行

### 环境要求

- Python 3.10+
- pip

### Windows 启动（命令提示符 CMD）

首次使用时安装 Python 3.10 或以上版本，安装时勾选 **Add Python to PATH**。将项目复制或解压到本机，例如 `D:\chatapp`。

打开 **命令提示符（CMD）**，执行以下命令；请把示例路径替换为实际项目路径：

```bat
cd /d D:\chatapp
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install flask requests
python app.py
```

如果提示找不到 `py`，先运行 `python --version` 确认 Python 已安装，再用 `python -m venv .venv` 创建虚拟环境。

看到 `Running on http://127.0.0.1:5000` 表示启动成功，打开浏览器访问 [http://127.0.0.1:5000](http://127.0.0.1:5000)。终端出现开发服务器的 `WARNING` 是正常提示，本机测试可以继续使用。

以后启动无需重复安装依赖，只需在 CMD 中执行：

```bat
cd /d D:\chatapp
.venv\Scripts\activate.bat
python app.py
```

运行期间保持终端打开，按 `Ctrl+C` 停止服务。

从 Mac 迁移到 Windows 时：

- 不要复制 Mac 的 `.venv` 文件夹，在 Windows 按上述步骤重新创建。
- 要沿用模型地址、密钥和模型名称，请把 `config.local.json` 一并复制到 `app.py` 所在目录。此文件被 Git 忽略，从 GitHub 下载不会包含它。
- 没有 `config.local.json` 时，可以在网页右上角设置中填写模型 A/B/C 的配置。

### macOS 启动（终端）

安装 Python 3.10 或以上版本，在终端进入解压后的项目目录（路径按实际位置替换）：

```bash
cd ~/Downloads/HealthyChat
python3 -m venv .venv
source .venv/bin/activate
python -m pip install flask requests
python app.py
```

以后启动只需：

```bash
cd ~/Downloads/HealthyChat
source .venv/bin/activate
python app.py
```

打开 [http://127.0.0.1:5000](http://127.0.0.1:5000)，保持终端打开，按 `Ctrl+C` 停止。

## 从源码构建 exe

### 额外安装

```bash
pip install pyinstaller
```

### 构建

```bash
python -m PyInstaller healthychat.spec --noconfirm
```

构建完成后，`dist/HealthyChat.exe` 即为可独立运行的单文件程序。

## 配置说明

启动后点击右上角齿轮图标进入设置，为模型 A/B/C 分别配置：

| 字段 | 说明 |
|------|------|
| 供应商 | Edge（OpenAI 兼容）/ OpenRouter / Qwen (通义千问) / DeepSeek |
| API Key | 对应供应商的 API 密钥 |
| 模型名称 | 使用的模型 ID，默认 `gpt-5.6-sol` |

## 情景陪伴

- 午后茶屋、雨天树洞、晚安小屋、专注书桌：切换插画、配色、开场建议和模型 A 的陪伴语气。
- 点击开场建议填入输入框，可修改后发送；切换情景保留本次对话。
- 点击「送一张心情贴图」发送小熊贴图，模型会收到对应文字含义。贴图不消耗输入框中的草稿。
- 插画与贴图位于 `static/art/`，为本地 SVG，不依赖外部图片服务。
- 真实回复仍需在设置中配置模型 API；健康提醒沿用现有流程。

离线回归测试（不调用付费模型）：`python -m unittest test_companion`。

## Edge 默认模型

A/B/C 默认使用 `https://edge.gpt.rmqg.org/v1` 与 `gpt-5.6-sol`，通过
`POST /chat/completions` 和 Bearer Authorization 调用。
本机密钥明文保存在项目目录的 `config.local.json`，已加入 Git 忽略。
配置字段为 `api_base`、`api_key`、`model`；修改后重启服务生效。
打包后将该文件放在可执行文件旁。换电脑时需自行配置此文件或在设置中填写。
环境变量 `HEALTHYCHAT_API_KEY`、`HEALTHYCHAT_API_BASE`、`HEALTHYCHAT_MODEL` 可覆盖文件设置。
界面手动配置仅保存在服务端内存中，重启恢复本机默认配置；浏览器 Cookie 仅包含会话标识。
