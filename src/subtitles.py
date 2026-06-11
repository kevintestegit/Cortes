import os
from .utils import cleanup_temp_files, make_ffmpeg_safe_file, run_command, logger


def _ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", " ")


def _write_ass(output_ass: str, word_items: list[dict], width: int = 1080, height: int = 1920) -> bool:
    if not word_items:
        return False

    groups = [word_items[i:i + 4] for i in range(0, len(word_items), 4)]
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write(f"PlayResX: {width}\nPlayResY: {height}\n\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Default,Arial,72,&H00FFFFFF,&H0000FFFF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,5,1,2,70,70,170,1\n\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for group in groups:
            group_start = float(group[0]["start"])
            group_end = float(group[-1]["end"])
            for active_index, word in enumerate(group):
                start = max(group_start, float(word["start"]))
                end = max(start + 0.08, float(word["end"]))
                text_parts = []
                for idx, item in enumerate(group):
                    clean = _ass_escape(str(item["word"]).strip())
                    if not clean:
                        continue
                    if idx == active_index:
                        text_parts.append(r"{\c&H00FFFF&}" + clean + r"{\c&HFFFFFF&}")
                    else:
                        text_parts.append(clean)
                f.write(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{' '.join(text_parts)}\n")

    return True


def generate_subtitles(video_path: str, start: float, duration: float, output_srt: str, language: str) -> bool:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster-whisper not installed. Skipping subtitles.")
        return False
        
    logger.info("Extracting audio for subtitles...")
    temp_audio = output_srt.replace(".srt", ".wav")
    temp_files = []
    ffmpeg_video_path = make_ffmpeg_safe_file(video_path, temp_files)
    
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-t", str(duration),
        "-i", ffmpeg_video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        temp_audio
    ]
    res = run_command(cmd, check=False)
    if res.returncode != 0:
        logger.error("Failed to extract audio for subtitles.")
        if res.stderr:
            logger.error(res.stderr[-2000:])
        cleanup_temp_files(temp_files)
        return False
        
    logger.info("Transcribing audio...")
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(
            temp_audio,
            language=language if language != "auto" else None,
            word_timestamps=True,
        )
        segments = list(segments)
        word_items = []
        
        with open(output_srt, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}\n")
                f.write(f"{segment.text.strip()}\n\n")
                for word in getattr(segment, "words", None) or []:
                    word_items.append({
                        "word": word.word,
                        "start": float(word.start),
                        "end": float(word.end),
                    })

        output_ass = output_srt.replace(".srt", ".ass")
        if _write_ass(output_ass, word_items):
            logger.info(f"Generated highlighted ASS subtitles: {output_ass}")
                
        os.remove(temp_audio)
        cleanup_temp_files(temp_files)
        return True
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        cleanup_temp_files(temp_files)
        return False

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"
