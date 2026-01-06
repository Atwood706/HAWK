"""
AWDL Standard Library - File I/O Tools

This module provides File I/O Tool implementations for AWDL workflows.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileReadTool:
    """
    File Read Tool.
    
    This tool reads the contents of a file.
    
    Inputs:
        path: Path to the file to read
        
    Outputs:
        content: File contents as a string
    """
    
    encoding: str = "utf-8"
    
    def execute(
        self,
        path: str,
    ) -> Dict[str, Any]:
        """
        Execute the file read.
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with 'content' key containing file contents
        """
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return {
                    "content": "",
                    "error": f"File not found: {path}",
                }
            
            content = file_path.read_text(encoding=self.encoding)
            
            return {
                "content": content,
            }
        except Exception as e:
            return {
                "content": "",
                "error": str(e),
            }
    
    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "FileReadTool":
        """Create a file read tool with configuration."""
        config = config or {}
        return cls(
            encoding=config.get("encoding", "utf-8"),
        )


@dataclass
class FileWriteTool:
    """
    File Write Tool.
    
    This tool writes content to a file.
    
    Inputs:
        path: Path to the file to write
        content: Content to write to the file
        
    Outputs:
        success: Whether the write succeeded
    """
    
    encoding: str = "utf-8"
    create_dirs: bool = True
    
    def execute(
        self,
        path: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Execute the file write.
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            Dictionary with 'success' key indicating success
        """
        try:
            file_path = Path(path)
            
            if self.create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_path.write_text(content, encoding=self.encoding)
            
            return {
                "success": True,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "FileWriteTool":
        """Create a file write tool with configuration."""
        config = config or {}
        return cls(
            encoding=config.get("encoding", "utf-8"),
            create_dirs=config.get("create_dirs", True),
        )

