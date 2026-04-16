"""
Supabase数据库存储模块
功能：使用Supabase数据库存储股票数据、跟踪记录和预测结果
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import time

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("[警告] 未安装supabase库，使用文件存储模式")


class SupabaseStorage:
    """Supabase数据库存储类"""
    
    def __init__(self, 
                 supabase_url: str = None, 
                 supabase_key: str = None):
        """
        初始化Supabase客户端
        
        参数:
            supabase_url: Supabase项目URL
            supabase_key: Supabase服务密钥
        """
        self.supabase_url = supabase_url or os.environ.get('SUPABASE_URL')
        self.supabase_key = supabase_key or os.environ.get('SUPABASE_KEY')
        
        self.client = None
        self.is_connected = False
        
        if self.supabase_url and self.supabase_key:
            self._connect()
        else:
            print("[警告] 未配置Supabase连接信息，使用文件存储模式")
    
    def _connect(self) -> bool:
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
    
    def save_stock_pool(self, stocks: List[Dict], table_name: str = 'stock_pool') -> bool:
        """
        保存股票池
        
        参数:
            stocks: 股票列表
            table_name: 表名
            
        返回:
            保存是否成功
        """
        if not self.is_connected:
            return self._save_to_file(stocks, 'stock_pool.json')
        
        try:
            data = {
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stocks': stocks
            }
            
            result = self.client.table(table_name).upsert(data).execute()
            print(f"[保存] 股票池已保存到Supabase: {len(stocks)} 只股票")
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
        if not self.is_connected:
            return self._save_to_file(results, 'stock_tracking_log.csv', 'csv')
        
        try:
            for result in results:
                result['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                self.client.table(table_name).insert(result).execute()
            
            print(f"[保存] 跟踪日志已保存到Supabase: {len(results)} 条记录")
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
        if not self.is_connected:
            return self._save_to_file(result, f"prediction_{result.get('code', 'unknown')}.json")
        
        try:
            result['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.client.table(table_name).insert(result).execute()
            
            print(f"[保存] 预测结果已保存到Supabase: {result.get('code')}")
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
        if not self.is_connected:
            return self._save_to_file(news_list, 'global_news.json')
        
        try:
            for news in news_list:
                news['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                self.client.table(table_name).insert(news).execute()
            
            print(f"[保存] 国际新闻已保存到Supabase: {len(news_list)} 条")
            return True
            
        except Exception as e:
            print(f"[错误] 保存国际新闻失败: {str(e)}")
            return self._save_to_file(news_list, 'global_news.json')
    
    def get_stock_pool(self, table_name: str = 'stock_pool') -> Optional[List[Dict]]:
        """
        获取股票池
        
        参数:
            table_name: 表名
            
        返回:
            股票列表
        """
        if not self.is_connected:
            return self._load_from_file('stock_pool.json')
        
        try:
            result = self.client.table(table_name).select('*').execute()
            
            if result.data:
                return result.data[0].get('stocks', [])
            
            return None
            
        except Exception as e:
            print(f"[错误] 获取股票池失败: {str(e)}")
            return self._load_from_file('stock_pool.json')
    
    def get_tracking_logs(self, stock_code: str = None, limit: int = 100, 
                         table_name: str = 'tracking_log') -> List[Dict]:
        """
        获取跟踪日志
        
        参数:
            stock_code: 股票代码（可选）
            limit: 返回数量限制
            table_name: 表名
            
        返回:
            跟踪日志列表
        """
        if not self.is_connected:
            return []
        
        try:
            query = self.client.table(table_name).select('*').order('created_at', desc=True).limit(limit)
            
            if stock_code:
                query = query.eq('stock_code', stock_code)
            
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"[错误] 获取跟踪日志失败: {str(e)}")
            return []
    
    def _save_to_file(self, data, filename: str, format_type: str = 'json') -> bool:
        """
        保存数据到文件（降级方案）
        
        参数:
            data: 数据
            filename: 文件名
            format_type: 格式类型
            
        返回:
            保存是否成功
        """
        try:
            os.makedirs('./data', exist_ok=True)
            file_path = f'./data/{filename}'
            
            if format_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format_type == 'csv':
                import csv
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
        """
        从文件加载数据（降级方案）
        
        参数:
            filename: 文件名
            
        返回:
            数据
        """
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
    
    # 尝试从环境变量获取配置
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    storage = SupabaseStorage(supabase_url, supabase_key)
    
    if storage.is_connected:
        print("✓ 已连接到Supabase数据库")
    else:
        print("⚠ 使用文件存储模式（未配置Supabase）")
    
    # 测试保存股票池
    test_stocks = [
        {'code': '601988', 'name': '中国银行', 'date': '2024-04-16'},
        {'code': '601929', 'name': '吉视传媒', 'date': '2024-04-16'}
    ]
    
    storage.save_stock_pool(test_stocks)
    
    # 测试保存跟踪日志
    test_log = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stock_code': '601988',
        'stock_name': '中国银行',
        'latest_price': 3.5,
        'price_change_pct': 1.2,
        'volume': 1000000,
        'tracking_note': '正常跟踪'
    }
    
    storage.save_tracking_log([test_log])


if __name__ == "__main__":
    main()
