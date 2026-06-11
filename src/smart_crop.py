import cv2
import numpy as np

from .utils import logger


def estimate_focus_x(video_path: str, start: float, duration: float, fps_hint: float = 30.0) -> float:
    """Return a normalized horizontal focus center, using faces first and motion as fallback."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.5

    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    sample_count = max(4, min(18, int(duration / 2)))
    step_frames = max(1, int((fps_hint or 30.0) * max(0.75, duration / sample_count)))

    face_centers = []
    motion_centers = []
    texture_centers = []
    active_spans = []
    prev_gray = None

    for _ in range(sample_count):
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        small_w = 426
        small_h = max(1, int(h * small_w / w))
        small = cv2.resize(frame, (small_w, small_h))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(28, 28))
        for x, y, fw, fh in faces:
            weight = max(1, fw * fh)
            face_centers.append(((x + fw / 2) / small_w, weight))

        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        energy = np.mean(np.abs(grad_x) + np.abs(grad_y), axis=0)
        if float(np.max(energy)) > 0:
            threshold = max(float(np.percentile(energy, 65)), float(np.max(energy)) * 0.18)
            active_cols = np.where(energy >= threshold)[0]
            if active_cols.size:
                left = int(active_cols[0])
                right = int(active_cols[-1])
                active_spans.append((left / small_w, right / small_w))
                weights = energy[active_cols]
                center = float(np.average(active_cols, weights=weights)) / small_w
                texture_centers.append(center)

        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            _, mask = cv2.threshold(diff, 24, 255, cv2.THRESH_BINARY)
            moments = cv2.moments(mask)
            if moments["m00"] > 0:
                motion_centers.append((moments["m10"] / moments["m00"]) / small_w)

        prev_gray = gray
        current = cap.get(cv2.CAP_PROP_POS_FRAMES)
        cap.set(cv2.CAP_PROP_POS_FRAMES, current + step_frames)

    cap.release()

    pillarbox_detected = False
    if active_spans:
        median_width = float(np.median([right - left for left, right in active_spans]))
        pillarbox_detected = median_width < 0.78

    if pillarbox_detected and texture_centers:
        focus = float(np.median(texture_centers))
        logger.info(f"Smart crop focus from active content area: {focus:.2f}")
        return max(0.0, min(1.0, focus))

    if face_centers:
        total = sum(weight for _, weight in face_centers)
        focus = sum(center * weight for center, weight in face_centers) / total
        logger.info(f"Smart crop focus from face tracking: {focus:.2f}")
        return max(0.0, min(1.0, float(focus)))

    if motion_centers:
        focus = float(np.median(motion_centers))
        logger.info(f"Smart crop focus from motion tracking: {focus:.2f}")
        return max(0.0, min(1.0, focus))

    if texture_centers:
        focus = float(np.median(texture_centers))
        logger.info(f"Smart crop focus from texture tracking: {focus:.2f}")
        return max(0.0, min(1.0, focus))

    return 0.5


def crop_box_for_target(
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    focus_x: float,
) -> tuple[int, int, int, int]:
    target_ratio = target_width / target_height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_h = source_height
        crop_w = int(crop_h * target_ratio)
        crop_w = max(2, crop_w - (crop_w % 2))
        x = int((source_width * focus_x) - (crop_w / 2))
        x = max(0, min(source_width - crop_w, x))
        y = 0
    else:
        crop_w = source_width
        crop_h = int(crop_w / target_ratio)
        crop_h = max(2, crop_h - (crop_h % 2))
        x = 0
        y = max(0, int((source_height - crop_h) / 2))

    return crop_w, crop_h, x, y
