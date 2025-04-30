#!/usr/bin/env python
import os
import json
import zipfile
import argparse
import tempfile
import shutil
import re

from espsecure import digest_sbv2_public_key


def find_project_root(start_path=None, markers=(".git")):
    """
    Determines the top-level directory of a project by searching for specific marker files.
    If no marker is found, returns the directory where the script is executed.

    :param start_path: The directory to start searching from. Defaults to current working directory.
    :param markers: A tuple of filenames or directories that indicate the project root.
    :return: The absolute path of the project root directory.
    """
    if start_path is None:
        start_path = os.getcwd()

    current_dir = os.path.abspath(start_path)

    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        if any(os.path.exists(os.path.join(current_dir, marker)) for marker in markers):
            return current_dir
        current_dir = os.path.dirname(current_dir)

    return os.getcwd()  # Default to current working directory if no marker is found


def parse_flasher_args(build_dir, temp_dir):
    """Parses flasher_args.json, detects Secure Boot and Encryption, and creates a modified version for release."""
    flasher_args_path = os.path.join(build_dir, "flasher_args.json")

    if not os.path.exists(flasher_args_path):
        raise FileNotFoundError(f"❌ flasher_args.json not found in {build_dir}")

    with open(flasher_args_path, "r") as f:
        data = json.load(f)

    bootloader_offset = "0x0"
    bootloader_path = "bootloader/bootloader.bin"

    # **Check if the app is encrypted (ignoring other sections)**
    encryption_required = data.get("app", {}).get("encrypted") == "true"

    # **Check Secure Boot: If "bootloader" section is missing, Secure Boot is enabled**
    secure_boot_enabled = "bootloader" not in data

    if secure_boot_enabled:
        print(
            "🔒 Secure Boot detected! Modifying release version of flasher_args.json..."
        )

        # **Add bootloader section**
        data["bootloader"] = {
            "offset": bootloader_offset,
            "file": bootloader_path,
            "encrypted": "true" if encryption_required else "false",
        }

        # **Add bootloader to flash_files**
        data["flash_files"][bootloader_offset] = bootloader_path

        # **Modify write_flash_args to include --force**
        if "--force" not in data["write_flash_args"]:
            print("⚠️  Adding --force to write_flash_args...")
            data["write_flash_args"].insert(0, "--force")

    else:
        print("✅ Bootloader already present. Secure Boot is DISABLED.")

        # **Ensure bootloader section exists and update encrypted status**
        if "bootloader" in data:
            data["bootloader"]["encrypted"] = "true" if encryption_required else "false"

    # **Update security settings**
    data.setdefault("security", {})["secure_boot"] = secure_boot_enabled
    data["security"]["encryption"] = encryption_required

    # **Add --encrypt to write_flash_args if encryption is required**
    if encryption_required:
        print("🔒 App is encrypted. Adding --encrypt to write_flash_args...")
        if "--encrypt" not in data["write_flash_args"]:
            data["write_flash_args"].append("--encrypt")
    else:
        print("⚠️ App is not encrypted. Encryption will not be enforced.")

    # **Sort flash_files to ensure bootloader is always first**
    data["flash_files"] = dict(
        sorted(data["flash_files"].items(), key=lambda x: int(x[0], 16))
    )

    print("✅ Release version of flasher_args.json created.")

    return data


def parse_project_description(build_dir):
    """Parses project_description.json to extract project name and version."""
    project_desc_path = os.path.join(build_dir, "project_description.json")

    if not os.path.exists(project_desc_path):
        raise FileNotFoundError(f"project_description.json not found in {build_dir}")

    with open(project_desc_path, "r") as f:
        data = json.load(f)

    return {
        "project_name": data.get("project_name", "unknown_project"),
        "project_version": data.get("project_version", "0.0.0"),
    }


def generate_secure_boot_digest(signing_key_path, flash_data, temp_dir):
    """Generates the secure boot public key digest."""
    print(f"🔑 Generating Secure Boot V2 public key digest from {signing_key_path}...")

    digest_name = "digest.bin"
    digest_path = os.path.join(temp_dir, digest_name)

    class MockEspsecureArgs:
        def __init__(self, keyFile, output):
            self.keyfile = keyFile
            self.output = output

    try:
        # Open the key file and pass the file object instead of a string
        with open(signing_key_path, "rb") as keyfile:
            digest_sbv2_public_key(MockEspsecureArgs(keyfile, digest_path))
            flash_data["security"]["digest_file"] = digest_name

        print(f"✅ Secure Boot V2 public key digest generated.")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to generate secure boot digest: {e}")

    return flash_data


