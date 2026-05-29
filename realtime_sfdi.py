from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw, ImageEnhance

import external_functions


SFDI_COLORS = ("green", "red")
SFDI_PHASES = tuple(range(6))
RAW_CAMERA_MAX = 1023.0
CAPTURE_CROP = (100, 900, 0, 800)  # upper, lower, left, right
ROI_FRACTION = (0.2, 0.75, 0.35, 0.7)  # top, bottom, left, right
PATTERN_FREQUENCY_TO_SPATIAL_SCALE = 2 * np.pi / 160.0
REFERENCE_ENV_VAR = "SFDI_REFERENCE_ID"
REFERENCE_PARAM_FILES = ("reference_params.json", "ref_params.json")

DEFAULT_REF_MUA = {"green": 0.5, "red": 0.5}
DEFAULT_REF_MUS_PRIME = {"green": 25.0, "red": 25.0}

_PATTERN_RE = re.compile(r"^(?P<freq>\d+)_(?P<phase>\d+)$")


@dataclass(frozen=True)
class RealtimePattern:
    color: str
    frequency: int
    phase: int
    key: tuple[str, str]
    path: Path
    factor: float

    @property
    def save_name(self) -> str:
        return f"{self.frequency}_{self.phase}"


@dataclass
class RealtimeSFDIResult:
    frequency: int | None = None
    saved_files: list[Path] = field(default_factory=list)
    metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    processed: bool = False
    message: str = ""


def select_realtime_patterns(patterns: Mapping[Any, tuple[str, float]]) -> list[RealtimePattern]:
    """Pick the highest frequency that has six phases for green and red."""
    indexed: dict[int, dict[str, dict[int, RealtimePattern]]] = {}

    for key, value in patterns.items():
        if not isinstance(key, tuple) or len(key) != 2:
            continue

        color, stem = key
        if color not in SFDI_COLORS:
            continue

        match = _PATTERN_RE.match(str(stem))
        if match is None:
            continue

        frequency = int(match.group("freq"))
        phase = int(match.group("phase"))
        if phase not in SFDI_PHASES:
            continue

        path, factor = value
        indexed.setdefault(frequency, {}).setdefault(color, {})[phase] = RealtimePattern(
            color=color,
            frequency=frequency,
            phase=phase,
            key=key,
            path=Path(path),
            factor=float(factor),
        )

    complete_frequencies = [
        frequency
        for frequency, by_color in indexed.items()
        if all(
            color in by_color and all(phase in by_color[color] for phase in SFDI_PHASES)
            for color in SFDI_COLORS
        )
    ]

    if not complete_frequencies:
        raise ValueError("No complete green/red pattern set with phases 0..5 was found")

    selected_frequency = max(complete_frequencies)
    return [
        indexed[selected_frequency][color][phase]
        for color in SFDI_COLORS
        for phase in SFDI_PHASES
    ]


