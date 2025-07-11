#!/usr/bin/env python3
"""
USAF 1951 Resolution Target Analyzer

A comprehensive tool for analyzing USAF 1951 resolution targets in microscopy and imaging systems.
"""

import hashlib
import io
import logging
import os
import re  # Add import for regex
import tempfile
import time
from typing import Any

import cv2
import matplotlib.patheffects as PathEffects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit_nested_layout  # noqa: F401
import tifffile
from PIL import Image, ImageDraw
from skimage import exposure, img_as_ubyte
from streamlit_image_coordinates import streamlit_image_coordinates

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# --- Constants ---
# File Paths
DEFAULT_IMAGE_PATH = os.path.expanduser(
    "~/Library/CloudStorage/Box-Box/FOIL/Aaron/2025-05-12/airforcetarget_images/AF_2_2_00001.png"
)

# ROI Colors
ROI_COLORS = [
    "#00FF00",
    "#FF00FF",
    "#00FFFF",
    "#FFFF00",
    "#FF8000",
    "#0080FF",
    "#8000FF",
    "#FF0080",
]
INVALID_ROI_COLOR = "#FF0000"  # Red for invalid ROIs

# Session State Prefixes
SESSION_STATE_PREFIXES = [
    "group_",
    "element_",
    "analyzed_roi_",
    "analysis_results_",
    "last_group_",
    "last_element_",
    "coordinates_",
    "image_path_",
    "image_name_",
    "roi_valid_",
]

# UI Defaults
DEFAULT_GROUP = 2
DEFAULT_ELEMENT = 2

# Welcome screen constants
WELCOME_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/d/d6/1951usaf_test_target.jpg"
)
WELCOME_IMAGE_CAPTION = "Example USAF 1951 Target"

# --- Utility Functions ---


def _get_effective_bit_depth(image: np.ndarray) -> int:
    """
    Estimate the effective bit depth of an image by examining its maximum value.
    For example, a 16-bit image with max value 4095 is likely 12-bit digitized.
    """
    if not hasattr(image, "dtype"):
        return 8
    if image.dtype == np.uint8:
        return 8
    max_val = np.max(image)
    return next(
        (
            bits
            for bits in (8, 10, 12, 14, 16, 32)
            if max_val <= (1 << bits) - 1
        ),
        16,
    )


def parse_filename_for_defaults(filename: str) -> dict[str, Any]:
    """
    Parse filename to extract magnification and USAF target values.

    Expected pattern examples:
    - Zoom23_AFT74_00001.tif - Zoom=23.0, AFT=7.4 (Group 7, Element 4)
    - Zoom7.6_AFT56_00001.tif - Zoom=7.6, AFT=5.6 (Group 5, Element 6)

    Args:
        filename: The filename to parse

    Returns:
        Dictionary with 'magnification', 'group', and 'element' if found
    """
    result = {}

    try:
        # Extract just the filename if a full path is given
        base_name = os.path.basename(filename)

        if zoom_match := re.search(
            r"Zoom(\d+(?:\.\d+)?)", base_name, re.IGNORECASE
        ):
            try:
                magnification = float(zoom_match[1])
                result["magnification"] = magnification
            except (ValueError, TypeError):
                pass

        if aft_match := re.search(r"AFT(\d)(\d)", base_name, re.IGNORECASE):
            try:
                group = int(aft_match[1])
                element = int(aft_match[2])
                result["group"] = group
                result["element"] = element
            except (ValueError, TypeError, IndexError):
                pass
    except Exception as e:
        logger.warning(f"Error parsing filename for defaults: {e}")

    return result


def rotate_image(image: np.ndarray, rotation_count: int) -> np.ndarray:
    """
    Rotate an image by 90-degree increments.

    Args:
        image: The image to rotate
        rotation_count: Number of 90-degree rotations (0-3)

    Returns:
        Rotated image
    """
    if image is None:
        return None

    try:
        # Normalize rotation count to 0-3
        rotation_count %= 4

        return image if rotation_count == 0 else np.rot90(image, k=rotation_count)
    except Exception as e:
        logger.error(f"Error rotating image: {e}")
        return image  # Return original image on error


def normalize_to_uint8(
    image,
    autoscale=True,
    invert=False,
    normalize=False,
    saturated_pixels=0.5,
    equalize_histogram=False,
):
    """
    Normalize image to uint8 (0-255) range with ImageJ-like contrast enhancement options.
    """
    if image is None or image.size == 0:
        return np.zeros((1, 1), dtype=np.uint8)

    image_copy = _prepare_image_copy(image)
    is_multichannel = image_copy.ndim > 2 and image_copy.shape[-1] <= 4

    if equalize_histogram:
        image_copy = _apply_histogram_equalization(image_copy, is_multichannel)
    elif image_copy.dtype != np.uint8 or normalize:
        image_copy = _apply_normalization_strategies(
            image_copy, is_multichannel, autoscale, normalize, saturated_pixels
        )

    if invert:
        image_copy = 255 - image_copy

    return image_copy


def _prepare_image_copy(image: np.ndarray) -> np.ndarray:
    """Prepare a copy of the image, normalizing float images to 0-1 range."""
    image_copy = image.copy()
    if np.issubdtype(image_copy.dtype, np.floating) and (np.max(image_copy) > 1.0 or np.min(image_copy) < -1.0):
        min_val, max_val = np.min(image_copy), np.max(image_copy)
        if max_val > min_val:
            image_copy = (image_copy - min_val) / (max_val - min_val)
        else:
            image_copy = np.zeros_like(image_copy)
    return image_copy


def _apply_histogram_equalization(
    image: np.ndarray, is_multichannel: bool
) -> np.ndarray:
    """Apply histogram equalization to the image."""
    if is_multichannel:
        result = np.zeros_like(image, dtype=np.uint8)
        for c in range(image.shape[-1]):
            channel = image[..., c]
            try:
                equalized = exposure.equalize_hist(channel)
                result[..., c] = img_as_ubyte(equalized)
            except Exception as e:
                logger.warning(f"Error equalizing histogram for channel {c}: {e}")
                result[..., c] = img_as_ubyte(channel)
        return result
    else:
        try:
            equalized = exposure.equalize_hist(image)
            return img_as_ubyte(equalized)
        except Exception as e:
            logger.warning(f"Error equalizing histogram: {e}")
            return image


def _apply_normalization_strategies(
    image: np.ndarray,
    is_multichannel: bool,
    autoscale: bool,
    normalize: bool,
    saturated_pixels: float,
) -> np.ndarray:
    """Apply different normalization strategies based on parameters."""
    bit_depth = _get_effective_bit_depth(image)

    if autoscale:
        return _normalize_autoscale(image, is_multichannel, saturated_pixels)
    elif normalize:
        return _normalize_full_range(image, is_multichannel)
    else:
        return _normalize_by_bit_depth(image, is_multichannel, bit_depth)


def _normalize_channel_autoscale(
    channel: np.ndarray, saturated_pixels: float
) -> np.ndarray:
    """Autoscale a single channel using percentile-based contrast stretching."""
    try:
        p_low, p_high = saturated_pixels / 2, 100 - saturated_pixels / 2
        p_min, p_max = np.percentile(channel, (p_low, p_high))
        if p_max > p_min:
            rescaled = exposure.rescale_intensity(
                channel, in_range=(p_min, p_max), out_range=(0, 255)
            )
            return img_as_ubyte(rescaled)
        return np.zeros_like(channel, dtype=np.uint8)
    except Exception as e:
        logger.warning(f"Error autoscaling channel: {e}")
        return _normalize_channel_fallback(channel)


def _normalize_autoscale(
    image: np.ndarray, is_multichannel: bool, saturated_pixels: float
) -> np.ndarray:
    """Autoscale image using percentile-based contrast stretching."""
    if not is_multichannel:
        return _normalize_channel_autoscale(image, saturated_pixels)
    result = np.zeros_like(image, dtype=np.uint8)
    for c in range(image.shape[-1]):
        result[..., c] = _normalize_channel_autoscale(
            image[..., c], saturated_pixels
        )
    return result


def _normalize_channel_full_range(channel: np.ndarray) -> np.ndarray:
    """Normalize a single channel to the full 0-255 range."""
    try:
        min_val, max_val = np.min(channel), np.max(channel)
        if max_val > min_val:
            normalized = exposure.rescale_intensity(
                channel, in_range=(min_val, max_val), out_range=(0, 255)
            )
            return img_as_ubyte(normalized)
        return np.zeros_like(channel, dtype=np.uint8)
    except Exception as e:
        logger.warning(f"Error normalizing channel to full range: {e}")
        return np.zeros_like(channel, dtype=np.uint8)


def _normalize_full_range(image: np.ndarray, is_multichannel: bool) -> np.ndarray:
    """Normalize image to the full 0-255 range."""
    if not is_multichannel:
        return _normalize_channel_full_range(image)
    result = np.zeros_like(image, dtype=np.uint8)
    for c in range(image.shape[-1]):
        result[..., c] = _normalize_channel_full_range(image[..., c])
    return result


def _normalize_channel_by_bit_depth(channel: np.ndarray, bit_depth: int) -> np.ndarray:
    """Scale a single channel to its digitization bit depth."""
    max_val = (1 << bit_depth) - 1
    try:
        rescaled = exposure.rescale_intensity(
            channel, in_range=(0, max_val), out_range=(0, 255)
        )
        return img_as_ubyte(rescaled)
    except Exception as e:
        logger.warning(f"Error scaling channel by bit depth: {e}")
        return np.clip((channel / max_val * 255), 0, 255).astype(np.uint8)


def _normalize_by_bit_depth(
    image: np.ndarray, is_multichannel: bool, bit_depth: int
) -> np.ndarray:
    """Scale image to its digitization bit depth."""
    if not is_multichannel:
        return _normalize_channel_by_bit_depth(image, bit_depth)
    result = np.zeros_like(image, dtype=np.uint8)
    for c in range(image.shape[-1]):
        result[..., c] = _normalize_channel_by_bit_depth(image[..., c], bit_depth)
    return result


def _normalize_channel_fallback(channel: np.ndarray) -> np.ndarray:
    """Fallback simple normalization for a channel."""
    min_val, max_val = np.min(channel), np.max(channel)
    if max_val > min_val:
        return np.clip(
            ((channel - min_val) / (max_val - min_val) * 255), 0, 255
        ).astype(np.uint8)
    return np.zeros_like(channel, dtype=np.uint8)


def get_unique_id_for_image(image_file) -> str:
    try:
        if isinstance(image_file, str):
            filename = os.path.basename(image_file)
        else:
            filename = (
                image_file.name if hasattr(image_file, "name") else id(image_file)
            )
        short_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"img_{short_hash}"
    except Exception as e:
        logger.error(f"Error generating unique ID: {e}")
        return f"img_{int(time.time() * 1000)}"


def load_default_image():
    return DEFAULT_IMAGE_PATH if os.path.exists(DEFAULT_IMAGE_PATH) else None


def process_uploaded_file(uploaded_file) -> tuple[np.ndarray | None, str | None]:
    if uploaded_file is None:
        return None, None

    unique_id = get_unique_id_for_image(uploaded_file)
    settings = _get_image_processing_settings(unique_id)

    try:
        if isinstance(uploaded_file, str):
            return _process_image_from_path(uploaded_file, unique_id, settings)
        else:
            return _process_image_from_buffer(uploaded_file, unique_id, settings)
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        st.error(f"Error processing file: {e}")
        return None, None


def _get_image_processing_settings(unique_id: str) -> dict:
    """Get image processing settings from session state."""
    return {
        "autoscale": st.session_state.get(f"autoscale_{unique_id}", True),
        "invert": st.session_state.get(f"invert_{unique_id}", False),
        "normalize": st.session_state.get(f"normalize_{unique_id}", False),
        "saturated_pixels": st.session_state.get(f"saturated_pixels_{unique_id}", 0.5),
        "equalize_histogram": st.session_state.get(
            f"equalize_histogram_{unique_id}", False
        ),
    }


