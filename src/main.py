import os
import sys
import json
from .config import parse_args
from .utils import logger
from .scene_detector import get_video_info, detect_scenes, generate_candidates
from .watermark_detector import detect_watermark_regions
from .scorer import score_candidates, filter_overlapping
from .llm_ranker import rerank_with_llm
from .renderer import build_scene_switches, render_short
from .smart_crop import estimate_focus_x
from .subtitles import generate_subtitles
from .metadata import export_metadata, generate_title
from .drive_exporter import export_run_to_google_drive

def main():
    args = parse_args()
    
    if not os.path.exists(args.input_video):
        logger.error(f"Input video not found: {args.input_video}")
        sys.exit(1)
        
    logger.info("Starting Shorts Auto Cutter MVP")
    logger.info(f"Input: {args.input_video}")
    logger.info(f"Max shorts: {args.max_shorts}, Duration: {args.min_duration}s - {args.max_duration}s")
    
    # 1. Get Video Info
    video_info = get_video_info(args.input_video)
    logger.info(f"Video: {video_info.width}x{video_info.height}, {video_info.fps:.2f} fps, {video_info.duration:.2f}s")
    
    # 2. Watermark Detection
    watermark_regions = detect_watermark_regions(args.input_video)
    if watermark_regions:
        watermark_action = "blur will be applied" if args.blur_watermark else "blur disabled by default"
        logger.warning(f"Detected {len(watermark_regions)} watermark region(s) - {watermark_action}")
        for reg in watermark_regions:
            logger.warning(f"  => region ({reg.x},{reg.y},{reg.width},{reg.height}) | {reg.confidence:.0%} confidence")
    else:
        logger.info("No significant watermark regions detected.")
    
    # 2. Detect Scenes
    scenes = detect_scenes(args.input_video)
    if not scenes:
        logger.error("No scenes detected. Exiting.")
        sys.exit(1)
        
    # 3. Generate Candidates
    candidates = generate_candidates(scenes, args.min_duration, args.max_duration)
    if not candidates:
        logger.error(f"No candidates found between {args.min_duration}s and {args.max_duration}s. Exiting.")
        sys.exit(1)
        
    # 4. Score Candidates
    scored_candidates = score_candidates(args.input_video, candidates, video_info)
    if args.use_llm_ranking:
        scored_candidates = rerank_with_llm(
            scored_candidates,
            args.max_shorts,
            provider=args.llm_provider,
            model=args.llm_model,
        )
    
    # 5. Filter Overlapping
    selected = filter_overlapping(scored_candidates, args.max_shorts)
    logger.info(f"Selected top {len(selected)} candidates for rendering.")
    
    # 6. Render and Generate Metadata
    shorts_dir = "output/shorts"
    reports_dir = "output/reports"
    os.makedirs(shorts_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    for name in os.listdir(shorts_dir):
        if name.startswith("short_") and name.lower().endswith((".mp4", ".srt", ".ass")):
            try:
                os.remove(os.path.join(shorts_dir, name))
            except OSError:
                pass

    for name in ("metadata.csv", "metadata.json", "index.html"):
        path = os.path.join(reports_dir, name)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
    
    rendered_candidates = []

    for i, cand in enumerate(selected, start=1):
        output_index = len(rendered_candidates) + 1
        output_file = f"{shorts_dir}/short_{output_index:03d}.mp4"
        title = generate_title(args.theme, i)
        focus_x = 0.5
        if args.smart_crop:
            focus_x = estimate_focus_x(
                args.input_video,
                cand.candidate.start_time,
                cand.candidate.duration,
                video_info.fps,
            )
        
        subtitle_srt = None
        if args.add_subtitles:
            subtitle_srt = f"{shorts_dir}/short_{output_index:03d}.srt"
            logger.info(f"Generating subtitles for part {i}...")
            success = generate_subtitles(
                args.input_video, cand.candidate.start_time, cand.candidate.duration, 
                subtitle_srt, args.language
            )
            if not success:
                subtitle_srt = None
                
        success = render_short(
            video_path=args.input_video,
            cand=cand,
            output_path=output_file,
            title=title,
            part_number=i,
            add_logo=args.add_logo,
            subtitle_srt=subtitle_srt,
            watermark_regions=watermark_regions if args.blur_watermark else [],
            parrot_dir=args.parrot_dir,
            add_parrot_reaction=args.add_parrot_reaction,
            scene_switches=build_scene_switches(
                scenes,
                cand.candidate.start_time,
                cand.candidate.end_time,
            ),
            add_suspense=args.add_suspense,
            suspense_sound=args.suspense_sound,
            suspense_volume=args.suspense_volume,
            source_width=video_info.width,
            source_height=video_info.height,
            focus_x=focus_x,
            smart_crop=args.smart_crop,
        )
        
        if success:
            logger.info(f"Successfully generated {output_file}")
            rendered_candidates.append(cand)
        else:
            logger.error(f"Skipping metadata entry because render failed: {output_file}")
            
    # 7. Export Metadata
    if not rendered_candidates:
        logger.error("No valid shorts were rendered. Report was not generated.")
        sys.exit(1)

    export_metadata(rendered_candidates, args.theme, reports_dir, shorts_dir)

    export_result = {
        "enabled": False,
        "report_path": os.path.abspath(os.path.join(reports_dir, "index.html")),
    }
    if args.copy_to_drive:
        export_result = export_run_to_google_drive(
            args.input_video,
            shorts_dir,
            reports_dir,
            preferred_path=args.drive_output_dir,
            delete_local_media=args.delete_local_after_drive,
        )

    last_run = {
        "report_path": export_result.get("report_path", os.path.abspath(os.path.join(reports_dir, "index.html"))),
        "drive_export": export_result,
        "local_reports_dir": os.path.abspath(reports_dir),
        "local_shorts_dir": os.path.abspath(shorts_dir),
        "shorts_count": len(rendered_candidates),
    }
    with open(os.path.join("output", "last_run.json"), "w", encoding="utf-8") as f:
        json.dump(last_run, f, indent=2, ensure_ascii=False)

    logger.info("Process completed successfully!")
    logger.info(f"Check the HTML report at {last_run['report_path']}")

if __name__ == "__main__":
    main()
