"""
メインウィンドウの実装
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QMessageBox,
    QToolBar, QStatusBar
)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QAction, QKeySequence
from pathlib import Path
from typing import Optional, List

from .image_list_widget import ImageListWidget
# デバッグ用：同期版を使用する場合はコメントを切り替える
# from .image_list_widget_sync import ImageListWidgetSync as ImageListWidget
from .image_preview_widget import ImagePreviewWidget
from .settings_dialog import SettingsDialog
from ..core.file_operations import FileOperationManager
from ..models.image_item import ImageItem


class MainWindow(QMainWindow):
    """画像選別アプリケーションのメインウィンドウ"""
    
    # カスタムシグナル
    folder_loaded = Signal(Path)
    image_selected = Signal(Path)
    image_moved = Signal(Path, Path)
    
    def __init__(self):
        super().__init__()
        self.file_operations = FileOperationManager()
        self.settings = QSettings("ImageRenameApp", "MainWindow")
        self.current_folder: Optional[Path] = None
        self.keep_folder: Optional[Path] = None
        self.delete_folder: Optional[Path] = None
        self.undo_stack: List[tuple] = []  # (action, source, destination)
        
        self.setup_ui()
        self.setup_shortcuts()
        self.load_settings()
        
    def setup_ui(self):
        """UIのセットアップ"""
        self.setWindowTitle("画像選別アプリ")
        self.setGeometry(100, 100, 1200, 800)
        
        # セントラルウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        
        # ツールバー
        self.setup_toolbar()
        
        # スプリッター（左：リスト、右：プレビュー）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左側：画像リスト
        self.image_list = ImageListWidget()
        self.image_list.currentItemChanged.connect(self.on_image_selected)
        splitter.addWidget(self.image_list)
        
        # 右側：プレビュー
        self.image_preview = ImagePreviewWidget()
        splitter.addWidget(self.image_preview)
        
        # スプリッターの比率設定
        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)
        
        # ボタンバー
        button_layout = QHBoxLayout()
        
        # 受入れボタン
        self.accept_button = QPushButton("受入れ (Enter)")
        self.accept_button.clicked.connect(self.move_to_keep_folder)
        button_layout.addWidget(self.accept_button)
        
        # 破棄ボタン
        self.reject_button = QPushButton("破棄 (Backspace)")
        self.reject_button.clicked.connect(self.move_to_trash)
        button_layout.addWidget(self.reject_button)
        
        # Undoボタン
        self.undo_button = QPushButton("Undo (Ctrl+Z)")
        self.undo_button.clicked.connect(self.undo_last_action)
        button_layout.addWidget(self.undo_button)
        
        main_layout.addLayout(button_layout)
        
        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("")
        
    def setup_toolbar(self):
        """ツールバーのセットアップ"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # フォルダを開く
        open_action = QAction("フォルダを開く", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_folder)
        toolbar.addAction(open_action)
        
        # 設定
        settings_action = QAction("設定", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        # 現在のフォルダ表示
        self.folder_label = QLabel("フォルダが選択されていません")
        toolbar.addWidget(self.folder_label)
        
    def setup_shortcuts(self):
        """キーボードショートカットのセットアップ"""
        # Enter: 保持フォルダへ移動
        enter_action = QAction(self)
        enter_action.setShortcut(Qt.Key_Return)
        enter_action.triggered.connect(self.move_to_keep_folder)
        self.addAction(enter_action)
        
        # Backspace: 削除フォルダへ移動（ゴミ箱へ）
        delete_action = QAction(self)
        delete_action.setShortcut(Qt.Key_Backspace)
        delete_action.triggered.connect(self.move_to_trash)
        self.addAction(delete_action)
        
        # Ctrl+Z: 元に戻す
        undo_action = QAction(self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo_last_action)
        self.addAction(undo_action)
        
        # 上矢印: 前の画像
        up_action = QAction(self)
        up_action.setShortcut(Qt.Key_Up)
        up_action.triggered.connect(self.select_previous_image)
        self.addAction(up_action)
        
        # 下矢印: 次の画像
        down_action = QAction(self)
        down_action.setShortcut(Qt.Key_Down)
        down_action.triggered.connect(self.select_next_image)
        self.addAction(down_action)
        
        # F11: フルスクリーン切り替え
        fullscreen_action = QAction(self)
        fullscreen_action.setShortcut(Qt.Key_F11)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(fullscreen_action)
        
    def open_folder(self):
        """フォルダを開く"""
        from PySide6.QtWidgets import QFileDialog
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "画像フォルダを選択",
            str(Path.home())
        )
        
        if folder:
            self.load_folder(Path(folder))
            
    def load_folder(self, folder_path: Path):
        """フォルダから画像を読み込む"""
        try:
            self.current_folder = folder_path
            images = self.file_operations.get_images_from_folder(folder_path)
            
            self.image_list.clear()
            for image_path in images:
                self.image_list.add_image(image_path)
                
            self.folder_label.setText(f"フォルダ: {folder_path.name}")
            self.update_status(f"{len(images)}枚の画像を読み込みました")
            self.folder_loaded.emit(folder_path)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フォルダの読み込みに失敗しました: {str(e)}")
            
    def open_settings(self):
        """設定ダイアログを開く"""
        dialog = SettingsDialog(self)
        dialog.set_keep_folder(self.keep_folder)
        dialog.set_delete_folder(self.delete_folder)
        
        if dialog.exec():
            self.keep_folder = dialog.get_keep_folder()
            self.delete_folder = dialog.get_delete_folder()
            self.save_settings()
            
    def on_image_selected(self, current, previous):
        """画像が選択されたときの処理"""
        if current:
            image_item = self.image_list.itemWidget(current)
            if image_item and hasattr(image_item, 'image_path'):
                self.image_preview.set_image(image_item.image_path)
                self.image_selected.emit(image_item.image_path)
                self.update_status(f"選択中: {image_item.image_path.name}")
                
    def move_to_keep_folder(self):
        """現在の画像を保持フォルダへ移動"""
        if not self.keep_folder:
            QMessageBox.warning(self, "警告", "保持フォルダが設定されていません")
            return
            
        self._move_current_image(self.keep_folder, "keep")
        
    def move_to_trash(self):
        """現在の画像をゴミ箱へ移動（Del キー）"""
        current_item = self.image_list.currentItem()
        if not current_item:
            return
            
        image_widget = self.image_list.itemWidget(current_item)
        if not image_widget or not hasattr(image_widget, 'image_path'):
            return
            
        source_path = image_widget.image_path
        
        try:
            # 次の画像を選択
            next_row = self.image_list.row(current_item) + 1
            if next_row < self.image_list.count():
                self.image_list.setCurrentRow(next_row)
            elif self.image_list.count() > 1:
                self.image_list.setCurrentRow(self.image_list.count() - 2)
                
            # ファイルをゴミ箱へ
            if self.file_operations.delete_file(source_path):
                # リストから削除
                self.image_list.takeItem(self.image_list.row(current_item))
                
                # ステータス更新
                self.update_status(f"{source_path.name} をゴミ箱へ移動しました")
            else:
                QMessageBox.critical(self, "エラー", "ファイルの削除に失敗しました")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルの削除に失敗しました: {str(e)}")
            
    def move_to_delete_folder(self):
        """現在の画像を削除フォルダへ移動"""
        if not self.delete_folder:
            QMessageBox.warning(self, "警告", "削除フォルダが設定されていません")
            return
            
        self._move_current_image(self.delete_folder, "delete")
        
    def _move_current_image(self, destination_folder: Path, action: str):
        """現在選択中の画像を指定フォルダへ移動"""
        current_item = self.image_list.currentItem()
        if not current_item:
            return
            
        image_widget = self.image_list.itemWidget(current_item)
        if not image_widget or not hasattr(image_widget, 'image_path'):
            return
            
        source_path = image_widget.image_path
        
        try:
            # 次の画像を選択
            next_row = self.image_list.row(current_item) + 1
            if next_row < self.image_list.count():
                self.image_list.setCurrentRow(next_row)
            elif self.image_list.count() > 1:
                self.image_list.setCurrentRow(self.image_list.count() - 2)
                
            # ファイルを移動
            destination_path = self.file_operations.move_file(source_path, destination_folder)
            
            # Undo スタックに追加
            self.undo_stack.append((action, source_path, destination_path))
            
            # リストから削除
            self.image_list.takeItem(self.image_list.row(current_item))
            
            # ステータス更新
            self.update_status(f"{source_path.name} を {action} フォルダへ移動しました")
            self.image_moved.emit(source_path, destination_path)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルの移動に失敗しました: {str(e)}")
            
    def undo_last_action(self):
        """最後の操作を元に戻す"""
        if not self.undo_stack:
            self.update_status("元に戻す操作がありません")
            return
            
        action, source_path, destination_path = self.undo_stack.pop()
        
        try:
            # ファイルを元の場所に戻す
            self.file_operations.move_file(destination_path, source_path.parent)
            
            # リストに再追加
            self.image_list.add_image(source_path)
            
            self.update_status(f"{source_path.name} を元に戻しました")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"元に戻す操作に失敗しました: {str(e)}")
            
    def select_previous_image(self):
        """前の画像を選択"""
        current_row = self.image_list.currentRow()
        if current_row > 0:
            self.image_list.setCurrentRow(current_row - 1)
            
    def select_next_image(self):
        """次の画像を選択"""
        current_row = self.image_list.currentRow()
        if current_row < self.image_list.count() - 1:
            self.image_list.setCurrentRow(current_row + 1)
            
    def update_status(self, message: str):
        """ステータスバーを更新"""
        self.status_bar.showMessage(message)
        
    def toggle_fullscreen(self):
        """フルスクリーン表示を切り替え"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        
    def save_settings(self):
        """設定を保存"""
        self.settings.setValue("keep_folder", str(self.keep_folder) if self.keep_folder else "")
        self.settings.setValue("delete_folder", str(self.delete_folder) if self.delete_folder else "")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
    def load_settings(self):
        """設定を読み込む"""
        keep_folder = self.settings.value("keep_folder", "")
        if keep_folder:
            self.keep_folder = Path(keep_folder)
            
        delete_folder = self.settings.value("delete_folder", "")
        if delete_folder:
            self.delete_folder = Path(delete_folder)
            
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
            
    def closeEvent(self, event):
        """ウィンドウを閉じる時の処理"""
        self.save_settings()
        event.accept()