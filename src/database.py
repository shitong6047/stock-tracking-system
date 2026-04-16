"""
Supabase数据库存储模块
功能：使用Supabase数据库存储股票数据、跟踪记录和预测结果
"""

import os
import json
import csv
from typing import List, Dict, Optional
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    create_client = None
    print("[警告] 未安装supabase库，使用文件存储模式")

try:
    import psycopg2
    from psycopg2 import sql
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("[警告] 未安装psycopg2库，使用文件存储模式")


class SupabaseStorage:
    """Supabase数据库存储类"""
    
    def __init__(self, 
                 supabase_url: str = None, 
                 supabase_key: str = None,
                 database_url: str = None):
        """
        初始化Supabase客户端
        
        参数:
            supabase_url: Supabase项目URL
            supabase_key: Supabase服务密钥
            database_url: PostgreSQL数据库连接URL
        """
        self.supabase_url = supabase_url or os.environ.get('SUPABASE_URL')
        self.supabase_key = supabase_key or os.environ.get('SUPABASE_KEY')
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        
        self.client = None
        self.connection = None
        self.is_connected = False
        
        if self.supabase_url and self.supabase_key and HAS_SUPABASE and create_client:
            self._connect_supabase()
        elif self.database_url and HAS_PSYCOPG2:
            self._connect_postgres()
        else:
            print("[警告] 未配置Supabase连接信息，使用文件存储模式")
    
    def _connect_supabase(self) -> bool:
        """
        连接Supabase
        
        返回:
            连接是否成功
        """
        if not self.supabase_url or not self.supabase_key:
            return False
        
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.is_connected = True
            print("[成功] 已连接到Supabase数据库")
            return True
        except Exception as e:
            print(f"[错误] 连接Supabase失败: {str(e)}")
            self.is_connected = False
            return False
    
    def _connect_postgres(self) -> bool:
        """
        连接PostgreSQL数据库
        
        返回:
            连接是否成功
        """
        if not self.database_url:
            return False
        
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.connection.autocommit = True
            self.is_connected = True
            print("[成功] 已连接到PostgreSQL数据库")
            
            # 初始化表结构
            self._init_tables()
            
            return True
        except Exception as e:
            print(f"[错误] 连接PostgreSQL失败: {str(e)}")
            self.is_connected = False
            return False
    
    def _init_tables(self):
        """初始化数据库表结构"""
        try:
            cursor = self.connection.cursor()
            
            # 创建股票池表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_pool (
                    id SERIAL PRIMARY KEY,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    stocks JSONB
                )
            """)
            
            # 创建跟踪日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracking_log (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    stock_code VARCHAR(20),
                    stock_name VARCHAR(50),
                    latest_price DECIMAL(10,2),
                    price_change_pct DECIMAL(6,2),
                    volume BIGINT,
                    tracking_note VARCHAR(200),
                    alert_signal VARCHAR(200)
                )
            """)
            
            # 创建预测结果表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    code VARCHAR(20),
                    name VARCHAR(50),
                    direction VARCHAR(10),
                    probability DECIMAL(5,4),
                    confidence VARCHAR(20),
                    total_score INTEGER,
                    key_signals JSONB,
                    risk_warning TEXT
                )
            """)
            
            # 创建国际新闻表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS global_news (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    title VARCHAR(500),
                    summary TEXT,
                    pub_time VARCHAR(50),
                    source VARCHAR(100),
                    url VARCHAR(500),
                    impact VARCHAR(20),
                    impact_score DECIMAL(5,3)
                )
            """)
            
            cursor.close()
            print("[成功] 数据库表结构初始化完成")
            
        except Exception as e:
            print(f"[错误] 初始化表结构失败: {str(e)}")
    
    def save_stock_pool(self, stocks: List[Dict], table_name: str = 'stock_pool') -> bool:
        """
        保存股票池
        
        参数:
            stocks: 股票列表
            table_name: 表名
            
        返回:
            保存是否成功
        """
        if self.connection:
            return self._save_stock_pool_postgres(stocks)
        elif self.is_connected:
            return self._save_stock_pool_supabase(stocks)
        else:
            return self._save_to_file(stocks, 'stock_pool.json')
    
    def _save_stock_pool_supabase(self, stocks: List[Dict]) -> bool:
        """使用Supabase保存股票池"""
        try:
            data = {
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stocks': stocks
            }
            
            result = self.client.table('stock_pool').upsert(data).execute()
            print(f"[保存] 股票池已保存到Supabase: {len(stocks)} 只股票")
            return True
            
        except Exception as e:
            print(f"[错误] 保存股票池失败: {str(e)}")
            return self._save_to_file(stocks, 'stock_pool.json')
    
    def _save_stock_pool_postgres(self, stocks: List[Dict]) -> bool:
        """使用PostgreSQL保存股票池"""
        try:
            cursor = self.connection.cursor()
            
            data_json = json.dumps(stocks, ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO stock_pool (create_time, update_time, stocks)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  data_json))
            
            self.connection.commit()
            cursor.close()
            
            print(f"[保存] 股票池已保存到数据库: {len(stocks)} 只股票")
            return True
            
        except Exception as e:
            print(f"[错误] 保存股票池失败: {str(e)}")
            return self._save_to_file(stocks, 'stock_pool.json')
    
    def save_tracking_log(self, results: List[Dict], table_name: str = 'tracking_log') -> bool:
        """
        保存跟踪日志
        
        参数:
            results: 跟踪结果列表
            table_name: 表名
            
        返回:
            保存是否成功
        """
        if self.connection:
            return self._save_tracking_log_postgres(results)
        elif self.is_connected:
            return self._save_tracking_log_supabase(results)
        else:
            return self._save_to_file(results, 'stock_tracking_log.csv', 'csv')
    
    def _save_tracking_log_supabase(self, results: List[Dict]) -> bool:
        """使用Supabase保存跟踪日志"""
        try:
            for result in results:
                data = {
                    'created_at': result.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'stock_code': result.get('stock_code', ''),
                    'stock_name': result.get('stock_name', ''),
                    'latest_price': result.get('latest_price'),
                    'price_change_pct': result.get('price_change_pct'),
                    'volume': result.get('volume'),
                    'tracking_note': result.get('tracking_note', ''),
                    'alert_signal': result.get('alert_signal', '')
                }
                
                self.client.table('tracking_log').insert(data).execute()
            
            print(f"[保存] 跟踪日志已保存到Supabase: {len(results)} 条记录")
            return True
            
        except Exception as e:
            print(f"[错误] 保存跟踪日志失败: {str(e)}")
            return self._save_to_file(results, 'stock_tracking_log.csv', 'csv')
    
    def _save_tracking_log_postgres(self, results: List[Dict]) -> bool:
        """使用PostgreSQL保存跟踪日志"""
        try:
            cursor = self.connection.cursor()
            
            for result in results:
                cursor.execute("""
                    INSERT INTO tracking_log 
                    (created_at, stock_code, stock_name, latest_price, 
                     price_change_pct, volume, tracking_note, alert_signal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    result.get('stock_code', ''),
                    result.get('stock_name', ''),
                    result.get('latest_price'),
                    result.get('price_change_pct'),
                    result.get('volume'),
                    result.get('tracking_note', ''),
                    result.get('alert_signal', '')
                ))
            
            self.connection.commit()
            cursor.close()
            
            print(f"[保存] 跟踪日志已保存到数据库: {len(results)} 条记录")
            return True
            
        except Exception as e:
            print(f"[错误] 保存跟踪日志失败: {str(e)}")
            return self._save_to_file(results, 'stock_tracking_log.csv', 'csv')
    
    def save_prediction(self, result: Dict, table_name: str = 'predictions') -> bool:
        """
        保存预测结果
        
        参数:
            result: 预测结果
            table_name: 表名
            
        返回:
            保存是否成功
        """
        if self.connection:
            return self._save_prediction_postgres(result)
        elif self.is_connected:
            return self._save_prediction_supabase(result)
        else:
            return self._save_to_file(result, f"prediction_{result.get('code', 'unknown')}.json")
    
    def _save_prediction_supabase(self, result: Dict) -> bool:
        """使用Supabase保存预测结果"""
        try:
            result['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.client.table('predictions').insert(result).execute()
            
            print(f"[保存] 预测结果已保存到Supabase: {result.get('code')}")
            return True
            
        except Exception as e:
            print(f"[错误] 保存预测结果失败: {str(e)}")
            return self._save_to_file(result, f"prediction_{result.get('code', 'unknown')}.json")
    
    def _save_prediction_postgres(self, result: Dict) -> bool:
        """使用PostgreSQL保存预测结果"""
        try:
            cursor = self.connection.cursor()
            
            key_signals_json = json.dumps(result.get('key_signals', []), ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO predictions 
                (created_at, code, name, direction, probability, 
                 confidence, total_score, key_signals, risk_warning)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                result.get('code', ''),
                result.get('name', ''),
                result.get('direction', ''),
                result.get('probability'),
                result.get('confidence', ''),
                result.get('total_score'),
                key_signals_json,
                result.get('risk_warning', '')
            ))
            
            self.connection.commit()
            cursor.close()
            
            print(f"[保存] 预测结果已保存到数据库: {result.get('code')}")
            return True
            
        except Exception as e:
            print(f"[错误] 保存预测结果失败: {str(e)}")
            return self._save_to_file(result, f"prediction_{result.get('code', 'unknown')}.json")
    
    def save_global_news(self, news_list: List[Dict], table_name: str = 'global_news') -> bool:
        """
        保存国际新闻数据
        
        参数:
            news_list: 新闻列表
            table_name: 表名
            
        返回:
            保存是否成功
        """
        if self.connection:
            return self._save_global_news_postgres(news_list)
        elif self.is_connected:
            return self._save_global_news_supabase(news_list)
        else:
            return self._save_to_file(news_list, 'global_news.json')
    
    def _save_global_news_supabase(self, news_list: List[Dict]) -> bool:
        """使用Supabase保存国际新闻"""
        try:
            for news in news_list:
                news['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                self.client.table('global_news').insert(news).execute()
            
            print(f"[保存] 国际新闻已保存到Supabase: {len(news_list)} 条")
            return True
            
        except Exception as e:
            print(f"[错误] 保存国际新闻失败: {str(e)}")
            return self._save_to_file(news_list, 'global_news.json')
    
    def _save_global_news_postgres(self, news_list: List[Dict]) -> bool:
        """使用PostgreSQL保存国际新闻"""
        try:
            cursor = self.connection.cursor()
            
            for news in news_list:
                cursor.execute("""
                    INSERT INTO global_news 
                    (created_at, title, summary, pub_time, source, 
                     url, impact, impact_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    news.get('title', ''),
                    news.get('summary', ''),
                    news.get('pub_time', ''),
                    news.get('source', ''),
                    news.get('url', ''),
                    news.get('impact', ''),
                    news.get('impact_score')
                ))
            
            self.connection.commit()
            cursor.close()
            
            print(f"[保存] 国际新闻已保存到数据库: {len(news_list)} 条")
            return True
            
        except Exception as e:
            print(f"[错误] 保存国际新闻失败: {str(e)}")
            return self._save_to_file(news_list, 'global_news.json')
    
    def get_stock_pool(self, table_name: str = 'stock_pool') -> Optional[List[Dict]]:
        """获取股票池"""
        if self.connection:
            return self._get_stock_pool_postgres()
        elif self.is_connected:
            return self._get_stock_pool_supabase()
        else:
            return self._load_from_file('stock_pool.json')
    
    def _get_stock_pool_supabase(self) -> Optional[List[Dict]]:
        """使用Supabase获取股票池"""
        try:
            result = self.client.table('stock_pool').select('*').execute()
            
            if result.data:
                return result.data[0].get('stocks', [])
            
            return None
            
        except Exception as e:
            print(f"[错误] 获取股票池失败: {str(e)}")
            return self._load_from_file('stock_pool.json')
    
    def _get_stock_pool_postgres(self) -> Optional[List[Dict]]:
        """使用PostgreSQL获取股票池"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT stocks FROM stock_pool 
                ORDER BY create_time DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                return result[0]
            
            return None
            
        except Exception as e:
            print(f"[错误] 获取股票池失败: {str(e)}")
            return self._load_from_file('stock_pool.json')
    
    def get_tracking_logs(self, stock_code: str = None, limit: int = 100, 
                         table_name: str = 'tracking_log') -> List[Dict]:
        """获取跟踪日志"""
        if self.connection:
            return self._get_tracking_logs_postgres(stock_code, limit)
        elif self.is_connected:
            return self._get_tracking_logs_supabase(stock_code, limit)
        else:
            return []
    
    def _get_tracking_logs_supabase(self, stock_code: str = None, limit: int = 100) -> List[Dict]:
        """使用Supabase获取跟踪日志"""
        try:
            query = self.client.table('tracking_log').select('*').order('created_at', desc=True).limit(limit)
            
            if stock_code:
                query = query.eq('stock_code', stock_code)
            
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"[错误] 获取跟踪日志失败: {str(e)}")
            return []
    
    def _get_tracking_logs_postgres(self, stock_code: str = None, limit: int = 100) -> List[Dict]:
        """使用PostgreSQL获取跟踪日志"""
        try:
            cursor = self.connection.cursor()
            
            if stock_code:
                cursor.execute("""
                    SELECT * FROM tracking_log 
                    WHERE stock_code = %s
                    ORDER BY created_at DESC LIMIT %s
                """, (stock_code, limit))
            else:
                cursor.execute("""
                    SELECT * FROM tracking_log 
                    ORDER BY created_at DESC LIMIT %s
                """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            cursor.close()
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            print(f"[错误] 获取跟踪日志失败: {str(e)}")
            return []
    
    def _save_to_file(self, data, filename: str, format_type: str = 'json') -> bool:
        """保存数据到文件（降级方案）"""
        try:
            os.makedirs('./data', exist_ok=True)
            file_path = f'./data/{filename}'
            
            if format_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format_type == 'csv':
                if isinstance(data, list) and len(data) > 0:
                    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            
            print(f"[降级] 数据已保存到文件: {file_path}")
            return True
            
        except Exception as e:
            print(f"[错误] 保存文件失败: {str(e)}")
            return False
    
    def _load_from_file(self, filename: str) -> Optional[Dict]:
        """从文件加载数据（降级方案）"""
        try:
            file_path = f'./data/{filename}'
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"[错误] 加载文件失败: {str(e)}")
            return None


def main():
    """主函数"""
    print("Supabase数据库存储模块测试")
    print("=" * 60)
    
    storage = SupabaseStorage()
    
    if storage.is_connected:
        print("✓ 已连接到数据库")
    else:
        print("⚠ 使用文件存储模式（未配置数据库）")
    
    test_stocks = [
        {'code': '601988', 'name': '中国银行', 'date': '2024-04-16'},
        {'code': '601929', 'name': '吉视传媒', 'date': '2024-04-16'}
    ]
    
    storage.save_stock_pool(test_stocks)


if __name__ == "__main__":
    main()
