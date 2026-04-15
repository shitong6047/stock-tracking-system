"""
预测模型模块
功能：构建多因子预测模型，预测次日涨跌
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import os

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

from technical_analysis import TechnicalAnalysis
from value_evaluation import ValueEvaluation
from data_acquisition import DataAcquisition


@dataclass
class PredictionResult:
    """预测结果数据类"""
    code: str
    name: str
    prediction_time: str
    direction: str
    probability: float
    confidence: str
    technical_score: float
    value_score: float
    sentiment_score: float
    macro_score: float
    total_score: float
    key_signals: List[str]
    risk_warning: str


class PredictionModel:
    """股票预测模型类"""
    
    def __init__(self, model_path: str = './models'):
        """
        初始化预测模型
        
        参数:
            model_path: 模型保存路径
        """
        self.model_path = model_path
        self.model = None
        self.feature_names = []
        
        self.ta = TechnicalAnalysis()
        self.ve = ValueEvaluation()
        
        self.factor_weights = {
            'technical': 0.35,
            'value': 0.30,
            'sentiment': 0.20,
            'macro': 0.15
        }
        
        os.makedirs(model_path, exist_ok=True)
    
    def build_features(self, code: str, data_acq: DataAcquisition) -> Optional[np.ndarray]:
        """
        构建预测特征
        
        参数:
            code: 股票代码
            data_acq: 数据获取器
            
        返回:
            特征数组
        """
        features = {}
        
        realtime = data_acq.get_stock_realtime(code)
        if not realtime:
            return None
        
        features['price'] = realtime['latest_price']
        features['change_pct'] = realtime['change_pct']
        features['turnover_rate'] = realtime['turnover_rate']
        features['pe_ratio'] = realtime['pe_ratio']
        features['pb_ratio'] = realtime['pb_ratio']
        
        hist_df = data_acq.get_stock_history(code, days=120)
        if hist_df is None or len(hist_df) < 60:
            return None
        
        hist_df = self.ta.calculate_all_indicators(hist_df)
        tech_score = self.ta.get_technical_score(hist_df)
        
        features['ma5'] = hist_df['MA5'].iloc[-1] if 'MA5' in hist_df.columns else 0
        features['ma10'] = hist_df['MA10'].iloc[-1] if 'MA10' in hist_df.columns else 0
        features['ma20'] = hist_df['MA20'].iloc[-1] if 'MA20' in hist_df.columns else 0
        features['dif'] = hist_df['DIF'].iloc[-1] if 'DIF' in hist_df.columns else 0
        features['dea'] = hist_df['DEA'].iloc[-1] if 'DEA' in hist_df.columns else 0
        features['macd'] = hist_df['MACD'].iloc[-1] if 'MACD' in hist_df.columns else 0
        features['k'] = hist_df['K'].iloc[-1] if 'K' in hist_df.columns else 50
        features['d'] = hist_df['D'].iloc[-1] if 'D' in hist_df.columns else 50
        features['rsi6'] = hist_df['RSI6'].iloc[-1] if 'RSI6' in hist_df.columns else 50
        features['tech_score'] = tech_score['score']
        
        financial = data_acq.get_stock_financial_indicator(code)
        if financial:
            financial_data = {
                'pe_ratio': realtime['pe_ratio'],
                'pb_ratio': realtime['pb_ratio'],
                'roe': financial.get('roe', 0),
                'dividend_yield': 0,
                'revenue_growth': 0,
                'profit_growth': 0
            }
            value_result = self.ve.get_value_score(financial_data, realtime['latest_price'])
            features['value_score'] = value_result['score']
            features['roe'] = financial.get('roe', 0)
        else:
            features['value_score'] = 50
            features['roe'] = 0
        
        features['sentiment_score'] = 50
        features['macro_score'] = 50
        
        features['volume_ratio'] = realtime.get('volume_ratio', 1)
        features['amplitude'] = realtime.get('amplitude', 0)
        
        if len(hist_df) >= 20:
            recent_high = hist_df['close' if 'close' in hist_df.columns else '收盘'].tail(20).max()
            recent_low = hist_df['close' if 'close' in hist_df.columns else '收盘'].tail(20).min()
            features['price_position'] = (realtime['latest_price'] - recent_low) / (recent_high - recent_low + 1e-10) * 100
        else:
            features['price_position'] = 50
        
        self.feature_names = list(features.keys())
        return np.array(list(features.values())).reshape(1, -1)
    
    def predict(self, code: str, data_acq: DataAcquisition = None) -> Optional[PredictionResult]:
        """
        预测股票次日涨跌
        
        参数:
            code: 股票代码
            data_acq: 数据获取器
            
        返回:
            预测结果
        """
        if data_acq is None:
            data_acq = DataAcquisition()
        
        realtime = data_acq.get_stock_realtime(code)
        if not realtime:
            print(f"[错误] 无法获取股票 {code} 的实时数据")
            return None
        
        hist_df = data_acq.get_stock_history(code, days=120)
        if hist_df is None or len(hist_df) < 60:
            print(f"[错误] 股票 {code} 历史数据不足")
            return None
        
        hist_df = self.ta.calculate_all_indicators(hist_df)
        tech_result = self.ta.get_technical_score(hist_df)
        
        financial = data_acq.get_stock_financial_indicator(code)
        if financial:
            financial_data = {
                'pe_ratio': realtime['pe_ratio'],
                'pb_ratio': realtime['pb_ratio'],
                'roe': financial.get('roe', 0),
                'dividend_yield': 0,
                'revenue_growth': 0,
                'profit_growth': 0
            }
            value_result = self.ve.get_value_score(financial_data, realtime['latest_price'])
        else:
            value_result = {'score': 50, 'details': []}
        
        sentiment_score = self._calculate_sentiment_score(code, realtime)
        macro_score = self._calculate_macro_score(data_acq)
        
        total_score = (
            tech_result['score'] * self.factor_weights['technical'] +
            value_result['score'] * self.factor_weights['value'] +
            sentiment_score * self.factor_weights['sentiment'] +
            macro_score * self.factor_weights['macro']
        )
        
        if total_score >= 60:
            direction = '上涨'
            probability = min(0.95, 0.5 + (total_score - 50) / 100)
        elif total_score >= 45:
            direction = '震荡'
            probability = 0.5
        else:
            direction = '下跌'
            probability = max(0.05, 0.5 - (50 - total_score) / 100)
        
        if direction == '上涨':
            probability = min(0.95, probability)
        elif direction == '下跌':
            probability = max(0.05, 1 - probability)
        
        if probability >= 0.7 or probability <= 0.3:
            confidence = '高'
        elif probability >= 0.6 or probability <= 0.4:
            confidence = '中'
        else:
            confidence = '低'
        
        key_signals = []
        for signal in tech_result.get('buy_signals', [])[:3]:
            key_signals.append(f"[买入]{signal['type']}")
        for signal in tech_result.get('sell_signals', [])[:3]:
            key_signals.append(f"[卖出]{signal['type']}")
        
        if value_result.get('score', 50) >= 70:
            key_signals.append('价值面良好')
        elif value_result.get('score', 50) < 40:
            key_signals.append('价值面偏弱')
        
        risk_warning = self._generate_risk_warning(realtime, tech_result, value_result)
        
        return PredictionResult(
            code=code,
            name=realtime['name'],
            prediction_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            direction=direction,
            probability=round(probability, 2),
            confidence=confidence,
            technical_score=round(tech_result['score'], 1),
            value_score=round(value_result['score'], 1),
            sentiment_score=round(sentiment_score, 1),
            macro_score=round(macro_score, 1),
            total_score=round(total_score, 1),
            key_signals=key_signals[:5],
            risk_warning=risk_warning
        )
    
    def _calculate_sentiment_score(self, code: str, realtime: Dict) -> float:
        """
        计算情绪因子得分
        
        参数:
            code: 股票代码
            realtime: 实时行情数据
            
        返回:
            情绪得分
        """
        score = 50
        
        change_pct = realtime.get('change_pct', 0)
        if change_pct > 5:
            score += 20
        elif change_pct > 2:
            score += 10
        elif change_pct < -5:
            score -= 20
        elif change_pct < -2:
            score -= 10
        
        turnover = realtime.get('turnover_rate', 0)
        if turnover > 10:
            score += 10
        elif turnover > 5:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_macro_score(self, data_acq: DataAcquisition) -> float:
        """
        计算宏观因子得分
        
        参数:
            data_acq: 数据获取器
            
        返回:
            宏观得分
        """
        score = 50
        
        try:
            global_data = data_acq.get_global_market_data()
            
            if global_data.get('us_dow_jones'):
                score += 5
            
            if global_data.get('us_nasdaq'):
                score += 5
        except:
            pass
        
        return score
    
    def _generate_risk_warning(self, realtime: Dict, tech_result: Dict, 
                               value_result: Dict) -> str:
        """
        生成风险提示
        
        参数:
            realtime: 实时行情
            tech_result: 技术分析结果
            value_result: 价值评估结果
            
        返回:
            风险提示文本
        """
        warnings = []
        
        if realtime.get('pe_ratio', 0) > 50:
            warnings.append('PE估值偏高')
        
        if tech_result.get('score', 50) < 30:
            warnings.append('技术面弱势')
        
        if len(tech_result.get('sell_signals', [])) > 2:
            warnings.append('存在多个卖出信号')
        
        if value_result.get('score', 50) < 40:
            warnings.append('基本面偏弱')
        
        if not warnings:
            warnings.append('投资有风险，决策需谨慎')
        
        return '；'.join(warnings)
    
    def predict_batch(self, codes: List[str], 
                      data_acq: DataAcquisition = None) -> List[PredictionResult]:
        """
        批量预测股票
        
        参数:
            codes: 股票代码列表
            data_acq: 数据获取器
            
        返回:
            预测结果列表
        """
        if data_acq is None:
            data_acq = DataAcquisition()
        
        results = []
        for code in codes:
            print(f"\n正在预测 {code}...")
            result = self.predict(code, data_acq)
            if result:
                results.append(result)
        
        return results
    
    def save_prediction(self, result: PredictionResult, output_dir: str = './reports'):
        """
        保存预测结果
        
        参数:
            result: 预测结果
            output_dir: 输出目录
        """
        os.makedirs(output_dir, exist_ok=True)
        
        result_dict = {
            'code': result.code,
            'name': result.name,
            'prediction_time': result.prediction_time,
            'direction': result.direction,
            'probability': result.probability,
            'confidence': result.confidence,
            'scores': {
                'technical': result.technical_score,
                'value': result.value_score,
                'sentiment': result.sentiment_score,
                'macro': result.macro_score,
                'total': result.total_score
            },
            'key_signals': result.key_signals,
            'risk_warning': result.risk_warning
        }
        
        filename = f"prediction_{result.code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        
        print(f"[保存] 预测结果已保存到 {filepath}")


def format_prediction_report(result: PredictionResult) -> str:
    """
    格式化预测报告
    
    参数:
        result: 预测结果
        
    返回:
        格式化的报告文本
    """
    report = []
    report.append("=" * 60)
    report.append(f"股票预测报告 - {result.name}({result.code})")
    report.append("=" * 60)
    report.append(f"预测时间: {result.prediction_time}")
    report.append("")
    report.append("【预测结果】")
    report.append(f"  预测方向: {result.direction}")
    report.append(f"  概率: {result.probability * 100:.1f}%")
    report.append(f"  置信度: {result.confidence}")
    report.append("")
    report.append("【因子得分】")
    report.append(f"  技术面: {result.technical_score}")
    report.append(f"  价值面: {result.value_score}")
    report.append(f"  情绪面: {result.sentiment_score}")
    report.append(f"  宏观面: {result.macro_score}")
    report.append(f"  综合得分: {result.total_score}")
    report.append("")
    report.append("【关键信号】")
    for signal in result.key_signals:
        report.append(f"  - {signal}")
    report.append("")
    report.append("【风险提示】")
    report.append(f"  {result.risk_warning}")
    report.append("=" * 60)
    
    return "\n".join(report)


if __name__ == "__main__":
    print("=" * 60)
    print("测试预测模型模块")
    print("=" * 60)
    
    model = PredictionModel()
    data_acq = DataAcquisition()
    
    test_codes = ['000001', '600519']
    
    for code in test_codes:
        print(f"\n预测股票 {code}:")
        result = model.predict(code, data_acq)
        
        if result:
            print(format_prediction_report(result))
            model.save_prediction(result)