def _load_image_array(image_path: str) -> np.ndarray | None:
    """Load image from path into a numpy array."""
    ext = os.path.splitext(image_path)[1].lower()
    if ext in [".tif", ".tiff"]:
        try:
            with tifffile.TiffFile(image_path) as tif:
                if len(tif.pages) == 0:
                    st.error(f"TIFF file has no pages: {image_path}")
                    return None
                return tif.pages[0].asarray()
        except Exception as e:
            logger.error(f"Failed to load TIFF: {image_path} ({e})")
            st.error(f"Failed to load TIFF: {image_path} ({e})")
            return None
    else:
        try:
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if image is None:
                logger.info(f"OpenCV failed to load image, trying PIL: {image_path}")
                pil_image = Image.open(image_path)
                image = np.array(pil_image)
            return image
        except Exception as e:
            logger.error(f"Error loading image: {image_path} ({e})")
            st.error(f"Error loading image: {image_path} ({e})")
            return None


def _normalize_and_prepare_image(
    image: np.ndarray, unique_id: str, settings: dict
) -> np.ndarray | None:
    """Normalize the image and prepare it for display."""
    logger.info(
        f"Loaded image: shape={image.shape}, dtype={image.dtype}, range={np.min(image)}-{np.max(image)}"
    )
    if len(image.shape) == 3 and image.shape[2] == 3:  # BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    bit_depth = _get_effective_bit_depth(image)
    st.session_state[f"bit_depth_{unique_id}"] = bit_depth

    try:
        image = normalize_to_uint8(
            image,
            autoscale=settings["autoscale"],
            invert=settings["invert"],
            normalize=settings["normalize"],
            saturated_pixels=settings["saturated_pixels"],
            equalize_histogram=settings["equalize_histogram"],
        )
        if image.ndim == 2:  # Grayscale to RGB
            image = np.stack([image] * 3, axis=-1)
        elif image.shape[-1] == 1:  # Single channel to RGB
            image = np.repeat(image, 3, axis=-1)
        return image
    except Exception as e:
        logger.error(f"Error normalizing image: {e}")
        st.error(f"Error normalizing image: {e}")
        return None


def _process_image_from_path(
    image_path: str, unique_id: str, settings: dict
) -> tuple[np.ndarray | None, str | None]:
    """Process an image loaded from a file path."""
    if not os.path.exists(image_path):
        st.error(f"File not found: {image_path}")
        return None, None

    image_array = _load_image_array(image_path)
    if image_array is None:
        return None, None

    processed_image = _normalize_and_prepare_image(image_array, unique_id, settings)
    if processed_image is None:
        return None, None

    return processed_image, image_path


