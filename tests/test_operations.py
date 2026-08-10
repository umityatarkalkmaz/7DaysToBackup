import filecmp
import os
import zipfile

import pytest

from src.core import operations


def build_save(root, name="SaveA", files=None):
    """Create a small save-shaped directory tree."""
    files = files or {"Region/r.0.7rg": b"region-data", "player.ttp": b"player-data"}
    save_dir = os.path.join(str(root), name)
    for rel, content in files.items():
        path = os.path.join(save_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
    return save_dir


def trees_equal(a, b):
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(
        trees_equal(os.path.join(a, sub), os.path.join(b, sub))
        for sub in cmp.common_dirs
    )


# --------------------------------------------------------------- copy / backup


def test_copy_save_reproduces_tree(tmp_path):
    src = build_save(tmp_path)
    dst = os.path.join(str(tmp_path), "SaveA_backup")
    operations.copy_save(src, dst)
    assert trees_equal(src, dst)


def test_copy_save_reports_progress(tmp_path):
    src = build_save(tmp_path)
    seen = []
    operations.copy_save(
        src,
        os.path.join(str(tmp_path), "b"),
        progress=lambda done, total: seen.append((done, total)),
    )
    assert seen == [(1, 2), (2, 2)]


def test_copy_save_preserves_empty_directories(tmp_path):
    src = build_save(tmp_path)
    os.makedirs(os.path.join(src, "EmptyDir"))
    dst = os.path.join(str(tmp_path), "copy")
    operations.copy_save(src, dst)
    assert os.path.isdir(os.path.join(dst, "EmptyDir"))


def test_cancelled_copy_leaves_no_partial_directory(tmp_path):
    """A partial backup must not survive: it would be listed as a real save."""
    src = build_save(tmp_path, files={f"f{i}.bin": b"x" * 100 for i in range(10)})
    dst = os.path.join(str(tmp_path), "partial")
    calls = {"n": 0}

    def cancel_after_three():
        calls["n"] += 1
        return calls["n"] > 3

    with pytest.raises(operations.OperationCancelled):
        operations.copy_save(src, dst, is_cancelled=cancel_after_three)
    assert not os.path.exists(dst)


def test_failed_copy_leaves_no_partial_directory(tmp_path):
    src = build_save(tmp_path)
    dst = os.path.join(str(tmp_path), "partial")

    def explode():
        raise OSError("disk full")

    with pytest.raises(OSError):
        operations.copy_save(src, dst, is_cancelled=explode)
    assert not os.path.exists(dst)


# ------------------------------------------------------------------- naming


def test_unique_path_disambiguates_directories(tmp_path):
    taken = os.path.join(str(tmp_path), "SaveA_backup")
    os.makedirs(taken)
    assert operations.unique_path(taken) == taken + "_2"


def test_unique_path_keeps_extension(tmp_path):
    taken = os.path.join(str(tmp_path), "SaveA.zip")
    open(taken, "w").close()
    assert operations.unique_path(taken) == os.path.join(str(tmp_path), "SaveA_2.zip")


def test_unique_path_passes_through_when_free(tmp_path):
    free = os.path.join(str(tmp_path), "nothing-here")
    assert operations.unique_path(free) == free


def test_two_backups_in_the_same_second_do_not_collide(tmp_path):
    src = build_save(tmp_path)
    first = operations.unique_path(f"{src}_backup_{operations.timestamp_suffix()}")
    operations.copy_save(src, first)
    second = operations.unique_path(f"{src}_backup_{operations.timestamp_suffix()}")
    operations.copy_save(src, second)
    assert first != second
    assert os.path.isdir(first) and os.path.isdir(second)


# ------------------------------------------------------------ export / import


def test_export_import_round_trip(tmp_path):
    src = build_save(tmp_path)
    zip_path = os.path.join(str(tmp_path), "out.zip")
    operations.export_save(src, zip_path)

    target = os.path.join(str(tmp_path), "target")
    os.makedirs(target)
    operations.import_save(zip_path, target)
    assert trees_equal(src, os.path.join(target, "SaveA"))


@pytest.mark.parametrize("level", [1, 6, 9])
def test_round_trip_is_identical_at_every_compression_level(tmp_path, level):
    src = build_save(tmp_path)
    zip_path = os.path.join(str(tmp_path), f"out{level}.zip")
    operations.export_save(src, zip_path, compresslevel=level)
    target = os.path.join(str(tmp_path), f"t{level}")
    os.makedirs(target)
    operations.import_save(zip_path, target)
    assert trees_equal(src, os.path.join(target, "SaveA"))


def test_export_does_not_clobber_previous_archive(tmp_path):
    src = build_save(tmp_path)
    first = operations.unique_path(os.path.join(str(tmp_path), "SaveA.zip"))
    operations.export_save(src, first)
    second = operations.unique_path(os.path.join(str(tmp_path), "SaveA.zip"))
    operations.export_save(src, second)
    assert first != second
    assert os.path.exists(first) and os.path.exists(second)


def test_cancelled_export_removes_partial_archive(tmp_path):
    src = build_save(tmp_path, files={f"f{i}.bin": b"x" * 50 for i in range(10)})
    zip_path = os.path.join(str(tmp_path), "partial.zip")
    calls = {"n": 0}

    def cancel_after_two():
        calls["n"] += 1
        return calls["n"] > 2

    with pytest.raises(operations.OperationCancelled):
        operations.export_save(src, zip_path, is_cancelled=cancel_after_two)
    assert not os.path.exists(zip_path)


# ------------------------------------------------------------ import guards


def make_zip(path, names):
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, b"data")
    return path


