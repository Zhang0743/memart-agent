import sqlite3
import pandas as pd
from typing import Dict, Any, List
from config import Config


class SQLAgent:
    """SQL查询Agent"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                prompt TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                user_id TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                question TEXT,
                answer TEXT,
                strategy TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def execute_query(self, query: str) -> str:
        """执行SQL查询"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                if results:
                    columns = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(results, columns=columns)
                    return df.to_string()
                return "查询无结果"
            else:
                conn.commit()
                return f"执行成功，影响行数: {cursor.rowcount}"
        except Exception as e:
            return f"SQL错误: {str(e)}"
        finally:
            conn.close()

    def save_image_record(self, filename: str, prompt: str, user_id: str = "default"):
        """保存图片记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO images (filename, prompt, user_id) VALUES (?, ?, ?)",
            (filename, prompt, user_id)
        )
        conn.commit()
        conn.close()
        return f"已保存图片记录: {filename}"

    def get_recent_images(self, user_id: str = "default", limit: int = 10) -> str:
        """获取最近的图片"""
        conn = sqlite3.connect(self.db_path)
        query = f"""
            SELECT prompt, created_at, filename 
            FROM images 
            WHERE user_id = '{user_id}'
            ORDER BY created_at DESC 
            LIMIT {limit}
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return "暂无图片记录"
        return df.to_string()