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
        self.feature_columns = []
        self.model_trained = False
        
        # 初始化分析器
        self.ta = TechnicalAnalysis()
        self.ve = ValueEvaluation()
        
        # 模型参数
        self.model_params = {
            'n_estimators': 100,
            'max_depth': 5,
            'learning_rate': 0.1,
            'random_state': 42
        }
        
        # 创建模型目录
        os.makedirs(model_path, exist_ok=True)
    
    def prepare_features(self, stock_code: str, data_acquisition: DataAcquisition) -> pd.DataFrame:
        """
        准备特征数据
        
        参数:
            stock_code: 股票代码
            data_acquisition: 数据获取器
            
        返回:
            特征DataFrame
        """
        try:
            # 获取历史数据
            history_df = data_acquisition.get_stock_history(stock_code, days=60)
            
            if history_df.empty or len(history_df) < 30:
                return pd.DataFrame()
            
            # 计算技术指标
            history_df = self.ta.calculate_all_indicators(history_df)
            
            # 计算特征
            features = self._calculate_features(history_df)
            
            return features
            
        except Exception as e:
            print(f"[错误] 准备特征失败 {stock_code}: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算特征
        
        参数:
            df: 历史数据DataFrame
            
        返回:
            特征DataFrame
        """
        features = pd.DataFrame()
        
        # 价格特征
        features['price_change'] = df['收盘'].pct_change()
        features['price_volatility'] = df['收盘'].rolling(window=20).std()
        features['price_momentum'] = df['收盘'].pct_change(periods=5)
        
        # 移动平均线特征
        for period in [5, 10, 20]:
            features[f'ma_{period}'] = df[f'MA{period}']
            features[f'ma_ratio_{period}'] = df['收盘'] / df[f'MA{period}']
        
        # MACD特征
        features['macd'] = df['MACD']
        features['macd_signal'] = df['MACD_signal']
        features['macd_histogram'] = df['MACD_histogram']
        
        # RSI特征
        for period in [6, 12, 24]:
            features[f'rsi_{period}'] = df[f'RSI{period}']
        
        # KDJ特征
        features['kdj_k'] = df['K']
        features['kdj_d'] = df['D']
        features['kdj_j'] = df['J']
        
        # 布林带特征
        features['bb_position'] = (df['收盘'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        # 成交量特征
        features['volume_change'] = df['成交量'].pct_change()
        features['volume_ratio'] = df['成交量'] / df['成交量'].rolling(window=20).mean()
        
        # 价格位置特征
        features['price_position'] = (df['收盘'] - df['最低'].rolling(window=20).min()) / \
                                   (df['最高'].rolling(window=20).max() - df['最低'].rolling(window=20).min())
        
        # 波动率特征
        features['atr'] = self._calculate_atr(df)
        
        # 填充缺失值
        features = features.fillna(method='ffill').fillna(0)
        
        return features
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算平均真实波幅
        
        参数:
            df: 历史数据DataFrame
            period: 计算周期
            
        返回:
            ATR序列
        """
        high = df['最高']
        low = df['最低']
        close = df['收盘']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def train_model(self, training_data: List[Dict]) -> bool:
        """
        训练模型
        
        参数:
            training_data: 训练数据列表
            
        返回:
            训练是否成功
        """
        try:
            # 准备训练集
            X_train = []
            y_train = []
            
            for data in training_data:
                features = data['features']
                target = data['target']
                
                if not features.empty:
                    X_train.append(features.values.flatten())
                    y_train.append(target)
            
            if not X_train or not y_train:
                print("[错误] 训练数据为空")
                return False
            
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            # 选择模型
            if HAS_XGBOOST:
                self.model = XGBClassifier(**self.model_params)
            else:
                self.model = RandomForestClassifier(**self.model_params)
            
            # 训练模型
            self.model.fit(X_train, y_train)
            self.model_trained = True
            
            # 保存模型
            self._save_model()
            
            print("[成功] 模型训练完成")
            return True
            
        except Exception as e:
            print(f"[错误] 模型训练失败: {str(e)}")
            return False
    
    def predict(self, stock_code: str, data_acquisition: DataAcquisition) -> Optional[PredictionResult]:
        """
        预测股票涨跌
        
        参数:
            stock_code: 股票代码
            data_acquisition: 数据获取器
            
        返回:
            预测结果
        """
        if not self.model_trained:
            print("[警告] 模型未训练，使用简单规则预测")
            return self._simple_predict(stock_code, data_acquisition)
        
        try:
            # 准备特征
            features = self.prepare_features(stock_code, data_acquisition)
            
            if features.empty:
                return None
            
            # 预测
            prediction = self.model.predict([features.values.flatten()])[0]
            probability = self.model.predict_proba([features.values.flatten()])[0]
            
            # 计算置信度
            confidence = self._calculate_confidence(features, probability)
            
            # 生成信号
            signals = self._generate_signals(features)
            
            # 风险警告
            risk_warning = self._assess_risk(features)
            
            return PredictionResult(
                code=stock_code,
                name=data_acquisition.get_stock_history(stock_code, days=1).iloc[-1]['收盘'] if not features.empty else '',
                prediction_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                direction='上涨' if prediction == 1 else '下跌',
                probability=probability[1] if prediction == 1 else probability[0],
                confidence=confidence,
                technical_score=self._calculate_technical_score(features),
                value_score=50,  # 简化处理
                sentiment_score=50,  # 简化处理
                macro_score=50,  # 简化处理
                total_score=self._calculate_total_score(features, prediction),
                key_signals=signals,
                risk_warning=risk_warning
            )
            
        except Exception as e:
            print(f"[错误] 预测失败 {stock_code}: {str(e)}")
            return None
    
    def _simple_predict(self, stock_code: str, data_acquisition: DataAcquisition) -> Optional[PredictionResult]:
        """
        简单规则预测
        
        参数:
            stock_code: 股票代码
            data_acquisition: 数据获取器
            
        返回:
            预测结果
        """
        try:
            # 获取实时数据
            realtime_data = data_acquisition.get_batch_realtime([stock_code])
            
            if stock_code not in realtime_data:
                return None
            
            data = realtime_data[stock_code]
            
            # 简单规则
            change_pct = data['change_pct']
            if change_pct > 2:
                direction = '上涨'
                probability = 0.7
            elif change_pct < -2:
                direction = '下跌'
                probability = 0.7
            else:
                direction = '震荡'
                probability = 0.5
            
            return PredictionResult(
                code=stock_code,
                name=data['name'],
                prediction_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                direction=direction,
                probability=probability,
                confidence='中等',
                technical_score=50,
                value_score=50,
                sentiment_score=50,
                macro_score=50,
                total_score=50,
                key_signals=[f'当前涨跌幅: {change_pct:.2f}%'],
                risk_warning='中等风险'
            )
            
        except Exception as e:
            print(f"[错误] 简单预测失败 {stock_code}: {str(e)}")
            return None
    
    def _calculate_confidence(self, features: pd.DataFrame, probability: np.ndarray) -> str:
        """
        计算置信度
        
        参数:
            features: 特征数据
            probability: 预测概率
            
        返回:
            置信度等级
        """
        max_prob = max(probability)
        
        if max_prob >= 0.8:
            return '高'
        elif max_prob >= 0.6:
            return '中等'
        else:
            return '低'
    
    def _generate_signals(self, features: pd.DataFrame) -> List[str]:
        """
        生成交易信号
        
        参数:
            features: 特征数据
            
        返回:
            信号列表
        """
        signals = []
        
        # MACD信号
        if features['macd'].iloc[-1] > features['macd_signal'].iloc[-1]:
            signals.append('MACD金叉')
        
        # RSI信号
        if features['rsi_6'].iloc[-1] > 70:
            signals.append('RSI超买')
        elif features['rsi_6'].iloc[-1] < 30:
            signals.append('RSI超卖')
        
        # 布林带信号
        bb_position = features['bb_position'].iloc[-1]
        if bb_position > 0.8:
            signals.append('接近上轨')
        elif bb_position < 0.2:
            signals.append('接近下轨')
        
        return signals
    
    def _assess_risk(self, features: pd.DataFrame) -> str:
        """
        评估风险
        
        参数:
            features: 特征数据
            
        返回:
        风险等级
        """
        volatility = features['price_volatility'].iloc[-1]
        volume_ratio = features['volume_ratio'].iloc[-1]
        
        if volatility > 0.05 or volume_ratio > 2:
            return '高风险'
        elif volatility > 0.02 or volume_ratio > 1.5:
            return '中等风险'
        else:
            return '低风险'
    
    def _calculate_technical_score(self, features: pd.DataFrame) -> float:
        """
        计算技术评分
        
        参数:
            features: 特征数据
            
        返回:
            技术评分
        """
        # 简化的技术评分计算
        score = 50
        
        # 趋势评分
        if features['ma_ratio_5'].iloc[-1] > 1:
            score += 10
        if features['ma_ratio_10'].iloc[-1] > 1:
            score += 10
        
        # 动量评分
        if features['price_momentum'].iloc[-1] > 0:
            score += 10
        
        # RSI评分
        rsi = features['rsi_6'].iloc[-1]
        if 30 < rsi < 70:
            score += 10
        
        return min(100, max(0, score))
    
    def _calculate_total_score(self, features: pd.DataFrame, prediction: int) -> float:
        """
        计算总分
        
        参数:
            features: 特征数据
            prediction: 预测结果
            
        返回:
            总分
        """
        technical_score = self._calculate_technical_score(features)
        
        # 简化的总分计算
        total_score = technical_score * 0.6 + 50 * 0.4
        
        if prediction == 1:
            total_score += 10
        
        return min(100, max(0, total_score))
    
    def _save_model(self):
        """保存模型"""
        if self.model:
            model_file = os.path.join(self.model_path, 'prediction_model.json')
            model_data = {
                'model_type': type(self.model).__name__,
                'model_params': self.model_params,
                'feature_columns': self.feature_columns,
                'trained': self.model_trained
            }
            
            with open(model_file, 'w') as f:
                json.dump(model_data, f, indent=2)
    
    def load_model(self) -> bool:
        """加载模型"""
        model_file = os.path.join(self.model_path, 'prediction_model.json')
        
        if os.path.exists(model_file):
            try:
                with open(model_file, 'r') as f:
                    model_data = json.load(f)
                
                self.model_params = model_data.get('model_params', {})
                self.feature_columns = model_data.get('feature_columns', [])
                self.model_trained = model_data.get('trained', False)
                
                print("[成功] 模型加载完成")
                return True
                
            except Exception as e:
                print(f"[错误] 模型加载失败: {str(e)}")
                return False
        
        return False
    
    def save_prediction(self, result: PredictionResult, report_dir: str):
        """
        保存预测结果
        
        参数:
            result: 预测结果
            report_dir: 报告目录
        """
        os.makedirs(report_dir, exist_ok=True)
        
        prediction_file = os.path.join(report_dir, f'prediction_{result.code}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        prediction_data = {
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
            'signals': result.key_signals,
            'risk_warning': result.risk_warning
        }
        
        with open(prediction_file, 'w', encoding='utf-8') as f:
            json.dump(prediction_data, f, ensure_ascii=False, indent=2)
        
        print(f"[保存] 预测结果已保存到 {prediction_file}")
    
    def format_prediction_report(self, predictions: List[PredictionResult]) -> str:
        """
        格式化预测报告
        
        参数:
            predictions: 预测结果列表
            
        返回:
            报告文本
        """
        if not predictions:
            return "无预测结果"
        
        report = []
        report.append("=" * 80)
        report.append("股票预测报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # 统计信息
        up_count = len([p for p in predictions if p.direction == '上涨'])
        down_count = len([p for p in predictions if p.direction == '下跌'])
        neutral_count = len([p for p in predictions if p.direction == '震荡'])
        
        report.append(f"预测上涨: {up_count}只")
        report.append(f"预测下跌: {down_count}只")
        report.append(f"预测震荡: {neutral_count}只")
        report.append("")
        
        # 详细结果
        for prediction in sorted(predictions, key=lambda x: x.probability, reverse=True):
            report.append(f"{prediction.code} {prediction.name}")
            report.append(f"  预测方向: {prediction.direction}")
            report.append(f"  概率: {prediction.probability*100:.1f}%")
            report.append(f"  置信度: {prediction.confidence}")
            report.append(f"  总分: {prediction.total_score:.1f}")
            report.append(f"  信号: {', '.join(prediction.key_signals)}")
            report.append(f"  风险: {prediction.risk_warning}")
            report.append("")
        
        report.append("=" * 80)
        report.append("风险提示: 本报告仅供参考，不构成投资建议。投资有风险，决策需谨慎。")
        report.append("=" * 80)
        
        return "\n".join(report)