# Unity Debug Converter

A Python script that automates the process of converting a Unity game release build into a debug build and enabling script debugging in game configuration.

Intended to help with modding.

## Requirements

- Python 3
- Unity Hub or a standalone Unity installation with the appropriate Unity version for your game

## Usage examples

### Using Unity Hub path and version
```bash
python unity_debug_converter.py --unity_hub_path "C:/Program Files/Unity/Hub/Editor" --unity_version "2022.3.32f1" --game_path "C:/Steam/steamapps/common/MyGame"
```

### Using direct Unity installation path
```bash
python unity_debug_converter.py --unity_path "C:/Program Files/Unity/Hub/Editor/2022.3.32f1" --game_path "C:/Steam/steamapps/common/MyGame"
```

### Dry run (simulate conversion, recommended for first-time use)
```bash
python unity_debug_converter.py --unity_hub_path "C:/Program Files/Unity/Hub/Editor" --unity_version "2022.3.45f1" --game_path "C:/Games/MyUnityGame" --dry-run
```

### Dry run with direct Unity path
```bash
python unity_debug_converter.py --unity_path "C:/Program Files/Unity/Hub/Editor/2022.3.45f1" --game_path "C:/Games/MyUnityGame" --dry-run
```

### Command line arguments

- `--unity_path`: Direct path to Unity installation (e.g., `C:/Program Files/Unity/Hub/Editor/2022.3.32f1`)
- `--unity_hub_path`: Path to Unity Hub Editor directory (e.g., `C:/Program Files/Unity/Hub/Editor`)
- `--unity_version`: Unity editor version (e.g., `2022.3.32f1`)

- `--game_path` (required): Path to game installation directory
- `--dry-run` (optional): Preview changes without modifying any files
- `--help`: Show help message

You must provide either `--unity_path` OR both `--unity_hub_path` and `--unity_version`. You cannot use both options together.

## How it works

The script automates the conversion process through these steps:

1. Verifies that Unity Hub installation and game paths exist
2. Automatically finds the game executable and data directory (with interactive selection if multiple executables found)
3. Locates debug build files in Unity installation variations:
   - `WindowsPlayer.exe` -> will be renamed to `GameName.exe`
   - `UnityPlayer.dll` -> copied as-is
   - `WinPixEventRuntime.dll` -> copied if present (some Unity versions)
   - `player_win.exe` -> for older Unity versions, used instead of `WindowsPlayer.exe`
4. Copies debug files to game directory with proper naming (overwrites existing files)
5. Creates `boot.config` file with script debugging enabled

## File locations

The script searches for debug files in these Unity variations (in order):
1. `{unity_path}/Editor/Data/PlaybackEngines/windowsstandalonesupport/Variations/win64_player_development_mono/`
2. `{unity_path}/Editor/Data/PlaybackEngines/windowsstandalonesupport/Variations/win32_player_development_mono/`

Where `{unity_path}` is:
- If using `--unity_path`: the provided path directly
- If using `--unity_hub_path` and `--unity_version`: `{unity_hub_path}/{unity_version}`

If the game requires a different Unity variation, add the corresponding variation name to `variations` list in the script.

### Debug configuration

The script creates a `boot.config` file in the `GameName_Data` directory with these settings:
```
player-connection-debug=1
```

## Getting Unity version

To find your game's Unity version:
1. Right-click the game executable in Windows Explorer
2. Select "Properties"
3. Go to the "Details" tab
4. Look for Unity version in the file details or product version

## Notes

- This script directly overwrites existing game files. Make your own backup if needed, or make use of the Steam game file integrity check to restore original files.
- It's recommended to run with `--dry-run` flag first to preview changes.

## License

This script is provided as-is for development and modding purposes.

## Contributing

Feel free to submit issues, feature requests, or improvements.
