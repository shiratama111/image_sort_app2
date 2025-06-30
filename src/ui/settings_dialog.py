"""
設定ダイアログの実装
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QDialogButtonBox, QGroupBox, QCheckBox,
    QSpinBox, QComboBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QSettings
from pathlib import Path
from typing import Optional


class SettingsDialog(QDialog):
    """設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("ImageRenameApp", "Settings")
        self.keep_folder: Optional[Path] = None
        self.delete_folder: Optional[Path] = None
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UIのセットアップ"""
        self.setWindowTitle("設定")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # タブウィジェット
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # フォルダ設定タブ
        folder_tab = self.create_folder_tab()
        tab_widget.addTab(folder_tab, "フォルダ設定")
        
        # 表示設定タブ
        display_tab = self.create_display_tab()
        tab_widget.addTab(display_tab, "表示設定")
        
        # ショートカット設定タブ
        shortcut_tab = self.create_shortcut_tab()
        tab_widget.addTab(shortcut_tab, "ショートカット")
        
        # ダイアログボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def create_folder_tab(self) -> QWidget:
        """フォルダ設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 選別先フォルダ設定
        folder_group = QGroupBox("選別先フォルダ")
        folder_layout = QGridLayout(folder_group)
        
        # 保持フォルダ
        folder_layout.addWidget(QLabel("保持フォルダ:"), 0, 0)
        self.keep_folder_edit = QLineEdit()
        self.keep_folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.keep_folder_edit, 0, 1)
        
        keep_browse_btn = QPushButton("参照...")
        keep_browse_btn.clicked.connect(self.browse_keep_folder)
        folder_layout.addWidget(keep_browse_btn, 0, 2)
        
        # 削除フォルダ
        folder_layout.addWidget(QLabel("削除フォルダ:"), 1, 0)
        self.delete_folder_edit = QLineEdit()
        self.delete_folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.delete_folder_edit, 1, 1)
        
        delete_browse_btn = QPushButton("参照...")
        delete_browse_btn.clicked.connect(self.browse_delete_folder)
        folder_layout.addWidget(delete_browse_btn, 1, 2)
        
        layout.addWidget(folder_group)
        
        # 自動作成オプション
        auto_create_group = QGroupBox("オプション")
        auto_create_layout = QVBoxLayout(auto_create_group)
        
        self.auto_create_folders_check = QCheckBox("フォルダが存在しない場合は自動作成")
        self.auto_create_folders_check.setChecked(True)
        auto_create_layout.addWidget(self.auto_create_folders_check)
        
        self.create_date_folders_check = QCheckBox("日付別のサブフォルダを作成")
        auto_create_layout.addWidget(self.create_date_folders_check)
        
        layout.addWidget(auto_create_group)
        layout.addStretch()
        
        return widget
        
    def create_display_tab(self) -> QWidget:
        """表示設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # サムネイルサイズ
        thumbnail_group = QGroupBox("サムネイル")
        thumbnail_layout = QGridLayout(thumbnail_group)
        
        thumbnail_layout.addWidget(QLabel("サイズ:"), 0, 0)
        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(50, 300)
        self.thumbnail_size_spin.setValue(150)
        self.thumbnail_size_spin.setSuffix(" px")
        thumbnail_layout.addWidget(self.thumbnail_size_spin, 0, 1)
        
        layout.addWidget(thumbnail_group)
        
        # プレビュー設定
        preview_group = QGroupBox("プレビュー")
        preview_layout = QVBoxLayout(preview_group)
        
        self.fit_to_window_check = QCheckBox("画像をウィンドウサイズに合わせる")
        self.fit_to_window_check.setChecked(True)
        preview_layout.addWidget(self.fit_to_window_check)
        
        self.show_info_check = QCheckBox("画像情報を表示")
        self.show_info_check.setChecked(True)
        preview_layout.addWidget(self.show_info_check)
        
        layout.addWidget(preview_group)
        
        # テーマ設定
        theme_group = QGroupBox("テーマ")
        theme_layout = QHBoxLayout(theme_group)
        
        theme_layout.addWidget(QLabel("カラーテーマ:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["ライト", "ダーク", "システム"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
        return widget
        
    def create_shortcut_tab(self) -> QWidget:
        """ショートカット設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # ショートカット一覧
        shortcuts_group = QGroupBox("キーボードショートカット")
        shortcuts_layout = QGridLayout(shortcuts_group)
        
        shortcuts = [
            ("保持フォルダへ移動", "Enter"),
            ("ゴミ箱へ移動", "Backspace"),
            ("前の画像", "↑"),
            ("次の画像", "↓"),
            ("元に戻す", "Ctrl+Z"),
            ("フォルダを開く", "Ctrl+O"),
            ("フルスクリーン切り替え", "F11"),
            ("ズームイン", "Ctrl++"),
            ("ズームアウト", "Ctrl+-"),
            ("実際のサイズ", "Ctrl+0"),
            ("ウィンドウに合わせる", "Ctrl+F")
        ]
        
        for i, (action, shortcut) in enumerate(shortcuts):
            shortcuts_layout.addWidget(QLabel(action), i, 0)
            shortcut_label = QLabel(shortcut)
            shortcut_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; padding: 2px 5px;")
            shortcuts_layout.addWidget(shortcut_label, i, 1)
            
        layout.addWidget(shortcuts_group)
        
        # カスタムショートカット（将来の拡張用）
        custom_group = QGroupBox("カスタムショートカット")
        custom_layout = QVBoxLayout(custom_group)
        custom_label = QLabel("カスタムショートカットは今後のバージョンで対応予定です。")
        custom_label.setStyleSheet("color: #666;")
        custom_layout.addWidget(custom_label)
        
        layout.addWidget(custom_group)
        layout.addStretch()
        
        return widget
        
    def browse_keep_folder(self):
        """保持フォルダを選択"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "保持フォルダを選択",
            str(self.keep_folder) if self.keep_folder else str(Path.home())
        )
        
        if folder:
            self.keep_folder = Path(folder)
            self.keep_folder_edit.setText(str(self.keep_folder))
            
    def browse_delete_folder(self):
        """削除フォルダを選択"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "削除フォルダを選択",
            str(self.delete_folder) if self.delete_folder else str(Path.home())
        )
        
        if folder:
            self.delete_folder = Path(folder)
            self.delete_folder_edit.setText(str(self.delete_folder))
            
    def set_keep_folder(self, folder: Optional[Path]):
        """保持フォルダを設定"""
        self.keep_folder = folder
        if folder:
            self.keep_folder_edit.setText(str(folder))
            
    def set_delete_folder(self, folder: Optional[Path]):
        """削除フォルダを設定"""
        self.delete_folder = folder
        if folder:
            self.delete_folder_edit.setText(str(folder))
            
    def get_keep_folder(self) -> Optional[Path]:
        """保持フォルダを取得"""
        return self.keep_folder
        
    def get_delete_folder(self) -> Optional[Path]:
        """削除フォルダを取得"""
        return self.delete_folder
        
    def save_settings(self):
        """設定を保存"""
        # フォルダ設定
        self.settings.setValue("keep_folder", str(self.keep_folder) if self.keep_folder else "")
        self.settings.setValue("delete_folder", str(self.delete_folder) if self.delete_folder else "")
        self.settings.setValue("auto_create_folders", self.auto_create_folders_check.isChecked())
        self.settings.setValue("create_date_folders", self.create_date_folders_check.isChecked())
        
        # 表示設定
        self.settings.setValue("thumbnail_size", self.thumbnail_size_spin.value())
        self.settings.setValue("fit_to_window", self.fit_to_window_check.isChecked())
        self.settings.setValue("show_info", self.show_info_check.isChecked())
        self.settings.setValue("theme", self.theme_combo.currentText())
        
    def load_settings(self):
        """設定を読み込む"""
        # フォルダ設定
        keep_folder = self.settings.value("keep_folder", "")
        if keep_folder:
            self.set_keep_folder(Path(keep_folder))
            
        delete_folder = self.settings.value("delete_folder", "")
        if delete_folder:
            self.set_delete_folder(Path(delete_folder))
            
        self.auto_create_folders_check.setChecked(
            self.settings.value("auto_create_folders", True, type=bool)
        )
        self.create_date_folders_check.setChecked(
            self.settings.value("create_date_folders", False, type=bool)
        )
        
        # 表示設定
        self.thumbnail_size_spin.setValue(
            self.settings.value("thumbnail_size", 150, type=int)
        )
        self.fit_to_window_check.setChecked(
            self.settings.value("fit_to_window", True, type=bool)
        )
        self.show_info_check.setChecked(
            self.settings.value("show_info", True, type=bool)
        )
        
        theme = self.settings.value("theme", "システム")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
    def accept(self):
        """OKボタンが押された時の処理"""
        self.save_settings()
        super().accept()