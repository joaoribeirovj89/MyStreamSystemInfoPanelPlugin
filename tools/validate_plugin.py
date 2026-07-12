#!/usr/bin/env python3
import argparse
import sys
import zipfile
from pathlib import Path


REQUIRED_MANIFEST_KEYS = {
    "format",
    "id",
    "name",
    "version",
    "category",
    "library",
    "plugin_api_version",
    "sdk_version",
    "sdk_min_version",
    "sdk_max_version",
}


def parse_key_value_text(text: str, source: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{source}:{line_number}: expected key=value, got {raw_line!r}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"{source}:{line_number}: empty key")
        values[key] = value
    return values


def find_manifest(zip_file: zipfile.ZipFile, package_path: Path) -> str:
    manifest_names = [
        name
        for name in zip_file.namelist()
        if name.endswith("mystream-plugin.manifest") and not name.endswith("/")
    ]
    if not manifest_names:
        raise ValueError(f"{package_path}: missing mystream-plugin.manifest")
    if len(manifest_names) > 1:
        raise ValueError(f"{package_path}: expected one manifest, found {len(manifest_names)}")
    return manifest_names[0]


def validate_package(package_path: Path) -> list[str]:
    errors: list[str] = []
    if not package_path.exists():
        return [f"package does not exist: {package_path}"]
    if package_path.suffix != ".zip":
        return [f"package is not a .zip file: {package_path}"]

    try:
        with zipfile.ZipFile(package_path, "r") as zip_file:
            bad_file = zip_file.testzip()
            if bad_file:
                return [f"corrupt zip entry: {bad_file}"]

            manifest_name = find_manifest(zip_file, package_path)
            manifest = parse_key_value_text(
                zip_file.read(manifest_name).decode("utf-8"),
                f"{package_path}:{manifest_name}",
            )

            missing = sorted(REQUIRED_MANIFEST_KEYS - manifest.keys())
            if missing:
                errors.append(f"manifest missing keys: {', '.join(missing)}")

            library_name = manifest.get("library", "")
            library_entries = [
                name
                for name in zip_file.namelist()
                if Path(name).name == library_name and not name.endswith("/")
            ]
            if not library_entries:
                errors.append(f"library not found in package: {library_name}")
            elif len(library_entries) > 1:
                errors.append(f"library appears multiple times in package: {library_name}")

            version = manifest.get("version")
            if version and version not in package_path.name:
                errors.append(f"package filename should include version {version}: {package_path.name}")
    except zipfile.BadZipFile:
        errors.append(f"invalid zip file: {package_path}")
    except UnicodeDecodeError:
        errors.append("manifest is not UTF-8")
    except ValueError as error:
        errors.append(str(error))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a MyStream plugin package.")
    parser.add_argument("package", type=Path, help="Plugin package ZIP.")
    args = parser.parse_args()

    errors = validate_package(args.package.resolve())
    if errors:
        print("Plugin package validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Plugin package validation passed: {args.package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
