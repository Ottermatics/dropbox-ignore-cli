#!/usr/bin/env python3
"""
dropblock - A cross-platform CLI tool to ignore files and folders in Dropbox
"""

import os
import sys
import platform
import subprocess
import argparse
import glob
import re
import traceback
from pathlib import Path
from typing import List, Optional, Set


class DropboxIgnore:
    """Main class for handling Dropbox ignore operations"""
    
    def __init__(self, ignore_conflicts: bool = False, verbose: bool = False):
        self.ignore_conflicts = ignore_conflicts
        self.verbose = verbose
        self.ignored_files: Set[str] = set()
        self.removed_conflicts: Set[str] = set()
        self.system = platform.system()
        
    def find_conflicts(self, path: Path) -> List[Path]:
        """Find conflicted copies related to a path"""
        parent = path.parent
        base_name = path.stem
        ext = path.suffix
        
        conflict_pattern = re.compile(
            rf"{re.escape(base_name)}\s*\(.*conflicted copy.*\){re.escape(ext)}"
        )
        
        conflicts = []
        if parent.exists():
            for item in parent.iterdir():
                if conflict_pattern.match(item.name):
                    conflicts.append(item)
                    
        return conflicts
    
    def remove_conflicts(self, path: Path) -> None:
        """Remove conflicted copies of a file"""
        if self.ignore_conflicts:
            return
            
        conflicts = self.find_conflicts(path)
        for conflict in conflicts:
            try:
                if conflict.is_dir():
                    import shutil
                    shutil.rmtree(conflict)
                else:
                    conflict.unlink()
                self.removed_conflicts.add(str(conflict))
                if self.verbose:
                    print(f"Removed conflict: {conflict}")
            except Exception as e:
                print(f"Error removing conflict {conflict}:", file=sys.stderr)
                traceback.print_exc()
    
    def windows_ignore(self, path: Path) -> bool:
        """Ignore file/folder on Windows using PowerShell"""
        try:
            ps_command = [
                'powershell', '-Command',
                f"Set-Content -Path '{str(path)}' -Stream com.dropbox.ignored -Value 1"
            ]
            result = subprocess.run(ps_command, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error ignoring on Windows:", file=sys.stderr)
            traceback.print_exc()
            return False
    
    def macos_ignore(self, path: Path) -> bool:
        """Ignore file/folder on macOS using xattr"""
        try:
            # Check if File Provider is being used
            dropbox_path = str(path)
            if 'CloudStorage/Dropbox' in dropbox_path:
                # File Provider enabled
                cmd = ['xattr', '-w', 'com.apple.fileprovider.ignore#P', '1', str(path)]
            else:
                # File Provider not enabled
                cmd = ['xattr', '-w', 'com.dropbox.ignored', '1', str(path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error ignoring on macOS:", file=sys.stderr)
            traceback.print_exc()
            return False
    
    def linux_ignore(self, path: Path) -> bool:
        """Ignore file/folder on Linux using xattr"""
        try:
            # Linux uses attr command or xattr depending on distribution
            # Try xattr first
            cmd = ['attr', '-w', 'com.dropbox.ignored', '1', str(path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try attr command as fallback
                cmd = ['attr', '-s', 'com.dropbox.ignored', '-V', '1', str(path)]
                result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error ignoring on Linux:", file=sys.stderr)
            traceback.print_exc()
            return False
    
    def cross_platform_ignore(self, path: Path) -> bool:
        """Dispatch to appropriate platform-specific ignore function"""
        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            return False
        
        # Remove conflicts first
        self.remove_conflicts(path)
        
        # Dispatch to platform-specific function
        if self.system == 'Windows':
            success = self.windows_ignore(path)
        elif self.system == 'Darwin':  # macOS
            success = self.macos_ignore(path)
        elif self.system == 'Linux':
            success = self.linux_ignore(path)
        else:
            print(f"Error: Unsupported platform: {self.system}", file=sys.stderr)
            return False
        
        if success:
            self.ignored_files.add(str(path))
            if self.verbose:
                print(f"Ignored: {path}")
        else:
            print(f"Failed to ignore: {path}", file=sys.stderr)
            
        return success
    
    def process_path(self, path_str: str) -> List[Path]:
        """Process a path string and return list of paths to ignore"""
        paths_to_ignore = []
        
        # Handle path ending with * (ignore parent folder)
        if path_str.endswith('*'):
            parent_path = Path(path_str[:-1]).resolve()
            if parent_path.exists() and parent_path.is_dir():
                paths_to_ignore.append(parent_path)
        # Handle wildcard in the middle of path
        elif '*' in path_str:
            # Use glob to expand the pattern
            expanded_paths = glob.glob(path_str, recursive=True)
            for p in expanded_paths:
                paths_to_ignore.append(Path(p).resolve())
        else:
            # Regular path
            path = Path(path_str).resolve()
            if path.exists():
                paths_to_ignore.append(path)
            else:
                print(f"Warning: Path does not exist: {path_str}", file=sys.stderr)
        
        return paths_to_ignore
    
    def ignore_paths(self, paths: List[str]) -> None:
        """Process and ignore multiple paths"""
        all_paths = []
        for path_str in paths:
            all_paths.extend(self.process_path(path_str))
        
        for path in all_paths:
            self.cross_platform_ignore(path)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Ignore files and folders in Dropbox',
        prog='dropblock'
    )
    
    parser.add_argument(
        'paths',
        nargs='+',
        help='Paths to ignore (supports wildcards)'
    )
    
    parser.add_argument(
        '--ignore-conflicts',
        action='store_true',
        help="Don't remove conflicted copies"
    )
    
    parser.add_argument(
        '-n', '--no-output',
        action='store_true',
        help='Suppress output of ignored files list'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    # 
    # parser.add_argument(
    #     '--debug',
    #     action='store_true',
    #     help='Show debug output and tracebacks (also enabled by DEBUG environment variable)'
    # )
    # 
    args = parser.parse_args()
    
    # Create DropboxIgnore instance
    ignorer = DropboxIgnore(
        ignore_conflicts=args.ignore_conflicts,
        verbose=args.verbose
    )
    
    # Process paths
    ignorer.ignore_paths(args.paths)
    
    # Print summary unless --no-output is specified
    if not args.no_output:
        if ignorer.ignored_files:
            print("\nIgnored files/folders:")
            for path in sorted(ignorer.ignored_files):
                print(f"  ✓ {path}")
        
        if ignorer.removed_conflicts:
            print("\nRemoved conflicts:")
            for path in sorted(ignorer.removed_conflicts):
                print(f"  ✗ {path}")
        
        if not ignorer.ignored_files and not ignorer.removed_conflicts:
            print("No files were ignored.")
    
    # Exit with appropriate code
    sys.exit(0 if ignorer.ignored_files else 1)


if __name__ == '__main__':
    main()