def test_conflicts_detects_second_root(tmp_path):
    """The original guard only inspected members[0], so SaveB slipped through."""
    zip_path = make_zip(
        os.path.join(str(tmp_path), "multi.zip"),
        ["SaveA/file.txt", "SaveB/file.txt"],
    )
    target = os.path.join(str(tmp_path), "maps")
    os.makedirs(os.path.join(target, "SaveB"))
    assert operations.archive_conflicts(zip_path, target) == ["SaveB"]


def test_conflicts_detects_folder_when_first_entry_is_a_loose_file(tmp_path):
    """members[0] being a top-level file made the old check meaningless."""
    zip_path = make_zip(
        os.path.join(str(tmp_path), "filefirst.zip"),
        ["readme.txt", "SaveA/file.txt"],
    )
    target = os.path.join(str(tmp_path), "maps")
    os.makedirs(os.path.join(target, "SaveA"))
    assert operations.archive_conflicts(zip_path, target) == ["SaveA"]


def test_no_conflicts_when_target_is_clean(tmp_path):
    zip_path = make_zip(
        os.path.join(str(tmp_path), "clean.zip"), ["SaveA/file.txt"]
    )
    target = os.path.join(str(tmp_path), "maps")
    os.makedirs(target)
    assert operations.archive_conflicts(zip_path, target) == []


def test_import_refuses_oversized_archive(tmp_path):
    zip_path = make_zip(os.path.join(str(tmp_path), "big.zip"), ["SaveA/file.txt"])
    target = os.path.join(str(tmp_path), "maps")
    os.makedirs(target)
    with pytest.raises(ValueError, match="expands to"):
        operations.import_save(zip_path, target, max_bytes=1)
    assert os.listdir(target) == []


def test_import_refuses_empty_archive(tmp_path):
    zip_path = os.path.join(str(tmp_path), "empty.zip")
    with zipfile.ZipFile(zip_path, "w"):
        pass
    target = os.path.join(str(tmp_path), "maps")
    os.makedirs(target)
    with pytest.raises(ValueError, match="Empty archive"):
        operations.import_save(zip_path, target)


def test_import_cannot_escape_target_directory(tmp_path):
    """Regression guard: zipfile strips '..', and we depend on that."""
    zip_path = os.path.join(str(tmp_path), "evil.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../escaped.txt", b"pwned")
    target = os.path.join(str(tmp_path), "maps")
    os.makedirs(target)
    operations.import_save(zip_path, target)
    assert not os.path.exists(os.path.join(str(tmp_path), "escaped.txt"))
    assert os.path.exists(os.path.join(target, "escaped.txt"))


# ------------------------------------------------------------------- delete


def test_delete_save_removes_tree(tmp_path):
    src = build_save(tmp_path)
    operations.delete_save(src)
    assert not os.path.exists(src)
