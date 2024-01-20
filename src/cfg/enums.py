""" Global Enums/Types for the project. """
from enum import Enum
from pathlib import Path


class DatasetType(Enum):
    """Enum for the dataset type."""

    ANIME_DATASET = Path(
        "/media/omarabdelgawad/New Volume/Datasets/image_coloring/anime_dataset/"
    )
    NATURAL_VIEW_DATASET = Path(
        "/media/omarabdelgawad/New Volume/Datasets/image_coloring/natural_view/"
    )
    EDGES2SHOES = Path(
        "/media/omarabdelgawad/New Volume/Datasets/image_coloring/edges2shoes/"
    )
    AFHQ_CATS_DATASET = Path("/home/eyad/Downloads/afhq/")


class PaddingType(Enum):
    """Enum for the padding type."""

    REFLECT = "reflect"
    REPLICATE = "replicate"
    ZERO = "zero"


class NormalizationType(Enum):
    """Enum for the normalization type."""

    BATCH = "batch"
    INSTANCE = "instance"
    LAYER = "layer"
    NONE = None


class ActivationType(Enum):
    """Enum for the activation type."""

    RELU = "relu"
    LEAKY_RELU = "leaky_relu"
    TANH = "tanh"
    SIGMOID = "sigmoid"
    NONE = None