def run_realtime_sfdi_cycle(app: Any) -> RealtimeSFDIResult:
    """Capture one realtime SFDI cycle and process it if a reference stack exists."""
    result = RealtimeSFDIResult()

    try:
        sequence = select_realtime_patterns(app.patterns)
    except ValueError as exc:
        message = f"SFDI realtime skipped: {exc}"
        _log(app, message)
        result.message = message
        return result

    result.frequency = sequence[0].frequency

    if not getattr(app.thor_camera, "cam", None):
        app.log_frame.insert_log("Exception")
        result.message = "ThorCam is closed"
        return result

    if not getattr(app, "current_directory", None):
        app.renew_current_directory("SFDI")

    _prepare_measurement_directory(app, sequence)

    frame_map: dict[tuple[str, int], np.ndarray] = {}

    try:
        app.thor_camera.cam.set_exposure(app.exposure)
        app.thor_camera.cam.start_acquisition(
            auto_start=False,
            nframes=1,
            frames_per_trigger=1,
        )

        app.flag = True
        external_functions.change_button_state(app, block=True)
        _log(app, f"SFDI realtime capture started: freq {result.frequency}, green/red, 6 phases")

        for pattern in sequence:
            if not app.flag:
                result.message = "SFDI realtime stopped by user"
                _log(app, result.message)
                break

            _show_projector_pattern(app, pattern)
            app.after(30)

            raw_img = app.thor_camera.get_frame()
            if raw_img is None:
                result.message = f"SFDI realtime missing frame: {pattern.color} {pattern.save_name}"
                _log(app, result.message)
                continue

            cropped_array, _ = _crop_frame(raw_img, CAPTURE_CROP)
            roi_array = _apply_roi(cropped_array, ROI_FRACTION)
            roi_image = PILImage.fromarray(roi_array)
            frame_map[(pattern.color, pattern.phase)] = roi_array

            file_path = Path(app.current_directory) / pattern.color / f"{pattern.save_name}.TIF"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            roi_image.save(file_path)
            result.saved_files.append(file_path)

            _show_thor_preview(app, raw_img)
            app.after(15)

        app.projection_window.set_background("black")

    except Exception as exc:  # GUI capture should unblock controls even on device errors.
        result.message = f"SFDI realtime capture failed: {exc}"
        _log(app, result.message)
        return result

    finally:
        external_functions.change_button_state(app, block=False)
        if result.saved_files and hasattr(app, "save_factors_snapshot"):
            app.save_factors_snapshot()

    if len(frame_map) != len(sequence):
        if not result.message:
            result.message = "SFDI realtime skipped processing: incomplete capture"
            _log(app, result.message)
        return result

    metrics, message = process_realtime_frames(
        frame_map=frame_map,
        measurement_dir=Path(app.current_directory),
        frequency=result.frequency,
    )

    result.metrics = metrics
    result.message = message
    result.processed = bool(metrics)

    if metrics:
        app.update_sfdi_plots(metrics)
        _log(app, f"SFDI realtime processed: {message}")
    else:
        _log(app, f"SFDI realtime processing skipped: {message}")

    return result


def process_realtime_frames(
    frame_map: Mapping[tuple[str, int], np.ndarray],
    measurement_dir: Path,
    frequency: int,
) -> tuple[dict[str, dict[str, float]], str]:
    reference_dir, expected_reference = _find_reference_directory(measurement_dir, frequency)
    if reference_dir is None:
        return {}, f"reference not found; expected {expected_reference}"

    try:
        _ensure_sfdi_fitter_on_path()
        from sfdi_fitter.data import SFDIStack, StackAxis
        from sfdi_fitter.demodulation import ClassicalDemodulator
        from sfdi_fitter.fitter import NNMCMLmodel
        from sfdi_fitter.reflectance import ReflectanceCalculator
        from sfdi_fitter.transformers import MeanSmoother, StackSqueezer
    except Exception as exc:
        return {}, f"pipeline dependencies unavailable: {exc}"

    try:
        spatial_frequency = _pattern_frequency_to_spatial(frequency)
        raw_stack = _build_stack(SFDIStack, StackAxis, frame_map, spatial_frequency)
        expected_frame_shape = _first_frame_shape(frame_map)
        reference_map = _load_reference_frame_map(reference_dir, frequency, expected_frame_shape)
        reference_stack = _build_stack(SFDIStack, StackAxis, reference_map, spatial_frequency)
    except Exception as exc:
        return {}, f"reference/raw stack error: {exc}"

    try:
        demodulator = ClassicalDemodulator(add_dc=True)
        smoother = MeanSmoother(kernel_size=9)
        squeezer = StackSqueezer(inplace=False)

        raw_demod = squeezer.process(smoother.process(demodulator.process(raw_stack)))
        reference_demod = squeezer.process(smoother.process(demodulator.process(reference_stack)))

        expected_frequencies = [0, spatial_frequency]
        if list(raw_demod.spatial_frequencies) != expected_frequencies:
            return {}, f"unexpected demodulated frequencies: {raw_demod.spatial_frequencies}"

        ref_mua, ref_mus_prime, refractive_index = _load_reference_params(reference_dir)
        model = NNMCMLmodel(multiple_frequencies_strategy="max_freq")

        reflectance = ReflectanceCalculator(
            reference_stack=reference_demod,
            reflectance_model=model,
            ref_mua=ref_mua,
            ref_mus_prime=ref_mus_prime,
            refractive_index=refractive_index,
        ).process(raw_demod)

        metrics, fit_diagnostics = _fit_reflectance_metrics(reflectance, model)

    except Exception as exc:
        return {}, f"pipeline error: {exc}"

    return metrics, (
        f"reference {reference_dir.name}, pattern freq {frequency}, "
        f"spatial freq {spatial_frequency:.4f}, {fit_diagnostics}"
    )


