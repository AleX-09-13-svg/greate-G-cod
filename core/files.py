# -*- coding: utf-8 -*-
import os


def file_snapshot(output_dir):
    return {
        name: os.path.getmtime(os.path.join(output_dir, name))
        for name in os.listdir(output_dir)
    }


def detect_changed_file(output_dir, before_files):
    after_files = file_snapshot(output_dir)
    created = sorted(set(after_files) - set(before_files))
    if created:
        return os.path.join(output_dir, created[-1])

    modified = sorted(
        name for name, mtime in after_files.items() if before_files.get(name) != mtime
    )
    if modified:
        return os.path.join(output_dir, modified[-1])

    return None


def rename_file(source_path, target_path):
    if os.path.abspath(source_path) == os.path.abspath(target_path):
        return target_path

    if os.path.exists(target_path):
        os.remove(target_path)
    os.rename(source_path, target_path)
    return target_path
