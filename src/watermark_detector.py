import cv2
import numpy as np
from dataclasses import dataclass
from typing import List
from .utils import logger

@dataclass
class WatermarkRegion:
    x: int
    y: int
    width: int
    height: int
    frame_width: int
    frame_height: int
    confidence: float  # 0.0 to 1.0

def detect_watermark_regions(video_path: str, sample_interval: float = 2.0) -> List[WatermarkRegion]:
    """
    Detect potential watermark regions by analyzing static areas in video frames.
    Returns list of WatermarkRegion with coordinates and confidence.
    """
    logger.info("Detecting potential watermark regions...")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Could not open video for watermark detection")
        return []
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    
    if duration == 0 or frame_width == 0 or frame_height == 0:
        cap.release()
        return []
    
    sample_rate = max(1, int(fps * sample_interval))
    total_samples = 0
    prev_frame = None
    static_regions = {}
    
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_num % sample_rate == 0:
            total_samples += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                diff = cv2.absdiff(gray, prev_frame)
                _, static_mask = cv2.threshold(diff, 10, 255, cv2.THRESH_BINARY_INV)
                contours, _ = cv2.findContours(static_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 200:
                        x, y, w, h = cv2.boundingRect(contour)
                        norm_key = (x // 20, y // 20, w // 20, h // 20)
                        static_regions[norm_key] = static_regions.get(norm_key, 0) + 1
            
            prev_frame = gray
            
        frame_num += 1
        
    cap.release()
    
    regions = []
    min_frequency = max(3, int(total_samples * 0.15))
    
    for (gx, gy, gw, gh), count in static_regions.items():
        if count < min_frequency:
            continue
            
        x, y, w, h = gx * 20, gy * 20, gw * 20, gh * 20
        confidence = count / total_samples
        
        is_corner = (
            (x < frame_width * 0.2 and y < frame_height * 0.2) or
            (x > frame_width * 0.8 and y < frame_height * 0.2) or
            (x < frame_width * 0.2 and y > frame_height * 0.8) or
            (x > frame_width * 0.8 and y > frame_height * 0.8) or
            (y < frame_height * 0.12) or
            (y > frame_height * 0.88) or
            (x < frame_width * 0.12) or
            (x > frame_width * 0.88)
        )
        
        if is_corner:
            regions.append(WatermarkRegion(
                x=x, y=y, width=w, height=h,
                frame_width=frame_width,
                frame_height=frame_height,
                confidence=confidence
            ))
    
    # Merge overlapping regions
    if regions:
        merged = [regions[0]]
        for reg in regions[1:]:
            prev = merged[-1]
            gap_x = reg.x - (prev.x + prev.width)
            gap_y = reg.y - (prev.y + prev.height)
            if abs(gap_x) < 40 and abs(gap_y) < 40:
                x1 = min(prev.x, reg.x)
                y1 = min(prev.y, reg.y)
                x2 = max(prev.x + prev.width, reg.x + reg.width)
                y2 = max(prev.y + prev.height, reg.y + reg.height)
                merged[-1] = WatermarkRegion(
                    x=x1, y=y1,
                    width=x2 - x1, height=y2 - y1,
                    frame_width=frame_width,
                    frame_height=frame_height,
                    confidence=max(prev.confidence, reg.confidence)
                )
            else:
                merged.append(reg)
        regions = merged
    
    if regions:
        logger.warning(f"Potential watermark(s) detected: {len(regions)} region(s)")
        for i, reg in enumerate(regions, 1):
            pos = "top-left" if reg.y < reg.frame_height * 0.3 else "top-right" if reg.x > reg.frame_width * 0.7 else "bottom-left" if reg.y > reg.frame_height * 0.7 else "bottom-right"
            logger.warning(f"  #{i}: {pos} corner | confidence: {reg.confidence:.0%} | area: ({reg.x},{reg.y},{reg.width},{reg.height})")
    else:
        logger.info("No obvious watermark regions detected")
        
    return regions