def _prepare_measurement_directory(app: Any, sequence: list[RealtimePattern]) -> None:
    Path(app.current_directory).mkdir(parents=True, exist_ok=True)
    for color in SFDI_COLORS:
        (Path(app.current_directory) / color).mkdir(parents=True, exist_ok=True)

    while any(
        (Path(app.current_directory) / pattern.color / f"{pattern.save_name}.TIF").exists()
        for pattern in sequence
    ):
        app.patient_entry.configure(state="normal")
        app.patient_entry.insert("end", "_1")
        external_functions.create_patient_directory(app.patient_entry.get(), modes=["SFDI"])
        app.renew_current_directory("SFDI")
        Path(app.current_directory).mkdir(parents=True, exist_ok=True)
        for color in SFDI_COLORS:
            (Path(app.current_directory) / color).mkdir(parents=True, exist_ok=True)


def _show_projector_pattern(app: Any, pattern: RealtimePattern) -> None:
    import customtkinter

    factor = _current_pattern_factor(app, pattern.color, pattern.factor)
    with PILImage.open(pattern.path) as im:
        enhanced = ImageEnhance.Brightness(im).enhance(factor)
        image = customtkinter.CTkImage(enhanced, size=(enhanced.width, enhanced.height))

    app._last_sfdi_projector_image = image
    app.projection_window.pattern_window.configure(image=image)
    app.projection_window.update()