def _process_image_from_buffer(
    uploaded_file, unique_id: str, settings: dict
) -> tuple[np.ndarray | None, str | None]:
    """Process an image loaded from an uploaded file buffer."""
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
        ) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name

        image_array = _load_image_array(temp_path)
        if image_array is None:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None, None

        processed_image = _normalize_and_prepare_image(image_array, unique_id, settings)
        if processed_image is None:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None, None

        return processed_image, temp_path
    except Exception as e:
        logger.error(f"Error processing uploaded file buffer: {e}")
        st.error(f"Error processing uploaded file buffer: {e}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return None, None


def extract_roi_image(
    image, roi_coordinates: tuple[int, int, int, int], rotation: int = 0
) -> np.ndarray | None:
    try:
        if roi_coordinates is None:
            return None
        x, y, width, height = roi_coordinates
        if hasattr(image, "select_roi"):
            roi = image.select_roi(roi_coordinates)
        elif image is not None and x >= 0 and y >= 0 and width > 0 and height > 0:
            roi = image[y : y + height, x : x + width]
        else:
            return None

        # Apply rotation if specified
        if rotation > 0 and roi is not None:
            roi = rotate_image(roi, rotation)

        return roi
    except Exception as e:
        st.error(f"Error extracting ROI: {e}")
        return None


def initialize_session_state():
    if "usaf_target" not in st.session_state:
        st.session_state.usaf_target = USAFTarget()
    if "uploaded_files_list" not in st.session_state:
        st.session_state.uploaded_files_list = []
    if "default_image_added" not in st.session_state:
        st.session_state.default_image_added = False
    if "image_index_to_id" not in st.session_state:
        st.session_state.image_index_to_id = {}

    # Handle cleanup of rotation and sensitivity session state when images are removed
    if "rotation_state_cleanup" not in st.session_state:
        st.session_state.rotation_state_cleanup = set()

    current_image_ids = {
        get_unique_id_for_image(file) for file in st.session_state.uploaded_files_list
    }
    # Store the current set of image IDs for next cleanup check
    old_image_ids = st.session_state.rotation_state_cleanup
    for image_id in old_image_ids:
        if image_id not in current_image_ids:
            # Remove session state variables for this image
            prefixes_to_clean = [
                f"rotation_{image_id}",
                f"last_rotation_{image_id}",
                f"sensitivity_{image_id}",
                f"last_sensitivity_{image_id}",
                f"min_distance_{image_id}",
                f"last_min_distance_{image_id}",
                f"roi_rotation_{image_id}",  # Add ROI rotation state cleanup
                # Add last ROI rotation state cleanup
                f"last_roi_rotation_{image_id}",
            ]
            for prefix in prefixes_to_clean:
                if prefix in st.session_state:
                    del st.session_state[prefix]

    # Update the set of image IDs that need cleanup on next check
    st.session_state.rotation_state_cleanup = current_image_ids


def get_image_session_keys(idx, image_file=None):
    if image_file is not None:
        unique_id = get_unique_id_for_image(image_file)
        st.session_state.image_index_to_id[idx] = unique_id
    else:
        unique_id = st.session_state.image_index_to_id.get(idx, f"idx_{idx}")
    return {
        "group": f"group_{unique_id}",
        "element": f"element_{unique_id}",
        "analyzed_roi": f"analyzed_roi_{unique_id}",
        "analysis_results": f"analysis_results_{unique_id}",
        "last_group": f"last_group_{unique_id}",
        "last_element": f"last_element_{unique_id}",
        "coordinates": f"coordinates_{unique_id}",
        "image_path": f"image_path_{unique_id}",
        "image_name": f"image_name_{unique_id}",
        "roi_valid": f"roi_valid_{unique_id}",
        # Add key for ROI rotation
        "roi_rotation": f"roi_rotation_{unique_id}",
        # Add key for last ROI rotation
        "last_roi_rotation": f"last_roi_rotation_{unique_id}",
    }


def find_best_two_line_pairs(dark_bar_starts):
    """
    Given a list of dark bar starts, find the two consecutive pairs whose widths are most similar.
    Returns the two pairs and their average width.
    """
    pairs = [
        (dark_bar_starts[i], dark_bar_starts[i + 1])
        for i in range(len(dark_bar_starts) - 1)
    ]
    widths = [end - start for start, end in pairs]
    if len(widths) < 2:
        return [], 0.0  # Not enough pairs
    # Find the two widths that are closest to each other
    min_diff = float("inf")
    best_indices = (0, 1)
    for i in range(len(widths)):
        for j in range(i + 1, len(widths)):
            diff = abs(widths[i] - widths[j])
            if diff < min_diff:
                min_diff = diff
                best_indices = (i, j)
    # Get the best two pairs and their average width
    best_pairs = [pairs[best_indices[0]], pairs[best_indices[1]]]
    avg_width = (widths[best_indices[0]] + widths[best_indices[1]]) / 2
    return best_pairs, avg_width


# --- Core Classes ---


class USAFTarget:
    def __init__(self):
        self.base_lp_per_mm = 1.0

    def lp_per_mm(self, group: int, element: int) -> float:
        return self.base_lp_per_mm * (2 ** (group + (element - 1) / 6))

    def line_pair_width_microns(self, group: int, element: int) -> float:
        return 1000.0 / self.lp_per_mm(group, element)


def detect_significant_transitions(profile):
    """
    Detect significant intensity transitions in a profile using only sign changes in the derivative.
    Returns:
        tuple of (all_transitions, transition_types, derivative)
    """
    derivative = np.diff(profile)
    # Find zero crossings in the derivative (sign changes)
    sign_changes = np.where(np.diff(np.sign(derivative)) != 0)[0] + 1
    all_transitions = sign_changes.tolist()
    # Determine transition type: 1 for positive slope, -1 for negative slope
    transition_types = [
        1 if derivative[i - 1] < derivative[i] else -1 for i in sign_changes
    ]
    return all_transitions, transition_types, derivative


def extract_alternating_patterns(transitions, transition_types):
    """
    Extract alternating light-to-dark and dark-to-light transition patterns.

    Args:
        transitions: Array of transition positions
        transition_types: Array of transition types (1: dark-to-light, -1: light-to-dark)

    Returns:
        tuple of (pattern_transitions, pattern_types)
    """
    if len(transitions) <= 2:
        return transitions, transition_types

    # Try to identify proper line pair transitions by looking for alternating patterns
    proper_transitions = []
    proper_types = []

    start_idx = 1 if transition_types and transition_types[0] == 1 else 0
    # Extract transitions by expected pattern
    i = start_idx
    while i < len(transitions) - 1:
        # Check for a light-to-dark followed by dark-to-light pattern
        if (
            i + 1 < len(transition_types)
            and transition_types[i] == -1
            and transition_types[i + 1] == 1
        ):
            proper_transitions.extend([transitions[i], transitions[i + 1]])
            proper_types.extend([transition_types[i], transition_types[i + 1]])
            i += 2
        else:
            # Skip this transition if it doesn't fit the pattern
            i += 1

    # If we found proper transitions, use them
    if len(proper_transitions) >= 2:
        return proper_transitions, proper_types

    return transitions, transition_types


def limit_transitions_to_strongest(
    transitions, transition_types, derivative, max_transitions=5, min_strength=10
):
    """
    If there are too many transitions, keep only the strongest ones above a minimum strength threshold.

    Args:
        transitions: Array of transition positions
        transition_types: Array of transition types
        derivative: The derivative array
        max_transitions: Maximum number of transitions to keep
        min_strength: Minimum absolute derivative value to consider a transition

    Returns:
        tuple of (strongest_transitions, strongest_types)
    """
    # Filter out transitions below the minimum strength
    filtered = [
        (t, typ)
        for t, typ in zip(transitions, transition_types, strict=False)
        if abs(derivative[t]) >= min_strength
    ]
    if not filtered:
        return [], []
    filtered_transitions, filtered_types = zip(*filtered, strict=False)
    filtered_transitions = list(filtered_transitions)
    filtered_types = list(filtered_types)
    if len(filtered_transitions) <= max_transitions:
        return filtered_transitions, filtered_types
    # Sort transitions by derivative magnitude
    transition_strengths = np.abs([derivative[t] for t in filtered_transitions])
    strongest_indices = np.argsort(transition_strengths)[-max_transitions:]
    # Resort by position to maintain order
    strongest_indices = np.sort(strongest_indices)
    strongest_transitions = [filtered_transitions[i] for i in strongest_indices]
    strongest_types = [filtered_types[i] for i in strongest_indices]
    return strongest_transitions, strongest_types


def find_line_pair_boundaries_derivative(profile):
    """
    Find line pair boundaries using sign changes in the derivative.
    Returns:
        (dark_bar_starts, derivative, transition_types)
    Only -1 (light-to-dark) transitions are returned as boundaries.
    """
    all_transitions, all_types, derivative = detect_significant_transitions(profile)
    pattern_transitions, pattern_types = extract_alternating_patterns(
        all_transitions, all_types
    )
    # Adaptive threshold: 20% of max derivative
    max_deriv = np.max(np.abs(derivative)) if len(derivative) > 0 else 0
    min_strength = 0.2 * max_deriv if max_deriv > 0 else 0
    final_transitions, final_types = limit_transitions_to_strongest(
        pattern_transitions, pattern_types, derivative, min_strength=min_strength
    )
    # Only keep -1 transitions (light-to-dark, i.e., dark bar starts)
    dark_bar_starts = [
        t for t, typ in zip(final_transitions, final_types, strict=False) if typ == -1
    ]
    dark_bar_types = [-1] * len(dark_bar_starts)
    return dark_bar_starts, derivative, dark_bar_types


def find_line_pair_boundaries_windowed(profile, window=5):
    """
    Find line pair boundaries using sign changes in a windowed mean difference.
    Returns:
        (dark_bar_starts, pseudo_derivative, transition_types)
    Only -1 (light-to-dark) transitions are returned as boundaries.
    """
    profile = np.asarray(profile)
    pseudo_derivative = np.zeros_like(profile, dtype=float)
    edges = []
    transition_types = []
    for i in range(window, len(profile) - window):
        left = np.mean(profile[i - window : i])
        right = np.mean(profile[i : i + window])
        diff = right - left
        pseudo_derivative[i] = diff
        if i > window and np.sign(pseudo_derivative[i - 1]) != np.sign(diff):
            edges.append(i)
            transition_types.append(1 if diff > 0 else -1)
    pattern_transitions, pattern_types = extract_alternating_patterns(
        edges, transition_types
    )
    # Adaptive threshold: 20% of max pseudo_derivative
    max_deriv = np.max(np.abs(pseudo_derivative)) if len(pseudo_derivative) > 0 else 0
    min_strength = 0.2 * max_deriv if max_deriv > 0 else 0
    final_transitions, final_types = limit_transitions_to_strongest(
        pattern_transitions, pattern_types, pseudo_derivative, min_strength=min_strength
    )
    # Only keep -1 transitions (light-to-dark, i.e., dark bar starts)
    dark_bar_starts = [
        t for t, typ in zip(final_transitions, final_types, strict=False) if typ == -1
    ]
    dark_bar_types = [-1] * len(dark_bar_starts)
    return dark_bar_starts, pseudo_derivative, dark_bar_types


def find_line_pair_boundaries_threshold(profile, threshold):
    """
    Find line pair boundaries by locating where the profile crosses a threshold value.

    Args:
        profile: The intensity profile array
        threshold: The threshold value to use

    Returns:
        (dark_bar_starts, thresholded_profile, transition_types)
    Only -1 (light-to-dark) transitions are returned as boundaries.
    """
    # Convert profile to numpy array
    profile_array = np.array(profile)

    # Ensure threshold is within valid range for uint8 data (0-255)
    threshold = max(0, min(255, threshold))

    # Create a binary mask where True is above threshold
    above_threshold = profile_array > threshold

    dark_bar_starts = [
        i
        for i in range(1, len(above_threshold))
        if above_threshold[i - 1] == True and above_threshold[i] == False
    ]
    # Create corresponding transition types (all -1 for light-to-dark)
    transition_types = [-1] * len(dark_bar_starts)

    logger.info(
        f"Profile range: {np.min(profile_array)} to {np.max(profile_array)}, threshold: {threshold}"
    )
    if len(dark_bar_starts) <= 0:
        logger.warning(f"No dark bar starts found with threshold {threshold}!")

    # Create a pseudo derivative for compatibility with the rest of the code
    thresholded_profile = np.ones_like(profile_array) * threshold

    return dark_bar_starts, thresholded_profile, transition_types


class RoiManager:
    """
    Class for managing Regions of Interest (ROIs) in images.
    Handles selection, validation, and extraction of ROIs.
    """

    def __init__(self):
        self.coordinates = None  # (point1, point2) tuple
        self.roi_tuple = None  # (x, y, width, height) tuple
        self.is_valid = False

    def set_coordinates(self, point1, point2):
        """Set ROI coordinates from two points and validate the selection"""
        self.coordinates = (point1, point2)
        self.validate_and_convert()
        return self.is_valid

    def validate_and_convert(self):
        """Convert corner points to (x, y, width, height) format and validate"""
        if self.coordinates is None:
            self.is_valid = False
            self.roi_tuple = None
            return

        point1, point2 = self.coordinates
        roi_x = min(point1[0], point2[0])
        roi_y = min(point1[1], point2[1])
        roi_width = abs(point2[0] - point1[0])
        roi_height = abs(point2[1] - point1[1])

        # Basic validation: ensure non-zero dimensions
        if roi_width <= 0 or roi_height <= 0:
            logger.warning(
                f"Invalid ROI dimensions: width={roi_width}, height={roi_height}"
            )
            self.is_valid = False
            self.roi_tuple = None
        else:
            self.roi_tuple = (int(roi_x), int(roi_y), int(roi_width), int(roi_height))
            self.is_valid = True

    def validate_against_image(self, image):
        """
        Validate ROI against image dimensions

        Args:
            image: Image to validate against (numpy array or PIL Image)

        Returns:
            bool: True if valid, False otherwise
        """
        if not self.is_valid or self.roi_tuple is None:
            return False

        roi_x, roi_y, roi_width, roi_height = self.roi_tuple

        # Get image dimensions
        img_height, img_width = None, None
        if hasattr(image, "shape"):
            if len(image.shape) > 1:
                img_height, img_width = image.shape[0], image.shape[1]
        elif hasattr(image, "size"):
            img_width, img_height = image.size

        # Validate ROI is within image bounds
        if (
            img_width is not None
            and img_height is not None
            and (
                roi_x < 0
                or roi_y < 0
                or roi_x + roi_width > img_width
                or roi_y + roi_height > img_height
            )
        ):
            logger.warning(
                f"ROI extends beyond image dimensions: "
                f"roi=({roi_x},{roi_y},{roi_width},{roi_height}), "
                f"image=({img_width},{img_height})"
            )
            self.is_valid = False

        return self.is_valid

    def extract_roi(self, image):
        """
        Extract ROI from image

        Args:
            image: Image to extract ROI from (numpy array)

        Returns:
            numpy.ndarray: Extracted ROI or None if invalid
        """
        if not self.is_valid or self.roi_tuple is None:
            return None

        roi_x, roi_y, roi_width, roi_height = self.roi_tuple

        try:
            if hasattr(image, "select_roi"):
                return image.select_roi(self.roi_tuple)

            if (
                image is not None
                and roi_x >= 0
                and roi_y >= 0
                and roi_width > 0
                and roi_height > 0
            ):
                return image[roi_y : roi_y + roi_height, roi_x : roi_x + roi_width]

            return None
        except Exception as e:
            logger.error(f"Error extracting ROI: {e}")
            return None


class ProfileVisualizer:
    """
    Class for visualizing profile analysis results.
    Handles generating plots and visualizations of intensity profiles and transition analysis.
    """

    def __init__(self):
        # Configure default plot style
        self.configure_plot_style()

        # Define colors for different elements
        self.light_to_dark_color = "#FF4500"  # Orange-red

        self.annotation_color = "#FFFF99"  # Yellow
        self.profile_color = "#2c3e50"  # Dark blue-gray
        self.individual_profile_color = "#6b88b6"  # Light blue

        # Shadow effect for text
        self.shadow_effect = [
            PathEffects.withSimplePatchShadow(
                offset=(1.0, -1.0), shadow_rgbFace="black", alpha=0.6
            )
        ]

    def configure_plot_style(self):
        """Configure matplotlib plot style"""
        plt.rcParams.update(
            {
                "font.family": "serif",
                "font.serif": ["Times New Roman", "DejaVu Serif", "Palatino", "serif"],
                "mathtext.fontset": "stix",
                "axes.titlesize": 11,
                "axes.labelsize": 10,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
            }
        )

    def create_figure(self, figsize=(8, 8), dpi=150):
        """Create a square matplotlib figure with properly configured layout"""
        fig = plt.figure(figsize=figsize, dpi=dpi, facecolor="white")
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.05)

        # Set explicit figure margins to avoid tight_layout issues
        fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.05)

        # Create subplot axes
        ax_img = fig.add_subplot(gs[0])
        ax_profile = fig.add_subplot(gs[1], sharex=ax_img)

        # Configure axes appearance
        ax_img.set_xticks([])
        ax_img.set_yticks([])
        ax_img.set_ylabel("")

        # Increased font size
        ax_profile.set_xlabel("Position (pixels)", fontsize=12)
        # Increased font size
        ax_profile.set_ylabel("Intensity (a.u.)", fontsize=12)
        ax_profile.grid(True, alpha=0.15, linestyle="-", linewidth=0.5)
        # Increased tick font size
        ax_profile.tick_params(axis="both", which="major", labelsize=11)

        # Remove unnecessary spines
        for ax in [ax_img, ax_profile]:
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        ax_img.spines["left"].set_visible(False)
        ax_img.spines["bottom"].set_visible(False)

        return fig, ax_img, ax_profile

    def plot_image(
        self,
        ax,
        image,
        group=None,
        element=None,
        avg_line_pair_width=None,
        lp_width_um=None,
        magnification=None,
        lp_per_mm=None,
    ):
        """Plot the ROI image"""
        ax.imshow(image, cmap="gray", aspect="auto", interpolation="bicubic")
        if title_text := self._build_plot_title(
            group,
            element,
            avg_line_pair_width,
            lp_width_um,
            magnification,
            lp_per_mm,
        ):
            ax.set_title(
                title_text,
                fontweight="normal",
                pad=15,
                fontsize=20,
            )

    def _build_plot_title(
        self, group, element, avg_line_pair_width, lp_width_um, magnification, lp_per_mm
    ):
        """Helper function to build the title string for the plot_image method."""
        if group is None or element is None:
            return ""

        title_lines = []
        group_str = f"$\\mathbf{{{group}}}$"
        element_str = f"$\\mathbf{{{element}}}$"
        title_lines.append(f"USAF Target: Group {group_str}, Element {element_str}")

        lp_per_mm_str = ""
        if lp_per_mm is not None:
            lp_per_mm_str = f"Line Pairs/mm: $\\mathbf{{{lp_per_mm:.2f}}}$"

        avg_width_str = ""
        if avg_line_pair_width is not None and avg_line_pair_width > 0:
            avg_width_str = f"Avg. LP Width: $\\mathbf{{{avg_line_pair_width:.2f}}}$ px"

        if lp_per_mm_str or avg_width_str:
            combined_str = (
                f"{lp_per_mm_str}  |  {avg_width_str}"
                if lp_per_mm_str and avg_width_str
                else lp_per_mm_str or avg_width_str
            )
            title_lines.append(combined_str)

        pixel_size_str = ""
        if (
            avg_line_pair_width is not None
            and avg_line_pair_width > 0
            and lp_width_um is not None
        ):
            pixel_size = lp_width_um / avg_line_pair_width
            pixel_size_str = f"Pixel Size: $\\mathbf{{{pixel_size:.3f}}}$ µm/pixel"

        mag_str = ""
        if magnification is not None:
            mag_str = f"Magnification: $\\mathbf{{{magnification:.1f}\\times}}$"

        if pixel_size_str or mag_str:
            combined_pixel_mag_str = (
                f"{pixel_size_str}  |  {mag_str}"
                if pixel_size_str and mag_str
                else pixel_size_str or mag_str
            )
            title_lines.append(combined_pixel_mag_str)

        return "\n".join(title_lines)

    def plot_profiles(
        self,
        ax,
        profile,
        individual_profiles=None,
        avg_line_pair_width=0.0,
        profile_type="max",
        edge_method=None,
        threshold=None,
    ):
        """Plot the intensity profile and individual profiles
        Args:
            ax: The matplotlib axis to plot on
            profile: The 1D intensity profile
            individual_profiles: Optional, the 2D array of individual row profiles
            avg_line_pair_width: Optional, average line pair width for annotation
            profile_type: 'mean' or 'max', used for labeling
        """
        # Plot individual profiles if available
        if individual_profiles is not None:
            n_rows = individual_profiles.shape[0]
            step = max(1, n_rows // 20)
            for i in range(0, n_rows, step):
                ax.plot(
                    individual_profiles[i],
                    color=self.individual_profile_color,
                    alpha=0.12,
                    linewidth=0.7,
                    zorder=1,
                )
            # Create label for intensity
            intensity_label = "Max Intensity"
        if avg_line_pair_width > 0:
            intensity_label += f"\n(Avg. LP Width: {avg_line_pair_width:.1f} px)"

        # Plot profile
        ax.plot(
            profile,
            color=self.profile_color,
            linewidth=2.5,
            alpha=1.0,  # Increased linewidth
            label=intensity_label,
            zorder=2,
        )

        # Plot threshold line if applicable
        if threshold is not None and edge_method == "threshold":
            ax.axhline(
                y=threshold,
                color="r",
                linestyle="--",
                alpha=0.8,
                linewidth=1.5,
                zorder=3,
                label="Threshold",
            )  # Increased linewidth

        # Increase font size for axis labels and ticks
        # Increased tick font size
        ax.tick_params(axis="both", which="major", labelsize=11)
        # Increased label font size
        ax.set_xlabel("Position (pixels)", fontsize=12)
        # Increased label font size
        ax.set_ylabel("Intensity (a.u.)", fontsize=12)

    def find_line_pairs(self, boundaries, roi_img):
        """
        Find and return only the two best-matching line pairs for annotation.
        """
        best_pairs, _ = find_best_two_line_pairs(boundaries)
        line_pairs = []
        for j, (start_pos, end_pos) in enumerate(best_pairs):
            width_px = end_pos - start_pos
            if width_px >= 5:
                line_pairs.append((start_pos, end_pos, width_px, j))
        return line_pairs

    def draw_bracket(self, ax, x_start, x_end, y_pos, tick_size, color):
        """Draw a bracket with ticks between two x-positions"""
        line_width = 1.5

        # Draw horizontal line
        ax.annotate(
            "",
            xy=(x_start, y_pos),
            xytext=(x_end, y_pos),
            arrowprops=dict(arrowstyle="-", color=color, linewidth=line_width),
        )

        # Draw tick marks on ends
        ax.annotate(
            "",
            xy=(x_start, y_pos),
            xytext=(x_start, y_pos + tick_size),
            arrowprops=dict(arrowstyle="-", color=color, linewidth=line_width),
        )
        ax.annotate(
            "",
            xy=(x_end, y_pos),
            xytext=(x_end, y_pos + tick_size),
            arrowprops=dict(arrowstyle="-", color=color, linewidth=line_width),
        )

    def annotate_line_pairs(self, ax, line_pairs, roi_img):
        """
        Annotate line pairs with brackets and labels using dark bar starts.
        """
        vertical_position = (
            0.35  # Initial vertical position (0-1 relative to image height)
        )
        tick_height = 0.04  # Height of the tick marks
        for start_pos, end_pos, width_px, j in line_pairs:
            y_offset = 0.0 if j == 0 else 0.15 * j
            y_pos = roi_img.shape[0] * (vertical_position + y_offset)
            tick_size = roi_img.shape[0] * tick_height
            mid_point = (start_pos + end_pos) / 2
            self.draw_bracket(
                ax, start_pos, end_pos, y_pos, tick_size, self.annotation_color
            )
            label_y_pos = y_pos + tick_size * 0.5
            line_pair_text = ax.text(
                mid_point,
                label_y_pos,
                "Line Pair",
                color=self.annotation_color,
                ha="center",
                va="top",
                fontsize=16,
                fontweight="bold",
            )  # Increased font size
            line_pair_text.set_path_effects(self.shadow_effect)
            measurement = f"{int(round(width_px))} px"
            measurement_text = ax.text(
                mid_point,
                label_y_pos + tick_size * 1.5,
                measurement,
                color=self.annotation_color,
                ha="center",
                va="top",
                fontsize=14,
                fontweight="bold",
            )  # Increased font size
            measurement_text.set_path_effects(self.shadow_effect)

    def create_caption(
        self,
        group=None,
        element=None,
        lp_width_um=None,
        edge_method=None,
        lp_per_mm=None,
    ):
        """Create an HTML caption for the plot, including edge detection method."""
        if edge_method == "parallel":
            method_str = "Windowed Step (Robust)"
        elif edge_method == "threshold":
            method_str = "Threshold-based"
        else:
            method_str = "Original"

        if group is not None and element is not None and lp_width_um is not None:
            lp_per_mm_str = f"{lp_per_mm:.2f} lp/mm" if lp_per_mm is not None else ""

            return f"""
            <div style='text-align:center; font-family: "Times New Roman", Times, serif;'>
                <p style='margin-bottom:0.3rem; font-size:1.25rem;'><b>Figure: Intensity Profile Analysis of USAF Target</b></p>
                <p style='margin-top:0; font-size:1.0rem; color:#333;'>
                    Group {group}, Element {element} with theoretical line pair width of {lp_width_um:.2f} µm 
                    {f"({lp_per_mm_str})" if lp_per_mm_str else ""}.<br>
                    <b>Max Intensity Profile</b> with <b>Edge Detection Method:</b> <span style='color:#0074D9'>{method_str}</span><br>
                    Each line pair consists of one complete dark bar and one complete light bar.<br>
                    <span style='color:{self.light_to_dark_color};'>Orange</span> lines indicate the start of dark bars (threshold crossings).
                </p>
            </div>
            """
        else:
            return f"""
            <div style='text-align:center; font-family: "Times New Roman", Times, serif;'>
                <p style='margin-bottom:0.3rem; font-size:1.25rem;'><b>Figure: Aligned Visual Analysis</b></p>
                <p style='margin-top:0; font-size:1.0rem; color:#333;'>
                    <b>Max Intensity Profile</b> with <b>Edge Detection Method:</b> <span style='color:#0074D9'>{method_str}</span><br>
                    Each line pair consists of one complete dark bar and one complete light bar.<br>
                    <span style='color:{self.light_to_dark_color};'>Orange</span> lines indicate the start of dark bars (threshold crossings).
                </p>
            </div>
            """

    def visualize_profile(
        self,
        results,
        roi_img,
        group=None,
        element=None,
        lp_width_um=None,
        magnification=None,
    ):
        """
        Create a complete visualization of profile analysis
        Args:
            results: Analysis results dictionary
            roi_img: The ROI image to display
            group: USAF target group
            element: USAF target element
            lp_width_um: Theoretical line pair width in microns
            magnification: User-provided magnification value
        Returns:
            fig: Matplotlib figure
        """
        # Validate inputs
        if "profile" not in results or results["profile"] is None or roi_img is None:
            return None
        # Convert profile to numpy array
        profile = np.array(results["profile"])
        # Create figure
        fig, ax_img, ax_profile = self.create_figure()
        # Plot ROI image
        avg_line_pair_width = results.get("avg_line_pair_width", 0.0)
        # Get Line Pairs per mm from results
        lp_per_mm = results.get("lp_per_mm", None)
        self.plot_image(
            ax_img,
            roi_img,
            group,
            element,
            avg_line_pair_width,
            lp_width_um,
            magnification,
            lp_per_mm,
        )
        # Plot profiles
        individual_profiles = results.get("individual_profiles")
        profile_type = results.get("profile_type", "max")
        edge_method = results.get("edge_method", "original")
        threshold = results.get("threshold", None)
        self.plot_profiles(
            ax_profile,
            profile,
            individual_profiles,
            avg_line_pair_width,
            profile_type=profile_type,
            edge_method=edge_method,
            threshold=threshold,
        )
        # Get transition information
        boundaries = results.get("boundaries", [])
        self._plot_transitions_and_annotations(
            ax_img, ax_profile, boundaries, roi_img, profile
        )

        # Set x-axis limits
        x_max = len(profile) if len(profile) > 0 else 100
        ax_profile.set_xlim(0, x_max)
        ax_img.set_xlim(0, x_max)
        # Return the figure - the caller is responsible for displaying it using st.pyplot(fig)
        return fig

    def _plot_transitions_and_annotations(
        self, ax_img, ax_profile, boundaries, roi_img, profile
    ):
        """Helper function to plot transition lines and annotations."""
        if len(boundaries) > 0:
            # Draw transition boundary lines
            for boundary in boundaries:
                ax_profile.axvline(
                    x=boundary,
                    color=self.light_to_dark_color,
                    linestyle="-",
                    alpha=0.7,
                    linewidth=1.8,
                    zorder=4,
                )
                ax_img.axvline(
                    x=boundary,
                    color=self.light_to_dark_color,
                    linestyle="--",
                    alpha=0.6,
                    linewidth=1.0,
                    zorder=3,
                )

            # Find and annotate line pairs
            if len(boundaries) >= 2:
                line_pairs = self.find_line_pairs(boundaries, roi_img)
                self.annotate_line_pairs(ax_img, line_pairs, roi_img)
            else:
                logger.info("Not enough boundaries to annotate line pairs.")

        else:
            ax_profile.text(
                0.5,
                0.5,
                "No boundaries detected!\nTry adjusting the threshold.",
                transform=ax_profile.transAxes,
                ha="center",
                va="center",
                color="red",
                fontsize=14,
                fontweight="bold",
            )
            logger.warning("No boundaries detected for visualization")


class ImageProcessor:
    def __init__(self, usaf_target: USAFTarget = None):
        self.image = None
        self.original_image = None  # Store the original unprocessed image
        self.grayscale = None
        self.original_grayscale = None  # Store the original grayscale image
        self.roi_manager = RoiManager()
        self.roi = None
        self.original_roi = None  # Store the original ROI before processing
        self.profile = None
        self.individual_profiles = None
        self.usaf_target = usaf_target or USAFTarget()
        self.boundaries = None
        self.transition_types = None
        self.derivative = None
        self.line_pair_widths = []

        self.dark_regions = []
        self.light_regions = []
        self.contrast = 0.0
        self.processing_params = {
            "autoscale": True,
            "invert": False,
            "normalize": False,
            "saturated_pixels": 0.5,
            "equalize_histogram": True,  # Changed default to True
        }
        self.roi_rotation = (
            0  # Store ROI rotation (0, 1, 2, or 3 for 0°, 90°, 180°, 270°)
        )

    def load_image(self, image_path: str) -> bool:
        try:
            if not os.path.isfile(image_path):
                logger.error(f"Image file not found: {image_path}")
                return False
            try:
                # Load the image without any processing first
                if image_path.lower().endswith((".tif", ".tiff")):
                    try:
                        with tifffile.TiffFile(image_path) as tif:
                            if len(tif.pages) == 0:
                                logger.error(f"TIFF file has no pages: {image_path}")
                                return False
                            self.original_image = tif.pages[0].asarray()
                    except Exception as e:
                        logger.error(f"Failed to load TIFF: {image_path} ({e})")
                        return False
                else:
                    self.original_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
                    if self.original_image is None:
                        # If OpenCV fails, try PIL
                        logger.info(
                            f"OpenCV failed to load image, trying PIL: {image_path}"
                        )
                        pil_image = Image.open(image_path)
                        self.original_image = np.array(pil_image)

                if self.original_image is None:
                    logger.error(f"Failed to load image: {image_path}")
                    return False

                # Convert BGR to RGB if needed (OpenCV loads as BGR)
                if (
                    len(self.original_image.shape) == 3
                    and self.original_image.shape[2] == 3
                ):
                    self.original_image = cv2.cvtColor(
                        self.original_image, cv2.COLOR_BGR2RGB
                    )

                # Create grayscale version of the original image
                if len(self.original_image.shape) > 2:
                    self.original_grayscale = cv2.cvtColor(
                        self.original_image, cv2.COLOR_RGB2GRAY
                    )
                else:
                    self.original_grayscale = self.original_image

                # Create display version with default processing
                self.apply_processing()

                return True
            except Exception as e:
                logger.error(f"Error loading image: {e}")
                return False
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return False

    def apply_processing(self):
        """Apply current processing parameters to the original image"""
        try:
            # Apply processing to the original image
            self.image = normalize_to_uint8(
                self.original_image,
                autoscale=self.processing_params["autoscale"],
                invert=self.processing_params["invert"],
                normalize=self.processing_params["normalize"],
                saturated_pixels=self.processing_params["saturated_pixels"],
                equalize_histogram=self.processing_params["equalize_histogram"],
            )

            # Create grayscale version of the processed image
            if len(self.image.shape) > 2:
                self.grayscale = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
            else:
                self.grayscale = self.image

            # If we have an ROI, reapply processing to it
            if self.original_roi is not None:
                self.roi = normalize_to_uint8(
                    self.original_roi,
                    autoscale=self.processing_params["autoscale"],
                    invert=self.processing_params["invert"],
                    normalize=self.processing_params["normalize"],
                    saturated_pixels=self.processing_params["saturated_pixels"],
                    equalize_histogram=self.processing_params["equalize_histogram"],
                )

            return True
        except Exception as e:
            logger.error(f"Error applying processing: {e}")
            return False

    def update_processing_params(self, **kwargs):
        """Update processing parameters and reapply processing"""
        for key, value in kwargs.items():
            if key in self.processing_params:
                self.processing_params[key] = value

        return self.apply_processing()

    def set_roi(self, roi_coordinates: tuple[int, int, int, int]) -> bool:
        """
        Set and validate ROI coordinates

        Args:
            roi_coordinates: ROI tuple (x, y, width, height)

        Returns:
            bool: True if ROI is valid, False otherwise
        """
        if not isinstance(roi_coordinates, tuple) or len(roi_coordinates) != 4:
            logger.error(f"Invalid ROI coordinates format: {roi_coordinates}")
            return False

        x, y, width, height = roi_coordinates
        point1 = (x, y)
        point2 = (x + width, y + height)

        # Use ROI manager to set and validate coordinates
        valid = self.roi_manager.set_coordinates(point1, point2)
        valid = valid and self.roi_manager.validate_against_image(self.grayscale)

        if valid:
            self.select_roi()

        return valid

    def set_roi_rotation(self, rotation_count: int) -> None:
        """
        Set ROI rotation count (number of 90° rotations).

        Args:
            rotation_count: Number of 90-degree rotations (0-3)
        """
        self.roi_rotation = rotation_count % 4

    def select_roi(self) -> np.ndarray | None:
        """
        Extract the ROI based on the current roi_manager settings

        Returns:
            Optional[np.ndarray]: The extracted ROI or None
        """
        if self.grayscale is None or not self.roi_manager.is_valid:
            return None

        try:
            # Extract ROI from both original and processed grayscale images
            self.original_roi = self.roi_manager.extract_roi(self.original_grayscale)
            self.roi = self.roi_manager.extract_roi(self.grayscale)

            # Apply rotation if needed
            if self.roi_rotation > 0:
                self.original_roi = rotate_image(self.original_roi, self.roi_rotation)
                self.roi = rotate_image(self.roi, self.roi_rotation)

            return self.roi
        except Exception as e:
            logger.error(f"Error selecting ROI: {e}")
            return None

    def get_line_profile(self, use_max=False) -> np.ndarray | None:
        if self.roi is None:
            return None
        try:
            use_roi = self.roi
            self.individual_profiles = use_roi.copy()
            self.profile = np.max(use_roi, axis=0) if use_max else np.mean(use_roi, axis=0)
            return self.profile
        except Exception as e:
            logger.error(f"Error getting line profile: {e}")
            return None

    def detect_edges(self, edge_method="original"):
        if self.profile is None:
            logger.error("No profile available for edge detection")
            return False
        if edge_method == "parallel":
            self.boundaries, self.derivative, self.transition_types = (
                find_line_pair_boundaries_windowed(self.profile)
            )
        else:
            self.boundaries, self.derivative, self.transition_types = (
                find_line_pair_boundaries_derivative(self.profile)
            )
        return len(self.boundaries) > 0

    def calculate_contrast(self):
        """
        Calculate contrast from the detected light and dark regions.

        Returns:
            float: The calculated contrast value
        """
        if (
            self.profile is None
            or self.boundaries is None
            or self.transition_types is None
        ):
            return 0.0

        try:
            # Identify dark and light regions based on transitions
            self.dark_regions = []
            self.light_regions = []

            for i in range(len(self.boundaries) - 1):
                if i + 1 < len(self.transition_types):
                    start, end = self.boundaries[i], self.boundaries[i + 1]
                    if start < end and start >= 0 and end < len(self.profile):
                        if (
                            self.transition_types[i] == -1
                            and self.transition_types[i + 1] == 1
                        ):
                            # This is a dark bar (from L→D to D→L)
                            self.dark_regions.append(self.profile[start:end])
                        elif (
                            self.transition_types[i] == 1
                            and self.transition_types[i + 1] == -1
                        ):
                            # This is a light bar (from D→L to L→D)
                            self.light_regions.append(self.profile[start:end])

            # Calculate contrast if we have both light and dark regions
            if self.dark_regions and self.light_regions:
                min_intensity = np.mean(
                    [np.mean(region) for region in self.dark_regions]
                )
                max_intensity = np.mean(
                    [np.mean(region) for region in self.light_regions]
                )
                self.contrast = (max_intensity - min_intensity) / (
                    max_intensity + min_intensity
                )
            else:
                # Fallback if segmentation didn't work as expected
                self.contrast = (np.max(self.profile) - np.min(self.profile)) / (
                    np.max(self.profile) + np.min(self.profile)
                )
        except Exception:
            # Fallback calculation
            if len(self.profile) > 0:
                self.contrast = (np.max(self.profile) - np.min(self.profile)) / (
                    np.max(self.profile) + np.min(self.profile)
                )

        return self.contrast

    def analyze_profile(self, group: int, element: int) -> dict:
        """
        Analyze the current profile for the specified USAF target group and element.

        Args:
            group: USAF group number
            element: USAF element number

        Returns:
            Dictionary with analysis results
        """
        # Ensure we have a profile to analyze
        if self.profile is None:
            logger.error("No profile available for analysis")
            return {"error": "No profile available for analysis"}

        # Step 1: Detect edges in the profile if not already detected
        # (skip if boundaries are already set, e.g., by threshold detection)
        if self.boundaries is None or len(self.boundaries) == 0:
            self.detect_edges()
            # Step 2: Use only the best two line pairs
            self.line_pair_widths = []

        if self.boundaries is not None and len(self.boundaries) >= 3:
            best_pairs, avg_width = find_best_two_line_pairs(self.boundaries)

            self.line_pair_widths = [end - start for start, end in best_pairs]
            self.avg_line_pair_width = avg_width
        else:
            self.avg_line_pair_width = 0.0

        # Step 3: Calculate contrast
        self.calculate_contrast()

        # Calculate theoretical values based on USAF target
        num_line_pairs = len(self.line_pair_widths)
        lp_per_mm = self.usaf_target.lp_per_mm(group, element)

        # Create results dictionary
        results = {
            "group": group,
            "element": element,
            "lp_per_mm": float(lp_per_mm),
            "theoretical_lp_width_um": self.usaf_target.line_pair_width_microns(
                group, element
            ),
            "num_line_pairs": num_line_pairs,
            "num_boundaries": (
                len(self.boundaries) if self.boundaries is not None else 0
            ),
            "boundaries": self.boundaries,
            "transition_types": self.transition_types,
            "line_pair_widths": self.line_pair_widths,
            "avg_line_pair_width": self.avg_line_pair_width,
            "contrast": self.contrast,
            "derivative": (
                self.derivative.tolist() if hasattr(self.derivative, "tolist") else None
            ),
            "profile": (
                self.profile.tolist() if hasattr(self.profile, "tolist") else None
            ),
            "processing_params": self.processing_params.copy(),  # Include processing parameters
        }

        # Add individual profiles to the results
        if self.individual_profiles is not None:
            results["individual_profiles"] = self.individual_profiles

        return results

    def process_and_analyze(
        self,
        image_path: str,
        roi: tuple[int, int, int, int],
        group: int,
        element: int,
        use_max: bool = True,
        edge_method: str = "original",
        threshold: float = None,
        roi_rotation: int = 0,
        **processing_params,
    ) -> dict:
        """
        Complete pipeline: load image, select ROI, and analyze profile
        Args:
            image_path: Path to the image file
            roi: Region of interest tuple (x, y, width, height)
            group: USAF group number
            element: USAF group element
            use_max: If True, use max for profile; else mean (defaults to True)
            edge_method: 'original' or 'parallel', for legend
            threshold: Threshold value for edge detection (if None, use edge_method)
            roi_rotation: Number of 90-degree rotations to apply to the ROI (0-3)
            **processing_params: Additional processing parameters (autoscale, invert, etc.)
        Returns:
            Dictionary with analysis results
        """
        if not self._load_and_prepare_image_data(
            image_path, roi, roi_rotation, processing_params
        ):
            return {"error": "Failed to load or prepare image data."}

        if threshold is not None:
            results = self._analyze_with_threshold(threshold, group, element)
        else:
            results = self.analyze_profile_with_edge_method(edge_method, group, element)

        results["threshold"] = threshold if threshold is not None else 0
        results["roi_rotation"] = self.roi_rotation
        return results

    def _load_and_prepare_image_data(
        self, image_path, roi, roi_rotation, processing_params
    ):
        """Helper to load image, set ROI, and get profile."""
        if processing_params:
            self.update_processing_params(**processing_params)
        self.set_roi_rotation(roi_rotation)

        if not self.load_image(image_path):
            logger.error(f"Failed to load image: {image_path}")
            return False
        if not self.set_roi(roi):
            logger.error(f"Failed to set ROI: {roi}")
            return False
        if self.get_line_profile(use_max=True) is None:
            logger.error("Failed to get line profile.")
            return False

        return True

    def _analyze_with_threshold(self, threshold, group, element):
        """Helper to analyze profile using threshold-based edge detection."""
        self.boundaries, self.derivative, self.transition_types = (
            find_line_pair_boundaries_threshold(self.profile, threshold)
        )
        results = self.analyze_profile(group, element)
        results["profile_type"] = "max"
        results["edge_method"] = "threshold"
        return results

    def analyze_profile_with_edge_method(self, edge_method, group, element):
        """
        Analyze the profile using the specified edge detection method.
        Args:
            edge_method: The edge detection method to use ('original', 'parallel', etc.)
            group: USAF group number
            element: USAF group element
        Returns:
            Dictionary with analysis results, including profile type and edge method.
        """
        self.detect_edges(edge_method=edge_method)

        result = self.analyze_profile(group, element)
        result["profile_type"] = "max"
        result["edge_method"] = edge_method
        return result


# --- Streamlit UI Functions ---


def display_roi_info(idx: int, image=None) -> tuple[int, int, int, int] | None:
    keys = get_image_session_keys(idx)
    coordinates_key = keys["coordinates"]
    roi_valid_key = keys["roi_valid"]
    if (
        coordinates_key not in st.session_state
        or st.session_state[coordinates_key] is None
    ):
        st.session_state[roi_valid_key] = False
        return None
    try:
        point1, point2 = st.session_state[coordinates_key]
        roi_x = min(point1[0], point2[0])
        roi_y = min(point1[1], point2[1])
        roi_width = abs(point2[0] - point1[0])
        roi_height = abs(point2[1] - point1[1])
        if roi_width <= 0 or roi_height <= 0:
            logger.warning(
                f"Invalid ROI dimensions: width={roi_width}, height={roi_height}"
            )
            st.session_state[roi_valid_key] = False
            return None
        if image is not None:
            img_height, img_width = None, None
            if hasattr(image, "shape"):
                if len(image.shape) > 1:
                    img_height, img_width = image.shape[0], image.shape[1]
            elif hasattr(image, "size"):
                img_width, img_height = image.size
            if (
                img_width is not None
                and img_height is not None
                and (
                    roi_x < 0
                    or roi_y < 0
                    or roi_x + roi_width > img_width
                    or roi_y + roi_height > img_height
                )
            ):
                logger.warning(
                    f"ROI extends beyond image dimensions: "
                    f"roi=({roi_x},{roi_y},{roi_width},{roi_height}), "
                    f"image=({img_width},{img_height})"
                )
                st.session_state[roi_valid_key] = False
                return None
        st.session_state[roi_valid_key] = True
        return (int(roi_x), int(roi_y), int(roi_width), int(roi_height))
    except Exception as e:
        logger.error(f"Error processing ROI: {e}")
        st.session_state[roi_valid_key] = False
        return None


def handle_image_selection(
    idx: int,
    image_file,
    image_to_display: np.ndarray,
    key: str = "usaf_image",
    rotation: int = 0,
) -> bool:
    keys = get_image_session_keys(idx, image_file)
    coordinates_key = keys["coordinates"]
    roi_valid_key = keys["roi_valid"]
    if coordinates_key not in st.session_state:
        st.session_state[coordinates_key] = None
        st.session_state[roi_valid_key] = False
    unique_id = keys["coordinates"].split("_")[1]
    component_key = f"{key}_{unique_id}"

    # No rotation is applied to the display image - we only want to rotate the extracted ROI
    coords_component_output = streamlit_image_coordinates(
        image_to_display, key=component_key, click_and_drag=True
    )
    roi_changed = False
    if (
        coords_component_output is not None
        and coords_component_output.get("x1") is not None
        and coords_component_output.get("x2") is not None
        and coords_component_output.get("y1") is not None
        and coords_component_output.get("y2") is not None
    ):
        # Get coordinates from the component output
        point1 = (coords_component_output["x1"], coords_component_output["y1"])
        point2 = (coords_component_output["x2"], coords_component_output["y2"])

        if point1[0] != point2[0] and point1[1] != point2[1]:
            current_coordinates = st.session_state.get(coordinates_key)
            if current_coordinates != (point1, point2):
                # Store the coordinates in the session state
                st.session_state[coordinates_key] = (point1, point2)
                is_valid = (
                    point1[0] >= 0
                    and point1[1] >= 0
                    and point2[0] >= 0
                    and point2[1] >= 0
                    and abs(point2[0] - point1[0]) > 0
                    and abs(point2[1] - point1[1]) > 0
                )
                st.session_state[roi_valid_key] = is_valid
                roi_changed = True
    return roi_changed


def display_welcome_screen():
    st.info("Please upload a USAF 1951 target image to begin analysis.")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(
            WELCOME_IMAGE_URL,
            caption=WELCOME_IMAGE_CAPTION,
            use_container_width=True,
        )
    with col2:
        st.subheader("USAF 1951 Target Format")
        st.latex(
            r"\text{resolution (lp/mm)} = 2^{\text{group} + (\text{element} - 1)/6}"
        )
        st.latex(
            r"\text{Line Pair Width (μm)} = \frac{1000}{2 \times \text{resolution (lp/mm)}}"
        )


def display_analysis_details(results):
    group = results.get("group")
    element = results.get("element")
    lp_width_um = st.session_state.usaf_target.line_pair_width_microns(group, element)
    lp_per_mm = results.get("lp_per_mm")
    avg_measured_lp_width_px = results.get("avg_line_pair_width", 0.0)
    st.markdown(
        """<div class="usaf-line-pair-info">
        <b>A line pair</b> = one black bar + one white bar (one cycle)<br>
        <b>Line pair width</b> = distance from start of one black bar to the next
        </div>""",
        unsafe_allow_html=True,
    )
    st.latex(rf"Group = {group}, \quad Element = {element}")
    st.latex(
        rf"\text{{Line Pairs per mm (Theoretical)}} = 2^{{{group} + ({element} - 1)/6}} = {lp_per_mm:.2f}"
    )
    st.latex(
        rf"\text{{Line Pair Width (µm, Theoretical)}} = \frac{{1000}}{{{lp_per_mm:.2f} \text{{ lp/mm}}}} = {lp_width_um:.2f} \text{{ µm}}"
    )
    st.latex(
        rf"\text{{Avg. Measured Line Pair Width (pixels)}} = {avg_measured_lp_width_px:.2f} \text{{ px}}"
    )
    if avg_measured_lp_width_px > 0 and lp_width_um is not None:
        implied_pixel_size = lp_width_um / avg_measured_lp_width_px
        st.latex(
            rf"\text{{Implied Pixel Size (µm/pixel)}} = \frac{{{lp_width_um:.2f} \text{{ µm}}}}{{{avg_measured_lp_width_px:.2f} \text{{ px}}}} = {implied_pixel_size:.3f} \text{{ µm/pixel}}"
        )
    else:
        st.latex(
            r"\text{Implied Pixel Size (µm/pixel)} = \text{N/A (requires measurement)}"
        )


def analyze_and_display_image(idx, uploaded_file):
    filename = (
        os.path.basename(uploaded_file)
        if isinstance(uploaded_file, str)
        else (
            uploaded_file.name if hasattr(uploaded_file, "name") else f"Image {idx+1}"
        )
    )
    keys = get_image_session_keys(idx, uploaded_file)
    st.session_state[keys["image_name"]] = filename

    # Parse filename to get default values for magnification, group, and element
    default_values = parse_filename_for_defaults(filename)
    default_group = default_values.get("group", DEFAULT_GROUP)
    default_element = default_values.get("element", DEFAULT_ELEMENT)
    default_magnification = default_values.get("magnification", 10.0)

    # Get unique ID for this image
    unique_id = get_unique_id_for_image(uploaded_file)

    # Keep ROI rotation state for extracted ROI only, not for display
    roi_rotation_key = keys["roi_rotation"]
    last_roi_rotation_key = keys["last_roi_rotation"]

    if roi_rotation_key not in st.session_state:
        st.session_state[roi_rotation_key] = 0
    if last_roi_rotation_key not in st.session_state:
        st.session_state[last_roi_rotation_key] = 0

    # Define keys for image processing settings
    autoscale_key = f"autoscale_{unique_id}"
    invert_key = f"invert_{unique_id}"
    normalize_key = f"normalize_{unique_id}"
    saturated_pixels_key = f"saturated_pixels_{unique_id}"
    equalize_histogram_key = f"equalize_histogram_{unique_id}"
    bit_depth_key = f"bit_depth_{unique_id}"
    magnification_key = f"magnification_{unique_id}"
    threshold_key = f"threshold_{unique_id}"
    settings_changed_key = f"settings_changed_{unique_id}"

    # Initialize settings in session state if they don't exist yet
    if autoscale_key not in st.session_state:
        st.session_state[autoscale_key] = True
    if invert_key not in st.session_state:
        st.session_state[invert_key] = False
    if normalize_key not in st.session_state:
        st.session_state[normalize_key] = False
    if saturated_pixels_key not in st.session_state:
        st.session_state[saturated_pixels_key] = 0.5
    if equalize_histogram_key not in st.session_state:
        st.session_state[equalize_histogram_key] = True
    if magnification_key not in st.session_state:
        st.session_state[magnification_key] = default_magnification
    if settings_changed_key not in st.session_state:
        st.session_state[settings_changed_key] = False

    # Reset settings_changed flag if we're in a rerun triggered by settings changing
    if st.session_state.get(settings_changed_key, False):
        st.session_state[settings_changed_key] = False

    with st.expander(f"📸 Image {idx+1}: {filename}", expanded=(idx == 0)):
        image, temp_path = _load_and_display_image_header(
            uploaded_file, idx, filename, keys, default_values, bit_depth_key
        )
        if image is None:
            return

        # Determine default and max threshold based on ROI
        roi_tuple_for_threshold = display_roi_info(idx, image)
        default_threshold_val, max_threshold_val = _calculate_threshold_defaults(
            image, roi_tuple_for_threshold
        )

        # Store the original threshold value from session state or use default
        current_threshold = int(
            st.session_state.get(threshold_key, default_threshold_val)
        )

        # Combined analysis interface - no more tab switching!
        (
            selected_group,
            selected_element,
            magnification,
            autoscale,
            normalize,
            invert,
            equalize_histogram,
            saturated_pixels,
            threshold,
            new_rotation,
        ) = _display_combined_analysis_interface(
            idx,
            uploaded_file,
            image,
            keys,
            unique_id,
            default_group,
            default_element,
            magnification_key,
            autoscale_key,
            normalize_key,
            invert_key,
            equalize_histogram_key,
            saturated_pixels_key,
            threshold_key,
            current_threshold,
            max_threshold_val,
            roi_rotation_key,
        )

        _update_session_state_and_trigger_analysis(
            keys,
            unique_id,
            selected_group,
            selected_element,
            magnification,
            autoscale,
            normalize,
            invert,
            equalize_histogram,
            saturated_pixels,
            threshold,
            new_rotation,
            roi_rotation_key,
            magnification_key,
            autoscale_key,
            invert_key,
            normalize_key,
            saturated_pixels_key,
            equalize_histogram_key,
            threshold_key,
            settings_changed_key,
            idx,
            image,
            temp_path,
            last_roi_rotation_key,
        )

        _display_detailed_analysis_results(keys)


def _load_and_display_image_header(
    uploaded_file, idx, filename, keys, default_values, bit_depth_key
):
    """Loads the image and displays the header section for an image."""
    image, temp_path = process_uploaded_file(uploaded_file)
    if image is None:
        st.error(f"❌ Failed to load image: {filename}")
        return None, None
    st.session_state[keys["image_path"]] = temp_path

    header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
    with header_col1:
        if default_values:
            values_list = [
                (
                    f"🔍 {default_values['magnification']}×"
                    if "magnification" in default_values
                    else ""
                ),
                f"📊 G{default_values['group']}" if "group" in default_values else "",
                (
                    f"🎯 E{default_values['element']}"
                    if "element" in default_values
                    else ""
                ),
            ]
            if values_list := [v for v in values_list if v]:
                st.success(f"**Auto-detected:** {' • '.join(values_list)}")
        else:
            st.info("**Ready for analysis** - Configure settings below")
    with header_col2:
        bit_depth = st.session_state.get(bit_depth_key, 8)
        st.info(f"**{bit_depth}-bit** (0-{(1 << bit_depth)-1})")
    with header_col3:
        if roi_tuple := display_roi_info(idx, image):
            # Attempt to get profile range from the *processed* image
            temp_roi_for_header = extract_roi_image(image, roi_tuple)
            if temp_roi_for_header is not None:
                profile_max_for_header = np.max(temp_roi_for_header, axis=0)
                if len(profile_max_for_header) > 0:
                    min_val_h, max_val_h = np.min(profile_max_for_header), np.max(
                        profile_max_for_header
                    )
                    st.metric("Profile Range", f"{int(min_val_h)}-{int(max_val_h)}")
                else:
                    st.info("**Profile:** Not available")
            else:
                st.info("**Profile:** Not available")

        else:
            st.info("**Profile:** Select ROI")
    st.markdown("---")
    return image, temp_path


def _calculate_threshold_defaults(image_for_roi, roi_tuple):
    """Calculates default and max threshold values based on ROI profile."""
    default_threshold = 50
    max_threshold = 255
    if roi_tuple:
        temp_roi = extract_roi_image(image_for_roi, roi_tuple)  # Use the passed image
        if temp_roi is not None:
            profile_max = np.max(temp_roi, axis=0)
            if len(profile_max) > 0:
                min_val, max_val = np.min(profile_max), np.max(profile_max)
                default_threshold = int(min_val + (max_val - min_val) * 0.4)
                default_threshold = max(0, min(255, default_threshold))
    return default_threshold, max_threshold


def _display_combined_analysis_interface(
    idx,
    uploaded_file,
    image,
    keys,
    unique_id,
    default_group,
    default_element,
    magnification_key,
    autoscale_key,
    normalize_key,
    invert_key,
    equalize_histogram_key,
    saturated_pixels_key,
    threshold_key,
    current_threshold,
    max_threshold_val,
    roi_rotation_key,
):
    """Combined interface - settings and ROI selection in one streamlined view."""
    
    # Main content in two columns: Settings on left, ROI & Results on right
    settings_col, roi_col = st.columns([1, 1.2])

    with settings_col:
        st.markdown("### ⚙️ Analysis Setup")

        # Target parameters in a container
        with st.container():
            st.markdown("**🎯 Target Parameters**")
            group_options = ["-2", "-1", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            selected_group = st.radio(
                "Group",
                options=group_options,
                index=(
                    group_options.index(str(default_group))
                    if str(default_group) in group_options
                    else 2
                ),
                key=f"group_radio_{unique_id}",
                horizontal=True,
                help="USAF target group number",
            )
            element_options = ["1", "2", "3", "4", "5", "6"]
            selected_element = st.radio(
                "Element",
                options=element_options,
                index=int(default_element) - 1 if 0 < int(default_element) <= 6 else 0,
                key=f"element_radio_{unique_id}",
                horizontal=True,
                help="USAF target element number",
            )
            magnification = st.number_input(
                "Magnification (×)",
                min_value=0.1,
                max_value=1000.0,
                value=st.session_state[magnification_key],
                step=0.1,
                format="%.1f",
                key=f"magnification_widget_{unique_id}",
                help="Optical magnification for display",
            )

        st.markdown("---")

        # Analysis controls in a container
        with st.container():
            st.markdown("**🔍 Analysis Controls**")
            threshold = st.slider(
                "Threshold Line",
                min_value=0,
                max_value=max_threshold_val,
                value=current_threshold,
                key=f"threshold_widget_{unique_id}",
                help="Edge detection threshold - adjust to optimize line detection",
            )

            prev_rotation = st.session_state.get(roi_rotation_key, 0)
            rotation_options = ["0°", "90°", "180°", "270°"]
            selected_rotation_str = st.radio(
                "ROI Rotation",
                options=rotation_options,
                index=prev_rotation,
                horizontal=True,
                key=f"roi_rotation_radio_{unique_id}",
                help="Rotate extracted ROI for optimal line pair orientation",
            )
            new_rotation = rotation_options.index(selected_rotation_str)

        st.markdown("---")

        # Image processing in an expander to save space
        with st.expander("🖼️ Image Processing Options", expanded=False):
            toggle_col1, toggle_col2 = st.columns(2)
            with toggle_col1:
                autoscale = st.toggle(
                    "Autoscale",
                    value=st.session_state[autoscale_key],
                    key=f"autoscale_widget_{unique_id}",
                    help="Percentile-based contrast",
                )
                normalize = st.toggle(
                    "Normalize", 
                    value=st.session_state[normalize_key],
                    key=f"normalize_widget_{unique_id}",
                    help="Full range (0-255)",
                )
            with toggle_col2:
                invert = st.toggle(
                    "Invert",
                    value=st.session_state[invert_key],
                    key=f"invert_widget_{unique_id}",
                    help="Invert colors",
                )
                equalize_histogram = st.toggle(
                    "Equalize",
                    value=st.session_state[equalize_histogram_key],
                    key=f"equalize_histogram_widget_{unique_id}",
                    help="Histogram equalization",
                )
            saturated_pixels = st.slider(
                "Saturated Pixels (%)",
                min_value=0.0,
                max_value=20.0,
                value=st.session_state[saturated_pixels_key],
                step=0.1,
                format="%.1f",
                key=f"saturated_pixels_widget_{unique_id}",
                disabled=not autoscale,
                help="Percentage of pixels to saturate",
            )

    with roi_col:
        st.markdown("### 🎯 ROI Selection & Results")

        # ROI selection
        st.markdown("**Select Analysis Region**")
        pil_img = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_img)
        current_coords = st.session_state.get(keys["coordinates"])

        if current_coords:
            p1, p2 = current_coords
            coords = (
                min(p1[0], p2[0]),
                min(p1[1], p2[1]),
                max(p1[0], p2[0]),
                max(p1[1], p2[1]),
            )
            roi_valid_status = st.session_state.get(keys["roi_valid"], False)
            outline_color = (
                ROI_COLORS[idx % len(ROI_COLORS)]
                if roi_valid_status
                else INVALID_ROI_COLOR
            )
            draw.rectangle(coords, outline=outline_color, width=3)

        if roi_changed := handle_image_selection(
            idx, uploaded_file, pil_img, key=f"usaf_image_{idx}", rotation=0
        ):
            st.session_state[f"settings_changed_{unique_id}"] = True

        # ROI status
        if current_coords:
            if st.session_state.get(keys["roi_valid"], False):
                st.success("✅ **Valid ROI selected** - Ready for analysis")
            else:
                st.error("❌ **Invalid ROI** - Please reselect area")
        else:
            st.info("👆 **Click and drag** to select analysis region")

        st.markdown("---")

        # Results section
        st.markdown("**📊 Analysis Results**")
        if analysis_results_for_plot := st.session_state.get(
            keys["analysis_results"]
        ):
            roi_rotation_from_results = analysis_results_for_plot.get("roi_rotation", 0)
            roi_for_display = extract_roi_image(
                image,
                st.session_state.get(keys["analyzed_roi"]),
                rotation=roi_rotation_from_results,
            )

            current_magnification = st.session_state.get(magnification_key, 10.0)
            visualizer = ProfileVisualizer()
            group_val_plot = st.session_state.get(keys["last_group"])
            element_val_plot = st.session_state.get(keys["last_element"])
            lp_width_um_plot = None
            if (
                group_val_plot is not None
                and element_val_plot is not None
                and "usaf_target" in st.session_state
            ):
                lp_width_um_plot = st.session_state.usaf_target.line_pair_width_microns(
                    group_val_plot, element_val_plot
                )

            if fig := visualizer.visualize_profile(
                analysis_results_for_plot,
                roi_for_display,
                group=group_val_plot,
                element=element_val_plot,
                lp_width_um=lp_width_um_plot,
                magnification=current_magnification,
            ):
                st.pyplot(fig)
                # Download button
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
                buf.seek(0)
                pixel_size_str_fig = "NA"
                if (
                    lp_width_um_plot
                    and analysis_results_for_plot.get("avg_line_pair_width", 0) > 0
                ):
                    pixel_size_fig = (
                        lp_width_um_plot
                        / analysis_results_for_plot["avg_line_pair_width"]
                    )
                    pixel_size_str_fig = f"{pixel_size_fig:.3f}um"

                group_str_fig = (
                    f"group{group_val_plot}"
                    if group_val_plot is not None
                    else "groupNA"
                )
                mag_str_fig = (
                    f"mag{int(round(current_magnification))}x"
                    if current_magnification is not None
                    else "magNA"
                )
                plot_file_name = f"usaf_processed_{group_str_fig}_pix{pixel_size_str_fig}_{mag_str_fig}.png"

                st.download_button(
                    label="📥 Download Plot",
                    data=buf,
                    file_name=plot_file_name,
                    mime="image/png",
                    use_container_width=True,
                )
                caption_text = visualizer.create_caption(
                    group_val_plot,
                    element_val_plot,
                    lp_width_um_plot,
                    edge_method=analysis_results_for_plot.get(
                        "edge_method", "original"
                    ),
                )
                st.markdown(caption_text, unsafe_allow_html=True)

        elif current_coords:  # ROI selected, but no analysis results yet
            try:
                p1_preview, p2_preview = current_coords
                coords_preview = (
                    min(p1_preview[0], p2_preview[0]),
                    min(p1_preview[1], p2_preview[1]),
                    max(p1_preview[0], p2_preview[0]),
                    max(p1_preview[1], p2_preview[1]),
                )
                roi_rotation_preview = st.session_state.get(
                    f"roi_rotation_{unique_id}", 0
                )
                roi_img_preview = Image.fromarray(image).crop(coords_preview)
                if roi_rotation_preview > 0:
                    roi_img_preview = Image.fromarray(
                        rotate_image(np.array(roi_img_preview), roi_rotation_preview)
                    )
                st.image(
                    roi_img_preview, caption="🔍 ROI Preview", use_container_width=True
                )
                st.info(
                    "💡 **Adjust settings** and the analysis will update automatically"
                )
            except Exception as e:
                st.warning(f"⚠️ Could not display ROI preview: {e!s}")
        else:
            st.info("👆 **Select an ROI above** to view analysis results")

    return (
        selected_group,
        selected_element,
        magnification,
        autoscale,
        normalize,
        invert,
        equalize_histogram,
        saturated_pixels,
        threshold,
        new_rotation,
    )





def _update_session_state_and_trigger_analysis(
    keys,
    unique_id,
    selected_group,
    selected_element,
    magnification,
    autoscale,
    normalize,
    invert,
    equalize_histogram,
    saturated_pixels,
    threshold,
    new_rotation,
    roi_rotation_key,
    magnification_key,
    autoscale_key,
    invert_key,
    normalize_key,
    saturated_pixels_key,
    equalize_histogram_key,
    threshold_key,
    settings_changed_key,
    idx,
    image,
    temp_path,
    last_roi_rotation_key,
):
    """Updates session state based on UI changes and triggers analysis if needed."""
    settings_changed = False
    if st.session_state.get(keys["group"]) != int(selected_group):
        st.session_state[keys["group"]] = int(selected_group)
        settings_changed = True
    if st.session_state.get(keys["element"]) != int(selected_element):
        st.session_state[keys["element"]] = int(selected_element)
        settings_changed = True
    # ... (similar checks for all other settings: magnification, autoscale, etc.) ...
    if st.session_state.get(magnification_key) != magnification:
        st.session_state[magnification_key] = magnification
        settings_changed = True
    if st.session_state.get(autoscale_key) != autoscale:
        st.session_state[autoscale_key] = autoscale
        settings_changed = True
    if st.session_state.get(invert_key) != invert:
        st.session_state[invert_key] = invert
        settings_changed = True
    if st.session_state.get(normalize_key) != normalize:
        st.session_state[normalize_key] = normalize
        settings_changed = True
    if st.session_state.get(saturated_pixels_key) != saturated_pixels:
        st.session_state[saturated_pixels_key] = saturated_pixels
        settings_changed = True
    if st.session_state.get(equalize_histogram_key) != equalize_histogram:
        st.session_state[equalize_histogram_key] = equalize_histogram
        settings_changed = True
    if (
        st.session_state.get(threshold_key) != threshold
    ):  # Ensure threshold_key is used for comparison
        st.session_state[threshold_key] = threshold
        settings_changed = True
    if st.session_state.get(roi_rotation_key, 0) != new_rotation:
        st.session_state[roi_rotation_key] = new_rotation
        settings_changed = True

    if settings_changed:
        st.session_state[settings_changed_key] = True

    current_selected_roi_tuple = display_roi_info(idx, image)
    group_for_trigger = st.session_state.get(keys["group"])
    element_for_trigger = st.session_state.get(keys["element"])
    roi_is_valid = st.session_state.get(keys["roi_valid"], False)

    # Use the updated threshold from session_state for analysis
    threshold_for_analysis = st.session_state.get(
        threshold_key, 50
    )  # Default if not found
    threshold_for_analysis = max(0, min(255, threshold_for_analysis))

    roi_rotation_for_analysis = st.session_state.get(roi_rotation_key, 0)

    if should_analyze := (
        st.session_state.get(settings_changed_key, False)
        and current_selected_roi_tuple is not None
        and roi_is_valid
        and group_for_trigger is not None
        and element_for_trigger is not None
    ):
        with st.spinner("🔄 Analyzing image..."):
            try:
                img_proc = ImageProcessor(usaf_target=st.session_state.usaf_target)
                processing_params_analysis = {
                    "autoscale": st.session_state[autoscale_key],
                    "invert": st.session_state[invert_key],
                    "normalize": st.session_state[normalize_key],
                    "saturated_pixels": st.session_state[saturated_pixels_key],
                    "equalize_histogram": st.session_state[equalize_histogram_key],
                }
                results_data = img_proc.process_and_analyze(
                    temp_path,
                    current_selected_roi_tuple,
                    group_for_trigger,
                    element_for_trigger,
                    use_max=True,
                    threshold=threshold_for_analysis,
                    roi_rotation=roi_rotation_for_analysis,
                    **processing_params_analysis,
                )
                st.session_state[keys["analyzed_roi"]] = current_selected_roi_tuple
                st.session_state[keys["analysis_results"]] = results_data
                st.session_state[keys["last_group"]] = group_for_trigger
                st.session_state[keys["last_element"]] = element_for_trigger
                st.session_state[last_roi_rotation_key] = roi_rotation_for_analysis
                st.session_state[settings_changed_key] = False
                st.success("✅ **Analysis completed successfully!**")
                st.rerun()
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                st.error(f"❌ **Analysis failed:** {e!s}")
                st.error(f"**Error details:** {type(e).__name__} - {e!s}")


def _display_detailed_analysis_results(keys):
    """Displays the detailed analysis results in an expander."""
    if analysis_results_for_details := st.session_state.get(keys["analysis_results"]):
        with st.expander("📈 **Detailed Analysis Results**", expanded=False):
            display_analysis_details(analysis_results_for_details)


def collect_analysis_data():
    """
    Collect analysis data for all processed images

    Returns:
        pandas.DataFrame: DataFrame with analysis data
    """
    data = {
        "Filename": [],
        "Magnification": [],
        "Group": [],
        "Element": [],
        "Line Pairs/mm": [],
        "Line Pair Width (µm)": [],
        "Pixel Size (µm/pixel)": [],
        "Contrast": [],
        "Line Pairs Detected": [],
        "Avg Line Pair Width (px)": [],
        "ROI Rotation": [],
    }

    for idx, uploaded_file in enumerate(st.session_state.uploaded_files_list):
        # Get unique ID and keys for this image
        unique_id = get_unique_id_for_image(uploaded_file)
        keys = get_image_session_keys(idx, uploaded_file)

        # Check if we have analysis results for this image
        if analysis_results := st.session_state.get(keys["analysis_results"]):
            # Get filename
            filename = st.session_state.get(keys["image_name"], f"Image {idx+1}")
            data["Filename"].append(filename)

            # Get magnification
            magnification = st.session_state.get(f"magnification_{unique_id}", 0)
            data["Magnification"].append(magnification)

            # Get group and element
            group = analysis_results.get("group", 0)
            element = analysis_results.get("element", 0)
            data["Group"].append(group)
            data["Element"].append(element)

            # Get line pairs per mm
            lp_per_mm = analysis_results.get("lp_per_mm", 0)
            data["Line Pairs/mm"].append(lp_per_mm)

            # Get theoretical line pair width in microns
            lp_width_um = analysis_results.get("theoretical_lp_width_um", 0)
            data["Line Pair Width (µm)"].append(lp_width_um)

            # Calculate pixel size
            avg_lp_width_px = analysis_results.get("avg_line_pair_width", 0)
            if avg_lp_width_px > 0 and lp_width_um > 0:
                pixel_size = lp_width_um / avg_lp_width_px
            else:
                pixel_size = 0
            data["Pixel Size (µm/pixel)"].append(pixel_size)

            # Get contrast
            contrast = analysis_results.get("contrast", 0)
            data["Contrast"].append(contrast)

            # Get number of line pairs detected
            num_line_pairs = analysis_results.get("num_line_pairs", 0)
            data["Line Pairs Detected"].append(num_line_pairs)

            # Get average line pair width in pixels
            data["Avg Line Pair Width (px)"].append(avg_lp_width_px)

            # Get ROI rotation
            roi_rotation = analysis_results.get("roi_rotation", 0)
            data["ROI Rotation"].append(f"{roi_rotation * 90}°")

    return pd.DataFrame(data)


def run_usaf_analyzer():
    """
    Main function to run the USAF Target Analyzer as a page within the main app.
    Note: st.set_page_config is handled by the main app, so we don't call it here.
    """
    try:
        initialize_session_state()
        _display_page_header()

        with st.container():
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            _display_control_tabs()
            st.markdown("</div>", unsafe_allow_html=True)

        _display_main_content()

    except Exception as e:
        st.error(f"❌ **Application Error:** {e}")
        st.info(
            "💡 For detailed error information, set DEBUG=1 in environment variables."
        )


def _display_page_header():
    """Displays the main page header."""
    st.title("🎯 USAF Target Analyzer")
    st.subheader(
        "Comprehensive analysis tool for USAF 1951 resolution targets in microscopy and imaging systems"
    )


def _display_control_tabs():
    """Displays the streamlined control panel with fewer tabs."""
    # Combine upload and manage into one tab, keep export and help separate
    main_tab, export_tab, help_tab = st.tabs(
        ["📁 Images & Management", "📤 Export Results", "💡 Help & Tips"]
    )
    with main_tab:
        _display_images_and_management_tab()
    with export_tab:
        _display_export_tab()
    with help_tab:
        _display_help_tab()


def _display_images_and_management_tab():
    """Combined upload and management functionality in one streamlined interface."""
    # Top row: Upload and status
    upload_col, status_col, manage_col = st.columns([2, 1, 1])

    with upload_col:
        st.markdown("**📁 Upload Images**")
        if new_uploaded_files := st.file_uploader(
            "Select USAF target image(s)",
            type=["jpg", "jpeg", "png", "tif", "tiff"],
            accept_multiple_files=True,
            help="Upload one or more images containing a USAF 1951 resolution target",
        ):
            for file in new_uploaded_files:
                file_names = [
                    f.name if hasattr(f, "name") else os.path.basename(f)
                    for f in st.session_state.uploaded_files_list
                ]
                new_file_name = (
                    file.name if hasattr(file, "name") else os.path.basename(file)
                )
                if new_file_name not in file_names:
                    st.session_state.uploaded_files_list.append(file)
                    st.success(f"✅ **Added:** {new_file_name}")

    with status_col:
        st.markdown("**📊 Status**")
        if st.session_state.uploaded_files_list:
            st.info(f"**{len(st.session_state.uploaded_files_list)}** loaded")
            analyzed_count = sum(bool(st.session_state.get(
                                                 get_image_session_keys(idx, uploaded_file)["analysis_results"]
                                             ))
                             for idx, uploaded_file in enumerate(
                                                 st.session_state.uploaded_files_list
                                             ))
            if analyzed_count > 0:
                st.success(f"**{analyzed_count}** analyzed")
            else:
                st.warning("**None analyzed**")
        else:
            st.info("**No images**")

    with manage_col:
        st.markdown("**🗂️ Management**")
        # Auto-load default image if no images present
        default_image_path = load_default_image()
        if (
            not st.session_state.uploaded_files_list
            and default_image_path
            and not st.session_state.default_image_added
        ):
            st.session_state.uploaded_files_list.append(default_image_path)
            st.session_state.default_image_added = True
            st.info("📷 Default loaded")

        if st.button("🗑️ Clear All", use_container_width=True, type="secondary"):
            st.session_state.uploaded_files_list = []
            st.session_state.default_image_added = False
            st.session_state.image_index_to_id = {}
            for key in list(st.session_state.keys()):
                if any(key.startswith(prefix) for prefix in SESSION_STATE_PREFIXES):
                    del st.session_state[key]
            st.success("✅ **All images cleared**")
            st.rerun()

    # Bottom section: Loaded images list (only if there are images)
    if st.session_state.uploaded_files_list:
        st.markdown("---")
        st.markdown("**📋 Loaded Images**")

        # Create a more compact display
        for idx, uploaded_file in enumerate(st.session_state.uploaded_files_list):
            filename = (
                uploaded_file.name
                if hasattr(uploaded_file, "name")
                else (
                    os.path.basename(uploaded_file)
                    if isinstance(uploaded_file, str)
                    else f"Image {idx+1}"
                )
            )
            keys = get_image_session_keys(idx, uploaded_file)
            has_results = st.session_state.get(keys["analysis_results"])

            # Use columns for a more compact layout
            img_col1, img_col2, img_col3 = st.columns([3, 1, 1])
            with img_col1:
                st.text(f"{idx+1}. {filename}")
            with img_col2:
                if has_results:
                    st.success("✅ Done")
                else:
                    st.warning("⏳ Pending")
            with img_col3:
                # Quick jump to image (optional enhancement for later)
                if has_results:
                    group = st.session_state.get(keys["last_group"], "?")
                    element = st.session_state.get(keys["last_element"], "?")
                    st.text(f"G{group}E{element}")
                else:
                    st.text("—")


def _display_export_tab():
    """Displays the content of the 'Export Results' tab."""
    st.markdown("#### 📤 **Export Analysis Results**")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📊 **Generate Analysis CSV**", use_container_width=True):
            if not st.session_state.uploaded_files_list:
                st.warning("⚠️ No images uploaded for analysis.")
            else:
                df = collect_analysis_data()
                if df.empty:
                    st.warning(
                        "⚠️ No analysis data available. Please analyze images first."
                    )
                else:
                    csv = df.to_csv(index=False)
                    st.session_state["csv_data"] = csv
                    st.session_state["csv_df"] = df
                    st.success(f"✅ **CSV generated with {len(df)} results**")
    with col2:
        if "csv_data" in st.session_state:
            st.download_button(
                label="📥 **Download CSV**",
                data=st.session_state["csv_data"],
                file_name="usaf_analysis_results.csv",
                mime="text/csv",
                use_container_width=True,
            )
            if st.checkbox("👀 **Show CSV Preview**"):
                st.dataframe(st.session_state["csv_df"], use_container_width=True)


def _display_help_tab():
    """Displays the content of the 'Help & Tips' tab."""
    help_col1, help_col2 = st.columns(2)
    with help_col1:
        st.markdown("#### 🎯 **ROI Selection Guide**")
        st.markdown(
            """
        - **Click and drag** on the image to select your region of interest
        - Select an area containing **clear line pairs**
        - Ensure the ROI is **large enough** to capture multiple line pairs
        - The ROI outline will be **green** when valid, **red** when invalid
        
        **Best practices:**
        - Include at least 3-5 line pairs in your ROI
        - Avoid edges and artifacts
        - Center the ROI on the clearest part of the target
        """
        )
        st.markdown("#### 🔄 **Image Rotation**")
        st.markdown(
            """
        Use the **ROI Rotation** controls to align line pairs horizontally 
        for optimal analysis when your USAF target appears tilted in the image.
        
        **Tip:** Most accurate results occur when line pairs are horizontal.
        """
        )
    with help_col2:
        st.markdown("#### ⚙️ **Settings Guide**")
        st.markdown(
            """
        **Image Processing:**
        - **Autoscale**: Automatic contrast adjustment (recommended)
        - **Normalize**: Use full intensity range
        - **Invert**: Flip dark/light (useful for some microscopy images)
        - **Equalize**: Enhance contrast using histogram equalization
        
        **Analysis:**
        - **Threshold**: Adjust edge detection sensitivity
        - **Group/Element**: Select the USAF target pattern to analyze
        """
        )
        st.markdown("#### 📏 **Understanding Results**")
        st.markdown(
            """
        **Key Metrics:**
        - **Line Pairs/mm**: Spatial frequency of the target
        - **Pixel Size**: Physical size per pixel in micrometers
        - **Contrast**: Measure of image sharpness
        - **Line Pair Width**: Theoretical width in micrometers
        
        **Quality Indicators:**
        - Higher contrast = better image quality
        - More detected line pairs = better resolution
        """
        )


def _display_main_content():
    """Displays the main content area with image analysis or welcome screen."""
    main_container = st.container()
    with main_container:
        if st.session_state.uploaded_files_list:
            for idx, uploaded_file in enumerate(st.session_state.uploaded_files_list):
                analyze_and_display_image(idx, uploaded_file)
        else:
            display_welcome_screen()


if __name__ == "__main__":
    st.set_page_config(
        page_title="USAF Target Analyzer",
        layout="wide",
        page_icon="🎯",
        initial_sidebar_state="collapsed",
    )
    run_usaf_analyzer()
