import wave
import struct
import os

def process_audio_file(input_path: str, output_path: str, boost_db: float = 4.0, normalize: bool = True, mode: str = "auto"):
    """
    Thuật toán Mastering chuẩn phòng thu (Pure Python):
    - Khử DC Offset: Làm sạch nền âm thanh.
    - Phân chia mức độ theo Mode (Tự động, Giọng nói, Nhạc cụ, Âm nhạc).
    - Nén dải động mềm (Soft Compression): Giúp âm thanh dày và chắc tiếng.
    - Giới hạn đỉnh (Brickwall Limiting): Chống vỡ tiếng (clipping).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Không tìm thấy tệp âm thanh tại: {input_path}")

    # Đọc tệp WAV nguồn
    with wave.open(input_path, 'rb') as wav_in:
        params = wav_in.getparams()
        n_channels, sampwidth, framerate, n_frames = params[:4]
        
        if sampwidth != 2:
            raise ValueError("Chỉ hỗ trợ tệp âm thanh chuẩn PCM 16-bit WAV.")
            
        frames = wav_in.readframes(n_frames)

    fmt = f"<{n_frames * n_channels}h"
    samples = list(struct.unpack(fmt, frames))
    if not samples:
        return output_path

    # 1. Khử DC Offset (Cân bằng lại tâm sóng âm)
    mean_val = sum(samples) / len(samples)
    samples = [int(s - mean_val) for s in samples]

    # 2. Tinh chỉnh hệ số khuếch đại theo chế độ (Mode)
    effective_boost = boost_db
    if mode == "voice":
        effective_boost = 3.0   # Giọng nói: Tăng độ rõ, hạn chế nén quá mạnh
    elif mode == "instrument":
        effective_boost = 3.5   # Nhạc cụ: Giữ độ động tự nhiên
    elif mode == "music":
        effective_boost = 5.0   # Âm nhạc tổng hợp: Tăng độ lớn và lực cho bản nhạc

    gain_factor = 10 ** (effective_boost / 20.0)

    # 3. Xử lý nén dải động (Compression) & Khuếch đại
    max_limit = 32767
    peak = max(abs(s) for s in samples) if samples else 1
    
    # Tính toán chuẩn hóa tự động (Normalization)
    auto_scale = (max_limit / peak) if (normalize and peak > 0) else 1.0
    auto_scale = min(auto_scale, 3.5) # Giới hạn mức phóng đại tối đa để tránh khuếch đại nhiễu nền

    processed_samples = []
    threshold = max_limit * 0.75  # Ngưỡng bắt đầu nén

    for sample in samples:
        # Khuếch đại biên độ cơ bản
        val = sample * gain_factor
        
        # Áp dụng nén mềm cho các đoạn âm thanh quá lớn để tránh méo tiếng
        if abs(val) > threshold:
            excess = abs(val) - threshold
            compressed_excess = excess * 0.6  # Nén bớt 40% phần vượt ngưỡng
            val = (threshold + compressed_excess) if val > 0 else -(threshold + compressed_excess)

        # Áp dụng hệ số chuẩn hóa
        new_val = int(val * auto_scale)

        # Giới hạn cứng chống vỡ tiếng (Limiter)
        if new_val > max_limit:
            new_val = max_limit
        elif new_val < -max_limit:
            new_val = -max_limit
            
        processed_samples.append(new_val)

    # Đóng gói lại dữ liệu byte
    output_frames = struct.pack(fmt, *processed_samples)

    # Ghi ra tệp đầu ra đã Mastered
    with wave.open(output_path, 'wb') as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(output_frames)

    return output_path
