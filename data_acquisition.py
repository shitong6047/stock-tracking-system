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
                return result
            except Exception as e:
                print(f"[警告] 第{attempt + 1}次请求失败: {str(e)}")
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"[错误] 请求失败，已达到最大重试次数: {self.retry_times}")
                    return None
    
    def get_all_stocks_realtime(self, use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        获取全部A股实时行情数据
        
        参数:
            use_cache: 是否使用缓存
            
        返回:
            DataFrame包含股票代码、名称、价格、涨跌幅等
        """
        cache_file = os.path.join(self.cache_dir, 'quotes', 'all_stocks_realtime.json')
        
        if use_cache and os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time < timedelta(hours=self.cache_expire_hours):
                try:
                    df = pd.read_json(cache_file, orient='records')
                    print(f"[缓存] 读取缓存数据，共 {len(df)} 只股票")
                    return df
                except:
                    pass
        
        print("[信息] 正在获取全部A股实时行情...")
        df = self._retry_request(ak.stock_zh_a_spot_em)
        
        if df is not None and not df.empty:
            df.to_json(cache_file, orient='records', force_ascii=False)
            print(f"[成功] 获取到 {len(df)} 只股票数据")
            return df
        return None
    
    def get_stock_realtime(self, code: str, use_cache: bool = True) -> Optional[Dict]:
        """
        获取个股实时行情
        
        参数:
            code: 股票代码
            use_cache: 是否使用缓存
            
        返回:
            字典形式的实时行情数据
        """
        df = self.get_all_stocks_realtime(use_cache=use_cache)
        if df is None:
            return None
        
        code = str(code).zfill(6)
        stock_data = df[df['代码'] == code]
        
        if stock_data.empty:
            print(f"[警告] 未找到股票 {code}")
            return None
        
        row = stock_data.iloc[0]
        return {
            'code': row['代码'],
            'name': row['名称'],
            'latest_price': float(row['最新价']) if pd.notna(row['最新价']) else 0,
            'change_pct': float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else 0,
            'change_amount': float(row['涨跌额']) if pd.notna(row['涨跌额']) else 0,
            'volume': int(row['成交量']) if pd.notna(row['成交量']) else 0,
            'amount': float(row['成交额']) if pd.notna(row['成交额']) else 0,
            'amplitude': float(row['振幅']) if pd.notna(row['振幅']) else 0,
            'high': float(row['最高']) if pd.notna(row['最高']) else 0,
            'low': float(row['最低']) if pd.notna(row['最低']) else 0,
            'open': float(row['今开']) if pd.notna(row['今开']) else 0,
            'prev_close': float(row['昨收']) if pd.notna(row['昨收']) else 0,
            'volume_ratio': float(row['量比']) if pd.notna(row['量比']) else 0,
            'turnover_rate': float(row['换手率']) if pd.notna(row['换手率']) else 0,
            'pe_ratio': float(row['市盈率-动态']) if pd.notna(row['市盈率-动态']) else 0,
            'pb_ratio': float(row['市净率']) if pd.notna(row['市净率']) else 0,
            'total_market_value': float(row['总市值']) if pd.notna(row['总市值']) else 0,
            'circulating_market_value': float(row['流通市值']) if pd.notna(row['流通市值']) else 0
        }
    
    def get_stock_history(self, code: str, days: int = 120,
                          adjust: str = "qfq") -> Optional[pd.DataFrame]:
        """
        获取个股历史K线数据
        
        参数:
            code: 股票代码
            days: 获取天数
            adjust: 复权类型(qfq前复权/hfq后复权/不复权)
            
        返回:
            DataFrame包含日期、开盘、收盘、最高、最低、成交量等
        """
        code = str(code).zfill(6)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        
        print(f"[信息] 正在获取股票 {code} 历史数据...")
        df = self._retry_request(
            ak.stock_zh_a_hist,
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        if df is not None and not df.empty:
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '换手率': 'turnover_rate'
            })
            print(f"[成功] 获取到 {len(df)} 条历史记录")
            return df.tail(days)
        return None
    
    def get_stock_financial_indicator(self, code: str) -> Optional[Dict]:
        """
        获取个股财务指标数据
        
        参数:
            code: 股票代码
            
        返回:
            字典形式的财务指标
        """
        code = str(code).zfill(6)
        print(f"[信息] 正在获取股票 {code} 财务指标...")
        
        df = self._retry_request(
            ak.stock_financial_analysis_indicator,
            symbol=code
        )
        
        if df is not None and not df.empty:
            latest = df.iloc[0]
            return {
                'code': code,
                'report_date': latest.get('日期', ''),
                'pe_ratio': float(latest.get('市盈率', 0)) if pd.notna(latest.get('市盈率')) else 0,
                'pb_ratio': float(latest.get('市净率', 0)) if pd.notna(latest.get('市净率')) else 0,
                'roe': float(latest.get('净资产收益率', 0)) if pd.notna(latest.get('净资产收益率')) else 0,
                'roa': float(latest.get('总资产净利率', 0)) if pd.notna(latest.get('总资产净利率')) else 0,
                'gross_margin': float(latest.get('销售毛利率', 0)) if pd.notna(latest.get('销售毛利率')) else 0,
                'net_margin': float(latest.get('销售净利率', 0)) if pd.notna(latest.get('销售净利率')) else 0,
                'debt_ratio': float(latest.get('资产负债率', 0)) if pd.notna(latest.get('资产负债率')) else 0,
                'current_ratio': float(latest.get('流动比率', 0)) if pd.notna(latest.get('流动比率')) else 0,
                'quick_ratio': float(latest.get('速动比率', 0)) if pd.notna(latest.get('速动比率')) else 0
            }
        return None
    
    def get_global_market_data(self) -> Dict:
        """
        获取国际市场数据
        
        返回:
            字典形式的国际市场数据
        """
        result = {
            'us_dow_jones': None,
            'us_nasdaq': None,
            'us_sp500': None,
            'gold': None,
            'oil': None,
            'vix': None,
            'usd_index': None
        }
        
        print("[信息] 正在获取国际市场数据...")
        
        try:
            us_index = self._retry_request(ak.index_us_stock_sina)
            if us_index is not None and not us_index.empty:
                for _, row in us_index.iterrows():
                    name = str(row.get('名称', ''))
                    if '道琼斯' in name:
                        result['us_dow_jones'] = float(row.get('最新价', 0))
                    elif '纳斯达克' in name:
                        result['us_nasdaq'] = float(row.get('最新价', 0))
                    elif '标普' in name:
                        result['us_sp500'] = float(row.get('最新价', 0))
        except Exception as e:
            print(f"[警告] 获取美股指数失败: {str(e)}")
        
        try:
            gold_df = self._retry_request(ak.fx_spot_quote, symbol="XAUUSD")
            if gold_df is not None and not gold_df.empty:
                result['gold'] = float(gold_df.iloc[0].get('最新价', 0))
        except:
            pass
        
        try:
            oil_df = self._retry_request(ak.energy_oil_hist, symbol="WTI")
            if oil_df is not None and not oil_df.empty:
                result['oil'] = float(oil_df.iloc[-1].get('收盘', 0))
        except:
            pass
        
        return result
    
    def get_batch_realtime(self, codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取股票实时行情
        
        参数:
            codes: 股票代码列表
            
        返回:
            字典形式的批量行情数据
        """
        df = self.get_all_stocks_realtime()
        if df is None:
            return {}
        
        result = {}
        for code in codes:
            code = str(code).zfill(6)
            stock_data = df[df['代码'] == code]
            
            if not stock_data.empty:
                row = stock_data.iloc[0]
                result[code] = {
                    'code': row['代码'],
                    'name': row['名称'],
                    'latest_price': float(row['最新价']) if pd.notna(row['最新价']) else 0,
                    'change_pct': float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else 0,
                    'volume': int(row['成交量']) if pd.notna(row['成交量']) else 0,
                    'amount': float(row['成交额']) if pd.notna(row['成交额']) else 0,
                    'turnover_rate': float(row['换手率']) if pd.notna(row['换手率']) else 0,
                    'pe_ratio': float(row['市盈率-动态']) if pd.notna(row['市盈率-动态']) else 0,
                    'pb_ratio': float(row['市净率']) if pd.notna(row['市净率']) else 0
                }
        
        return result


if __name__ == "__main__":
    data_acq = DataAcquisition()
    
    print("=" * 50)
    print("测试数据获取模块")
    print("=" * 50)
    
    print("\n测试获取单只股票实时数据:")
    stock = data_acq.get_stock_realtime("000001")
    if stock:
        for key, value in stock.items():
            print(f"  {key}: {value}")
    
    print("\n测试获取历史K线:")
    hist = data_acq.get_stock_history("000001", days=30)
    if hist is not None:
        print(hist.tail())
    
    print("\n测试获取财务指标:")
    financial = data_acq.get_stock_financial_indicator("000001")
    if financial:
        for key, value in financial.items():
            print(f"  {key}: {value}")
    
    print("\n测试获取国际市场数据:")
    global_data = data_acq.get_global_market_data()
    for key, value in global_data.items():
        print(f"  {key}: {value}")
