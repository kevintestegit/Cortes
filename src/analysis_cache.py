import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .scene_detector import SceneCandidate, VideoInfo
from .scorer import ScoredCandidate
from .utils import logger
from .watermark_detector import WatermarkRegion


CACHE_VERSION = 1
SCORING_CACHE_VERSION = 2
SCENE_CACHE_VERSION = 1
WATERMARK_CACHE_VERSION = 1
FOCUS_CACHE_VERSION = 1


def _hash_file_sample(path: str, chunk_size: int = 1024 * 1024) -> str:
    size = os.path.getsize(path)
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        hasher.update(f.read(chunk_size))
        if size > chunk_size * 2:
            f.seek(max(0, size // 2 - chunk_size // 2))
            hasher.update(f.read(chunk_size))
        if size > chunk_size:
            f.seek(max(0, size - chunk_size))
            hasher.update(f.read(chunk_size))
    return hasher.hexdigest()


def video_fingerprint(video_path: str) -> dict[str, Any]:
    absolute = os.path.abspath(video_path)
    stat = os.stat(absolute)
    signature = _hash_file_sample(absolute)
    key_payload = {
        "path": os.path.normcase(absolute),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "signature": signature,
    }
    digest = hashlib.sha256(json.dumps(key_payload, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "key": digest,
        "path": absolute,
        "name": os.path.basename(absolute),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "signature": signature,
    }


def _cache_file_for(fingerprint: dict[str, Any]) -> str:
    return os.path.join("output", "cache", "analysis", f"{fingerprint['key']}.json")


class AnalysisCache:
    def __init__(self, video_path: str, enabled: bool = True, refresh: bool = False):
        self.enabled = enabled
        self.refresh = refresh
        self.fingerprint = video_fingerprint(video_path)
        self.path = _cache_file_for(self.fingerprint)
        self.data = self._load()
        self.dirty = False

    def _new_data(self) -> dict[str, Any]:
        now = datetime.now().isoformat(timespec="seconds")
        return {
            "version": CACHE_VERSION,
            "created_at": now,
            "updated_at": now,
            "fingerprint": self.fingerprint,
            "video_info": None,
            "scenes": {},
            "watermark_regions": {},
            "scores": {},
            "focus_x": {},
        }

    def _load(self) -> dict[str, Any]:
        if not self.enabled or self.refresh or not os.path.exists(self.path):
            return self._new_data()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("version") != CACHE_VERSION:
                return self._new_data()
            if data.get("fingerprint", {}).get("key") != self.fingerprint["key"]:
                return self._new_data()
            logger.info(f"Loaded analysis cache: {self.path}")
            return data
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(f"Could not read analysis cache, rebuilding it: {exc}")
            return self._new_data()

    def save(self) -> None:
        if not self.enabled or not self.dirty:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved analysis cache: {self.path}")
        self.dirty = False

    def get_video_info(self) -> VideoInfo | None:
        item = self.data.get("video_info")
        if not item:
            return None
        logger.info("Using cached video info.")
        return VideoInfo(**item)

    def set_video_info(self, info: VideoInfo) -> None:
        self.data["video_info"] = asdict(info)
        self.dirty = True

    def get_scenes(self, key: str) -> list[tuple[float, float]] | None:
        item = self.data.get("scenes", {}).get(key)
        if not item or item.get("version") != SCENE_CACHE_VERSION:
            return None
        logger.info("Using cached scene detection.")
        return [(float(start), float(end)) for start, end in item.get("items", [])]

    def set_scenes(self, key: str, scenes: list[tuple[float, float]]) -> None:
        self.data.setdefault("scenes", {})[key] = {
            "version": SCENE_CACHE_VERSION,
            "items": [[round(start, 4), round(end, 4)] for start, end in scenes],
        }
        self.dirty = True

    def get_watermarks(self, key: str) -> list[WatermarkRegion] | None:
        item = self.data.get("watermark_regions", {}).get(key)
        if not item or item.get("version") != WATERMARK_CACHE_VERSION:
            return None
        logger.info("Using cached watermark analysis.")
        return [WatermarkRegion(**region) for region in item.get("items", [])]

    def set_watermarks(self, key: str, regions: list[WatermarkRegion]) -> None:
        self.data.setdefault("watermark_regions", {})[key] = {
            "version": WATERMARK_CACHE_VERSION,
            "items": [asdict(region) for region in regions],
        }
        self.dirty = True

    def get_scores(self, key: str) -> list[ScoredCandidate] | None:
        item = self.data.get("scores", {}).get(key)
        if not item or item.get("version") != SCORING_CACHE_VERSION:
            return None
        logger.info("Using cached candidate scores.")
        scored = []
        for row in item.get("items", []):
            cand = SceneCandidate(**row["candidate"])
            scored.append(ScoredCandidate(candidate=cand, **row["score"]))
        return scored

    def set_scores(self, key: str, scored: list[ScoredCandidate]) -> None:
        self.data.setdefault("scores", {})[key] = {
            "version": SCORING_CACHE_VERSION,
            "items": [
                {
                    "candidate": asdict(item.candidate),
                    "score": {
                        "score": item.score,
                        "reason": item.reason,
                        "motion_score": item.motion_score,
                        "audio_score": item.audio_score,
                        "brightness": item.brightness,
                        "viral_score": item.viral_score,
                        "hook_score": item.hook_score,
                        "retention_score": item.retention_score,
                        "action_score": item.action_score,
                        "sound_score": item.sound_score,
                        "viral_label": item.viral_label,
                        "viral_tip": item.viral_tip,
                    },
                }
                for item in scored
            ],
        }
        self.dirty = True

    def get_focus_x(self, key: str) -> float | None:
        item = self.data.get("focus_x", {}).get(key)
        if not item or item.get("version") != FOCUS_CACHE_VERSION:
            return None
        logger.info(f"Using cached smart crop focus: {float(item['value']):.2f}")
        return float(item["value"])

    def set_focus_x(self, key: str, value: float) -> None:
        self.data.setdefault("focus_x", {})[key] = {
            "version": FOCUS_CACHE_VERSION,
            "value": round(float(value), 6),
        }
        self.dirty = True


def scene_cache_key(threshold: float = 27.0) -> str:
    return f"content_threshold={threshold:.2f}"


def watermark_cache_key(sample_interval: float = 2.0) -> str:
    return f"sample_interval={sample_interval:.2f}"


def scores_cache_key(
    scenes: list[tuple[float, float]],
    min_duration: int,
    max_duration: int,
) -> str:
    payload = {
        "scoring_version": SCORING_CACHE_VERSION,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "scenes": [[round(start, 4), round(end, 4)] for start, end in scenes],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def focus_cache_key(start: float, duration: float, fps_hint: float) -> str:
    payload = {
        "focus_version": FOCUS_CACHE_VERSION,
        "start": round(start, 3),
        "duration": round(duration, 3),
        "fps_hint": round(fps_hint, 3),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def cache_summary_path(video_path: str) -> str:
    fingerprint = video_fingerprint(video_path)
    return str(Path(_cache_file_for(fingerprint)).resolve())
