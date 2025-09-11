# dropblock-cli

A cross-platform CLI tool to ignore or unblock files and folders in Dropbox using platform-specific methods, based on official documentation here https://help.dropbox.com/sync/ignored-files

## Features

- Cross-platform support (Windows, macOS, Linux)
- Wildcard and glob pattern support
- Automatic detection and removal of Dropbox conflicted copies
- Batch processing of multiple paths
- **Unblock (reverse) operation** to restore syncing for previously ignored files
- Verbose and quiet modes
- PyPI distribution for easy installation

## Installation

### From PyPI (Recommended)

```bash
pip install dropblock-cli
```

### From Source

```bash
git clone https://github.com/yourusername/dropbox-ignore-cli.git
cd dropbox-ignore-cli
pip install -e .
```

Or for system-wide installation:

```bash
pip install .
```

## Usage

### Basic Operations

**Ignore** files/folders (stop Dropbox sync):
```bash
dropblock /path/to/file
dropblock /path/to/folder
```

**Unblock** files/folders (restore Dropbox sync):
```bash
dropblock --unblock /path/to/file
dropblock --unblock /path/to/folder
```

### Multiple paths

Ignore multiple files/folders:
```bash
dropblock file1.txt folder1 file2.pdf
```

Unblock multiple files/folders:
```bash
dropblock --unblock file1.txt folder1 file2.pdf
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

- `--unblock`: Unblock files instead of ignoring them (restore Dropbox syncing)
- `--ignore-conflicts`: Don't remove conflicted copies when ignoring files
- `-n, --no-output`: Suppress the list of ignored/unblocked files
- `-v, --verbose`: Show verbose output

### Examples

**Ignoring files and folders:**
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

**Unblocking files and folders:**
```bash
# Restore syncing for a previously ignored folder
dropblock --unblock ~/Dropbox/large-folder

# Unblock multiple paths with verbose output
dropblock --unblock -v ~/projects/*/node_modules

# Restore syncing for cache folders
dropblock --unblock ~/Dropbox/cache ~/Dropbox/logs
```

**Common workflows:**
```bash
# Temporarily ignore large folders during initial sync
dropblock ~/Dropbox/videos ~/Dropbox/archives

# Later restore syncing when needed
dropblock --unblock ~/Dropbox/videos ~/Dropbox/archives
```

## How it works

The tool uses platform-specific methods to set or remove the ignore attribute:

### Ignore Operation (Default)
- **Windows**: Uses PowerShell to set the `com.dropbox.ignored` stream
- **macOS**: Uses `xattr` to set `com.dropbox.ignored` attribute  
- **Linux**: Uses `attr` command to set `com.dropbox.ignored` attribute

### Unblock Operation (`--unblock` flag)
- **Windows**: Uses PowerShell to clear the `com.dropbox.ignored` stream
- **macOS**: Uses `xattr` to remove the `com.dropbox.ignored` attribute
- **Linux**: Uses `attr` command to remove the `com.dropbox.ignored` attribute

When files are ignored, Dropbox stops syncing them but keeps local copies. When unblocked, Dropbox resumes syncing and the files become available across all devices again.

## Conflict handling

By default, the tool automatically detects and removes Dropbox conflicted copies (files matching the pattern `filename (user's conflicted copy date).ext`). Use `--ignore-conflicts` to disable this behavior.

## Requirements

- Python 3.8+
- Platform-specific tools:
  - Windows: PowerShell (built-in)
  - macOS: xattr (built-in)
  - Linux: attr package (`sudo apt install attr` on Debian/Ubuntu)

## License

MIT