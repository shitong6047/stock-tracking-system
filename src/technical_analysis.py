"""
技术分析模块
功能：计算技术指标、识别趋势、检测买卖信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TechnicalSignal:
    """技术信号数据类"""
    signal_type: str
    signal_strength: str
    description: str
    value: float = 0.0


class TechnicalAnalysis:
    """技术分析类"""
    
    def __init__(self):
        self.ma_periods = [5, 10, 20, 60]
        self.rsi_periods = [6, 12, 24]
        self.kdj_params = {'n': 9, 'm1': 3, 'm2': 3}
        self.macd_params = {'fast': 12, 'slow': 26, 'signal': 9}
        self.boll_params = {'n': 20, 'std': 2}
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        参数:
            df: 包含OHLCV数据的DataFrame
            
        返回:
            添加了技术指标的DataFrame
        """
        df = df.copy()
        
        df = self.calculate_ma(df)
        df = self.calculate_macd(df)
        df = self.calculate_kdj(df)
        df = self.calculate_rsi(df)
        df = self.calculate_boll(df)
        
        return df
    
    def calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算移动平均线
        
        参数:
            df: 包含价格数据的DataFrame
            
        返回:
            添加了MA指标的DataFrame
        """
        df = df.copy()
        
        for period in self.ma_periods:
            df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
        
        return df
    
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算MACD指标
        
        参数:
            df: 包含价格数据的DataFrame
            
        返回:
            添加了MACD指标的DataFrame
        """
        df = df.copy()
        
        ema_fast = df['收盘'].ewm(span=self.macd_params['fast']).mean()
        ema_slow = df['收盘'].ewm(span=self.macd_params['slow']).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=self.macd_params['signal']).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        return df
    
    def calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算KDJ指标
        
        参数:
            df: 包含价格数据的DataFrame
            
        返回:
            添加了KDJ指标的DataFrame
        """
        df = df.copy()
        
        low_list = df['最低'].rolling(window=self.kdj_params['n']).min()
        high_list = df['最高'].rolling(window=self.kdj_params['n']).max()
        rsv = (df['收盘'] - low_list) / (high_list - low_list) * 100
        
        df['K'] = rsv.ewm(com=self.kdj_params['m1'] - 1).mean()
        df['D'] = df['K'].ewm(com=self.kdj_params['m2'] - 1).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算RSI指标
        
        参数:
            df: 包含价格数据的DataFrame
            
        返回:
            添加了RSI指标的DataFrame
        """
        df = df.copy()
        
        for period in self.rsi_periods:
            delta = df['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'RSI{period}'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_boll(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算布林带指标
        
        参数:
            df: 包含价格数据的DataFrame
            
        返回:
            添加了布林带指标的DataFrame
        """
        df = df.copy()
        
        df['BB_middle'] = df['收盘'].rolling(window=self.boll_params['n']).mean()
        df['BB_std'] = df['收盘'].rolling(window=self.boll_params['n']).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * self.boll_params['std'])
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * self.boll_params['std'])
        
        return df
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """
        分析趋势
        
        参数:
            df: 包含技术指标的DataFrame
            
        返回:
            趋势分析结果
        """
        if len(df) < 20:
            return {'trend': '数据不足', 'strength': 0}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 分析短期趋势
        ma5_trend = 'up' if latest['MA5'] > prev['MA5'] else 'down'
        ma10_trend = 'up' if latest['MA10'] > prev['MA10'] else 'down'
        ma20_trend = 'up' if latest['MA20'] > prev['MA20'] else 'down'
        
        # 分析MACD
        macd_trend = 'up' if latest['MACD'] > prev['MACD'] else 'down'
        macd_signal = 'golden' if latest['MACD'] > latest['MACD_signal'] else 'dead'
        
        # 分析RSI
        rsi_overbought = latest['RSI6'] > 70
        rsi_oversold = latest['RSI6'] < 30
        
        # 综合趋势判断
        up_count = sum([1 for t in [ma5_trend, ma10_trend, ma20_trend] if t == 'up'])
        trend_strength = up_count / 3
        
        if trend_strength >= 0.7:
            trend = 'strong_up'
        elif trend_strength >= 0.4:
            trend = 'up'
        elif trend_strength <= 0.3:
            trend = 'down'
        else:
            trend = 'neutral'
        
        return {
            'trend': trend,
            'strength': trend_strength,
            'ma5_trend': ma5_trend,
            'ma10_trend': ma10_trend,
            'ma20_trend': ma20_trend,
            'macd_trend': macd_trend,
            'macd_signal': macd_signal,
            'rsi_overbought': rsi_overbought,
            'rsi_oversold': rsi_oversold
        }
    
    def generate_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """
        生成交易信号
        
        参数:
            df: 包含技术指标的DataFrame
            
        返回:
            信号列表
        """
        signals = []
        
        if len(df) < 20:
            return signals
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 金叉死叉信号
        if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
            signals.append(TechnicalSignal(
                signal_type='MACD_Golden_Cross',
                signal_strength='strong',
                description='MACD金叉，买入信号'
            ))
        elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
            signals.append(TechnicalSignal(
                signal_type='MACD_Dead_Cross',
                signal_strength='strong',
                description='MACD死叉，卖出信号'
            ))
        
        # KDJ信号
        if latest['K'] > latest['D'] and prev['K'] <= prev['D']:
            signals.append(TechnicalSignal(
                signal_type='KDJ_Golden_Cross',
                signal_strength='medium',
                description='KDJ金叉，买入信号'
            ))
        elif latest['K'] < latest['D'] and prev['K'] >= prev['D']:
            signals.append(TechnicalSignal(
                signal_type='KDJ_Dead_Cross',
                signal_strength='medium',
                description='KDJ死叉，卖出信号'
            ))
        
        # RSI信号
        if latest['RSI6'] > 70:
            signals.append(TechnicalSignal(
                signal_type='RSI_Overbought',
                signal_strength='weak',
                description='RSI超买，注意回调'
            ))
        elif latest['RSI6'] < 30:
            signals.append(TechnicalSignal(
                signal_type='RSI_Oversold',
                signal_strength='weak',
                description='RSI超卖，可能反弹'
            ))
        
        # 布林带信号
        if latest['收盘'] > latest['BB_upper']:
            signals.append(TechnicalSignal(
                signal_type='BB_Break_Upper',
                signal_strength='medium',
                description='价格突破上轨，强势'
            ))
        elif latest['收盘'] < latest['BB_lower']:
            signals.append(TechnicalSignal(
                signal_type='BB_Break_Lower',
                signal_strength='medium',
                description='价格突破下轨，弱势'
            ))
        
        return signals
    
    def get_support_resistance(self, df: pd.DataFrame, period: int = 20) -> Dict:
        """
        获取支撑位和阻力位
        
        参数:
            df: 包含价格数据的DataFrame
            period: 计算周期
            
        返回:
            支撑阻力位信息
        """
        if len(df) < period:
            return {'support': 0, 'resistance': 0}
        
        recent_high = df['最高'].rolling(window=period).max()
        recent_low = df['最低'].rolling(window=period).min()
        
        latest = df.iloc[-1]
        
        return {
            'support': recent_low.iloc[-1],
            'resistance': recent_high.iloc[-1],
            'current_price': latest['收盘'],
            'distance_to_support': (latest['收盘'] - recent_low.iloc[-1]) / latest['收盘'] * 100,
            'distance_to_resistance': (recent_high.iloc[-1] - latest['收盘']) / latest['收盘'] * 100
        }
    
    def analyze_volume(self, df: pd.DataFrame) -> Dict:
        """
        分析成交量
        
        参数:
            df: 包含成交量数据的DataFrame
            
        返回:
            成交量分析结果
        """
        if len(df) < 20:
            return {'volume_trend': '数据不足', 'volume_ratio': 1.0}
        
        latest = df.iloc[-1]
        avg_volume = df['成交量'].rolling(window=20).mean().iloc[-1]
        
        volume_ratio = latest['成交量'] / avg_volume if avg_volume > 0 else 1.0
        
        # 成交量趋势
        volume_ma5 = df['成交量'].rolling(window=5).mean()
        volume_trend = 'up' if volume_ma5.iloc[-1] > volume_ma5.iloc[-2] else 'down'
        
        return {
            'volume_trend': volume_trend,
            'volume_ratio': volume_ratio,
            'current_volume': latest['成交量'],
            'avg_volume': avg_volume,
            'volume_signal': 'high' if volume_ratio > 2 else 'normal' if volume_ratio > 0.5 else 'low'
        }