def _show_thor_preview(app: Any, raw_img: np.ndarray) -> None:
    import customtkinter

    preview = (raw_img.T.astype("float")[::2, ::2] * 255 // RAW_CAMERA_MAX).astype("uint8")
    preview_image = PILImage.fromarray(preview).transpose(PILImage.FLIP_LEFT_RIGHT)

    draw = ImageDraw.Draw(preview_image)
    draw.rectangle(_roi_rect_on_preview(raw_img), fill=None, outline=255)

    tk_image = customtkinter.CTkImage(
        preview_image,
        size=(np.shape(preview_image)[1], np.shape(preview_image)[0]),
    )
    app._last_sfdi_preview_image = tk_image
    app.pattern_copy.configure(image=tk_image)
    app.pattern_copy.update()


def _crop_frame(frame: np.ndarray, crop: tuple[int, int, int, int]) -> tuple[np.ndarray, PILImage.Image]:
    upper, lower, left, right = _clamp_crop(crop, frame.shape)
    image = PILImage.fromarray(frame)
    cropped = image.crop((left, upper, right, lower))
    return np.asarray(cropped), cropped


def _clamp_crop(crop: tuple[int, int, int, int], shape: tuple[int, ...]) -> tuple[int, int, int, int]:
    height, width = shape[:2]
    upper, lower, left, right = crop
    upper = max(0, min(int(upper), height))
    lower = max(upper + 1, min(int(lower), height))
    left = max(0, min(int(left), width))
    right = max(left + 1, min(int(right), width))
    return upper, lower, left, right


def _current_pattern_factor(app: Any, color: str, default: float) -> float:
    color_index = {"green": 0, "blue": 1, "red": 2}
    idx = color_index.get(color)
    if idx is None:
        return default
    try:
        return float(app.pattern_factors[idx])
    except (AttributeError, IndexError, TypeError, ValueError):
        return default


def _build_stack(sfdi_stack_cls: Any, stack_axis_cls: Any, frame_map: Mapping[tuple[str, int], np.ndarray], spatial_frequency: float) -> Any:
    data = np.stack(
        [
            np.stack([frame_map[(color, phase)] for phase in SFDI_PHASES], axis=0)
            for color in SFDI_COLORS
        ],
        axis=0,
    ).astype(np.float32)

    data = np.clip(data, 0, RAW_CAMERA_MAX) / RAW_CAMERA_MAX
    data = data[:, np.newaxis, :, :, :]
    return sfdi_stack_cls(
        data=data,
        axis_names=[
            stack_axis_cls.WAVELENGTH,
            stack_axis_cls.FREQUENCY,
            stack_axis_cls.PHASE,
            stack_axis_cls.X,
            stack_axis_cls.Y,
        ],
        spatial_frequencies=[spatial_frequency],
        wavelengths=list(SFDI_COLORS),
    )


def _pattern_frequency_to_spatial(frequency: int) -> float:
    return float(frequency) * PATTERN_FREQUENCY_TO_SPATIAL_SCALE


def _apply_roi(data: np.ndarray, roi_fraction: tuple[float, float, float, float]) -> np.ndarray:
    top_f, bottom_f, left_f, right_f = roi_fraction
    height = data.shape[-2]
    width = data.shape[-1]
    top = int(round(height * top_f))
    bottom = int(round(height * bottom_f))
    left = int(round(width * left_f))
    right = int(round(width * right_f))

    top = max(0, min(top, height - 1))
    bottom = max(top + 1, min(bottom, height))
    left = max(0, min(left, width - 1))
    right = max(left + 1, min(right, width))
    return data[..., top:bottom, left:right]


def _roi_shape() -> tuple[int, int]:
    crop_upper, crop_lower, crop_left, crop_right = CAPTURE_CROP
    crop_h = crop_lower - crop_upper
    crop_w = crop_right - crop_left
    top_f, bottom_f, left_f, right_f = ROI_FRACTION
    h = int(round(crop_h * bottom_f)) - int(round(crop_h * top_f))
    w = int(round(crop_w * right_f)) - int(round(crop_w * left_f))
    return h, w


def _roi_rect_on_preview(raw_img: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]]:
    """Rectangle coordinates (x0,y0),(x1,y1) for the ROI in the preview image space."""
    raw_h = raw_img.shape[0]
    crop_upper, crop_lower, crop_left, crop_right = CAPTURE_CROP
    crop_h = crop_lower - crop_upper
    crop_w = crop_right - crop_left
    top_f, bottom_f, left_f, right_f = ROI_FRACTION

    r0 = crop_upper + int(round(crop_h * top_f))
    r1 = crop_upper + int(round(crop_h * bottom_f))
    c0 = crop_left + int(round(crop_w * left_f))
    c1 = crop_left + int(round(crop_w * right_f))

    # Preview: raw_img.T[::2,::2] → PIL image → FLIP_LEFT_RIGHT
    # PIL pixel (px, py) maps to raw_img[raw_h - 2 - 2*px, 2*py]
    preview_w = raw_h // 2
    x0 = preview_w - 1 - r1 // 2
    x1 = preview_w - 1 - r0 // 2
    y0 = c0 // 2
    y1 = c1 // 2
    return (x0, y0), (x1, y1)


def _find_reference_directory(measurement_dir: Path, frequency: int) -> tuple[Path | None, Path]:
    date_dir = measurement_dir.parent
    env_reference = os.getenv(REFERENCE_ENV_VAR)
    reference_ids = [env_reference] if env_reference else []
    reference_ids.extend(["reference", "ref", "Reference", "REF"])

    candidates = [date_dir / reference_id for reference_id in reference_ids if reference_id]
    if date_dir.exists():
        candidates.extend(
            path
            for path in sorted(date_dir.iterdir())
            if path.is_dir()
            and path != measurement_dir
            and path.name.lower().startswith(("ref", "reference"))
        )

    for candidate in candidates:
        if _has_reference_frames(candidate, frequency):
            return candidate, candidates[0]

    expected = candidates[0] if candidates else date_dir / "reference"
    return None, expected


def _has_reference_frames(reference_dir: Path, frequency: int) -> bool:
    return all(
        (reference_dir / color / f"{frequency}_{phase}.TIF").exists()
        for color in SFDI_COLORS
        for phase in SFDI_PHASES
    )


