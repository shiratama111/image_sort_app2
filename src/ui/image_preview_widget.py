"""
画像プレビューウィジェットの実装
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QTransform
from pathlib import Path
from typing import Optional


class ImagePreviewWidget(QWidget):
    """画像プレビューウィジェット"""
    
    # カスタムシグナル
    image_loaded = Signal(Path)
    zoom_changed = Signal(float)
    
    def __init__(self):
        super().__init__()
        self.current_image_path: Optional[Path] = None
        self.original_pixmap: Optional[QPixmap] = None
        self.zoom_factor = 1.0
        self.rotation = 0
        self.fit_to_window_enabled = True
        self.setup_ui()
        
    def setup_ui(self):
        """UIのセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # スクロールエリア
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
        """)
        layout.addWidget(self.scroll_area)
        
        # 画像表示用ラベル
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)
        self.scroll_area.setWidget(self.image_label)
        
        # 初期表示
        self.show_placeholder()
        
    def show_placeholder(self):
        """プレースホルダーを表示"""
        self.image_label.setText("画像が選択されていません")
        self.image_label.setPixmap(QPixmap())
        
    def set_image(self, image_path: Path):
        """画像を設定"""
        if not image_path.exists():
            self.show_placeholder()
            return
            
        self.current_image_path = image_path
        
        try:
            # 画像を読み込む
            self.original_pixmap = QPixmap(str(image_path))
            
            if self.original_pixmap.isNull():
                self.image_label.setText(f"画像を読み込めません: {image_path.name}")
                return
                
            # 表示を更新
            self.update_display()
            self.image_loaded.emit(image_path)
            
        except Exception as e:
            self.image_label.setText(f"エラー: {str(e)}")
            
    def update_display(self):
        """表示を更新"""
        if not self.original_pixmap:
            return
            
        # 変換を適用
        transform = QTransform()
        transform.rotate(self.rotation)
        
        # 変換後のPixmapを作成
        transformed_pixmap = self.original_pixmap.transformed(
            transform,
            Qt.SmoothTransformation
        )
        
        # ウィンドウに合わせるか、ズーム倍率を適用
        if self.fit_to_window_enabled:
            self.fit_to_window(transformed_pixmap)
        else:
            scaled_pixmap = transformed_pixmap.scaled(
                transformed_pixmap.size() * self.zoom_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            
    def fit_to_window(self, pixmap: Optional[QPixmap] = None):
        """画像をウィンドウサイズに合わせる"""
        if pixmap is None:
            pixmap = self.original_pixmap
            
        if not pixmap:
            return
            
        # スクロールエリアのサイズを取得
        viewport_size = self.scroll_area.viewport().size()
        
        # アスペクト比を保持してスケール
        scaled_pixmap = pixmap.scaled(
            viewport_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        
        # ズーム倍率を計算
        self.zoom_factor = min(
            viewport_size.width() / pixmap.width(),
            viewport_size.height() / pixmap.height()
        )
        self.zoom_changed.emit(self.zoom_factor)
        
    def set_zoom(self, zoom_factor: float):
        """ズーム倍率を設定"""
        self.zoom_factor = max(0.1, min(5.0, zoom_factor))
        self.fit_to_window_enabled = False
        self.update_display()
        self.zoom_changed.emit(self.zoom_factor)
        
    def zoom_in(self):
        """ズームイン"""
        self.set_zoom(self.zoom_factor * 1.25)
        
    def zoom_out(self):
        """ズームアウト"""
        self.set_zoom(self.zoom_factor * 0.8)
        
    def zoom_reset(self):
        """ズームをリセット"""
        self.zoom_factor = 1.0
        self.fit_to_window_enabled = False
        self.update_display()
        
    def rotate_left(self):
        """左に90度回転"""
        self.rotation = (self.rotation - 90) % 360
        self.update_display()
        
    def rotate_right(self):
        """右に90度回転"""
        self.rotation = (self.rotation + 90) % 360
        self.update_display()
        
    def toggle_fit_to_window(self):
        """ウィンドウに合わせる表示を切り替え"""
        self.fit_to_window_enabled = not self.fit_to_window_enabled
        self.update_display()
        
    def resizeEvent(self, event):
        """リサイズイベント"""
        super().resizeEvent(event)
        
        # ウィンドウに合わせる表示が有効な場合は再調整
        if self.fit_to_window_enabled and self.original_pixmap:
            self.update_display()
            
    def wheelEvent(self, event):
        """マウスホイールイベント（ズーム）"""
        if event.modifiers() == Qt.ControlModifier:
            # Ctrl + ホイールでズーム
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
            
    def get_image_info(self) -> dict:
        """現在の画像情報を取得"""
        if not self.current_image_path or not self.original_pixmap:
            return {}
            
        return {
            'path': self.current_image_path,
            'width': self.original_pixmap.width(),
            'height': self.original_pixmap.height(),
            'size': self.current_image_path.stat().st_size,
            'zoom': self.zoom_factor,
            'rotation': self.rotation
        }