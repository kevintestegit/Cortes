import argparse
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    input_video: str
    max_shorts: int
    min_duration: int
    max_duration: int
    format: str
    language: str
    theme: str
    add_subtitles: bool
    add_logo: bool
    add_parrot_reaction: bool
    parrot_dir: str
    add_suspense: bool
    suspense_sound: Optional[str]
    suspense_volume: float
    blur_watermark: bool
    smart_crop: bool
    use_llm_ranking: bool
    llm_provider: str
    llm_model: Optional[str]
    copy_to_drive: bool
    drive_output_dir: Optional[str]
    delete_local_after_drive: bool
    use_cache: bool
    refresh_cache: bool

def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Shorts Auto Cutter MVP")
    parser.add_argument("--input", type=str, required=True, help="Path to input video (.mp4)")
    parser.add_argument("--max-shorts", type=int, default=10, help="Maximum number of shorts to generate")
    parser.add_argument("--min-duration", type=int, default=18, help="Minimum duration of a short in seconds")
    parser.add_argument("--max-duration", type=int, default=45, help="Maximum duration of a short in seconds")
    parser.add_argument("--format", type=str, default="vertical", choices=["vertical"], help="Output video format")
    parser.add_argument("--language", type=str, default="en", help="Language for subtitles")
    parser.add_argument("--theme", type=str, default="funny", help="Theme for title generation")
    parser.add_argument("--parrot-dir", type=str, default="downloads/youtube", help="Directory with parrot reaction videos")
    parser.add_argument("--suspense-sound", type=str, default=None, help="Optional custom suspense sound file (.wav/.mp3)")
    parser.add_argument("--suspense-volume", type=float, default=0.45, help="Suspense sound volume, from 0.0 to 1.0")
    parser.add_argument("--llm-provider", type=str, default="openai", choices=["openai"], help="LLM provider for optional ranking")
    parser.add_argument("--llm-model", type=str, default=None, help="LLM model for optional ranking")
    parser.add_argument("--drive-output-dir", type=str, default=None, help="Optional Google Drive destination folder")
    
    # Booleans
    parser.add_argument("--add-subtitles", type=str, default="false", help="Add subtitles (true/false)")
    parser.add_argument("--add-logo", type=str, default="true", help="Add logo if exists (true/false)")
    parser.add_argument("--add-parrot", type=str, default="true", help="Add parrot reaction video at the bottom 30%% (true/false)")
    parser.add_argument("--add-suspense", type=str, default="true", help="Add suspense sound at internal scene/video switches (true/false)")
    parser.add_argument("--blur-watermark", type=str, default="false", help="Blur detected watermark regions (true/false)")
    parser.add_argument("--smart-crop", type=str, default="true", help="Use face/motion-aware crop instead of blurred background layout (true/false)")
    parser.add_argument("--use-llm-ranking", type=str, default="false", help="Use optional LLM reranking for selected clips (true/false)")
    parser.add_argument("--copy-to-drive", type=str, default="false", help="Copy generated shorts and report to Google Drive Desktop (true/false)")
    parser.add_argument("--delete-local-after-drive", type=str, default="false", help="Delete local media files after a validated Drive copy (true/false)")
    parser.add_argument("--use-cache", type=str, default="true", help="Reuse cached video analysis when possible (true/false)")
    parser.add_argument("--refresh-cache", type=str, default="false", help="Ignore existing cache and rebuild analysis (true/false)")
    
    args = parser.parse_args()
    
    return Config(
        input_video=args.input,
        max_shorts=args.max_shorts,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        format=args.format,
        language=args.language,
        theme=args.theme,
        add_subtitles=args.add_subtitles.lower() == "true",
        add_logo=args.add_logo.lower() == "true",
        add_parrot_reaction=args.add_parrot.lower() == "true",
        parrot_dir=args.parrot_dir,
        add_suspense=args.add_suspense.lower() == "true",
        suspense_sound=args.suspense_sound,
        suspense_volume=max(0.0, min(1.0, args.suspense_volume)),
        blur_watermark=args.blur_watermark.lower() == "true",
        smart_crop=args.smart_crop.lower() == "true",
        use_llm_ranking=args.use_llm_ranking.lower() == "true",
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        copy_to_drive=args.copy_to_drive.lower() == "true",
        drive_output_dir=args.drive_output_dir,
        delete_local_after_drive=args.delete_local_after_drive.lower() == "true",
        use_cache=args.use_cache.lower() == "true",
        refresh_cache=args.refresh_cache.lower() == "true",
    )
