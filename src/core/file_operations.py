import shutil
from pathlib import Path
from typing import Optional, List, Tuple
from send2trash import send2trash
from dataclasses import dataclass
from enum import Enum


class OperationType(Enum):
    MOVE = "move"
    DELETE = "delete"


@dataclass
class FileOperation:
    operation_type: OperationType
    source_path: Path
    destination_path: Optional[Path] = None
    
    def undo(self) -> bool:
        if self.operation_type == OperationType.MOVE and self.destination_path:
            try:
                # 元のパスに既にファイルが存在する場合は、別の名前で復元
                restore_path = self.source_path
                if restore_path.exists():
                    base_name = self.source_path.stem
                    extension = self.source_path.suffix
                    counter = 1
                    while restore_path.exists():
                        restore_path = self.source_path.parent / f"{base_name}_restored_{counter}{extension}"
                        counter += 1
                
                shutil.move(str(self.destination_path), str(restore_path))
                return True
            except Exception as e:
                print(f"Undo failed: {e}")
                return False
        elif self.operation_type == OperationType.DELETE:
            # ゴミ箱からの復元は現時点ではサポートしない
            return False
        return False


class FileOperationManager:
    def __init__(self, max_history: int = 20):
        self.history: List[FileOperation] = []
        self.max_history = max_history
        
    def move_file(self, source: Path, destination_dir: Path, rename_pattern: Optional[str] = None) -> Optional[Path]:
        if not source.exists():
            return None
            
        if not destination_dir.exists():
            destination_dir.mkdir(parents=True, exist_ok=True)
            
        if rename_pattern:
            destination = destination_dir / rename_pattern
        else:
            destination = destination_dir / source.name
            
        if destination.exists():
            base_name = destination.stem
            extension = destination.suffix
            counter = 1
            while destination.exists():
                destination = destination_dir / f"{base_name}-{counter}{extension}"
                counter += 1
                
        try:
            shutil.move(str(source), str(destination))
            operation = FileOperation(OperationType.MOVE, source, destination)
            self._add_to_history(operation)
            return destination
        except Exception as e:
            print(f"Error moving file: {e}")
            return None
            
    def delete_file(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False
            
        try:
            send2trash(str(file_path))
            operation = FileOperation(OperationType.DELETE, file_path)
            self._add_to_history(operation)
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
            
    def undo_last_operation(self) -> bool:
        if not self.history:
            return False
            
        last_operation = self.history.pop()
        return last_operation.undo()
        
    def _add_to_history(self, operation: FileOperation):
        self.history.append(operation)
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
    def get_rename_pattern(self, original_name: str, index: int) -> str:
        path = Path(original_name)
        return f"{path.stem}-{index}{path.suffix}"
    
    def get_images_from_folder(self, folder_path: Path) -> List[Path]:
        """フォルダから画像ファイルを取得"""
        supported_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.PNG', '.JPG', '.JPEG', '.WEBP'}
        images = []
        
        if not folder_path.exists() or not folder_path.is_dir():
            return images
            
        for file_path in sorted(folder_path.iterdir()):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                images.append(file_path)
                
        return images