"""麦克风录音：sounddevice → float32 mono numpy 数组。"""
import numpy as np
import sounddevice as sd


def record_seconds(seconds: float, sample_rate: int = 16000) -> np.ndarray:
    """录制固定秒数音频，返回 float32 mono。

    用于最简管线与测试。生产路径用 record_until（由调用方决定何时停）。

    实现细节：先丢弃首块以预热硬件缓冲（避免开头截断/直流偏置），再读取
    目标秒数的样本。读取结果统一 reshape 成一维 float32 返回。
    """
    n = int(seconds * sample_rate)
    with sd.InputStream(channels=1, samplerate=sample_rate, dtype="float32") as stream:
        # 预热缓冲：丢弃第一块，消除开启流时的瞬态。
        stream.read(n)
        # 正式读取：sounddevice.InputStream.read 返回 (data, overflowed) 元组。
        data, _ = stream.read(n)
    return np.asarray(data).reshape(-1).astype(np.float32)


def record_into(frames: list, sample_rate: int = 16000) -> sd.InputStream:
    """开启输入流，持续把块 append 到 frames；返回 stream，调用方负责 stop()。

    供 PTT/toggle：按键开始 → record_into 起 → 按键结束 → stop()。
    """
    def _callback(indata, frames_count, time_info, status):  # noqa: ARG001
        frames.append(np.asarray(indata).reshape(-1).copy())
    stream = sd.InputStream(
        channels=1, samplerate=sample_rate, dtype="float32", callback=_callback
    )
    stream.start()
    return stream


def flatten(frames: list) -> np.ndarray:
    """把 record_into 累积的块列表拼成一维数组。"""
    if not frames:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(frames).astype(np.float32)
