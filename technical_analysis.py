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
    
    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算移动平均线
        
        参数:
            df: 包含收盘价的DataFrame
            periods: 均线周期列表
            
        返回:
            添加了均线列的DataFrame
        """
        df = df.copy()
        periods = periods or self.ma_periods
        
        close_col = 'close' if 'close' in df.columns else '收盘'
        
        for period in periods:
            df[f'MA{period}'] = df[close_col].rolling(window=period).mean()
        
        return df
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, 
                       slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        计算MACD指标
        
        参数:
            df: 包含收盘价的DataFrame
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        返回:
            添加了MACD指标的DataFrame
        """
        df = df.copy()
        
        close_col = 'close' if 'close' in df.columns else '收盘'
        
        ema_fast = df[close_col].ewm(span=fast, adjust=False).mean()
        ema_slow = df[close_col].ewm(span=slow, adjust=False).mean()
        
        df['DIF'] = ema_fast - ema_slow
        df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
        df['MACD'] = 2 * (df['DIF'] - df['DEA'])
        
        return df
    
    def calculate_kdj(self, df: pd.DataFrame, n: int = 9, 
                      m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """
        计算KDJ指标
        
        参数:
            df: 包含最高价、最低价、收盘价的DataFrame
            n: RSV周期
            m1: K值平滑周期
            m2: D值平滑周期
            
        返回:
            添加了KDJ指标的DataFrame
        """
        df = df.copy()
        
        high_col = 'high' if 'high' in df.columns else '最高'
        low_col = 'low' if 'low' in df.columns else '最低'
        close_col = 'close' if 'close' in df.columns else '收盘'
        
        low_n = df[low_col].rolling(window=n).min()
        high_n = df[high_col].rolling(window=n).max()
        
        df['RSV'] = (df[close_col] - low_n) / (high_n - low_n + 1e-10) * 100
        df['K'] = df['RSV'].ewm(alpha=1/m1, adjust=False).mean()
        df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算RSI指标
        
        参数:
            df: 包含收盘价的DataFrame
            periods: RSI周期列表
            
        返回:
            添加了RSI指标的DataFrame
        """
        df = df.copy()
        periods = periods or self.rsi_periods
        
        close_col = 'close' if 'close' in df.columns else '收盘'
        
        delta = df[close_col].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        for period in periods:
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / (avg_loss + 1e-10)
            df[f'RSI{period}'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_boll(self, df: pd.DataFrame, n: int = 20, 
                       std_dev: int = 2) -> pd.DataFrame:
        """
        计算布林带指标
        
        参数:
            df: 包含收盘价的DataFrame
            n: 周期
            std_dev: 标准差倍数
            
        返回:
            添加了布林带指标的DataFrame
        """
        df = df.copy()
        
        close_col = 'close' if 'close' in df.columns else '收盘'
        
        df['BOLL_MID'] = df[close_col].rolling(window=n).mean()
        std = df[close_col].rolling(window=n).std()
        
        df['BOLL_UPPER'] = df['BOLL_MID'] + std_dev * std
        df['BOLL_LOWER'] = df['BOLL_MID'] - std_dev * std
        
        return df
    
    def identify_trend(self, df: pd.DataFrame) -> Dict:
        """
        识别趋势方向和强度
        
        参数:
            df: 包含技术指标的DataFrame
            
        返回:
            趋势分析结果
        """
        if len(df) < 20:
            return {'trend': '未知', 'strength': 0, 'description': '数据不足'}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        signals = []
        
        ma5 = latest.get('MA5', 0)
        ma10 = latest.get('MA10', 0)
        ma20 = latest.get('MA20', 0)
        close = latest.get('close', latest.get('收盘', 0))
        
        if ma5 > ma10 > ma20:
            score += 30
            signals.append('均线多头排列')
        elif ma5 < ma10 < ma20:
            score -= 30
            signals.append('均线空头排列')
        
        if close > ma20:
            score += 20
            signals.append('价格站上MA20')
        elif close < ma20:
            score -= 20
            signals.append('价格跌破MA20')
        
        macd = latest.get('MACD', 0)
        dif = latest.get('DIF', 0)
        dea = latest.get('DEA', 0)
        prev_dif = prev.get('DIF', 0)
        prev_dea = prev.get('DEA', 0)
        
        if macd > 0:
            score += 15
            signals.append('MACD红柱')
        else:
            score -= 10
            signals.append('MACD绿柱')
        
        if dif > dea and prev_dif <= prev_dea:
            score += 20
            signals.append('MACD金叉')
        elif dif < dea and prev_dif >= prev_dea:
            score -= 20
            signals.append('MACD死叉')
        
        rsi6 = latest.get('RSI6', 50)
        if rsi6 > 70:
            score -= 10
            signals.append('RSI超买')
        elif rsi6 < 30:
            score += 10
            signals.append('RSI超卖')
        
        if score >= 50:
            trend = '强势上涨'
        elif score >= 20:
            trend = '偏强震荡'
        elif score >= -20:
            trend = '震荡整理'
        elif score >= -50:
            trend = '偏弱震荡'
        else:
            trend = '弱势下跌'
        
        return {
            'trend': trend,
            'strength': max(0, min(100, 50 + score)),
            'score': score,
            'signals': signals,
            'description': '，'.join(signals) if signals else '无明显信号'
        }
    
    def detect_signals(self, df: pd.DataFrame) -> List[TechnicalSignal]:
        """
        检测买卖信号
        
        参数:
            df: 包含技术指标的DataFrame
            
        返回:
            信号列表
        """
        signals = []
        
        if len(df) < 30:
            return signals
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        dif = latest.get('DIF', 0)
        dea = latest.get('DEA', 0)
        prev_dif = prev.get('DIF', 0)
        prev_dea = prev.get('DEA', 0)
        
        if dif > dea and prev_dif <= prev_dea:
            strength = '强' if dif > 0 else '中'
            signals.append(TechnicalSignal(
                signal_type='MACD金叉',
                signal_strength=strength,
                description=f'DIF({dif:.3f})上穿DEA({dea:.3f})',
                value=dif
            ))
        elif dif < dea and prev_dif >= prev_dea:
            strength = '强' if dif < 0 else '中'
            signals.append(TechnicalSignal(
                signal_type='MACD死叉',
                signal_strength=strength,
                description=f'DIF({dif:.3f})下穿DEA({dea:.3f})',
                value=dif
            ))
        
        k = latest.get('K', 50)
        d = latest.get('D', 50)
        j = latest.get('J', 50)
        
        if k < 20 and d < 20:
            signals.append(TechnicalSignal(
                signal_type='KDJ超卖',
                signal_strength='强',
                description=f'K({k:.1f})和D({d:.1f})均低于20，超卖区域',
                value=k
            ))
        elif k > 80 and d > 80:
            signals.append(TechnicalSignal(
                signal_type='KDJ超买',
                signal_strength='强',
                description=f'K({k:.1f})和D({d:.1f})均高于80，超买区域',
                value=k
            ))
        
        prev_k = prev.get('K', 50)
        prev_d = prev.get('D', 50)
        if k > d and prev_k <= prev_d:
            signals.append(TechnicalSignal(
                signal_type='KDJ金叉',
                signal_strength='中',
                description=f'K({k:.1f})上穿D({d:.1f})',
                value=k
            ))
        elif k < d and prev_k >= prev_d:
            signals.append(TechnicalSignal(
                signal_type='KDJ死叉',
                signal_strength='中',
                description=f'K({k:.1f})下穿D({d:.1f})',
                value=k
            ))
        
        rsi6 = latest.get('RSI6', 50)
        if rsi6 < 30:
            signals.append(TechnicalSignal(
                signal_type='RSI超卖',
                signal_strength='中',
                description=f'RSI6({rsi6:.1f})低于30，超卖区域',
                value=rsi6
            ))
        elif rsi6 > 70:
            signals.append(TechnicalSignal(
                signal_type='RSI超买',
                signal_strength='中',
                description=f'RSI6({rsi6:.1f})高于70，超买区域',
                value=rsi6
            ))
        
        close = latest.get('close', latest.get('收盘', 0))
        ma20 = latest.get('MA20', 0)
        boll_upper = latest.get('BOLL_UPPER', 0)
        boll_lower = latest.get('BOLL_LOWER', 0)
        
        if close > ma20 and prev.get('close', prev.get('收盘', 0)) <= ma20:
            signals.append(TechnicalSignal(
                signal_type='突破MA20',
                signal_strength='中',
                description=f'价格({close:.2f})突破MA20({ma20:.2f})',
                value=close
            ))
        elif close < ma20 and prev.get('close', prev.get('收盘', 0)) >= ma20:
            signals.append(TechnicalSignal(
                signal_type='跌破MA20',
                signal_strength='中',
                description=f'价格({close:.2f})跌破MA20({ma20:.2f})',
                value=close
            ))
        
        if close > boll_upper:
            signals.append(TechnicalSignal(
                signal_type='突破布林上轨',
                signal_strength='中',
                description=f'价格({close:.2f})突破布林上轨({boll_upper:.2f})',
                value=close
            ))
        elif close < boll_lower:
            signals.append(TechnicalSignal(
                signal_type='跌破布林下轨',
                signal_strength='中',
                description=f'价格({close:.2f})跌破布林下轨({boll_lower:.2f})',
                value=close
            ))
        
        return signals
    
    def get_technical_score(self, df: pd.DataFrame) -> Dict:
        """
        获取技术面综合评分
        
        参数:
            df: 包含技术指标的DataFrame
            
        返回:
            技术评分结果
        """
        trend = self.identify_trend(df)
        signals = self.detect_signals(df)
        
        buy_signals = [s for s in signals if '金叉' in s.signal_type or '超卖' in s.signal_type or '突破' in s.signal_type]
        sell_signals = [s for s in signals if '死叉' in s.signal_type or '超买' in s.signal_type or '跌破' in s.signal_type]
        
        score = trend['strength']
        
        for s in buy_signals:
            if s.signal_strength == '强':
                score += 10
            else:
                score += 5
        
        for s in sell_signals:
            if s.signal_strength == '强':
                score -= 10
            else:
                score -= 5
        
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'trend': trend,
            'buy_signals': [{'type': s.signal_type, 'strength': s.signal_strength, 'desc': s.description} for s in buy_signals],
            'sell_signals': [{'type': s.signal_type, 'strength': s.signal_strength, 'desc': s.description} for s in sell_signals],
            'signal_count': len(signals),
            'evaluation': self._evaluate_score(score)
        }
    
    def _evaluate_score(self, score: int) -> str:
        """评估分数等级"""
        if score >= 80:
            return '技术面强势，建议关注买入机会'
        elif score >= 60:
            return '技术面偏强，可考虑逢低布局'
        elif score >= 40:
            return '技术面中性，建议观望'
        elif score >= 20:
            return '技术面偏弱，注意风险'
        else:
            return '技术面弱势，建议规避'


if __name__ == "__main__":
    from data_acquisition import DataAcquisition
    
    print("=" * 50)
    print("测试技术分析模块")
    print("=" * 50)
    
    data_acq = DataAcquisition()
    ta = TechnicalAnalysis()
    
    code = "000001"
    print(f"\n获取股票 {code} 历史数据:")
    df = data_acq.get_stock_history(code, days=120)
    
    if df is not None:
        print("\n计算技术指标:")
        df = ta.calculate_all_indicators(df)
        print(df[['date', 'close', 'MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'K', 'D', 'RSI6']].tail())
        
        print("\n趋势分析:")
        trend = ta.identify_trend(df)
        print(f"  趋势: {trend['trend']}")
        print(f"  强度: {trend['strength']}")
        print(f"  信号: {trend['description']}")
        
        print("\n信号检测:")
        signals = ta.detect_signals(df)
        for s in signals:
            print(f"  [{s.signal_strength}] {s.signal_type}: {s.description}")
        
        print("\n技术评分:")
        score = ta.get_technical_score(df)
        print(f"  综合评分: {score['score']}")
        print(f"  评价: {score['evaluation']}")
        print(f"  买入信号: {len(score['buy_signals'])}个")
        print(f"  卖出信号: {len(score['sell_signals'])}个")
