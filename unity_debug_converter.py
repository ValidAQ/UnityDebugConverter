"""
Unity Game Debug Converter

This script converts a Unity game release build into a debug build by:
1. Copying debug build files from Unity installation
2. Creating the required configuration file for script debugging

Usage:
    # Using Unity Hub path and version
    python unity_debug_converter.py --unity_hub_path <hub_path> --unity_version <version> --game_path <game_path>

    # Using direct Unity installation path
    python unity_debug_converter.py --unity_path <unity_path> --game_path <game_path>
"""

import argparse
import logging
import shutil
import sys
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DryRunMode(Enum):
    ENABLED = True
    DISABLED = False


class UnityDebugConverter:
    def __init__(
        self,
        game_path: str,
        unity_path: str | None = None,
        unity_hub_path: str | None = None,
        unity_version: str | None = None,
        dry_run: DryRunMode = DryRunMode.DISABLED,
    ):
        self.game_path = Path(game_path)

        # Determine Unity installation path
        if unity_path:
            self.unity_path = Path(unity_path)
            self.unity_hub_path = None
            self.unity_version = None
        elif unity_hub_path and unity_version:
            self.unity_hub_path = Path(unity_hub_path)
            self.unity_version = unity_version
            self.unity_path = self.unity_hub_path / unity_version
        else:
            msg = "Either --unity_path or both --unity_hub_path and --unity_version must be provided"
            raise ValueError(msg)

        self.game_name: str = ""
        self.game_data_path: Path = Path()
        self.dry_run = dry_run

    def validate_paths(self) -> bool:
        """Validate that the provided paths exist and are valid."""
        if not self.unity_path.exists():
            logger.error("Unity installation path does not exist: %s", self.unity_path)
            return False

        if not self.game_path.exists():
            logger.error("Game installation path does not exist: %s", self.game_path)
            return False

        # Check for Unity playback engines directory
        playback_engines = (
            self.unity_path / "Editor" / "Data" / "PlaybackEngines" / "windowsstandalonesupport" / "Variations"
        )
        if not playback_engines.exists():
            logger.error("Unity playback engines not found at: %s", playback_engines)
            return False

        return True

    def detect_game_info(self) -> bool:
        """Detect the game executable and data directory."""

        exe_files = list(self.game_path.glob("*.exe"))
        # Ignore UnityCrashHandler.exe if present
        exe_files = [exe for exe in exe_files if "unitycrashhandler" not in exe.name.lower()]

        if not exe_files:
            logger.error("No executable files found in game directory")
            return False

        if len(exe_files) > 1:
            print("Multiple executables found. Please select the main game executable:")
            for i, exe in enumerate(exe_files):
                print(f"{i + 1}. {exe.name}")

            while True:
                try:
                    choice = int(input(f"Enter choice (1-{len(exe_files)}): ")) - 1
                    if 0 <= choice < len(exe_files):
                        game_exe = exe_files[choice]
                        break
                    print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
        else:
            game_exe = exe_files[0]

        self.game_name = game_exe.stem
        self.game_data_path = self.game_path / f"{self.game_name}_Data"

        if not self.game_data_path.exists():
            logger.error("Game data directory not found: %s", self.game_data_path)
            return False

        logger.info("Detected game: %s", self.game_name)
        logger.info("Game data directory: %s", self.game_data_path)
        return True

    def process_variation(self, variation: str) -> dict:
        """Process a specific Unity variation to find debug files."""
        debug_path = (
            self.unity_path
            / "Editor"
            / "Data"
            / "PlaybackEngines"
            / "windowsstandalonesupport"
            / "Variations"
            / variation
        )

        files_to_copy: dict[str, Path] = {}

        if not debug_path.exists():
            return files_to_copy

        # Check for newer Unity versions files
        windows_player = debug_path / "WindowsPlayer.exe"
        unity_player_dll = debug_path / "UnityPlayer.dll"
        winpix_dll = debug_path / "WinPixEventRuntime.dll"
        player_win = debug_path / "player_win.exe"

        if windows_player.exists():
            files_to_copy["WindowsPlayer.exe"] = windows_player
            logger.info("Found WindowsPlayer.exe at: %s", windows_player)

        if unity_player_dll.exists():
            files_to_copy["UnityPlayer.dll"] = unity_player_dll
            logger.info("Found UnityPlayer.dll at: %s", unity_player_dll)

        if winpix_dll.exists():
            files_to_copy["WinPixEventRuntime.dll"] = winpix_dll
            logger.info("Found WinPixEventRuntime.dll at: %s", winpix_dll)

        if player_win.exists() and "player_win.exe" not in files_to_copy:
            files_to_copy["player_win.exe"] = player_win
            logger.info("Found player_win.exe at: %s", player_win)

        return files_to_copy

    def find_debug_files(self) -> dict:
        """Find the debug build files in Unity installation."""

        variations = [
            "win64_player_development_mono",
            "win32_player_development_mono",
        ]

        files_to_copy: dict[str, Path] = {}

        # Try each variation until we find debug files
        for variation in variations:
            variation_files = self.process_variation(variation)
            essential_files_found = {"WindowsPlayer.exe", "player_win.exe"} & variation_files.keys()
            if variation_files and essential_files_found:
                files_to_copy = variation_files
                logger.info("Using Unity variation: %s", variation)
                break

        if not files_to_copy:
            logger.error("No debug build files found in any variation")

        return files_to_copy

    def copy_debug_files(self, debug_files: dict) -> bool:
        """Copy debug files to game directory."""
        try:
            for filename, source_path in debug_files.items():
                if filename == "WindowsPlayer.exe":
                    # Rename WindowsPlayer.exe to game name
                    dest_path = self.game_path / f"{self.game_name}.exe"
                elif filename == "player_win.exe":
                    # Rename player_win.exe to game name (older Unity versions)
                    dest_path = self.game_path / f"{self.game_name}.exe"
                else:
                    # Copy DLLs with original names
                    dest_path = self.game_path / filename

                if self.dry_run:
                    logger.info("[DRY RUN] Would copy: %s -> %s", filename, dest_path.name)
                else:
                    shutil.copy2(source_path, dest_path)
                    logger.info("Copied: %s -> %s", filename, dest_path.name)

        except (OSError, shutil.Error):
            if not self.dry_run:
                logger.exception("Error copying debug files")
                return False
        return True

    def create_boot_config(self) -> bool:
        """Create boot.config file for script debugging (Unity 2017.2+)."""
        boot_config_path = self.game_data_path / "boot.config"

        # Default configuration for script debugging
        config_content = [
            "player-connection-debug=1",
            # "wait-for-managed-debugger=1",
        ]

        try:
            if self.dry_run:
                logger.info("[DRY RUN] Would create boot.config at: %s", boot_config_path)
                logger.info("[DRY RUN] Content: %s", ", ".join(config_content))
            else:
                with open(boot_config_path, "w") as f:
                    f.writelines(config_content)
                logger.info("Created boot.config at: %s", boot_config_path)
        except OSError:
            if not self.dry_run:
                logger.exception("Error creating boot.config")
                return False
        return True

    def convert_to_debug(self) -> bool:
        """Convert the game to debug build."""
        if self.dry_run:
            logger.info("Starting debug conversion preview (DRY RUN MODE)...")
        else:
            logger.info("Starting debug conversion...")

        # Find debug files
        logger.info("Step 1: Finding debug files...")
        debug_files = self.find_debug_files()
        if not debug_files:
            return False

        # Copy debug files
        logger.info("Step 2: Copying debug files...")
        if not self.copy_debug_files(debug_files):
            return False

        # Create boot.config
        logger.info("Step 3: Creating boot.config...")
        if not self.create_boot_config():
            logger.warning("Failed to create boot.config. Script debugging may not work.")

        return True


