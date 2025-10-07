"""
全局配置模块
原子化设计：所有配置集中管理，便于维护和测试
"""
import os
from pathlib import Path

class Config:
    """应用全局配置类"""
    
    # 应用信息
    APP_NAME = "ClipboardManager"
    APP_VERSION = "1.0.0"
    
    # 数据库配置
    DB_NAME = "clipboard_history.db"
    
    @staticmethod
    def get_db_path():
        """
        获取数据库路径（跨平台兼容）
        Android: /data/data/包名/databases/
        PC测试: ./data/
        """
        if os.environ.get('ANDROID_STORAGE'):
            # Android环境
            base_path = os.environ.get('ANDROID_STORAGE')
        else:
            # 开发/测试环境
            base_path = Path(__file__).parent / "data"
            base_path.mkdir(exist_ok=True)
        
        return str(Path(base_path) / Config.DB_NAME)
    
    # 剪切板配置
    MAX_PREVIEW_LENGTH = 100  # 预览文本最大长度
    DUPLICATE_CHECK_ENABLED = True  # 是否启用去重
    
    # 性能配置
    BATCH_SIZE = 50  # 分页查询大小
    MAX_CONTENT_LENGTH = 1_000_000  # 单条内容最大字符数（100万）
    
    # 搜索配置
    SEARCH_MIN_LENGTH = 2  # 最小搜索关键词长度

# 常量定义
class ContentType:
    """内容类型枚举"""
    TEXT = "text"
    URL = "url"
    CODE = "code"
    UNKNOWN = "unknown"
    
    @staticmethod
    def detect(content: str) -> str:
        """简单检测内容类型"""
        if not content:
            return ContentType.UNKNOWN
        
        content_lower = content.lower().strip()
        
        # URL检测
        if content_lower.startswith(('http://', 'https://', 'ftp://')):
            return ContentType.URL
        
        # 代码检测（简单规则）
        code_indicators = ['def ', 'class ', 'import ', 'function ', 'const ', 'var ']
        if any(indicator in content_lower for indicator in code_indicators):
            return ContentType.CODE
        
        return ContentType.TEXT