def _first_frame_shape(frame_map: Mapping[tuple[str, int], np.ndarray]) -> tuple[int, int]:
    first_frame = next(iter(frame_map.values()))
    return first_frame.shape[:2]


def _load_reference_frame_map(
    reference_dir: Path,
    frequency: int,
    expected_shape: tuple[int, int],
) -> dict[tuple[str, int], np.ndarray]:
    frame_map: dict[tuple[str, int], np.ndarray] = {}
    for color in SFDI_COLORS:
        for phase in SFDI_PHASES:
            frame_path = reference_dir / color / f"{frequency}_{phase}.TIF"
            with PILImage.open(frame_path) as image:
                arr = np.asarray(image)

            if arr.shape[:2] != expected_shape:
                roi_arr = _apply_roi(arr, ROI_FRACTION)
                if roi_arr.shape[:2] == expected_shape:
                    arr = roi_arr

            frame_map[(color, phase)] = arr
    return frame_map


def _load_reference_params(reference_dir: Path) -> tuple[dict[str, float], dict[str, float], float]:
    params = {}
    for file_name in REFERENCE_PARAM_FILES:
        params_path = reference_dir / file_name
        if params_path.exists():
            with open(params_path, "r", encoding="utf-8") as f:
                params = json.load(f)
            break

    ref_mua = _coerce_color_params(params.get("ref_mua"), DEFAULT_REF_MUA)
    ref_mus_prime = _coerce_color_params(params.get("ref_mus_prime"), DEFAULT_REF_MUS_PRIME)
    refractive_index = float(params.get("refractive_index", 1.37))
    return ref_mua, ref_mus_prime, refractive_index


def _coerce_color_params(value: Any, default: dict[str, float]) -> dict[str, float]:
    if value is None:
        value = default

    if isinstance(value, Mapping):
        if isinstance(default, Mapping):
            result = {color: float(default[color]) for color in SFDI_COLORS if color in default}
        else:
            result = {color: float(default) for color in SFDI_COLORS}

        for color in SFDI_COLORS:
            if color in value:
                result[color] = float(value[color])
        return result

    scalar = float(value)
    return {color: scalar for color in SFDI_COLORS}


def _fit_reflectance_metrics(reflectance_stack: Any, model: Any) -> tuple[dict[str, dict[str, float]], str]:
    metrics: dict[str, dict[str, float]] = {}
    diagnostics: list[str] = []

    for color_index, color in enumerate(reflectance_stack.wavelengths or SFDI_COLORS):
        reflectance_data = reflectance_stack.data[color_index]
        fit_mask = np.isfinite(reflectance_data).all(axis=0)
        fit_mask &= (reflectance_data > 0).all(axis=0)

        valid_pixels = int(fit_mask.sum())
        diagnostics.append(f"{color}: {valid_pixels} fit px")

        if valid_pixels == 0:
            continue

        fitted_data = model.fit(
            reflectance_stack.spatial_frequencies,
            reflectance_data,
            fit_mask=fit_mask,
        )

        color_metrics: dict[str, float] = {}
        for output_name in ("mua", "mus"):
            if output_name not in fitted_data:
                continue

            values = fitted_data[output_name].astype(float)
            values[values <= 0] = np.nan
            finite_values = values[np.isfinite(values)]
            if finite_values.size:
                color_metrics[output_name] = float(np.nanmedian(finite_values))

        if color_metrics:
            metrics[color] = color_metrics

    metric_keys = {
        color: sorted(color_metrics.keys())
        for color, color_metrics in metrics.items()
    }
    diagnostics.append(f"metrics {metric_keys}")
    return metrics, "; ".join(diagnostics)


def _ensure_sfdi_fitter_on_path() -> None:
    pipeline_root = Path(__file__).resolve().parent / "pipeline"
    if pipeline_root.exists() and str(pipeline_root) not in sys.path:
        sys.path.insert(0, str(pipeline_root))


def _log(app: Any, message: str) -> None:
    if hasattr(app, "log_frame"):
        app.log_frame.insert_log("SFDIStatus", message)