def parse_arguments():
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Unity game release build to debug build",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--unity_path",
        help=(
            "Direct path to Unity installation "
            "(e.g., 'C:/Program Files/Unity/Hub/Editor/2022.3.32f1'). "
            "Alternative to --unity_hub_path and --unity_version."
        ),
    )
    parser.add_argument(
        "--unity_hub_path",
        help=(
            "Path to Unity Hub Editor directory "
            "(e.g., 'C:/Program Files/Unity/Hub/Editor'). "
            "Must be used with --unity_version."
        ),
    )
    parser.add_argument(
        "--unity_version",
        help="Unity editor version (e.g., '2022.3.32f1'). Must be used with --unity_hub_path.",
    )
    parser.add_argument(
        "--game_path",
        help="Path to game installation directory",
        required=True,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying any files",
    )

    args = parser.parse_args()

    # Validate argument combinations
    if not args.unity_path and not (args.unity_hub_path and args.unity_version):
        parser.error("Either --unity_path or both --unity_hub_path and --unity_version must be provided")

    if args.unity_path and (args.unity_hub_path or args.unity_version):
        parser.error("Cannot use --unity_path together with --unity_hub_path or --unity_version")

    return args


def log_configuration(args):
    """Log the configuration settings."""
    logger.info("Unity Game Debug Converter")
    logger.info("=" * 40)
    if args.unity_path:
        logger.info("Unity Path: %s", args.unity_path)
    else:
        logger.info("Unity Hub Path: %s", args.unity_hub_path)
        logger.info("Unity Version: %s", args.unity_version)
    logger.info("Game Path: %s", args.game_path)
    if args.dry_run:
        logger.info("DRY RUN MODE (preview only)")
    logger.info("=" * 40)


def main():
    """Run the Unity Debug Converter."""
    args = parse_arguments()
    log_configuration(args)

    dry_run_mode = DryRunMode.ENABLED if args.dry_run else DryRunMode.DISABLED

    converter = UnityDebugConverter(
        game_path=args.game_path,
        unity_path=args.unity_path,
        unity_hub_path=args.unity_hub_path,
        unity_version=args.unity_version,
        dry_run=dry_run_mode,
    )

    # Validate paths
    if not converter.validate_paths():
        sys.exit(1)

    # Detect game information
    if not converter.detect_game_info():
        sys.exit(1)

    # Show conversion message
    mode_msg = "[DRY RUN] Preview conversion" if args.dry_run else "Ready to convert"
    print(f"\n{mode_msg} of '{converter.game_name}' to debug build.")

    # Perform conversion
    success = converter.convert_to_debug()
    log_results(success=success, is_dry_run=args.dry_run)

    if not success:
        sys.exit(1)


def log_results(*, success: bool, is_dry_run: bool):
    """
    Log the conversion results.

    :param success: Whether the conversion was successful.
    :param is_dry_run: Whether this was a dry run.
    """

    logger.info("=" * 40)
    if success:
        if is_dry_run:
            logger.info("Dry run completed successfully!")
            logger.info("This preview showed what would be done during conversion.")
            logger.info("Run without --dry-run to perform the actual conversion.")
        else:
            logger.info("Conversion completed successfully!")
            logger.info("Your Unity game has been converted to a debug build.")
            logger.info("You can now attach debuggers and use development tools.")
    else:
        if is_dry_run:
            msg = "Dry run failed. Check error messages above."
        else:
            msg = "Conversion failed. Check error messages above."
        logger.error(msg)


if __name__ == "__main__":
    main()
