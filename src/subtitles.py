import os
from .utils import run_command, logger

def generate_subtitles(video_path: str, start: float, duration: float, output_srt: str, language: str) -> bool:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster-whisper not installed. Skipping subtitles.")
        return False
        
    logger.info("Extracting audio for subtitles...")
    temp_audio = output_srt.replace(".srt", ".wav")
    
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-t", str(duration),
        "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        temp_audio
    ]
    res = run_command(cmd, check=False)
    if res.returncode != 0:
        logger.error("Failed to extract audio for subtitles.")
        return False
        
    logger.info("Transcribing audio...")
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(temp_audio, language=language if language != "auto" else None)
        
        with open(output_srt, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}\n")
                f.write(f"{segment.text.strip()}\n\n")
                
        os.remove(temp_audio)
        return True
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        return False

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"
