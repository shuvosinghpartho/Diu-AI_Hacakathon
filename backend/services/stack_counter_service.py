"""Local single-image banknote stack counter.

This service is adapted from the project's ``1ip_version.py`` prototype. It
counts exposed paper layers from one side image and does not identify currency
denominations.
"""

from dataclasses import dataclass

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


ANALYSIS_WIDTH = 1536
N_PROFILES = 120
MAX_LAYER_SPACING = 8


@dataclass(frozen=True)
class StackCountResult:
    count: int
    stack_depth_px: float
    layer_pitch_px: float
    evidence: float
    analysis_width: int


class StackCounterService:
    @staticmethod
    def _find_stack_roi(gray: np.ndarray) -> tuple[int, int]:
        height, _ = gray.shape
        y_start = int(height * 0.35)
        y_end = int(height * 0.95)
        search = gray[y_start:y_end]

        smooth = cv2.GaussianBlur(search, (9, 9), 2.0)
        gradient = cv2.Sobel(smooth, cv2.CV_32F, 0, 1, ksize=3)
        energy = gaussian_filter1d(
            np.mean(np.abs(gradient), axis=1).astype(float),
            4.0,
        )
        center = y_start + int(np.argmax(energy))
        return (
            max(0, center - int(height * 0.08)),
            min(height, center + int(height * 0.12)),
        )

    @staticmethod
    def _detect_layer_band(roi: np.ndarray) -> tuple[int, int, np.ndarray]:
        height, width = roi.shape
        x_start = int(width * 0.20)
        x_end = int(width * 0.80)

        enhanced = cv2.createCLAHE(
            clipLimit=1.5,
            tileGridSize=(8, 8),
        ).apply(roi)
        gradient = np.abs(
            cv2.Sobel(enhanced, cv2.CV_32F, 0, 1, ksize=3)
        )
        row_texture = gaussian_filter1d(
            np.percentile(gradient[:, x_start:x_end], 60, axis=1),
            1.0,
        )
        threshold = max(30.0, float(np.percentile(row_texture, 45)))

        active = (row_texture > threshold).astype(np.uint8)
        active = cv2.morphologyEx(
            active.reshape(1, -1),
            cv2.MORPH_CLOSE,
            np.ones((1, 7), np.uint8),
        ).ravel()
        active = cv2.morphologyEx(
            active.reshape(1, -1),
            cv2.MORPH_OPEN,
            np.ones((1, 3), np.uint8),
        ).ravel().astype(bool)

        runs = []
        start = None
        for y, value in enumerate(np.r_[active, False]):
            if value and start is None:
                start = y
            elif not value and start is not None:
                if y - start >= 10:
                    runs.append((start, y))
                start = None

        if not runs:
            raise RuntimeError("Could not locate a clear exposed stack edge.")

        top, bottom = max(
            runs,
            key=lambda run: np.sum(row_texture[run[0]:run[1]]),
        )
        return int(top), int(bottom), gradient

    @staticmethod
    def _estimate_pitch(
        gradient: np.ndarray,
        top: int,
        bottom: int,
    ) -> tuple[float, float]:
        _, width = gradient.shape
        gaps = []
        columns_with_evidence = 0
        sample_x = np.linspace(
            int(width * 0.20),
            int(width * 0.80) - 1,
            N_PROFILES,
        ).astype(int)

        for x in sample_x:
            signal = np.mean(
                gradient[
                    top:bottom,
                    max(0, x - 2):min(width, x + 3),
                ],
                axis=1,
            ).astype(float)
            signal = gaussian_filter1d(signal, 0.35)
            signal -= gaussian_filter1d(signal, 3.0)

            prominence = max(
                np.std(signal) * 0.18,
                np.percentile(np.abs(signal), 55) * 0.10,
                1.0,
            )
            peaks, _ = find_peaks(
                np.abs(signal),
                distance=1,
                prominence=prominence,
            )

            if len(peaks) >= 4:
                columns_with_evidence += 1
                spacing = np.diff(peaks)
                gaps.extend(
                    spacing[
                        (spacing >= 2) &
                        (spacing <= MAX_LAYER_SPACING)
                    ].tolist()
                )

        if not gaps:
            raise RuntimeError("Not enough visible paper edges to estimate a count.")

        gaps_array = np.asarray(gaps, dtype=float)
        integer_gaps = np.rint(gaps_array).astype(int)
        histogram = np.bincount(
            integer_gaps,
            minlength=MAX_LAYER_SPACING + 1,
        )
        pair_scores = [
            histogram[gap] + histogram[gap + 1]
            for gap in range(2, MAX_LAYER_SPACING)
        ]
        best_gap = 2 + int(np.argmax(pair_scores))
        selected = gaps_array[
            (integer_gaps == best_gap) |
            (integer_gaps == best_gap + 1)
        ]

        pitch = float(np.mean(selected))
        evidence_fraction = columns_with_evidence / N_PROFILES
        pair_fraction = len(selected) / len(gaps_array)
        evidence = float(np.clip(
            0.55 * evidence_fraction + 0.45 * pair_fraction,
            0.0,
            1.0,
        ))
        return pitch, evidence

    def analyze_image(self, image_bytes: bytes) -> StackCountResult:
        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("The uploaded file is not a readable image.")

        if image.shape[1] != ANALYSIS_WIDTH:
            scale = ANALYSIS_WIDTH / image.shape[1]
            image = cv2.resize(
                image,
                (ANALYSIS_WIDTH, int(round(image.shape[0] * scale))),
                interpolation=(cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC),
            )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        roi_top, roi_bottom = self._find_stack_roi(gray)
        roi = gray[roi_top:roi_bottom]
        band_top, band_bottom, gradient = self._detect_layer_band(roi)
        pitch, evidence = self._estimate_pitch(
            gradient,
            band_top,
            band_bottom,
        )

        stack_depth = float(band_bottom - band_top)
        count = max(1, int(round(stack_depth / pitch)))
        return StackCountResult(
            count=count,
            stack_depth_px=stack_depth,
            layer_pitch_px=pitch,
            evidence=evidence,
            analysis_width=ANALYSIS_WIDTH,
        )


stack_counter_service = StackCounterService()
