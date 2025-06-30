"""
画像アイテムのデータモデル
"""
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class ImageItem:
    """画像アイテムを表すデータクラス"""
    path: Path
    name: str
    size: int
    thumbnail: Optional[bytes] = None
    
    @classmethod
    def from_path(cls, path: Path) -> "ImageItem":
        """パスからImageItemを作成"""
        return cls(
            path=path,
            name=path.name,
            size=path.stat().st_size if path.exists() else 0
        )
    
    def __str__(self) -> str:
        return self.name