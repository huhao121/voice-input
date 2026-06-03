"""语音转文字：本地 SenseVoice via sherpa-onnx（中文最准、离线、~70ms、免翻墙）。

模型下载（见 README）：把 SenseVoice 的 model.int8.onnx 和 tokens.txt 放到
STT_MODEL_DIR 指向的目录（默认 ./models/sense-voice）。
"""

import os
import numpy as np

MODEL_DIR = os.getenv("STT_MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "models", "sense-voice"))
LANGUAGE = os.getenv("STT_LANGUAGE", "auto")  # auto / zh / en / ja / ko / yue

_recognizer = None


def _get_recognizer():
    """懒加载：第一次用时建好识别器并常驻内存（避免每次冷启动，降延迟）。"""
    global _recognizer
    if _recognizer is None:
        import sherpa_onnx  # 延迟导入，便于在没装的环境里也能 import 本模块
        model = os.path.join(MODEL_DIR, "model.int8.onnx")
        tokens = os.path.join(MODEL_DIR, "tokens.txt")
        if not os.path.exists(model):
            raise FileNotFoundError(f"找不到 STT 模型：{model}。请按 README 下载 SenseVoice 模型。")
        # 注意：不同 sherpa-onnx 版本参数名可能略有差异；报错时用
        #   help(sherpa_onnx.OfflineRecognizer.from_sense_voice) 查一下
        _recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=model,
            tokens=tokens,
            num_threads=2,
            use_itn=True,          # 反向文本规整：数字/标点更自然
            language=LANGUAGE,
            debug=False,
        )
    return _recognizer


def transcribe(audio_int16: np.ndarray) -> str:
    """把 int16 音频转成文字。"""
    if audio_int16 is None or len(audio_int16) == 0:
        return ""
    # sherpa-onnx 要 float32 且归一化到 [-1, 1]
    samples = (audio_int16.astype(np.float32) / 32768.0)
    rec = _get_recognizer()
    stream = rec.create_stream()
    stream.accept_waveform(16000, samples)
    rec.decode_stream(stream)
    return stream.result.text.strip()


if __name__ == "__main__":
    # 简单自检：录 3 秒，转写。需在有麦克风的机器（Windows）上跑。
    import sounddevice as sd
    print("录音 3 秒，请说话…")
    audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    print("识别结果：", transcribe(audio.flatten()))
