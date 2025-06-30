"""
サムネイルキャッシュの実装
"""
import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize, Qt
import os
import platform


class ThumbnailCache:
    """サムネイルキャッシュマネージャー"""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: int = 500):
        """
        Args:
            cache_dir: キャッシュディレクトリ（Noneの場合はシステムデフォルト）
            max_size_mb: キャッシュの最大サイズ（MB）
        """
        if cache_dir is None:
            self.cache_dir = self._get_default_cache_dir()
        else:
            self.cache_dir = cache_dir
            
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
    def _get_default_cache_dir(self) -> Path:
        """システムデフォルトのキャッシュディレクトリを取得"""
        if platform.system() == "Windows":
            app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            return Path(app_data) / "ImageRenameApp" / "cache"
        elif platform.system() == "Darwin":  # macOS
            return Path.home() / "Library" / "Caches" / "ImageRenameApp"
        else:  # Linux
            cache_home = os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
            return Path(cache_home) / "ImageRenameApp"
            
    def _load_metadata(self) -> dict:
        """メタデータを読み込む"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"files": {}, "total_size": 0}
        
    def _save_metadata(self):
        """メタデータを保存"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f)
            
    def _get_cache_key(self, image_path: Path, size: QSize) -> str:
        """キャッシュキーを生成"""
        # ファイルパスとサイズとmtimeからハッシュを生成
        stat = image_path.stat()
        key_string = f"{image_path}_{size.width()}x{size.height()}_{stat.st_mtime}"
        return hashlib.md5(key_string.encode()).hexdigest()
        
    def _get_cache_path(self, cache_key: str) -> Path:
        """キャッシュファイルのパスを取得"""
        return self.cache_dir / f"{cache_key}.png"
        
    def get(self, image_path: Path, size: QSize) -> Optional[QPixmap]:
        """キャッシュからサムネイルを取得"""
        if not image_path.exists():
            return None
            
        cache_key = self._get_cache_key(image_path, size)
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            pixmap = QPixmap(str(cache_path))
            if not pixmap.isNull():
                # アクセス時刻を更新（LRU用）
                self.metadata["files"][cache_key]["last_access"] = Path(cache_path).stat().st_atime
                return pixmap
                
        return None
        
    def put(self, image_path: Path, size: QSize, pixmap: QPixmap) -> bool:
        """サムネイルをキャッシュに保存"""
        if not image_path.exists() or pixmap.isNull():
            return False
            
        cache_key = self._get_cache_key(image_path, size)
        cache_path = self._get_cache_path(cache_key)
        
        # キャッシュサイズをチェック
        self._ensure_cache_size()
        
        # サムネイルを保存
        if pixmap.save(str(cache_path), "PNG"):
            file_size = cache_path.stat().st_size
            self.metadata["files"][cache_key] = {
                "path": str(cache_path),
                "size": file_size,
                "original": str(image_path),
                "last_access": cache_path.stat().st_atime
            }
            self.metadata["total_size"] += file_size
            self._save_metadata()
            return True
            
        return False
        
    def _ensure_cache_size(self):
        """キャッシュサイズを制限内に保つ"""
        while self.metadata["total_size"] > self.max_size_bytes:
            # 最も古いアクセスのファイルを削除
            if not self.metadata["files"]:
                break
                
            oldest_key = min(
                self.metadata["files"].keys(),
                key=lambda k: self.metadata["files"][k].get("last_access", 0)
            )
            
            file_info = self.metadata["files"].pop(oldest_key)
            cache_path = Path(file_info["path"])
            
            if cache_path.exists():
                cache_path.unlink()
                self.metadata["total_size"] -= file_info["size"]
                
        self._save_metadata()
        
    def clear(self):
        """キャッシュをクリア"""
        for cache_file in self.cache_dir.glob("*.png"):
            cache_file.unlink()
            
        self.metadata = {"files": {}, "total_size": 0}
        self._save_metadata()
        
    def generate_thumbnail(self, image_path: Path, size: QSize) -> Optional[QPixmap]:
        """サムネイルを生成してキャッシュに保存"""
        # キャッシュを確認
        cached = self.get(image_path, size)
        if cached:
            return cached
            
        # 新規生成
        try:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                # サムネイルサイズにスケール
                thumbnail = pixmap.scaled(
                    size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                # キャッシュに保存
                self.put(image_path, size, thumbnail)
                return thumbnail
                
        except Exception as e:
            print(f"サムネイル生成エラー: {image_path} - {str(e)}")
            
        return None