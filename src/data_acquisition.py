"""
数据获取模块
功能：从AkShare获取股票行情数据、财务数据、国际市场数据
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
import os
import json
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class DataAcquisition:
    """股票数据获取类"""
    
    def __init__(self, cache_dir: str = './data/cache', 
                 retry_times: int = 3, retry_delay: float = 1.0):
        """
        初始化数据获取器
        
        参数:
            cache_dir: 缓存目录
            retry_times: 重试次数
            retry_delay: 重试间隔(秒)
        """
        self.cache_dir = cache_dir
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.cache_expire_hours = 24
        
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'quotes'), exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'financial'), exist_ok=True)
    
    def _retry_request(self, func, *args, **kwargs) -> Optional[pd.DataFrame]:
        """
        带重试机制的请求方法
        
        参数:
            func: 请求函数
            args: 位置参数
            kwargs: 关键字参数
            
        返回:
            DataFrame或None
        """
        for attempt in range(self.retry_times):
            try:
                result = func(*args, **kwargs)
                if result is not None and not result.empty:
                    return result
            except Exception as e:
                if attempt == self.retry_times - 1:
                    print(f"[错误] 请求失败: {str(e)}")
                    return None
                time.sleep(self.retry_delay)
        
        return None
    
    def get_batch_realtime(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取实时行情数据
        
        参数:
            stock_codes: 股票代码列表
            
        返回:
            股票数据字典 {code: data}
        """
        print(f"[获取] 正在获取 {len(stock_codes)} 只股票的实时行情...")
        
        try:
            # 使用AkShare获取实时行情
            df = ak.stock_zh_a_spot()
            
            # 转换为字典格式
            result = {}
            for _, row in df.iterrows():
                code = row['代码']
                if code in stock_codes:
                    result[code] = {
                        'name': row['名称'],
                        'latest_price': float(row['现价']),
                        'change_pct': float(row['涨跌幅'].replace('%', '')),
                        'open': float(row['开盘']),
                        'high': float(row['最高']),
                        'low': float(row['最低']),
                        'volume': int(row['成交量']),
                        'amount': float(row['成交额']),
                        'turnover_rate': float(row['换手率'].replace('%', ''))
                    }
            
            print(f"[成功] 获取到 {len(result)} 只股票数据")
            return result
            
        except Exception as e:
            print(f"[错误] 获取实时行情失败: {str(e)}")
            # 返回空数据
            return {}
    
    def get_stock_history(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """
        获取股票历史数据
        
        参数:
            stock_code: 股票代码
            days: 天数
            
        返回:
            历史数据DataFrame
        """
        cache_file = os.path.join(self.cache_dir, 'quotes', f"{stock_code}_{days}days.csv")
        
        # 检查缓存
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if (datetime.now() - file_time).total_seconds() < self.cache_expire_hours * 3600:
                try:
                    return pd.read_csv(cache_file)
                except:
                    pass
        
        try:
            # 获取历史数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                   start_date=start_date, end_date=end_date)
            
            # 保存缓存
            df.to_csv(cache_file, index=False)
            
            return df
            
        except Exception as e:
            print(f"[错误] 获取历史数据失败 {stock_code}: {str(e)}")
            return pd.DataFrame()
    
    def get_financial_data(self, stock_code: str) -> Dict:
        """
        获取财务数据
        
        参数:
            stock_code: 股票代码
            
        返回:
            财务数据字典
        """
        try:
            # 获取财务指标
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            
            if not df.empty:
                return {
                    'pe_ratio': float(df.iloc[0]['市盈率TTM']),
                    'pb_ratio': float(df.iloc[0]['市净率TTM']),
                    'roe': float(df.iloc[0]['净资产收益率TTM']),
                    'eps': float(df.iloc[0]['每股收益TTM']),
                    'revenue_growth': float(df.iloc[0]['营业收入同比增长']),
                    'profit_growth': float(df.iloc[0]['净利润同比增长'])
                }
            
            return {}
            
        except Exception as e:
            print(f"[错误] 获取财务数据失败 {stock_code}: {str(e)}")
            return {}
    
    def get_industry_data(self, industry: str) -> List[Dict]:
        """
        获取行业数据
        
        参数:
            industry: 行业名称
            
        返回:
            行业股票列表
        """
        try:
            # 获取行业板块数据
            df = ak.stock_board_industry_name_em()
            
            # 筛选指定行业
            industry_df = df[df['板块名称'] == industry]
            
            if not industry_df.empty:
                stocks = []
                for _, row in industry_df.iterrows():
                    stocks.append({
                        'code': row['板块代码'],
                        'name': row['板块名称'],
                        'change_pct': float(row['涨跌幅'].replace('%', '')),
                        'turnover_rate': float(row['换手率'].replace('%', ''))
                    })
                return stocks
            
            return []
            
        except Exception as e:
            print(f"[错误] 获取行业数据失败 {industry}: {str(e)}")
            return []
    
    def clear_cache(self):
        """清除缓存"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            print("[清理] 缓存已清除")
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        cache_info = {
            'cache_dir': self.cache_dir,
            'cache_size': 0,
            'cache_files': 0,
            'expire_hours': self.cache_expire_hours
        }
        
        if os.path.exists(self.cache_dir):
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    cache_info['cache_size'] += os.path.getsize(file_path)
                    cache_info['cache_files'] += 1
        
        return cache_info