# 语音输入法 MVP

按住热键说话 → 转文字 → LLM 去口癖整理 → 自动粘到光标处。Windows 纯软件。
选型见 [RESEARCH.md](RESEARCH.md)，计划/验收见 [PLAN.md](PLAN.md)。

## 它由什么组成
| 文件 | 作用 | 在哪跑 |
|---|---|---|
| `src/cleanup.py` | LLM 整理（去口癖/补标点/纠同音） | 任意（已验证）|
| `src/recorder.py` | 麦克风录音 | Windows |
| `src/stt.py` | 本地 SenseVoice 语音转文字 | Windows |
| `src/inject.py` | 剪贴板+Ctrl+V 粘到光标处 | Windows |
| `src/main.py` | 串联：热键→录音→转写→整理→插入 | Windows |

## 在 Windows 上运行（5 步）

**1. 装依赖**（建议用虚拟环境）
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2. 配 LLM 整理用的 key（首次运行会自动生成 `config.json` 模板）**
直接 `python src\main.py` 跑一次，它会在程序目录生成 `config.json`，打开填好即可：
```json
{
  "provider": "zhipu",
  "api_key": "你的 key",
  "model": "glm-4-flash",
  "base_url": "https://open.bigmodel.cn/api/paas/v4"
}
```
- **用智谱 GLM**（默认）：`provider` 填 `zhipu`，去 open.bigmodel.cn 申请 key。模型可填 `glm-4-flash`（快/便宜），不行就试 `glm-4.5-flash`。
- **用 DeepSeek**：`provider` 填 `deepseek`，`model` 填 `deepseek-chat`，删掉 `base_url` 让它用默认即可。
- 也可以用环境变量代替（`LLM_PROVIDER` + `ZHIPU_API_KEY`/`DEEPSEEK_API_KEY`）。

**3. 跑起来**
```bat
python src\main.py
```
**首次运行会自动下载语音模型（~230MB，默认走国内 hf-mirror）**到程序目录的 `models\sense-voice\`，下完即用。
（换源：设 `MODEL_BASE_URL`；手动放模型：把 `model.int8.onnx` + `tokens.txt` 放进该目录即可，会自动跳过下载。）

**4. 用**
把光标放进任意输入框 → **按住 F9 说话** → **松开** → 整理后的文字自动出现。
（想换热键：`set VOICE_HOTKEY=f8`）

## 分步自测（排错用）
- 只测整理：`python src\cleanup.py`（不需要麦克风/模型，需配好 key）
- 只测录音+识别：`python src\stt.py`（录 3 秒并识别，首次会下模型）
- 只测插入：`python src\inject.py`（3 秒后往光标粘一段字）

## 已知坑
- **全局热键**：某些情况下需要「以管理员身份运行」终端。
- **插入到 Chrome/VSCode**：用的是剪贴板粘贴，最稳；若个别应用不灵，确认它支持 Ctrl+V。
- **首次识别慢**：模型要加载进内存，第一次会顿一下，之后就快了。
- **延迟**：整理走云端 LLM 有几百 ms；想更快可换更小/更近的模型，或加「流式逐字插入」（见 RESEARCH.md）。

## 验收标准（来自 PLAN.md）
按住热键录音✓ → 转文字✓ → 去口癖整理✓ → 自动插光标处✓ → 松手 <2s 出字 → 有录音提示。
在你 Windows 上跑通即 MVP 完成。

## 打包发布（做成 .exe，像别人 Release 页那样）

### 方式一：本地打包（最快，先验证）
在你 **Windows** 上：
```bat
.venv\Scripts\activate
pip install pyinstaller
pyinstaller --onefile --name voice-input --collect-all sherpa_onnx --collect-all sounddevice src\main.py
```
产物在 `dist\voice-input.exe`，双击即可跑（用户不用装 Python）。

### 方式二：GitHub Actions CI（自动构建 + 发布到 Release 页）
workflow 已在 `.github/workflows/build-windows.yml`。原理：打一个版本 tag → GitHub
分配一台 Windows 虚拟机 → 自动 PyInstaller 打包 → 上传到 Release。**触发**：

```bash
git tag v0.1.0 && git push origin v0.1.0
```
然后去仓库的 **Actions** 页看构建、**Releases** 页下 `.exe`。（也可在 Actions 页手动触发。）

> 想同时出 **Mac/Linux** 版？把 workflow 的 `runs-on` 改成矩阵
> `runs-on: ${{ matrix.os }}` + `strategy.matrix.os: [windows-latest, macos-latest, ubuntu-latest]`，
> 一套步骤三台机器各打一个包。（注意：本工具的「插入光标」用 Ctrl+V，Mac 要改成 Cmd+V。）

### ⚠️ 这个项目打包的几个坑（提前知道）
- **模型不进 exe**：SenseVoice 模型 ~250MB，不该塞进 exe。让 exe 首次运行时下载，或随包附带 `models/` 文件夹。
- **API key 不能打进去**：绝不能把你的 DeepSeek key 编译进 exe。让用户运行时设环境变量 / 读配置文件。
- **首次 CI 常要调 1-2 次**：sherpa-onnx / sounddevice 的原生库打包偶尔需要补 PyInstaller hook，第一次失败很正常，看日志补 `--collect-binaries` 之类即可。
