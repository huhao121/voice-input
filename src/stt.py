"""语音转文字：本地 SenseVoice via sherpa-onnx（中文最准、离线、~70ms）。

模型路径由 config.MODEL_DIR 决定；缺失时由 model_download 自动下载。
"""

import os
import numpy as np

from config import MODEL_DIR
from model_download import ensure_model

LANGUAGE = os.getenv("STT_LANGUAGE", "auto")  # auto / zh / en / ja / ko / yue

_recognizer = None


def _get_recognizer():
    """懒加载：第一次用时确保模型在位、建好识别器并常驻内存（降延迟）。"""
    global _recognizer
    if _recognizer is None:
        ensure_model()                       # 模型缺失则自动下载
        import sherpa_onnx
        model = os.path.join(MODEL_DIR, "model.int8.onnx")
        tokens = os.path.join(MODEL_DIR, "tokens.txt")
        # 不同 sherpa-onnx 版本参数名可能略有差异；报错时用
        #   help(sherpa_onnx.OfflineRecognizer.from_sense_voice) 查
        _recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=model,
            tokens=tokens,
            num_threads=2,
            use_itn=True,
            language=LANGUAGE,
            debug=False,
        )
    return _recognizer


def warmup():
    """启动时预热：建好识别器并跑一小段静音，把"冷启动"的开销提前花掉。"""
    rec = _get_recognizer()
    s = rec.create_stream()
    s.accept_waveform(16000, np.zeros(1600, dtype=np.float32))
    rec.decode_stream(s)


def transcribe(audio_int16: np.ndarray) -> str:
    """把 int16 音频转成文字。"""
    if audio_int16 is None or len(audio_int16) == 0:
        return ""
    samples = audio_int16.astype(np.float32) / 32768.0   # sherpa-onnx 要 float32 [-1,1]
    rec = _get_recognizer()
    stream = rec.create_stream()
    stream.accept_waveform(16000, samples)
    rec.decode_stream(stream)
    return stream.result.text.strip()


if __name__ == "__main__":
    import sounddevice as sd
    print("录音 3 秒，请说话…")
    audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    print("识别结果：", transcribe(audio.flatten()))
