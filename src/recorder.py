"""按住热键期间录音（push-to-talk）。输出 16kHz / mono / int16，喂给 STT。"""

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000


class Recorder:
    """start() 开始录，stop() 停止并返回整段音频(numpy int16)。"""

    def __init__(self, samplerate: int = SAMPLE_RATE):
        self.samplerate = samplerate
        self._frames = []
        self._stream = None

    def start(self):
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="int16",
            callback=self._on_audio,
        )
        self._stream.start()

    def _on_audio(self, indata, frames, time_info, status):
        # 录音回调：把每一小块拷进缓冲（在独立音频线程里跑）
        self._frames.append(indata.copy())

    def stop(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return np.zeros((0,), dtype="int16")
        return np.concatenate(self._frames, axis=0).flatten()
