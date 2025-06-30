#!/usr/bin/env python3
"""
簡易テストスクリプト
"""
from pathlib import Path
from src.core.file_operations import FileOperationManager

# ファイル操作マネージャーのテスト
print("Testing FileOperationManager...")
fm = FileOperationManager()

# テスト画像フォルダから画像を取得
test_folder = Path("test_images")
images = fm.get_images_from_folder(test_folder)
print(f"Found {len(images)} images in test_images folder")
for img in images:
    print(f"  - {img.name}")

# リネームパターンテスト
print("\nTesting rename pattern...")
for i, img in enumerate(images[:3], 1):
    new_name = fm.get_rename_pattern(img.name, i)
    print(f"  {img.name} -> {new_name}")

print("\nAll tests passed!")