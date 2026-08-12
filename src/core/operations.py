"""Save file operations.

Deliberately free of any Qt import so these can be unit tested without a display
and run on a worker thread without touching widgets. Every long-running function
accepts `progress` and `is_cancelled` callbacks; the UI supplies them, tests do
not have to.
"""
import contextlib
import os
import shutil
import zipfile
from collections.abc import Callable
from datetime import datetime

ProgressFn = Callable[[int, int], None]
CancelFn = Callable[[], bool]

# An archive claiming to expand beyond this is refused rather than allowed to
# fill the user's disk. Generous enough for any real save.
MAX_EXTRACT_BYTES = 20 * 1024 ** 3


class OperationCancelled(Exception):
    """Raised internally when the user cancels; callers treat it as a clean stop."""


def _check(is_cancelled: CancelFn | None) -> None:
    if is_cancelled is not None and is_cancelled():
        raise OperationCancelled()


def timestamp_suffix() -> str:
    """Shared by backup and export so the two cannot drift apart."""
    return datetime.now().strftime("%Y.%m.%d-%H.%M.%S")


def unique_path(path: str) -> str:
    """Return `path`, or `path_2`/`path_3`... if it is already taken.

    The timestamp only has one-second resolution, so two backups made in the
    same second would otherwise collide.
    """
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    counter = 2
    while os.path.exists(f"{root}_{counter}{ext}"):
        counter += 1
    return f"{root}_{counter}{ext}"


def _walk_files(root: str) -> list[str]:
    return [
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(root)
        for filename in filenames
    ]


def copy_save(
    source_path: str,
    destination_path: str,
    progress: ProgressFn | None = None,
    is_cancelled: CancelFn | None = None,
) -> None:
    """Copy a save directory, reporting progress and honouring cancellation.

    On cancellation or failure the partial destination is removed. Leaving it
    behind would put a half-copied directory in the saves folder, where the app
    (and the game) would list it as a real save.
    """
    files = _walk_files(source_path)
    total = len(files)
    try:
        os.makedirs(destination_path, exist_ok=True)
        for index, abs_path in enumerate(files, 1):
            _check(is_cancelled)
            relative = os.path.relpath(abs_path, source_path)
            target = os.path.join(destination_path, relative)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(abs_path, target)
            if progress is not None:
                progress(index, total)
        # Preserve empty directories, which walking files alone would drop.
        for dirpath, dirnames, _ in os.walk(source_path):
            for dirname in dirnames:
                relative = os.path.relpath(os.path.join(dirpath, dirname), source_path)
                os.makedirs(os.path.join(destination_path, relative), exist_ok=True)
    except BaseException:
        shutil.rmtree(destination_path, ignore_errors=True)
        raise


def delete_save(
    source_path: str,
    progress: ProgressFn | None = None,
    is_cancelled: CancelFn | None = None,
) -> None:
    """Delete a save directory.

    Intentionally not cancellable: stopping halfway through would leave a
    partially deleted save, which is worse than finishing.
    """
    shutil.rmtree(source_path)
    if progress is not None:
        progress(1, 1)


def export_save(
    source_path: str,
    zip_path: str,
    compresslevel: int = 1,
    progress: ProgressFn | None = None,
    is_cancelled: CancelFn | None = None,
) -> None:
    """Zip a save directory.

    compresslevel defaults to 1 rather than zlib's default of 6: save payloads
    are dominated by already-compressed region data, so level 6 costs ~20% more
    time for an archive of effectively identical size.
    """
    files = _walk_files(source_path)
    total = len(files)
    base = os.path.dirname(source_path)
    try:
        with zipfile.ZipFile(
            zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=compresslevel
        ) as zip_file:
            for index, abs_path in enumerate(files, 1):
                _check(is_cancelled)
                zip_file.write(abs_path, os.path.relpath(abs_path, base))
                if progress is not None:
                    progress(index, total)
    except BaseException:
        # A partial zip is not a usable backup; do not leave one lying around.
        if os.path.exists(zip_path):
            with contextlib.suppress(OSError):
                os.unlink(zip_path)
        raise


def archive_conflicts(zip_path: str, target_dir: str) -> list[str]:
    """Top-level names in the archive that already exist in `target_dir`.

    Checks *every* top-level entry. Inspecting only the first one (as the
    original did) let a multi-root archive, or one whose first entry is a loose
    file, overwrite existing saves without warning.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        names = zip_file.namelist()
    top_level = {name.replace("\\", "/").split("/")[0] for name in names if name.strip()}
    return sorted(
        name for name in top_level if os.path.exists(os.path.join(target_dir, name))
    )


def archive_uncompressed_size(zip_path: str) -> int:
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        return sum(info.file_size for info in zip_file.infolist())


def import_save(
    zip_path: str,
    target_dir: str,
    max_bytes: int = MAX_EXTRACT_BYTES,
    progress: ProgressFn | None = None,
    is_cancelled: CancelFn | None = None,
) -> None:
    """Extract an archive into `target_dir` after validating it.

    Path traversal needs no handling here: CPython's ZipFile._extract_member
    already strips drive letters and '..' components, so extract() cannot write
    outside the target. What it does not do is bound the output size, hence the
    max_bytes check.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        infos = zip_file.infolist()
        if not infos:
            raise ValueError("Empty archive")

        total_size = sum(info.file_size for info in infos)
        if total_size > max_bytes:
            raise ValueError(
                f"Archive expands to {total_size / 1024 ** 3:.1f} GB, "
                f"above the {max_bytes / 1024 ** 3:.0f} GB limit"
            )

        total = len(infos)
        for index, info in enumerate(infos, 1):
            _check(is_cancelled)
            zip_file.extract(info, target_dir)
            if progress is not None:
                progress(index, total)
