"""
画像リストウィジェットの実装
"""
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QSize, Signal, QThread, Signal as pyqtSignal
from PySide6.QtGui import QPixmap, QImage
from pathlib import Path
from typing import Optional
import concurrent.futures
from functools import lru_cache
from ..utils.thumbnail_cache import ThumbnailCache


class ThumbnailLoader(QThread):
    """サムネイル読み込み用スレッド"""
    thumbnail_loaded = pyqtSignal(Path, QPixmap)
    
    def __init__(self, image_path: Path, size: QSize, cache: ThumbnailCache):
        super().__init__()
        self.image_path = image_path
        self.size = size
        self.cache = cache
        
    def run(self):
        """サムネイルを読み込む（キャッシュ対応）"""
        try:
            # キャッシュまたは新規生成
            pixmap = self.cache.generate_thumbnail(self.image_path, self.size)
            if pixmap and not pixmap.isNull():
                self.thumbnail_loaded.emit(self.image_path, pixmap)
        except Exception as e:
            print(f"サムネイル読み込みエラー: {self.image_path} - {str(e)}")


class ImageItemWidget(QWidget):
    """画像アイテムウィジェット"""
    
    def __init__(self, image_path: Path, thumbnail_size: QSize = QSize(150, 150)):
        super().__init__()
        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.setup_ui()
        
    def setup_ui(self):
        """UIのセットアップ"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # サムネイル
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(self.thumbnail_size)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.thumbnail_label)
        
        # ファイル名
        self.filename_label = QLabel(self.image_path.name)
        self.filename_label.setWordWrap(True)
        layout.addWidget(self.filename_label, 1)
        
        # プレースホルダー画像を設定
        self.set_placeholder()
        
    def set_placeholder(self):
        """プレースホルダー画像を設定"""
        self.thumbnail_label.setText("読み込み中...")
        
    def set_thumbnail(self, pixmap: QPixmap):
        """サムネイルを設定"""
        self.thumbnail_label.setPixmap(pixmap)
        
    def get_info(self) -> str:
        """画像情報を取得"""
        try:
            size = self.image_path.stat().st_size / 1024 / 1024  # MB
            return f"{self.image_path.name} ({size:.1f}MB)"
        except:
            return self.image_path.name


class ImageListWidget(QListWidget):
    """画像リストウィジェット"""
    
    # カスタムシグナル
    image_selected = Signal(Path)
    
    def __init__(self):
        super().__init__()
        self.thumbnail_size = QSize(150, 150)
        self.thumbnail_loaders = []
        self.thumbnail_cache = ThumbnailCache()
        self.setup_ui()
        
    def setup_ui(self):
        """UIのセットアップ"""
        self.setViewMode(QListWidget.ListMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setMovement(QListWidget.Static)
        self.setSpacing(5)
        self.setUniformItemSizes(False)
        
        # スタイル設定
        self.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        
    def add_image(self, image_path: Path):
        """画像をリストに追加"""
        # アイテムウィジェットを作成
        item_widget = ImageItemWidget(image_path, self.thumbnail_size)
        
        # リストアイテムを作成
        item = QListWidgetItem()
        item.setSizeHint(QSize(400, self.thumbnail_size.height() + 10))
        
        # アイテムを追加
        self.addItem(item)
        self.setItemWidget(item, item_widget)
        
        # サムネイルを同期的に読み込む（パフォーマンスのため、今は同期版を使用）
        try:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                thumbnail = pixmap.scaled(
                    self.thumbnail_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                item_widget.set_thumbnail(thumbnail)
        except Exception as e:
            print(f"サムネイル読み込みエラー: {e}")
        
    def load_thumbnail_async(self, image_path: Path, item_widget: ImageItemWidget):
        """サムネイルを非同期で読み込む"""
        loader = ThumbnailLoader(image_path, self.thumbnail_size, self.thumbnail_cache)
        # ローダーにウィジェットの参照を保持
        loader.item_widget = item_widget
        loader.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        loader.start()
        self.thumbnail_loaders.append(loader)
        
    def on_thumbnail_loaded(self, image_path: Path, pixmap: QPixmap):
        """サムネイル読み込み完了時の処理"""
        # senderからローダーを取得
        loader = self.sender()
        if hasattr(loader, 'item_widget'):
            item_widget = loader.item_widget
            if item_widget.image_path == image_path:
                item_widget.set_thumbnail(pixmap)
            
        # 完了したローダーを削除
        for loader in self.thumbnail_loaders[:]:
            if not loader.isRunning():
                self.thumbnail_loaders.remove(loader)
                
    def get_selected_image_path(self) -> Optional[Path]:
        """選択中の画像パスを取得"""
        current_item = self.currentItem()
        if current_item:
            item_widget = self.itemWidget(current_item)
            if item_widget and hasattr(item_widget, 'image_path'):
                return item_widget.image_path
        return None
        
    def keyPressEvent(self, event):
        """キーイベント処理"""
        if event.key() == Qt.Key_Up:
            current_row = self.currentRow()
            if current_row > 0:
                self.setCurrentRow(current_row - 1)
                event.accept()
                return
        elif event.key() == Qt.Key_Down:
            current_row = self.currentRow()
            if current_row < self.count() - 1:
                self.setCurrentRow(current_row + 1)
                event.accept()
                return
                
        super().keyPressEvent(event)
        
    def clear(self):
        """リストをクリア"""
        # ローダーを停止
        for loader in self.thumbnail_loaders:
            if loader.isRunning():
                loader.quit()
                loader.wait()
        self.thumbnail_loaders.clear()
        
        # リストをクリア
        super().clear()