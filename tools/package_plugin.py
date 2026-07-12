#!/usr/bin/env python3
import argparse
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path


MANIFEST_NAME = "mystream-plugin.manifest"
DEFAULT_PLATFORM = "macos"


def run(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, check=True)


def parse_key_value_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: expected key=value, got {raw_line!r}")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def package_stem_from_library(library: str) -> str:
    stem = Path(library).stem
    if stem.startswith("lib"):
        stem = stem[3:]
    return stem


def find_manifest(build_dir: Path) -> Path:
    manifests = sorted(build_dir.rglob(MANIFEST_NAME))
    if not manifests:
        raise ValueError(f"No {MANIFEST_NAME} found under {build_dir}")
    if len(manifests) > 1:
        raise ValueError(f"Expected one plugin manifest, found {len(manifests)}")
    return manifests[0]


def zip_write_file(zip_file: zipfile.ZipFile, source_path: Path, archive_path: str) -> None:
    file_stat = source_path.stat()
    info = zipfile.ZipInfo(archive_path)
    info.date_time = (2026, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (stat.S_IMODE(file_stat.st_mode) or 0o644) << 16
    zip_file.writestr(info, source_path.read_bytes())


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    default_sdk_dir = Path(os.environ.get("MYSTREAM_PLUGIN_SDK_DIR", repo_root / "../MyStreamPluginSDK"))

    parser = argparse.ArgumentParser(description="Build and package one MyStream plugin.")
    parser.add_argument("--repo-root", type=Path, default=repo_root, help="Plugin repository root.")
    parser.add_argument("--sdk-dir", type=Path, default=default_sdk_dir, help="MyStreamPluginSDK repository root.")
    parser.add_argument("--build-dir", type=Path, default=repo_root / "build", help="CMake build directory.")
    parser.add_argument("--output-dir", type=Path, default=repo_root / "dist", help="Output directory for ZIP package.")
    parser.add_argument("--clean", action="store_true", help="Remove build and output directories before packaging.")
    parser.add_argument("--skip-validate", action="store_true", help="Skip ZIP package validation.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    sdk_dir = args.sdk_dir.resolve()
    build_dir = args.build_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not (sdk_dir / "include/mystream/plugin_sdk.hpp").exists():
        print(f"Missing MyStreamPluginSDK: {sdk_dir}", file=sys.stderr)
        return 2

    if args.clean:
        shutil.rmtree(build_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)

    build_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    sdk_version_path = repo_root / ".sdk-version"
    sdk_version = sdk_version_path.read_text(encoding="utf-8").strip() if sdk_version_path.exists() else "0.1.0"

    run(
        [
            "cmake",
            "-S",
            str(repo_root),
            "-B",
            str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DMYSTREAM_PLUGIN_SDK_DIR={sdk_dir}",
            f"-DMYSTREAM_PLUGIN_SDK_VERSION={sdk_version}",
        ]
    )
    run(["cmake", "--build", str(build_dir), "--config", "Release"])

    manifest_path = find_manifest(build_dir)
    manifest = parse_key_value_file(manifest_path)
    library_name = manifest["library"]
    library_path = manifest_path.parent / library_name
    if not library_path.exists():
        raise ValueError(f"Missing plugin library: {library_path}")

    package_stem = package_stem_from_library(library_name)
    archive_path = output_dir / f"{package_stem}-{DEFAULT_PLATFORM}-{manifest['version']}.zip"
    root_name = package_stem
    with zipfile.ZipFile(archive_path, "w") as zip_file:
        zip_write_file(zip_file, manifest_path, f"{root_name}/{MANIFEST_NAME}")
        zip_write_file(zip_file, library_path, f"{root_name}/{library_name}")

    if not args.skip_validate:
        run([sys.executable, str(repo_root / "tools/validate_plugin.py"), str(archive_path)])

    print(f"Generated package: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
