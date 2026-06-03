# 语音输入法 MVP · 计划 + 验收标准

> 极简 Python MVP。选型依据见 [RESEARCH.md](RESEARCH.md)。

## MVP 范围（先做最小可用，不贪多）
按住热键说话 → 松开 → 转成文字 → LLM 去口癖整理 → 自动粘到光标处。

## ✅ 验收标准（怎样算"做完"）
1. 按住全局热键时录音，松开停止录音。
2. 录音转成文字（中英混合可用）。
3. LLM 把文字整理成「可发送」：去掉 嗯/啊/那个/就是 等口癖、补标点、纠常见同音错。
4. 整理后的文字自动出现在当前光标处（任意 Windows 应用）。
5. 端到端延迟可接受（目标松手后 <2s 出字）。
6. 有个最简录音状态提示（托盘图标变化即可）。

## 开发/测试说明
- 运行平台是 **Windows**：热键、麦克风、剪贴板插入需在 Windows 上运行。
- 可在无 GUI/无麦克风环境（如 Linux/CI）单独测试的：`cleanup.py`（LLM 整理，纯文本进出，只需一个 DeepSeek API key）。
- 需在 Windows 上运行验证的：`recorder.py`（录音）、`stt.py`（转写）、`inject.py`（粘贴）、`main.py`（热键串联）。

## 文件结构
```
voice-input/
├── RESEARCH.md          选型调研（已完成）
├── PLAN.md              本文件
├── requirements.txt     依赖
└── src/
    ├── cleanup.py       LLM 文字整理（先做，可在此验证）✅
    ├── stt.py           语音转文字（SenseVoice/sherpa-onnx，Windows 跑）
    ├── recorder.py      按键录音（sounddevice，Windows 跑）
    ├── inject.py        粘到光标处（剪贴板+Ctrl+V，Windows 跑）
    └── main.py          热键串联 + 托盘（Windows 跑）
```

## 技术决策（来自调研）
- STT：本地 SenseVoice via sherpa-onnx（~70ms、中文最准、离线免翻墙）。
- 整理：LLM 一遍（需 DeepSeek API key；prompt 见 RESEARCH.md / cleanup.py）。
- 插入：剪贴板 + Ctrl+V（对中文最稳），存/恢复原剪贴板。
- 热键/录音：pynput + sounddevice。

## 进度
- [x] 选型调研（RESEARCH.md）
- [x] cleanup.py + LLM 整理验证 ✅（去口癖+补标点+纠"阿屁艾→API"）
- [x] Windows 端 stt/recorder/inject/main + README 脚手架 ✅
- [ ] Windows 上端到端跑通
