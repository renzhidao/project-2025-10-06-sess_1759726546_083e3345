"""
config.py 单元测试
测试所有配置项和工具方法
"""
import unittest
import os
from pathlib import Path
from config import Config, ContentType

class TestConfig(unittest.TestCase):
    """测试Config类"""
    
    def test_app_constants(self):
        """测试应用基本常量"""
        self.assertEqual(Config.APP_NAME, "ClipboardManager")
        self.assertIsInstance(Config.APP_VERSION, str)
        self.assertTrue(len(Config.APP_VERSION) > 0)
    
    def test_db_path_non_android(self):
        """测试非Android环境下的数据库路径"""
        # 确保不在Android环境
        if 'ANDROID_STORAGE' in os.environ:
            del os.environ['ANDROID_STORAGE']
        
        db_path = Config.get_db_path()
        self.assertIn("clipboard_history.db", db_path)
        self.assertTrue(Path(db_path).parent.exists())
    
    def test_db_path_android(self):
        """测试Android环境下的数据库路径"""
        os.environ['ANDROID_STORAGE'] = '/data/data/test.app'
        db_path = Config.get_db_path()
        
        self.assertIn('/data/data/test.app', db_path)
        self.assertIn('clipboard_history.db', db_path)
        
        # 清理
        del os.environ['ANDROID_STORAGE']
    
    def test_config_values(self):
        """测试配置值合理性"""
        self.assertGreater(Config.MAX_PREVIEW_LENGTH, 0)
        self.assertGreater(Config.BATCH_SIZE, 0)
        self.assertGreater(Config.MAX_CONTENT_LENGTH, 1000)
        self.assertIsInstance(Config.DUPLICATE_CHECK_ENABLED, bool)

class TestContentType(unittest.TestCase):
    """测试ContentType类"""
    
    def test_detect_url(self):
        """测试URL检测"""
        self.assertEqual(ContentType.detect("https://example.com"), ContentType.URL)
        self.assertEqual(ContentType.detect("http://test.org"), ContentType.URL)
        self.assertEqual(ContentType.detect("ftp://files.com"), ContentType.URL)
    
    def test_detect_code(self):
        """测试代码检测"""
        self.assertEqual(ContentType.detect("def hello():"), ContentType.CODE)
        self.assertEqual(ContentType.detect("class MyClass:"), ContentType.CODE)
        self.assertEqual(ContentType.detect("import os"), ContentType.CODE)
        self.assertEqual(ContentType.detect("function test() {}"), ContentType.CODE)
    
    def test_detect_text(self):
        """测试普通文本"""
        self.assertEqual(ContentType.detect("Hello World"), ContentType.TEXT)
        self.assertEqual(ContentType.detect("这是中文测试"), ContentType.TEXT)
    
    def test_detect_empty(self):
        """测试空内容"""
        self.assertEqual(ContentType.detect(""), ContentType.UNKNOWN)
        self.assertEqual(ContentType.detect(None), ContentType.UNKNOWN)

if __name__ == '__main__':
    unittest.main()