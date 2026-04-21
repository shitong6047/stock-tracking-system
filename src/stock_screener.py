"""
多因子选股模型模块
功能：整合技术面、基本面、资金面、情绪面四个维度，实现加权评分和Top N股票筛选
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json

from technical_analysis import TechnicalAnalysis
from value_evaluation import ValueEvaluation
from global_news import GlobalNewsCollector


@dataclass
class ScreeningResult:
    """单只股票筛选结果"""
    code: str = ""
    name: str = ""
    total_score: float = 0.0
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    capital_score: float = 0.0
    sentiment_score: float = 0.0
    rank: int = 0
    details: Dict = field(default_factory=dict)
    passed_filters: bool = True
    filter_reasons: List[str] = field(default_factory=list)


@dataclass
class ScreeningSummary:
    """筛选汇总信息"""
    total_stocks: int = 0
    passed_count: int = 0
    filtered_count: int = 0
    filter_reason_distribution: Dict = field(default_factory=dict)
    avg_total_score: float = 0.0
    avg_technical_score: float = 0.0
    avg_fundamental_score: float = 0.0
    avg_capital_score: float = 0.0
    avg_sentiment_score: float = 0.0
    top_n_results: List[ScreeningResult] = field(default_factory=list)
    screening_time: str = ""


class MultiFactorScreener:
    """
    多因子选股器 - 核心类
    
    整合四个维度的分析：
    - 技术面 (40%): 趋势/动量/超买超卖/波动率
    - 基本面 (30%): 估值/盈利能力/成长性/财务健康
    - 资金面 (20%): 成交量/换手率/量比/资金流向
    - 情绪面 (10%): 大盘趋势/板块轮动/新闻情绪/恐慌贪婪指数
    """

    def __init__(self,
                 weights: Dict[str, float] = None,
                 filters: Dict[str, Any] = None):
        """
        初始化多因子选股器
        
        参数:
            weights: 四维权重配置，默认 {'technical': 0.40, 'fundamental': 0.30, 'capital': 0.20, 'sentiment': 0.10}
            filters: 筛选条件字典
        """
        self.weights = weights or {
            'technical': 0.40,
            'fundamental': 0.30,
            'capital': 0.20,
            'sentiment': 0.10
        }

        self.filters = filters or {
            'min_market_cap': 50,
            'max_market_cap': 10000,
            'min_pe': 0,
            'max_pe': 200,
            'exclude_st': True,
            'exclude_suspended': True,
            'min_turnover_rate': 0.5,
            'max_volatility': 50
        }

        self.technical_analyzer = TechnicalAnalysis()
        self.value_evaluator = ValueEvaluation()
        self.news_collector = GlobalNewsCollector()

        self._cache = {}
        self._cache_lock = threading.Lock()
        self._progress_count = 0
        self._progress_lock = threading.Lock()

    def calculate_technical_score(self, stock_code: str, price_data: pd.DataFrame) -> Tuple[float, Dict]:
        """
        计算技术面评分 (0-100)
        
        评估维度：
        - 趋势得分：均线多头排列强度 (25%)
        - 动量得分：MACD/KDJ动量信号 (25%)
        - 超买超卖得分：RSI/CCI位置 (25%)
        - 波动率得分：布林带/ATR (25%)
        
        参数:
            stock_code: 股票代码
            price_data: 价格数据DataFrame（需包含OHLCV列）
            
        返回:
            (技术面得分, 详细信息字典)
        """
        details = {}
        
        try:
            if price_data is None or len(price_data) < 30:
                return 50.0, {'error': '数据不足', 'trend_score': 50, 'momentum_score': 50,
                             'oversold_score': 50, 'volatility_score': 50}

            df = self.technical_analyzer.calculate_all_indicators(price_data)
            
            trend_score = self._calculate_trend_score(df)
            momentum_score = self._calculate_momentum_score(df)
            oversold_score = self._calculate_oversold_score(df)
            volatility_score = self._calculate_volatility_score(df)

            total_score = (
                trend_score * 0.25 +
                momentum_score * 0.25 +
                oversold_score * 0.25 +
                volatility_score * 0.25
            )

            details = {
                'trend_score': round(trend_score, 1),
                'momentum_score': round(momentum_score, 1),
                'oversold_score': round(oversold_score, 1),
                'volatility_score': round(volatility_score, 1),
                'trend_analysis': self.technical_analyzer.analyze_trend(df),
                'signals': [s.description for s in self.technical_analyzer.generate_signals(df)],
                'volume_analysis': self.technical_analyzer.analyze_volume(df)
            }

            return round(total_score, 1), details

        except Exception as e:
            print(f"[错误] 技术面评分失败 {stock_code}: {str(e)}")
            return 50.0, {'error': str(e), 'trend_score': 50, 'momentum_score': 50,
                         'oversold_score': 50, 'volatility_score': 50}

    def _calculate_trend_score(self, df: pd.DataFrame) -> float:
        """计算趋势得分 (0-100)"""
        try:
            if len(df) < 20:
                return 50.0

            latest = df.iloc[-1]
            score = 50.0

            ma_alignment = 0
            if latest['MA5'] > latest['MA10'] > latest['MA20']:
                ma_alignment += 30
            elif latest['MA5'] > latest['MA10']:
                ma_alignment += 15

            ma_trend_up = 0
            prev = df.iloc[-2]
            if latest['MA5'] > prev['MA5']:
                ma_trend_up += 15
            if latest['MA10'] > prev['MA10']:
                ma_trend_up += 10
            if latest['MA20'] > prev['MA20']:
                ma_trend_up += 10

            price_above_ma = 0
            if latest['收盘'] > latest['MA5']:
                price_above_ma += 10
            if latest['收盘'] > latest['MA20']:
                price_above_ma += 10

            trend_analysis = self.technical_analyzer.analyze_trend(df)
            if trend_analysis.get('trend') == 'strong_up':
                score = 90 + min(10, ma_alignment * 0.3)
            elif trend_analysis.get('trend') == 'up':
                score = 75 + min(15, ma_trend_up * 0.5)
            elif trend_analysis.get('trend') == 'neutral':
                score = 55 + min(10, price_above_ma)
            else:
                score = max(25, 55 - abs(ma_trend_up))

            score += ma_alignment + ma_trend_up + price_above_ma

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 50.0

    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """计算动量得分 (0-100)"""
        try:
            if len(df) < 26:
                return 50.0

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            score = 50.0

            macd_signal = 0
            if latest['MACD'] > latest['MACD_signal']:
                macd_signal += 20
                if prev['MACD'] <= prev['MACD_signal']:
                    macd_signal += 15
            else:
                macd_signal -= 10
                if prev['MACD'] >= prev['MACD_signal']:
                    macd_signal -= 10

            macd_hist = latest['MACD_histogram']
            if macd_hist > 0:
                hist_score = min(15, macd_hist / (df['收盘'].iloc[-1] * 0.01))
                macd_signal += hist_score

            kdj_signal = 0
            if latest['K'] > latest['D']:
                kdj_signal += 15
                if prev['K'] <= prev['D']:
                    kdj_signal += 10
            else:
                kdj_signal -= 8

            j_position = latest['J']
            if 20 <= j_position <= 80:
                kdj_signal += 10
            elif j_position > 80:
                kdj_signal -= 5
            elif j_position < 20:
                kdj_signal += 5

            price_momentum = (latest['收盘'] - df['收盘'].iloc[-20]) / df['收盘'].iloc[-20] * 100
            if price_momentum > 10:
                score_adj = min(10, price_momentum * 0.5)
            elif price_momentum < -10:
                score_adj = max(-10, price_momentum * 0.5)
            else:
                score_adj = price_momentum * 0.3

            score = 50 + macd_signal + kdj_signal + score_adj

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 50.0

    def _calculate_oversold_score(self, df: pd.DataFrame) -> float:
        """计算超买超卖得分 (0-100)"""
        try:
            if len(df) < 12:
                return 50.0

            latest = df.iloc[-1]
            score = 50.0

            rsi6 = latest.get('RSI6', 50)
            rsi12 = latest.get('RSI12', 50)

            if 40 <= rsi6 <= 60:
                rsi_score = 85
            elif 35 <= rsi6 <= 65:
                rsi_score = 70
            elif 30 <= rsi6 <= 70:
                rsi_score = 55
            elif rsi6 > 70:
                rsi_score = max(30, 70 - (rsi6 - 70) * 1.5)
            elif rsi6 < 30:
                rsi_score = min(80, 50 + (30 - rsi6) * 1.2)
            else:
                rsi_score = 50

            rsi_consistency = abs(rsi6 - rsi12)
            if rsi_consistency < 5:
                rsi_score += 8
            elif rsi_consistency < 10:
                rsi_score += 4

            bb_position = 0
            if 'BB_upper' in df.columns and 'BB_lower' in df.columns:
                bb_range = latest['BB_upper'] - latest['BB_lower']
                if bb_range > 0:
                    bb_pos = (latest['收盘'] - latest['BB_lower']) / bb_range
                    if 0.3 <= bb_pos <= 0.7:
                        bb_position = 12
                    elif 0.2 <= bb_pos <= 0.8:
                        bb_position = 8
                    elif bb_pos > 0.9:
                        bb_position = -8
                    elif bb_pos < 0.1:
                        bb_position = 5

            score = rsi_score * 0.75 + 50 * 0.25 + bb_position

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 50.0

    def _calculate_volatility_score(self, df: pd.DataFrame) -> float:
        """计算波动率得分 (0-100)，适中波动率为优"""
        try:
            if len(df) < 20:
                return 50.0

            returns = df['收盘'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100

            if 15 <= volatility <= 35:
                vol_score = 85
            elif 10 <= volatility <= 45:
                vol_score = 70
            elif 5 <= volatility <= 55:
                vol_score = 55
            elif volatility > 55:
                vol_score = max(30, 55 - (volatility - 55) * 0.5)
            else:
                vol_score = min(65, 45 + (5 - volatility) * 2)

            atr = df['最高'] - df['最低']
            avg_atr = atr.rolling(window=14).mean().iloc[-1]
            price = df['收盘'].iloc[-1]

            if price > 0 and not np.isnan(avg_atr):
                atr_pct = avg_atr / price * 100
                if 2 <= atr_pct <= 5:
                    atr_bonus = 8
                elif 1 <= atr_pct <= 7:
                    atr_bonus = 4
                else:
                    atr_bonus = 0
            else:
                atr_bonus = 0

            vol_trend = returns.iloc[-5:].std() if len(returns) >= 5 else volatility
            vol_change = vol_trend / volatility if volatility > 0 else 1
            if 0.8 <= vol_change <= 1.2:
                stability_bonus = 7
            else:
                stability_bonus = 0

            score = vol_score + atr_bonus + stability_bonus

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 50.0

    def calculate_fundamental_score(self, stock_code: str, fundamental_data: Dict) -> Tuple[float, Dict]:
        """
        计算基本面评分 (0-100)
        
        调用ValueEvaluation的完整基本面分析
        
        参数:
            stock_code: 股票代码
            fundamental_data: 基本面数据字典
            
        返回:
            (基本面得分, 详细信息字典)
        """
        details = {}

        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                return 50.0, {'error': '数据缺失'}

            industry = fundamental_data.get('industry', '综合')
            fundamental_score = self.value_evaluator.calculate_fundamental_score(
                fundamental_data, industry)

            valuation = self.value_evaluator.analyze_valuation(fundamental_data, industry)
            profitability = self.value_evaluator.analyze_profitability(fundamental_data)
            growth = self.value_evaluator.analyze_growth(fundamental_data)
            health = self.value_evaluator.check_financial_health(fundamental_data)

            details = {
                'total_score': fundamental_score.total_score,
                'grade': fundamental_score.grade,
                'rating': fundamental_score.rating,
                'valuation_score': fundamental_score.valuation_score,
                'profitability_score': fundamental_score.profitability_score,
                'growth_score': fundamental_score.growth_score,
                'health_score': fundamental_score.health_score,
                'valuation_details': {
                    'pe_ratio': valuation.pe_ratio,
                    'pb_ratio': valuation.pb_ratio,
                    'peg_ratio': valuation.peg_ratio,
                    'pe_percentile': valuation.pe_percentile,
                    'market_cap_rank': valuation.market_cap_rank
                },
                'profitability_details': {
                    'roe': profitability.roe,
                    'roa': profitability.roa,
                    'gross_margin': profitability.gross_margin,
                    'net_margin': profitability.net_margin
                },
                'growth_details': {
                    'revenue_growth_yoy': growth.revenue_growth_yoy,
                    'profit_growth_yoy': growth.profit_growth_yoy,
                    'growth_quality_score': growth.growth_quality_score
                },
                'health_details': {
                    'debt_ratio': health.debt_ratio,
                    'current_ratio': health.current_ratio,
                    'warnings_count': len(health.health_warnings)
                },
                'strengths': fundamental_score.strengths[:5],
                'weaknesses': fundamental_score.weaknesses[:5],
                'suggestions': fundamental_score.suggestions[:3]
            }

            return round(fundamental_score.total_score, 1), details

        except Exception as e:
            print(f"[错误] 基本面评分失败 {stock_code}: {str(e)}")
            return 50.0, {'error': str(e)}

    def calculate_capital_score(self, stock_code: str, market_data: Dict) -> Tuple[float, Dict]:
        """
        计算资金面评分 (0-100)
        
        评估维度：
        - 成交量变化率 (25%)
        - 换手率活跃度 (25%)
        - 量比 (25%)
        - 主力资金流向模拟 (25%)
        
        参数:
            stock_code: 股票代码
            market_data: 市场行情数据字典
            
        返回:
            (资金面得分, 详细信息字典)
        """
        details = {}

        try:
            if not market_data or not isinstance(market_data, dict):
                return 50.0, {'error': '数据缺失'}

            volume_score = self._score_volume_change(market_data)
            turnover_score = self._score_turnover_rate(market_data)
            volume_ratio_score = self._score_volume_ratio(market_data)
            capital_flow_score = self._score_capital_flow(market_data)

            total_score = (
                volume_score * 0.25 +
                turnover_score * 0.25 +
                volume_ratio_score * 0.25 +
                capital_flow_score * 0.25
            )

            details = {
                'volume_score': round(volume_score, 1),
                'turnover_score': round(turnover_score, 1),
                'volume_ratio_score': round(volume_ratio_score, 1),
                'capital_flow_score': round(capital_flow_score, 1),
                'current_volume': market_data.get('current_volume', 0),
                'avg_volume_5d': market_data.get('avg_volume_5d', 0),
                'avg_volume_20d': market_data.get('avg_volume_20d', 0),
                'turnover_rate': market_data.get('turnover_rate', 0),
                'volume_ratio': market_data.get('volume_ratio', 1.0),
                'northbound_flow': market_data.get('northbound_flow', 0)
            }

            return round(total_score, 1), details

        except Exception as e:
            print(f"[错误] 资金面评分失败 {stock_code}: {str(e)}")
            return 50.0, {'error': str(e)}

    def _score_volume_change(self, market_data: Dict) -> float:
        """成交量变化率评分"""
        try:
            current_vol = market_data.get('current_volume', 0)
            avg_vol_5d = market_data.get('avg_volume_5d', 0)
            avg_vol_20d = market_data.get('avg_volume_20d', 0)

            if current_vol <= 0 or avg_vol_20d <= 0:
                return 50.0

            vol_vs_5d = current_vol / avg_vol_5d if avg_vol_5d > 0 else 1.0
            vol_vs_20d = current_vol / avg_vol_20d

            if 1.2 <= vol_vs_20d <= 1.8:
                score = 88
            elif 1.0 <= vol_vs_20d <= 2.2:
                score = 75
            elif 0.7 <= vol_vs_20d <= 3.0:
                score = 58
            elif vol_vs_20d > 3.0:
                score = max(40, 65 - (vol_vs_20d - 3) * 8)
            else:
                score = max(35, 50 + (vol_vs_20d - 0.7) * 30)

            if 1.1 <= vol_vs_5d <= 1.5:
                score += 7
            elif vol_vs_5d > 2.0:
                score -= 5

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 50.0

    def _score_turnover_rate(self, market_data: Dict) -> float:
        """换手率活跃度评分"""
        try:
            turnover = market_data.get('turnover_rate', 0)

            if turnover <= 0:
                return 40.0

            if 2 <= turnover <= 6:
                score = 88
            elif 1 <= turnover <= 8:
                score = 75
            elif 0.5 <= turnover <= 12:
                score = 60
            elif turnover > 15:
                score = max(38, 55 - (turnover - 15) * 3)
            else:
                score = max(42, 45 + turnover * 8)

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 50.0

    def _score_volume_ratio(self, market_data: Dict) -> float:
        """量比评分"""
        try:
            volume_ratio = market_data.get('volume_ratio', 1.0)

            if volume_ratio <= 0:
                return 50.0

            if 1.2 <= volume_ratio <= 2.0:
                score = 85
            elif 1.0 <= volume_ratio <= 2.5:
                score = 72
            elif 0.8 <= volume_ratio <= 3.5:
                score = 58
            elif volume_ratio > 4.0:
                score = max(40, 55 - (volume_ratio - 4) * 5)
            else:
                score = max(42, 48 + (0.8 - volume_ratio) * 20)

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 50.0

    def _score_capital_flow(self, market_data: Dict) -> float:
        """主力资金流向和北向资金评分"""
        try:
            northbound_flow = market_data.get('northbound_flow', 0)

            price_change = market_data.get('price_change_pct', 0)
            volume_ratio = market_data.get('volume_ratio', 1.0)

            flow_score = 50.0

            if northbound_flow > 0:
                if northbound_flow > 50000000:
                    flow_score = 88
                elif northbound_flow > 20000000:
                    flow_score = 78
                elif northbound_flow > 5000000:
                    flow_score = 68
                else:
                    flow_score = 58
            elif northbound_flow < -50000000:
                flow_score = 35
            elif northbound_flow < -20000000:
                flow_score = 42
            else:
                flow_score = 50

            if price_change > 0 and volume_ratio > 1.2:
                flow_score += 7
            elif price_change < 0 and volume_ratio > 1.5:
                flow_score -= 8

            return max(0, min(100, round(flow_score, 1)))

        except Exception as e:
            return 50.0

    def calculate_sentiment_score(self, stock_code: str, sentiment_data: Dict = None) -> Tuple[float, Dict]:
        """
        计算情绪面评分 (0-100)
        
        评估维度：
        - 大盘趋势方向 (30%)
        - 板块轮动效应 (25%)
        - 新闻情绪分析 (25%)
        - 市场恐慌/贪婪指数模拟 (20%)
        
        参数:
            stock_code: 股票代码
            sentiment_data: 情绪数据字典（可选）
            
        返回:
            (情绪面得分, 详细信息字典)
        """
        details = {}

        try:
            if not sentiment_data:
                sentiment_data = {}

            market_trend_score = self._score_market_trend(sentiment_data)
            sector_rotation_score = self._score_sector_rotation(sentiment_data)
            news_sentiment_score = self._score_news_sentiment(stock_code)
            fear_greed_score = self._score_fear_greed_index(sentiment_data)

            total_score = (
                market_trend_score * 0.30 +
                sector_rotation_score * 0.25 +
                news_sentiment_score * 0.25 +
                fear_greed_score * 0.20
            )

            details = {
                'market_trend_score': round(market_trend_score, 1),
                'sector_rotation_score': round(sector_rotation_score, 1),
                'news_sentiment_score': round(news_sentiment_score, 1),
                'fear_greed_score': round(fear_greed_score, 1),
                'market_trend': sentiment_data.get('market_trend', '未知'),
                'sector_performance': sentiment_data.get('sector_performance', {}),
                'news_summary': details.get('news_summary', ''),
                'fear_greed_level': self._get_fear_greed_label(fear_greed_score)
            }

            return round(total_score, 1), details

        except Exception as e:
            print(f"[错误] 情绪面评分失败 {stock_code}: {str(e)}")
            return 50.0, {'error': str(e)}

    def _score_market_trend(self, sentiment_data: Dict) -> float:
        """大盘趋势方向评分"""
        try:
            trend = sentiment_data.get('market_trend', 'neutral')
            trend_strength = sentiment_data.get('trend_strength', 0.5)

            trend_scores = {
                'strong_up': 88,
                'up': 75,
                'neutral': 55,
                'down': 38,
                'strong_down': 25
            }

            base_score = trend_scores.get(trend, 55)
            strength_adj = (trend_strength - 0.5) * 20

            return max(0, min(100, round(base_score + strength_adj, 1)))

        except Exception as e:
            return 55.0

    def _score_sector_rotation(self, sentiment_data: Dict) -> float:
        """板块轮动效应评分"""
        try:
            sector_perf = sentiment_data.get('sector_performance', {})

            if not sector_perf:
                return 55.0

            sector_values = list(sector_perf.values())
            if not sector_values:
                return 55.0

            avg_perf = np.mean(sector_values)
            std_perf = np.std(sector_values) if len(sector_values) > 1 else 0

            if avg_perf > 2:
                base_score = 78
            elif avg_perf > 0:
                base_score = 62
            elif avg_perf > -2:
                base_score = 48
            else:
                base_score = 35

            rotation_strength = min(std_perf * 5, 15)
            dispersion_penalty = max(0, (std_perf - 3) * 3) if std_perf > 3 else 0

            score = base_score + rotation_strength - dispersion_penalty

            return max(0, min(100, round(score, 1)))

        except Exception as e:
            return 55.0

    def _score_news_sentiment(self, stock_code: str) -> float:
        """新闻情绪分析评分"""
        try:
            news_list = self.news_collector.get_global_news(count=10)

            if not news_list:
                return 55.0

            analysis = self.news_collector.analyze_market_impact(news_list)

            positive_weight = analysis.get('positive_news_count', 0) * 8
            negative_weight = analysis.get('negative_news_count', 0) * (-8)
            relevance_boost = analysis.get('avg_relevance', 0.5) * 15

            base_score = 50 + positive_weight + negative_weight + relevance_boost

            sentiment_map = {
                '乐观': 72,
                '中性': 52,
                '悲观': 32
            }
            sentiment_adj = sentiment_map.get(analysis.get('market_sentiment', '中性'), 0) - 50

            final_score = base_score * 0.7 + (base_score + sentiment_adj) * 0.3

            return max(0, min(100, round(final_score, 1)))

        except Exception as e:
            return 55.0

    def _score_fear_greed_index(self, sentiment_data: Dict) -> float:
        """市场恐慌/贪婪指数模拟评分 (0-100)"""
        try:
            volatility = sentiment_data.get('market_volatility', 20)
            market_momentum = sentiment_data.get('market_momentum', 0)
            safe_demand = sentiment_data.get('safe_asset_demand', 0.5)

            fear_score = 50

            if volatility < 15:
                fear_score += 18
            elif volatility < 25:
                fear_score += 8
            elif volatility > 35:
                fear_score -= 15
            elif volatility > 28:
                fear_score -= 8

            if market_momentum > 3:
                fear_score += 15
            elif market_momentum > 1:
                fear_score += 8
            elif market_momentum < -3:
                fear_score -= 15
            elif market_momentum < -1:
                fear_score -= 8

            if safe_demand < 0.4:
                fear_score += 10
            elif safe_demand > 0.7:
                fear_score -= 12

            return max(0, min(100, round(fear_score, 1)))

        except Exception as e:
            return 50.0

    def _get_fear_greed_label(self, score: float) -> str:
        """获取恐慌贪婪指数标签"""
        if score >= 80:
            return "极度贪婪"
        elif score >= 65:
            return "贪婪"
        elif score >= 55:
            return "偏乐观"
        elif score >= 45:
            return "中性"
        elif score >= 35:
            return "偏恐惧"
        elif score >= 20:
            return "恐惧"
        else:
            return "极度恐惧"

    def calculate_composite_score(self, stock_code: str, data: Dict) -> Dict:
        """
        计算综合评分 - 核心方法
        
        整合四个维度的评分，返回完整的评分结果
        
        参数:
            stock_code: 股票代码
            data: 包含所有需要的数据字典，格式如下：
                  {
                      'name': '股票名称',
                      'price_data': DataFrame,          # 价格数据
                      'fundamental_data': Dict,           # 基本面数据
                      'market_data': Dict,                # 市场行情数据
                      'sentiment_data': Dict              # 情绪数据（可选）
                  }
                  
        返回:
            综合评分结果字典
        """
        result = ScreeningResult(code=stock_code)
        result.name = data.get('name', '')

        try:
            price_data = data.get('price_data')
            fundamental_data = data.get('fundamental_data')
            market_data = data.get('market_data')
            sentiment_data = data.get('sentiment_data')

            tech_score, tech_details = self.calculate_technical_score(stock_code, price_data)
            fund_score, fund_details = self.calculate_fundamental_score(stock_code, fundamental_data)
            cap_score, cap_details = self.calculate_capital_score(stock_code, market_data)
            sent_score, sent_details = self.calculate_sentiment_score(stock_code, sentiment_data)

            result.technical_score = tech_score
            result.fundamental_score = fund_score
            result.capital_score = cap_score
            result.sentiment_score = sent_score

            result.total_score = round(
                tech_score * self.weights['technical'] +
                fund_score * self.weights['fundamental'] +
                cap_score * self.weights['capital'] +
                sent_score * self.weights['sentiment'],
                1
            )

            result.details = {
                'technical': tech_details,
                'fundamental': fund_details,
                'capital': cap_details,
                'sentiment': sent_details,
                'weights_used': self.weights.copy(),
                'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            filter_result = self._apply_filters(stock_code, data)
            result.passed_filters = filter_result['passed']
            result.filter_reasons = filter_result['reasons']

        except Exception as e:
            print(f"[错误] 综合评分计算失败 {stock_code}: {str(e)}")
            result.total_score = 0
            result.details = {'error': str(e)}
            result.passed_filters = False
            result.filter_reasons.append(f'计算异常: {str(e)}')

        return {
            'code': result.code,
            'name': result.name,
            'total_score': result.total_score,
            'technical_score': result.technical_score,
            'fundamental_score': result.fundamental_score,
            'capital_score': result.capital_score,
            'sentiment_score': result.sentiment_score,
            'rank': 0,
            'details': result.details,
            'passed_filters': result.passed_filters,
            'filter_reasons': result.filter_reasons
        }

    def _apply_filters(self, stock_code: str, data: Dict) -> Dict:
        """
        应用筛选条件
        
        参数:
            stock_code: 股票代码
            data: 股票数据字典
            
        返回:
            {'passed': bool, 'reasons': List[str]}
        """
        reasons = []

        try:
            name = data.get('name', '')
            fundamental_data = data.get('fundamental_data', {})
            market_data = data.get('market_data', {})

            if self.filters.get('exclude_st', False):
                if 'ST' in name or 'st' in name:
                    reasons.append('ST股')
                    return {'passed': False, 'reasons': reasons}

            if self.filters.get('exclude_suspended', False):
                is_suspended = market_data.get('is_suspended', False)
                if is_suspended:
                    reasons.append('停牌')
                    return {'passed': False, 'reasons': reasons}

            market_cap = fundamental_data.get('valuation', {}).get('market_cap', 0)
            min_cap = self.filters.get('min_market_cap', 0)
            max_cap = self.filters.get('max_market_cap', float('inf'))

            if market_cap > 0:
                if market_cap < min_cap:
                    reasons.append(f'市值过低({market_cap:.0f}亿<{min_cap}亿)')
                elif market_cap > max_cap:
                    reasons.append(f'市值过高({market_cap:.0f}亿>{max_cap}亿)')

            pe_ratio = fundamental_data.get('valuation', {}).get('pe_ratio', 0)
            min_pe = self.filters.get('min_pe', 0)
            max_pe = self.filters.get('max_pe', float('inf'))

            if pe_ratio > 0:
                if pe_ratio < min_pe:
                    reasons.append(f'PE过低({pe_ratio:.1f}<{min_pe})')
                elif pe_ratio > max_pe:
                    reasons.append(f'PE过高({pe_ratio:.1f}>{max_pe})')

            turnover_rate = market_data.get('turnover_rate', 0)
            min_turnover = self.filters.get('min_turnover_rate', 0)

            if turnover_rate > 0 and turnover_rate < min_turnover:
                reasons.append(f'换手率过低({turnover_rate:.2f}%<{min_turnover}%)')

            max_volatility = self.filters.get('max_volatility', 100)
            volatility = market_data.get('volatility', 0)

            if volatility > max_volatility:
                reasons.append(f'波动率过高({volatility:.1f}%>{max_volatility}%)')

            return {'passed': len(reasons) == 0, 'reasons': reasons}

        except Exception as e:
            return {'passed': False, 'reasons': [f'筛选异常: {str(e)}']}

    def screen_market(self, scope: str = 'csi300', top_n: int = 10,
                     stocks_data: List[Dict] = None) -> Dict:
        """
        全市场扫描并返回 Top N 股票
        
        参数:
            scope: 扫描范围 ('csi300', 'csi500', 'all')
            top_n: 返回前N只股票
            stocks_data: 股票数据列表（如果为None则使用默认数据源）
            
        返回:
            包含筛选结果的字典
        """
        print(f"\n{'='*60}")
        print(f"🔍 开始多因子选股扫描")
        print(f"📊 扫描范围: {scope}")
        print(f"🎯 目标数量: Top {top_n}")
        print(f"⚖️ 权重配置: 技术{self.weights['technical']*100:.0f}% | "
              f"基本{self.weights['fundamental']*100:.0f}% | "
              f"资金{self.weights['capital']*100:.0f}% | "
              f"情绪{self.weights['sentiment']*100:.0f}%")
        print(f"{'='*60}\n")

        start_time = datetime.now()

        if stocks_data is None:
            stocks_data = self._get_default_stock_data(scope)

        all_results = []
        filter_stats = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_stock = {
                executor.submit(
                    self._process_single_stock,
                    stock['code'],
                    stock
                ): stock
                for stock in stocks_data
            }

            for future in as_completed(future_to_stock):
                stock = future_to_stock[future]
                try:
                    result = future.result()
                    all_results.append(result)

                    with self._progress_lock:
                        self._progress_count += 1
                        if self._progress_count % 50 == 0:
                            print(f"[进度] 已处理 {self._progress_count}/{len(stocks_data)} 只股票...")

                    if not result.get('passed_filters', True):
                        for reason in result.get('filter_reasons', []):
                            filter_stats[reason] = filter_stats.get(reason, 0) + 1

                except Exception as e:
                    print(f"[错误] 处理股票 {stock.get('code')} 失败: {str(e)}")

        passed_results = [r for r in all_results if r.get('passed_filters', False)]
        sorted_results = sorted(passed_results, key=lambda x: x.get('total_score', 0), reverse=True)

        for i, result in enumerate(sorted_results[:top_n], 1):
            result['rank'] = i

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        summary = ScreeningSummary(
            total_stocks=len(stocks_data),
            passed_count=len(passed_results),
            filtered_count=len(all_results) - len(passed_results),
            filter_reason_distribution=filter_stats,
            avg_total_score=np.mean([r['total_score'] for r in passed_results]) if passed_results else 0,
            avg_technical_score=np.mean([r['technical_score'] for r in passed_results]) if passed_results else 0,
            avg_fundamental_score=np.mean([r['fundamental_score'] for r in passed_results]) if passed_results else 0,
            avg_capital_score=np.mean([r['capital_score'] for r in passed_results]) if passed_results else 0,
            avg_sentiment_score=np.mean([r['sentiment_score'] for r in passed_results]) if passed_results else 0,
            top_n_results=[self._dict_to_screening_result(r) for r in sorted_results[:top_n]],
            screening_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
        )

        output = {
            'summary': self._summary_to_dict(summary),
            'top_n_stocks': sorted_results[:top_n],
            'all_passed_stocks': sorted_results,
            'statistics': self._generate_statistics(sorted_results),
            'processing_info': {
                'scope': scope,
                'top_n': top_n,
                'weights': self.weights,
                'filters': self.filters,
                'processing_time_seconds': round(processing_time, 2),
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        self._print_screening_output(output)

        return output

    def _process_single_stock(self, stock_code: str, stock_data: Dict) -> Dict:
        """处理单只股票的评分计算"""
        cache_key = f"{stock_code}_{hash(str(stock_data.get('price_data', {}).shape) if hasattr(stock_data.get('price_data'), 'shape') else '')}"

        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key].copy()

        result = self.calculate_composite_score(stock_code, stock_data)

        with self._cache_lock:
            self._cache[cache_key] = result.copy()

        return result

    def _get_default_stock_data(self, scope: str) -> List[Dict]:
        """
        获取默认股票数据（用于演示或测试）
        
        在实际应用中，这里应该从数据库或API获取真实数据
        """
        sample_stocks = [
            {'code': '600519', 'name': '贵州茅台'},
            {'code': '601318', 'name': '中国平安'},
            {'code': '000858', 'name': '五粮液'},
            {'code': '600036', 'name': '招商银行'},
            {'code': '601988', 'name': '中国银行'},
            {'code': '000333', 'name': '美的集团'},
            {'code': '002594', 'name': '比亚迪'},
            {'code': '300750', 'name': '宁德时代'},
            {'code': '601012', 'name': '隆基绿能'},
            {'code': '002475', 'name': '立讯精密'}
        ]

        enhanced_data = []
        np.random.seed(42)

        for stock in sample_stocks:
            dates = pd.date_range(end=datetime.now(), periods=120, freq='B')
            base_price = np.random.uniform(10, 200)
            prices = base_price * (1 + np.cumsum(np.random.randn(120) * 0.02))

            price_df = pd.DataFrame({
                '日期': dates,
                '开盘': prices * (1 + np.random.uniform(-0.02, 0.02, 120)),
                '最高': prices * (1 + np.abs(np.random.uniform(0, 0.04, 120))),
                '最低': prices * (1 - np.abs(np.random.uniform(0, 0.04, 120))),
                '收盘': prices,
                '成交量': np.random.uniform(1000000, 50000000, 120).astype(int)
            })

            pe_val = np.random.uniform(8, 60)
            pb_val = np.random.uniform(0.8, 10)
            roe_val = np.random.uniform(5, 30)
            revenue_growth = np.random.uniform(-10, 40)
            profit_growth = np.random.uniform(-15, 50)

            fundamental_data = {
                'industry': np.random.choice(['食品饮料', '金融', '医药生物', '电子', '电力设备']),
                'valuation': {
                    'pe_ratio': round(pe_val, 2),
                    'pb_ratio': round(pb_val, 2),
                    'ps_ratio': round(pe_val * 0.15, 2),
                    'pcf_ratio': round(pe_val * 0.12, 2),
                    'market_cap': round(np.random.uniform(100, 5000), 1)
                },
                'profitability': {
                    'roe': round(roe_val, 2),
                    'roa': round(roe_val * 0.4, 2),
                    'gross_margin': round(np.random.uniform(20, 60), 2),
                    'net_margin': round(np.random.uniform(5, 25), 2)
                },
                'growth': {
                    'revenue_growth_yoy': round(revenue_growth, 2),
                    'profit_growth': round(profit_growth, 2),
                    'eps_growth': round(profit_growth * 0.9, 2)
                },
                'financial_health': {
                    'debt_ratio': round(np.random.uniform(20, 70), 1),
                    'current_ratio': round(np.random.uniform(0.8, 2.5), 2),
                    'quick_ratio': round(np.random.uniform(0.5, 1.8), 2)
                }
            }

            market_data = {
                'current_volume': int(np.random.uniform(5000000, 80000000)),
                'avg_volume_5d': int(np.random.uniform(4000000, 60000000)),
                'avg_volume_20d': int(np.random.uniform(3000000, 50000000)),
                'turnover_rate': round(np.random.uniform(0.5, 12), 2),
                'volume_ratio': round(np.random.uniform(0.5, 3.0), 2),
                'price_change_pct': round(np.random.uniform(-5, 5), 2),
                'northbound_flow': int(np.random.uniform(-100000000, 150000000)),
                'volatility': round(np.random.uniform(15, 50), 1),
                'is_suspended': False
            }

            sentiment_data = {
                'market_trend': np.random.choice(['strong_up', 'up', 'neutral', 'down']),
                'trend_strength': np.random.uniform(0.3, 0.9),
                'sector_performance': {
                    '白酒': np.random.uniform(-3, 5),
                    '银行': np.random.uniform(-2, 4),
                    '新能源': np.random.uniform(-5, 8),
                    '半导体': np.random.uniform(-4, 6)
                },
                'market_volatility': np.random.uniform(15, 35),
                'market_momentum': np.random.uniform(-2, 4),
                'safe_asset_demand': np.random.uniform(0.3, 0.7)
            }

            enhanced_data.append({
                'code': stock['code'],
                'name': stock['name'],
                'price_data': price_df,
                'fundamental_data': fundamental_data,
                'market_data': market_data,
                'sentiment_data': sentiment_data
            })

        return enhanced_data

    def _dict_to_screening_result(self, result_dict: Dict) -> ScreeningResult:
        """将字典转换为ScreeningResult对象"""
        return ScreeningResult(
            code=result_dict.get('code', ''),
            name=result_dict.get('name', ''),
            total_score=result_dict.get('total_score', 0),
            technical_score=result_dict.get('technical_score', 0),
            fundamental_score=result_dict.get('fundamental_score', 0),
            capital_score=result_dict.get('capital_score', 0),
            sentiment_score=result_dict.get('sentiment_score', 0),
            rank=result_dict.get('rank', 0),
            details=result_dict.get('details', {}),
            passed_filters=result_dict.get('passed_filters', True),
            filter_reasons=result_dict.get('filter_reasons', [])
        )

    def _summary_to_dict(self, summary: ScreeningSummary) -> Dict:
        """将ScreeningSummary转换为字典"""
        return {
            'total_stocks': summary.total_stocks,
            'passed_count': summary.passed_count,
            'filtered_count': summary.filtered_count,
            'filter_reason_distribution': summary.filter_reason_distribution,
            'avg_total_score': round(summary.avg_total_score, 1),
            'avg_technical_score': round(summary.avg_technical_score, 1),
            'avg_fundamental_score': round(summary.avg_fundamental_score, 1),
            'avg_capital_score': round(summary.avg_capital_score, 1),
            'avg_sentiment_score': round(summary.avg_sentiment_score, 1),
            'screening_time': summary.screening_time
        }

    def _generate_statistics(self, results: List[Dict]) -> Dict:
        """生成统计信息"""
        if not results:
            return {}

        scores = [r['total_score'] for r in results]
        tech_scores = [r['technical_score'] for r in results]
        fund_scores = [r['fundamental_score'] for r in results]
        cap_scores = [r['capital_score'] for r in results]
        sent_scores = [r['sentiment_score'] for r in results]

        percentiles = {}
        for i, result in enumerate(results):
            percentile = (len(scores) - sum(1 for s in scores if s > result['total_score'])) / len(scores) * 100
            percentiles[result['code']] = round(percentile, 1)

        return {
            'count': len(results),
            'score_statistics': {
                'total': {
                    'mean': round(np.mean(scores), 1),
                    'median': round(np.median(scores), 1),
                    'std': round(np.std(scores), 1),
                    'min': round(min(scores), 1),
                    'max': round(max(scores), 1)
                },
                'technical': {
                    'mean': round(np.mean(tech_scores), 1),
                    'min': round(min(tech_scores), 1),
                    'max': round(max(tech_scores), 1)
                },
                'fundamental': {
                    'mean': round(np.mean(fund_scores), 1),
                    'min': round(min(fund_scores), 1),
                    'max': round(max(fund_scores), 1)
                },
                'capital': {
                    'mean': round(np.mean(cap_scores), 1),
                    'min': round(min(cap_scores), 1),
                    'max': round(max(cap_scores), 1)
                },
                'sentiment': {
                    'mean': round(np.mean(sent_scores), 1),
                    'min': round(min(sent_scores), 1),
                    'max': round(max(sent_scores), 1)
                }
            },
            'percentiles': percentiles,
            'score_distribution': {
                'excellent': len([s for s in scores if s >= 80]),
                'good': len([s for s in scores if 60 <= s < 80]),
                'average': len([s for s in scores if 40 <= s < 60]),
                'poor': len([s for s in scores if s < 40])
            }
        }

    def _print_screening_output(self, output: Dict):
        """打印筛选结果"""
        print("\n" + "=" * 80)
        print("📊 多因子选股扫描结果报告")
        print("=" * 80)

        summary = output['summary']
        stats = output['statistics']
        proc_info = output['processing_info']

        print(f"\n⏱️  扫描时间: {proc_info['start_time']} ~ {proc_info['end_time']}")
        print(f"⚡ 耗时: {proc_info['processing_time_seconds']} 秒")

        print(f"\n{'─'*60}")
        print("📈 筛选统计:")
        print(f"{'─'*60}")
        print(f"  • 扫描总数: {summary['total_stocks']} 只")
        print(f"  • 通过筛选: {summary['passed_count']} 只")
        print(f"  • 被淘汰数: {summary['filtered_count']} 只")

        if summary['filter_reason_distribution']:
            print(f"\n  📋 淘汰原因分布:")
            for reason, count in summary['filter_reason_distribution'].items():
                print(f"     - {reason}: {count} 只")

        if stats:
            print(f"\n{'─'*60}")
            print("📊 评分统计:")
            print(f"{'─'*60}")

            score_stats = stats.get('score_statistics', {}).get('total', {})
            print(f"  • 平均分: {score_stats.get('mean', 0):.1f}")
            print(f"  • 中位数: {score_stats.get('median', 0):.1f}")
            print(f"  • 最高分: {score_stats.get('max', 0):.1f}")
            print(f"  • 最低分: {score_stats.get('min', 0):.1f}")

            dist = stats.get('score_distribution', {})
            print(f"\n  📊 分数分布:")
            print(f"     - 优秀(≥80分): {dist.get('excellent', 0)} 只")
            print(f"     - 良好(60-79分): {dist.get('good', 0)} 只")
            print(f"     - 一般(40-59分): {dist.get('average', 0)} 只")
            print(f"     - 较差(<40分): {dist.get('poor', 0)} 只")

        print(f"\n{'='*80}")
        print(f"🏆 TOP {len(output['top_n_stocks'])} 排荐股票")
        print(f"{'='*80}")

        for i, stock in enumerate(output['top_n_stocks'], 1):
            print(f"\n{'─'*60}")
            print(f"  #{i} {stock['code']} {stock['name']}")
            print(f"{'─'*60}")
            print(f"  ⭐ 综合评分: {stock['total_score']:.1f}/100 (排名: #{stock['rank']})")
            print(f"  ┌─────────────────────────────────────┐")
            print(f"  │ 技术面: {stock['technical_score']:>6.1f} │ "
                  f"基本面: {stock['fundamental_score']:>6.1f} │")
            print(f"  │ 资金面: {stock['capital_score']:>6.1f} │ "
                  f"情绪面: {stock['sentiment_score']:>6.1f} │")
            print(f"  └─────────────────────────────────────┘")

            details = stock.get('details', {})
            fund_details = details.get('fundamental', {})
            if fund_details:
                grade = fund_details.get('grade', '-')
                rating = fund_details.get('rating', '-')
                print(f"  📋 基本面评级: {grade} ({rating})")

                strengths = fund_details.get('strengths', [])
                if strengths:
                    print(f"  ✅ 核心优势: {', '.join(strengths[:3])}")

            cap_details = details.get('capital', {})
            if cap_details:
                turnover = cap_details.get('turnover_rate', 0)
                vol_ratio = cap_details.get('volume_ratio', 0)
                print(f"  💰 换手率: {turnover:.2f}% | 量比: {vol_ratio:.2f}")

        print(f"\n{'='*80}")
        print("💡 使用说明:")
        print("  • 本系统采用四维加权模型进行综合评分")
        print("  • 评分越高代表投资价值越强")
        print("  • 请结合个人风险偏好和市场环境做最终决策")
        print("  • 本结果仅供参考，不构成投资建议")
        print("  • 投资有风险，决策需谨慎")
        print(f"{'='*80}\n")

    def update_weights(self, **kwargs):
        """
        自定义权重调整
        
        参数:
            **kwargs: 权重参数，如 technical=0.35, fundamental=0.35 等
        """
        for key, value in kwargs.items():
            if key in self.weights:
                old_value = self.weights[key]
                self.weights[key] = value
                print(f"[更新] {key}权重: {old_value} → {value}")

        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            print(f"[警告] 权重总和为{total:.3f}，建议调整为1.0")

    def update_filters(self, **kwargs):
        """
        更新筛选条件
        
        参数:
            **kwargs: 筛选条件参数
        """
        for key, value in kwargs.items():
            if key in self.filters:
                old_value = self.filters[key]
                self.filters[key] = value
                print(f"[更新] {key}: {old_value} → {value}")

    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            self._cache.clear()
        print("[清除] 结果缓存已清空")

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        with self._cache_lock:
            return len(self._cache)


def main():
    """主函数 - 演示多因子选股功能"""
    print("\n" + "=" * 60)
    print("🎯 多因子智能选股系统 v1.0")
    print("=" * 60)

    screener = MultiFactorScreener()

    custom_weights = {
        'technical': 0.35,
        'fundamental': 0.35,
        'capital': 0.20,
        'sentiment': 0.10
    }
    screener.update_weights(**custom_weights)

    custom_filters = {
        'min_market_cap': 100,
        'max_market_cap': 5000,
        'min_pe': 5,
        'max_pe': 80,
        'exclude_st': True,
        'exclude_suspended': True,
        'min_turnover_rate': 1.0,
        'max_volatility': 45
    }
    screener.update_filters(**custom_filters)

    result = screener.screen_market(scope='csi300', top_n=5)

    print(f"\n✅ 筛选完成！共推荐 {len(result['top_n_stocks'])} 只优质股票")


if __name__ == "__main__":
    main()
