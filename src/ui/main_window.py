"""
メインウィンドウの実装
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QMessageBox,
    QToolBar, QStatusBar, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QSettings, QSize
from PySide6.QtGui import QAction, QKeySequence, QPixmap
from pathlib import Path
from typing import Optional, List

from .image_list_widget import ImageListWidget, ImageItemWidget
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
        self.delete_to_trash: bool = True  # デフォルトはゴミ箱へ
        self.auto_rename: bool = True  # デフォルトは自動リネーム有効
        self.undo_stack: List[dict] = []  # {'action': str, 'source': Path, 'destination': Path, 'row': int}
        
        self.setup_ui()
        self.setup_menu()
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
        self.reject_button.clicked.connect(self.handle_delete_action)
        button_layout.addWidget(self.reject_button)
        
        # Undoボタン
        self.undo_button = QPushButton("Undo (Ctrl+Z)")
        self.undo_button.clicked.connect(self.undo_last_action)
        button_layout.addWidget(self.undo_button)
        
        main_layout.addLayout(button_layout)
        
        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # ファイル数表示用のラベル
        self.file_count_label = QLabel()
        self.status_bar.addPermanentWidget(self.file_count_label)
        
        self.update_status("")
        self.update_file_counts()
        
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
        
    def setup_menu(self):
        """メニューバーのセットアップ"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        open_action = QAction("フォルダを開く...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("終了", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # フォルダ管理メニュー
        folder_menu = menubar.addMenu("フォルダ管理")
        
        rename_keep_folder_action = QAction("選別先フォルダ名を変更...", self)
        rename_keep_folder_action.triggered.connect(self.rename_keep_folder)
        folder_menu.addAction(rename_keep_folder_action)
        
        # 編集メニュー
        edit_menu = menubar.addMenu("編集")
        
        undo_action = QAction("元に戻す", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo_last_action)
        edit_menu.addAction(undo_action)
        
        edit_menu.addSeparator()
        
        settings_action = QAction("設定...", self)
        settings_action.triggered.connect(self.open_settings)
        edit_menu.addAction(settings_action)
        
    def setup_shortcuts(self):
        """キーボードショートカットのセットアップ"""
        # Enter: 保持フォルダへ移動
        enter_action = QAction(self)
        enter_action.setShortcut(Qt.Key_Return)
        enter_action.triggered.connect(self.move_to_keep_folder)
        self.addAction(enter_action)
        
        # Backspace: 削除動作（設定により動作が変わる）
        delete_action = QAction(self)
        delete_action.setShortcut(Qt.Key_Backspace)
        delete_action.triggered.connect(self.handle_delete_action)
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
            self.update_file_counts()
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
            self.delete_to_trash = dialog.is_delete_to_trash()
            self.auto_rename = dialog.is_auto_rename_enabled()
            self.save_settings()
            self.update_file_counts()
            
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
        
    def handle_delete_action(self):
        """削除アクション（設定によりゴミ箱か削除フォルダへ）"""
        if self.delete_to_trash:
            self.move_to_trash()
        else:
            self.move_to_delete_folder()
        
    def move_to_trash(self):
        """現在の画像をゴミ箱へ移動（Backspace キー）"""
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
                
            # 現在の行番号を保存
            current_row = self.image_list.row(current_item)
            
            # ファイルをゴミ箱へ
            if self.file_operations.delete_file(source_path):
                # Undo スタックに追加（ゴミ箱操作は特別扱い）
                self.undo_stack.append({
                    'action': 'trash',
                    'source': source_path,
                    'destination': None,
                    'row': current_row
                })
                
                # リストから削除
                self.image_list.takeItem(current_row)
                
                # ステータス更新
                self.update_status(f"{source_path.name} をゴミ箱へ移動しました")
                self.update_file_counts()
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
            # 現在の行番号を保存
            current_row = self.image_list.row(current_item)
            
            # 次の画像を選択
            next_row = current_row + 1
            if next_row < self.image_list.count():
                self.image_list.setCurrentRow(next_row)
            elif self.image_list.count() > 1:
                self.image_list.setCurrentRow(self.image_list.count() - 2)
                
            # ファイルを移動（自動リネームが有効な場合は連番を付与）
            rename_pattern = None
            if self.auto_rename and action == "keep":
                index = self.file_operations.get_next_index_for_file(
                    destination_folder, source_path.stem, source_path.suffix
                )
                rename_pattern = self.file_operations.get_rename_pattern(source_path.name, index)
            
            destination_path = self.file_operations.move_file(source_path, destination_folder, rename_pattern)
            
            if destination_path:
                # Undo スタックに追加
                self.undo_stack.append({
                    'action': action,
                    'source': source_path,
                    'destination': destination_path,
                    'row': current_row
                })
                
                # リストから削除
                self.image_list.takeItem(current_row)
            
            # ステータス更新
            self.update_status(f"{source_path.name} を {action} フォルダへ移動しました")
            self.update_file_counts()
            self.image_moved.emit(source_path, destination_path)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルの移動に失敗しました: {str(e)}")
            
    def undo_last_action(self):
        """最後の操作を元に戻す"""
        if not self.undo_stack:
            self.update_status("元に戻す操作がありません")
            return
            
        operation = self.undo_stack.pop()
        action = operation['action']
        
        if action == "rename_folder":
            # フォルダ名変更を元に戻す
            old_path = operation['old_path']
            new_path = operation['new_path']
            try:
                new_path.rename(old_path)
                self.keep_folder = old_path
                self.save_settings()
                self.update_file_counts()
                self.update_status(f"フォルダ名を元に戻しました: {old_path.name}")
                return
            except Exception as e:
                self.update_status(f"フォルダ名を元に戻せませんでした: {str(e)}")
                # 失敗した場合はスタックに戻す
                self.undo_stack.append(operation)
                return
        
        source_path = operation['source']
        destination_path = operation['destination']
        original_row = operation['row']
        
        if action == "trash":
            self.update_status("ゴミ箱への移動は元に戻せません")
            # スタックに戻す
            self.undo_stack.append(operation)
            return
            
        try:
            # FileOperationManagerのundoを使用
            if self.file_operations.undo_last_operation():
                # リストの適切な位置に再追加
                # アイテムを作成
                item_widget = ImageItemWidget(source_path, self.image_list.thumbnail_size)
                item = QListWidgetItem()
                item.setSizeHint(QSize(400, self.image_list.thumbnail_size.height() + 10))
                
                # 元の位置に挿入
                if original_row <= self.image_list.count():
                    self.image_list.insertItem(original_row, item)
                else:
                    self.image_list.addItem(item)
                    
                self.image_list.setItemWidget(item, item_widget)
                
                # サムネイルを読み込む
                try:
                    pixmap = QPixmap(str(source_path))
                    if not pixmap.isNull():
                        thumbnail = pixmap.scaled(
                            self.image_list.thumbnail_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        item_widget.set_thumbnail(thumbnail)
                except Exception:
                    pass
                
                self.update_status(f"{source_path.name} を元に戻しました")
                self.update_file_counts()
            else:
                self.update_status("元に戻す操作に失敗しました")
                # 失敗した場合はスタックに戻す
                self.undo_stack.append(operation)
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"元に戻す操作に失敗しました: {str(e)}")
            # 失敗した場合はスタックに戻す
            self.undo_stack.append(operation)
            
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
        self.settings.setValue("delete_to_trash", self.delete_to_trash)
        self.settings.setValue("auto_rename", self.auto_rename)
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
            
        self.delete_to_trash = self.settings.value("delete_to_trash", True, type=bool)
        self.auto_rename = self.settings.value("auto_rename", True, type=bool)
            
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
            
    def update_file_counts(self):
        """フォルダ内のファイル数を更新"""
        source_count = 0
        dest_count = 0
        
        # 選別対象フォルダの画像数
        if self.current_folder and self.current_folder.exists():
            source_count = len(self.file_operations.get_images_from_folder(self.current_folder))
            
        # 選別先フォルダの画像数
        if self.keep_folder and self.keep_folder.exists():
            dest_count = len(self.file_operations.get_images_from_folder(self.keep_folder))
            
        # ステータスバーに表示
        count_text = f"選別対象: {source_count}枚 | 選別先: {dest_count}枚"
        self.file_count_label.setText(count_text)
        
    def rename_keep_folder(self):
        """選別先フォルダ名を変更"""
        if not self.keep_folder:
            QMessageBox.warning(self, "警告", "選別先フォルダが設定されていません")
            return
            
        from PySide6.QtWidgets import QInputDialog
        
        current_name = self.keep_folder.name
        new_name, ok = QInputDialog.getText(
            self,
            "フォルダ名を変更",
            "新しいフォルダ名:",
            text=current_name
        )
        
        if ok and new_name and new_name != current_name:
            try:
                # 新しいパスを作成
                new_path = self.keep_folder.parent / new_name
                
                # フォルダが既に存在するかチェック
                if new_path.exists():
                    QMessageBox.warning(self, "警告", f"フォルダ '{new_name}' は既に存在します")
                    return
                    
                # フォルダ名を変更
                self.keep_folder.rename(new_path)
                
                # Undo スタックに追加
                self.undo_stack.append({
                    'action': 'rename_folder',
                    'old_path': self.keep_folder,
                    'new_path': new_path,
                    'row': -1  # フォルダ操作なので行番号は不要
                })
                
                # 内部パスを更新
                self.keep_folder = new_path
                self.save_settings()
                self.update_file_counts()
                
                QMessageBox.information(self, "成功", f"フォルダ名を '{new_name}' に変更しました")
                
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"フォルダ名の変更に失敗しました: {str(e)}")
        
    def closeEvent(self, event):
        """ウィンドウを閉じる時の処理"""
        self.save_settings()
        event.accept()