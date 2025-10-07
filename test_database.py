"""
database.py 单元测试
完整测试所有数据库操作
"""
import unittest
import os
import tempfile
import time
from pathlib import Path
from database import DatabaseManager
from config import ContentType

class TestDatabaseManager(unittest.TestCase):
    """测试DatabaseManager类"""
    
    def setUp(self):
        """每个测试前创建临时数据库"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """每个测试后删除临时数据库"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """测试数据库初始化"""
        self.assertTrue(os.path.exists(self.temp_db.name))
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_items'], 0)
    
    def test_add_clipboard_item(self):
        """测试添加剪切板记录"""
        item_id = self.db.add_clipboard_item("Hello World")
        self.assertIsNotNone(item_id)
        self.assertGreater(item_id, 0)
        
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_items'], 1)
    
    def test_duplicate_check(self):
        """测试重复检测"""
        content = "Duplicate Test"
        
        # 第一次添加成功
        id1 = self.db.add_clipboard_item(content, check_duplicate=True)
        self.assertIsNotNone(id1)
        
        # 第二次添加应该被拒绝
        id2 = self.db.add_clipboard_item(content, check_duplicate=True)
        self.assertIsNone(id2)
        
        # 不检查重复时可以添加
        id3 = self.db.add_clipboard_item(content, check_duplicate=False)
        self.assertIsNotNone(id3)
    
    def test_content_type_detection(self):
        """测试内容类型自动检测"""
        # 添加URL
        url_id = self.db.add_clipboard_item("https://example.com")
        items = self.db.get_all_items()
        self.assertEqual(items[0]['content_type'], ContentType.URL)
        
        # 添加代码
        self.db.clear_all()
        code_id = self.db.add_clipboard_item("def hello():\n    pass")
        items = self.db.get_all_items()
        self.assertEqual(items[0]['content_type'], ContentType.CODE)
    
    def test_preview_generation(self):
        """测试预览文本生成"""
        long_text = "A" * 200
        self.db.add_clipboard_item(long_text)
        
        items = self.db.get_all_items()
        preview = items[0]['preview']
        
        self.assertLess(len(preview), len(long_text))
        self.assertTrue(preview.endswith("..."))
    
    def test_get_all_items_pagination(self):
        """测试分页查询"""
        # 添加10条记录
        for i in range(10):
            self.db.add_clipboard_item(f"Item {i}", check_duplicate=False)
            time.sleep(0.01)  # 确保时间戳不同
        
        # 第一页
        page1 = self.db.get_all_items(limit=5, offset=0)
        self.assertEqual(len(page1), 5)
        
        # 第二页
        page2 = self.db.get_all_items(limit=5, offset=5)
        self.assertEqual(len(page2), 5)
        
        # 验证顺序（最新的在前）
        self.assertIn("Item 9", page1[0]['content'])
    
    def test_search_items(self):
        """测试搜索功能"""
        self.db.add_clipboard_item("Python is awesome", check_duplicate=False)
        self.db.add_clipboard_item("Java is cool", check_duplicate=False)
        self.db.add_clipboard_item("Python rocks", check_duplicate=False)
        
        # 搜索包含Python的记录
        results = self.db.search_items("Python")
        self.assertEqual(len(results), 2)
        
        # 搜索不存在的内容
        results = self.db.search_items("Ruby")
        self.assertEqual(len(results), 0)
        
        # 关键词太短
        results = self.db.search_items("P")
        self.assertEqual(len(results), 0)
    
    def test_delete_item(self):
        """测试删除单条记录"""
        item_id = self.db.add_clipboard_item("To be deleted")
        
        # 删除成功
        success = self.db.delete_item(item_id)
        self.assertTrue(success)
        
        # 再次删除失败
        success = self.db.delete_item(item_id)
        self.assertFalse(success)
        
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_items'], 0)
    
    def test_clear_all(self):
        """测试清空所有记录"""
        for i in range(5):
            self.db.add_clipboard_item(f"Item {i}", check_duplicate=False)
        
        count = self.db.clear_all()
        self.assertEqual(count, 5)
        
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_items'], 0)
    
    def test_toggle_favorite(self):
        """测试收藏功能"""
        item_id = self.db.add_clipboard_item("Favorite Test")
        
        # 第一次切换：设为收藏
        is_fav = self.db.toggle_favorite(item_id)
        self.assertTrue(is_fav)
        
        # 第二次切换：取消收藏
        is_fav = self.db.toggle_favorite(item_id)
        self.assertFalse(is_fav)
    
    def test_statistics(self):
        """测试统计功能"""
        self.db.add_clipboard_item("Plain text", check_duplicate=False)
        self.db.add_clipboard_item("https://test.com", check_duplicate=False)
        self.db.add_clipboard_item("def code():", check_duplicate=False)
        
        stats = self.db.get_statistics()
        self.assertEqual(stats['total_items'], 3)
        self.assertIn('by_type', stats)
        self.assertGreater(len(stats['by_type']), 0)
    
    def test_max_content_length(self):
        """测试超长内容限制"""
        from config import Config
        
        # 超长内容应该被拒绝
        too_long = "A" * (Config.MAX_CONTENT_LENGTH + 1)
        item_id = self.db.add_clipboard_item(too_long)
        self.assertIsNone(item_id)
        
        # 正常长度可以添加
        normal = "A" * 1000
        item_id = self.db.add_clipboard_item(normal)
        self.assertIsNotNone(item_id)

if __name__ == '__main__':
    unittest.main()