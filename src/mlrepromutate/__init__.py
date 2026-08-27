"""MLReproMutate: mutation testing for ML experiment reproducibility."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mlrepromutate")
except PackageNotFoundError:
    __version__ = "0+unknown"
