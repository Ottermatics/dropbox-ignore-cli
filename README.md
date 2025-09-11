# dropblock

A cross-platform CLI tool to ignore or unblock files and folders in Dropbox using platform-specific methods.

## Features

- Cross-platform support (Windows, macOS, Linux)
- Wildcard and glob pattern support
- Automatic detection and removal of Dropbox conflicted copies
- Batch processing of multiple paths
- Unblock (reverse) operation to restore syncing
- Verbose and quiet modes

## Installation

```bash
pip install -e .
```

Or for system-wide installation:

```bash
pip install .
```

## Usage

### Basic usage

Ignore a single file or folder:
```bash
dropblock /path/to/file
dropblock /path/to/folder
```

### Multiple paths

Ignore multiple files/folders:
```bash
dropblock file1.txt folder1 file2.pdf
```

### Wildcard patterns

Ignore parent folder (path ending with *):
```bash
dropblock /path/to/folder/*
```

Ignore files matching a pattern:
```bash
dropblock /path/*/specific/file.txt
dropblock /home/user/*/node_modules
```

### Options

- `--ignore-conflicts`: Don't remove conflicted copies
- `-n, --no-output`: Suppress the list of ignored files
- `-v, --verbose`: Show verbose output

### Examples

```bash
# Ignore node_modules in all projects
dropblock ~/projects/*/node_modules

# Ignore a folder and don't remove conflicts
dropblock --ignore-conflicts ~/Dropbox/large-folder

# Quiet mode - no output
dropblock -n ~/Dropbox/temp/*

# Verbose mode
dropblock -v ~/Dropbox/cache ~/Dropbox/logs
```

## How it works

The tool uses platform-specific methods to set the ignore attribute:

- **Windows**: Uses PowerShell to set the `com.dropbox.ignored` stream
- **macOS**: Uses `xattr` to set either `com.apple.fileprovider.ignore#P` (File Provider) or `com.dropbox.ignored`
- **Linux**: Uses `xattr` or `attr` command to set `com.dropbox.ignored`

## Conflict handling

By default, the tool automatically detects and removes Dropbox conflicted copies (files matching the pattern `filename (user's conflicted copy date).ext`). Use `--ignore-conflicts` to disable this behavior.

## Requirements

- Python 3.6+
- Platform-specific tools:
  - Windows: PowerShell
  - macOS: xattr (built-in)
  - Linux: xattr or attr package

## License

MIT