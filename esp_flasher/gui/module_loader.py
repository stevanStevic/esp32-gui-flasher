import importlib.util
import inspect
import logging
import os
import sys

from esp_flasher.gui.module_base import GUIModule

logger = logging.getLogger(__name__)


def _import_module_from_file(path: str):
    """Import a single .py file and return the loaded Python module."""
    module_name = os.path.splitext(os.path.basename(path))[0]
    unique_name = f"esp_flasher_module_{module_name}_{id(path)}"

    spec = importlib.util.spec_from_file_location(unique_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create module spec for: {path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _resolve_path(path: str) -> str:
    """Resolve a module path to a concrete .py file.

    Accepts either:
      - A path to a ``.py`` file (returned as-is after validation).
      - A path to a Python package directory containing ``__init__.py``
        (returns the ``__init__.py`` path).
    """
    path = os.path.abspath(path)

    if os.path.isfile(path):
        if not path.endswith(".py"):
            raise ValueError(f"Module file must be a .py file, got: {path}")
        return path

    if os.path.isdir(path):
        init_file = os.path.join(path, "__init__.py")
        if os.path.isfile(init_file):
            return init_file
        raise ValueError(
            f"Module directory has no __init__.py: {path}"
        )

    raise FileNotFoundError(f"Module path not found: {path}")


def _find_gui_module_class(mod, path: str):
    """Find the first concrete GUIModule subclass in a loaded module."""
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, GUIModule) and obj is not GUIModule:
            return obj

    raise ValueError(
        f"No GUIModule subclass found in {path}. "
        f"The file must contain a class that inherits from "
        f"esp_flasher.gui.module_base.GUIModule."
    )


def load_modules(paths: list) -> list:
    """Dynamically load GUIModule subclasses from paths.

    Each path can be either a ``.py`` file or a Python package directory
    (containing ``__init__.py``).

    For each path the loader will:
      1. Resolve the path to a concrete ``.py`` file.
      2. Import it as a Python module.
      3. Find the first class that is a concrete subclass of ``GUIModule``.
      4. Instantiate it (no-arg constructor) and append to the result list.

    Args:
        paths: List of filesystem paths to ``.py`` files or package directories.

    Returns:
        A list of ``GUIModule`` instances, one per successfully loaded path.

    Raises:
        FileNotFoundError: If a path does not exist.
        ValueError: If a file has no ``GUIModule`` subclass.
        RuntimeError: If module instantiation fails.
    """
    modules: list[GUIModule] = []

    for path in paths:
        resolved = _resolve_path(path)

        try:
            mod = _import_module_from_file(resolved)
        except Exception as exc:
            raise RuntimeError(f"Failed to import module from {resolved}: {exc}") from exc

        gui_module_cls = _find_gui_module_class(mod, resolved)

        try:
            instance = gui_module_cls()
        except Exception as exc:
            raise RuntimeError(
                f"Failed to instantiate {gui_module_cls.__name__} from {resolved}: {exc}"
            ) from exc

        logger.info(f"Loaded module: {instance.get_name()} ({resolved})")
        modules.append(instance)

    return modules
