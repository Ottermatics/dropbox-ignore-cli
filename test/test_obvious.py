#!/usr/bin/env python3
"""
Unit tests for dropblock CLI tool
"""

import unittest
import platform
import tempfile
import subprocess
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Import the module to test
from dropblock import DropboxIgnore


class TestDropblockPlatforms(unittest.TestCase):
    """Test dropblock functionality on different platforms"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="dropblock_test_")
        self.test_file = Path(self.temp_dir) / "test_file.txt"
        self.test_file.write_text("test content")
        self.test_folder = Path(self.temp_dir) / "test_folder"
        self.test_folder.mkdir()

        # Create a conflicted copy for testing
        self.conflict_file = (
            Path(self.temp_dir) / "test_file (user's conflicted copy 2024-01-01).txt"
        )
        self.conflict_file.write_text("conflict content")

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @unittest.skipUnless(platform.system() == "Windows", "Windows-only test")
    def test_windows_ignore(self):
        """Test Windows-specific ignore functionality"""
        ignorer = DropboxIgnore(verbose=True)

        # Mock subprocess.run to simulate successful PowerShell command
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Test ignoring a file
            success = ignorer.windows_ignore(self.test_file)
            self.assertTrue(success)

            # Verify PowerShell command was called correctly
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "powershell")
            self.assertIn("Set-Content", args[2])
            self.assertIn("com.dropbox.ignored", args[2])
            self.assertIn(str(self.test_file), args[2])

            # Test ignoring a folder
            mock_run.reset_mock()
            success = ignorer.windows_ignore(self.test_folder)
            self.assertTrue(success)
            mock_run.assert_called_once()

    @unittest.skipUnless(platform.system() == "Darwin", "macOS-only test")
    def test_macos_ignore(self):
        """Test macOS-specific ignore functionality"""
        ignorer = DropboxIgnore(verbose=True)

        # Test non-File Provider path
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Test ignoring a file
            success = ignorer.macos_ignore(self.test_file)
            self.assertTrue(success)

            # Verify xattr command was called correctly
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "xattr")
            self.assertEqual(args[1], "-w")
            self.assertEqual(args[2], "com.dropbox.ignored")
            self.assertEqual(args[3], "1")
            self.assertEqual(args[4], str(self.test_file))

            # Test File Provider path
            mock_run.reset_mock()

    @unittest.skipUnless(platform.system() == "Linux", "Linux-only test")
    def test_linux_ignore(self):
        """Test Linux-specific ignore functionality"""
        ignorer = DropboxIgnore(verbose=True)

        with patch("subprocess.run") as mock_run:
            # First call to xattr succeeds
            mock_run.return_value = MagicMock(returncode=0)

            # Test ignoring a file
            success = ignorer.linux_ignore(self.test_file)
            self.assertTrue(success)

            # Verify xattr command was called correctly
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "attr")
            self.assertEqual(args[1], "-s")
            self.assertEqual(args[2], "com.dropbox.ignored")
            self.assertEqual(args[3], "1")
            self.assertEqual(args[4], str(self.test_file))

            # Test fallback to attr command
            mock_run.reset_mock()
            mock_run.side_effect = [
                MagicMock(returncode=1),  # xattr fails
                MagicMock(returncode=0),  # attr succeeds
            ]

            success = ignorer.linux_ignore(self.test_file)
            self.assertTrue(success)

            # Verify attr was called as fallback
            self.assertEqual(mock_run.call_count, 2)
            second_call_args = mock_run.call_args_list[1][0][0]
            self.assertEqual(second_call_args[0], "attr")

    def test_conflict_detection(self):
        """Test detection of conflicted copies"""
        ignorer = DropboxIgnore()

        # Find conflicts for the test file
        conflicts = ignorer.find_conflicts(self.test_file)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0], self.conflict_file)

    def test_conflict_removal(self):
        """Test removal of conflicted copies"""
        ignorer = DropboxIgnore(ignore_conflicts=False)

        # Ensure conflict exists
        self.assertTrue(self.conflict_file.exists())

        # Remove conflicts
        ignorer.remove_conflicts(self.test_file)

        # Verify conflict was removed
        self.assertFalse(self.conflict_file.exists())

    def test_ignore_conflicts_flag(self):
        """Test that --ignore-conflicts prevents removal"""
        ignorer = DropboxIgnore(ignore_conflicts=True)

        # Ensure conflict exists
        self.assertTrue(self.conflict_file.exists())

        # Try to remove conflicts (should do nothing)
        ignorer.remove_conflicts(self.test_file)

        # Verify conflict still exists
        self.assertTrue(self.conflict_file.exists())

    def test_wildcard_patterns(self):
        """Test wildcard pattern processing"""
        ignorer = DropboxIgnore()

        # Test path ending with *
        parent_folder = Path(self.temp_dir) / "parent"
        parent_folder.mkdir()
        paths = ignorer.process_path(str(parent_folder) + "/*")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].resolve(), parent_folder.resolve())

        # Test glob pattern
        subfolders = []
        for i in range(3):
            subfolder = Path(self.temp_dir) / f"project{i}" / "node_modules"
            subfolder.mkdir(parents=True)
            subfolders.append(subfolder)

        pattern = str(Path(self.temp_dir) / "*/node_modules")
        paths = ignorer.process_path(pattern)
        self.assertEqual(len(paths), 3)

        # Verify all subfolders were found
        resolved_paths = [p.resolve() for p in paths]
        for subfolder in subfolders:
            self.assertIn(subfolder.resolve(), resolved_paths)

    def test_cross_platform_ignore(self):
        """Test cross-platform ignore dispatcher"""
        ignorer = DropboxIgnore()

        current_platform = platform.system()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Test that correct platform method is called
            success = ignorer.cross_platform_ignore(self.test_file)
            self.assertTrue(success)

            # Verify file was added to ignored list
            self.assertIn(str(self.test_file), ignorer.ignored_files)

            # Verify subprocess was called
            mock_run.assert_called()

    def test_nonexistent_path(self):
        """Test handling of non-existent paths"""
        ignorer = DropboxIgnore()

        nonexistent = Path(self.temp_dir) / "nonexistent.txt"
        success = ignorer.cross_platform_ignore(nonexistent)
        self.assertFalse(success)

        # Verify file was not added to ignored list
        self.assertNotIn(str(nonexistent), ignorer.ignored_files)


if __name__ == "__main__":
    unittest.main()
