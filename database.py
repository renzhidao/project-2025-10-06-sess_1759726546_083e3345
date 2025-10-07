"""
数据库操作模块
原子化设计：完全独立，无UI依赖，纯数据层
"""
import sqlite3
import time
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
from config import Config, ContentType

class DatabaseManager:
    """剪切板数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        :param db_path: 数据库路径，默认使用Config中的路径
        """
        self.db_path = db_path or Config.get_db_path()
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典形式
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建剪切板历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clipboard_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    timestamp REAL NOT NULL,
                    char_count INTEGER DEFAULT 0,
                    preview TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')
            
            # 创建索引加速查询
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON clipboard_history(timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_content_type 
                ON clipboard_history(content_type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_favorite 
                ON clipboard_history(is_favorite)
            ''')
    
    def add_clipboard_item(self, content: str, check_duplicate: bool = True) -> Optional[int]:
        """
        添加剪切板记录
        :param content: 剪切板内容
        :param check_duplicate: 是否检查重复
        :return: 新记录ID，如果是重复则返回None
        """
        if not content or len(content) > Config.MAX_CONTENT_LENGTH:
            return None
        
        # 去重检查
        if check_duplicate and Config.DUPLICATE_CHECK_ENABLED:
            if self._is_duplicate(content):
                return None
        
        content_type = ContentType.detect(content)
        preview = self._generate_preview(content)
        char_count = len(content)
        timestamp = time.time()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clipboard_history 
                (content, content_type, timestamp, char_count, preview)
                VALUES (?, ?, ?, ?, ?)
            ''', (content, content_type, timestamp, char_count, preview))
            
            return cursor.lastrowid
    
    def _is_duplicate(self, content: str) -> bool:
        """检查是否重复（与最近的记录比较）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content FROM clipboard_history 
                ORDER BY timestamp DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            return row and row['content'] == content
    
    def _generate_preview(self, content: str) -> str:
        """生成预览文本"""
        preview = content[:Config.MAX_PREVIEW_LENGTH]
        if len(content) > Config.MAX_PREVIEW_LENGTH:
            preview += "..."
        return preview.replace('\n', ' ')
    
    def get_all_items(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        获取所有记录（分页）
        :param limit: 每页数量
        :param offset: 偏移量
        :return: 记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM clipboard_history 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_items(self, keyword: str, limit: int = 100) -> List[Dict]:
        """
        搜索记录
        :param keyword: 搜索关键词
        :param limit: 最大返回数量
        :return: 匹配的记录列表
        """
        if len(keyword) < Config.SEARCH_MIN_LENGTH:
            return []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM clipboard_history 
                WHERE content LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (f'%{keyword}%', limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_item(self, item_id: int) -> bool:
        """
        删除单条记录
        :param item_id: 记录ID
        :return: 是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM clipboard_history WHERE id = ?', (item_id,))
            return cursor.rowcount > 0
    
    def clear_all(self) -> int:
        """
        清空所有记录
        :return: 删除的记录数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM clipboard_history')
            count = cursor.fetchone()['count']
            cursor.execute('DELETE FROM clipboard_history')
            return count
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        :return: 统计数据字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM clipboard_history')
            total = cursor.fetchone()['total']
            
            cursor.execute('''
                SELECT content_type, COUNT(*) as count 
                FROM clipboard_history 
                GROUP BY content_type
            ''')
            type_stats = {row['content_type']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_items': total,
                'by_type': type_stats
            }
    
    def toggle_favorite(self, item_id: int) -> bool:
        """
        切换收藏状态
        :param item_id: 记录ID
        :return: 切换后的状态
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE clipboard_history 
                SET is_favorite = 1 - is_favorite 
                WHERE id = ?
            ''', (item_id,))
            
            cursor.execute('SELECT is_favorite FROM clipboard_history WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            return bool(row['is_favorite']) if row else False