def create_flash_script(temp_dir, flash_data):
    """Generates a Bash script for flashing with Secure Boot and Encryption warnings."""
    print("📝 Creating release flash script...")

    temp_script_path = os.path.join(temp_dir, "flash.sh")

    extra_esptool_args = flash_data.get("extra_esptool_args", {})
    flash_settings = flash_data.get("flash_settings", {})

    stub = extra_esptool_args.get("stub", True)
    no_stub = "" if stub is True else "--no-stub"

    # Check if encryption is required
    encryption_enabled = flash_data["security"].get("encryption", False)

    # Check if Secure Boot is enabled
    secure_boot_enabled = flash_data["security"].get("secure_boot", False)
    secure_boot_force_flag = "--force" if secure_boot_enabled else ""

    script_content = f"""#!/bin/bash
PORT="${{1:-/dev/ttyUSB0}}"  # Default to /dev/ttyUSB0 if not provided
BAUD=460800

echo "🚀 Flashing ESP32..."

"""

    # Secure Boot Warning
    if secure_boot_enabled:
        script_content += f"""
echo "⚠️  Secure Boot is enabled!"
echo "   - Secure Boot prevents flashing any region below 0x8000."
echo "   - The bootloader must be flashed using --force"
echo "   - ⚠️ WARNING: Incorrect usage of --force may permanently lock your device!"
echo ""
read -p "⚠️ Do you want to continue flashing with Secure Boot enabled? (y/N): " CONFIRM_SECURE_BOOT
if [[ ! $CONFIRM_SECURE_BOOT =~ ^[Yy]$ ]]; then
    echo "❌ Flashing aborted."
    exit 1
fi
"""

    # Encryption Warning
    if encryption_enabled:
        script_content += f"""
echo "🔒 Encryption is enabled!"
echo "   - This means the firmware will be encrypted when written to flash."
echo "   - You must use the same encryption key when updating the firmware in the future."
echo "   - WARNING: Losing the encryption key may render the device unbootable!"
echo ""
read -p "⚠️ Do you want to continue flashing with encryption? (y/N): " CONFIRM_ENCRYPT
if [[ ! $CONFIRM_ENCRYPT =~ ^[Yy]$ ]]; then
    echo "❌ Flashing aborted."
    exit 1
fi
"""

    script_content += f"""esptool.py -p $PORT -b $BAUD --before {extra_esptool_args["before"]} --after {extra_esptool_args["after"]} {no_stub} --chip {extra_esptool_args["chip"]} \\
    write_flash --flash_mode {flash_settings["flash_mode"]} --flash_freq {flash_settings["flash_freq"]} --flash_size {flash_settings["flash_size"]} {secure_boot_force_flag} \\
"""

    for offset, file_path in flash_data["flash_files"].items():
        script_content += f"    {offset} {file_path} \\\n"

    script_content = script_content.rstrip(" \\\n") + "\n"

    with open(temp_script_path, "w") as f:
        f.write(script_content)

    os.chmod(temp_script_path, 0o755)
    print("✅ Release version of flash.sh created.")

    return temp_script_path


def create_zip_package(build_dir, temp_dir, flash_data, output_zip):
    """Creates a zip archive with the modified flash files, flasher_args.json, and flash script."""
    print("📦 Creating ZIP package...")

    # Save modified version in temp directory
    temp_flasher_args_path = os.path.join(temp_dir, "flasher_args.json")
    with open(temp_flasher_args_path, "w") as f:
        json.dump(flash_data, f, indent=4)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(os.path.join(temp_dir, "flasher_args.json"), "flasher_args.json")
        zipf.write(os.path.join(temp_dir, "flash.sh"), "flash.sh")

        # Package digest file if secure boot is enabled.
        if flash_data.get("security", {}).get("secure_boot", False):
            zipf.write(os.path.join(temp_dir, "digest.bin"), "digest.bin")

        # Add all relevant flash files
        for file_path in flash_data["flash_files"].values():
            abs_path = os.path.join(build_dir, file_path)
            if os.path.exists(abs_path):
                zipf.write(abs_path, file_path)

    print(f"✅ Release ZIP package created: {output_zip}")


def generate_release_filename(project_info):
    """Generates a sanitized release ZIP filename based on project version."""

    project_name = project_info.get("project_name", "UnknownProject")
    project_version = project_info.get("project_version", "").strip()

    # Remove '-dirty' from version
    cleaned_version = re.sub(r"-dirty$", "", project_version)

    # Extract a valid semantic version (e.g., v0.0.1)
    version_match = re.search(r"v?\d+\.\d+(\.\d+)?", cleaned_version)
    if version_match:
        final_version = version_match.group(0)  # Use the matched version (e.g., v0.0.1)
    else:
        # If no semantic version found, fallback to full cleaned version
        final_version = cleaned_version if cleaned_version else "latest"

    # Generate the release filename
    release_name = f"{project_name}_{final_version}.zip"

    return release_name


def main():
    parser = argparse.ArgumentParser(
        description="Package ESP32 flashing files into a zip archive."
    )
    parser.add_argument(
        "--build-dir", type=str, default=None, help="Path to the build directory"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Path to the output directory"
    )
    parser.add_argument(
        "--signing-key",
        type=str,
        default="keys/secure_boot_signing_key.pem",
        help="Path to Secure Boot V2 public signing key",
    )

    args = parser.parse_args()

    # Determine the build directory
    project_root = find_project_root()
    build_dir = (
        args.build_dir if args.build_dir else os.path.join(project_root, "build")
    )

    if not os.path.isdir(build_dir):
        raise FileNotFoundError(f"Build directory not found: {build_dir}")

    temp_dir = tempfile.mkdtemp()

    # Parse required JSON files
    flash_data = parse_flasher_args(build_dir, temp_dir)
    project_info = parse_project_description(build_dir)

    # Generate release zip filename
    release_name = generate_release_filename(project_info)

    temp_script = create_flash_script(temp_dir, flash_data)

    # Determine output directory
    output_dir = (
        args.output_dir if args.output_dir else os.path.join(project_root, "release")
    )
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

    # Only generate public key digest if secure boot is enabled.
    if flash_data.get("security", {}).get("secure_boot", False):
        flash_data = generate_secure_boot_digest(args.signing_key, flash_data, temp_dir)

    output_zip = os.path.join(output_dir, release_name)
    create_zip_package(build_dir, temp_dir, flash_data, output_zip)

    shutil.rmtree(temp_dir)
    print(f"🎉 Flash package ready: {output_zip}")


if __name__ == "__main__":
    main()
