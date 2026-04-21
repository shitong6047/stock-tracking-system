"""
预测模型模块 v2.0
功能：构建多因子预测模型、历史回测验证、集成预测算法
包含：BacktestEngine回测引擎、EnsemblePredictor集成预测器、历史准确率追踪
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
from collections import deque

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


@dataclass
class BacktestResult:
    """回测结果数据类"""
    stock_code: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    total_predictions: int
    correct_predictions: int
    up_predictions: int
    down_predictions: int
    neutral_predictions: int
    up_hit_rate: float
    down_hit_rate: float
    avg_confidence: float
    backtest_period: Tuple[str, str]
    details: List[Dict] = field(default_factory=list)


@dataclass
class EnsemblePredictionResult:
    """集成预测结果数据类（增强版）"""
    code: str
    name: str
    prediction_time: str
    direction: str
    probability: float
    confidence: str
    expected_return_min: float
    expected_return_max: float
    key_signals: List[str]
    model_weights: Dict[str, float]
    model_scores: Dict[str, float]
    technical_score: float
    fundamental_score: float
    market_sentiment_score: float
    pattern_match_score: float
    stop_loss: float
    take_profit: float
    position_size: str
    risk_level: str
    rating: str


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


class BacktestEngine:
    """
    历史回测引擎
    
    使用滑动窗口方法验证预测模型的准确性：
    - 训练窗口：使用最近 lookback_days 天的数据训练模型
    - 验证窗口：在最近 validation_days 天的数据上测试模型表现
    - 输出指标：准确率、精确率、召回率、F1分数等
    """
    
    def __init__(self, lookback_days: int = 60, validation_days: int = 20):
        """
        初始化回测引擎
        
        参数:
            lookback_days: 训练数据回看天数（默认60天）
            validation_days: 验证数据天数（默认20天）
        """
        if not isinstance(lookback_days, int) or lookback_days <= 0:
            raise ValueError("lookback_days 必须是正整数")
        if not isinstance(validation_days, int) or validation_days <= 0:
            raise ValueError("validation_days 必须是正整数")
            
        self.lookback_days = lookback_days
        self.validation_days = validation_days
        self.ta = TechnicalAnalysis()
        self.prediction_model = PredictionModel()
        
        self.historical_predictions = deque(maxlen=100)
        self.accuracy_history = {}
    
    def run_backtest(self, stock_code: str, history_data: pd.DataFrame) -> BacktestResult:
        """
        执行滑动窗口回测
        
        参数:
            stock_code: 股票代码
            history_data: 历史行情数据（必须包含日期、收盘、最高、最低、成交量列）
            
        返回:
            BacktestResult 回测结果对象
        """
        if history_data is None or history_data.empty:
            raise ValueError("历史数据不能为空")
            
        required_columns = ['日期', '收盘', '最高', '最低', '成交量']
        missing_cols = [col for col in required_cols if col not in history_data.columns]
        if missing_cols:
            raise ValueError(f"历史数据缺少必要列: {missing_cols}")
            
        if len(history_data) < self.lookback_days + self.validation_days:
            raise ValueError(f"数据量不足，需要至少 {self.lookback_days + self.validation_days} 天数据，当前只有 {len(history_data)} 天")
        
        try:
            predictions = []
            actuals = []
            
            total_test_days = len(history_data) - self.lookback_days
            
            for i in range(max(0, total_test_days - self.validation_days), total_test_days):
                train_data = history_data.iloc[i:i + self.lookback_days].copy()
                test_point = history_data.iloc[i + self.lookback_days]
                
                if train_data.empty or test_point is None:
                    continue
                    
                train_data = self.ta.calculate_all_indicators(train_data)
                
                prediction = self._predict_single_day(train_data, test_point)
                actual_direction = self._determine_actual_direction(
                    history_data, 
                    i + self.lookback_days
                )
                
                if prediction and actual_direction:
                    predictions.append(prediction)
                    actuals.append(actual_direction)
                    
                    self.historical_predictions.append({
                        'date': str(test_point['日期']) if '日期' in test_point.index else str(test_point.name),
                        'stock_code': stock_code,
                        'predicted': prediction['direction'],
                        'actual': actual_direction,
                        'probability': prediction.get('probability', 0),
                        'confidence': prediction.get('confidence', '中')
                    })
            
            if not predictions:
                return BacktestResult(
                    stock_code=stock_code,
                    accuracy=0.0,
                    precision=0.0,
                    recall=0.0,
                    f1_score=0.0,
                    total_predictions=0,
                    correct_predictions=0,
                    up_predictions=0,
                    down_predictions=0,
                    neutral_predictions=0,
                    up_hit_rate=0.0,
                    down_hit_rate=0.0,
                    avg_confidence=0.0,
                    backtest_period=('N/A', 'N/A')
                )
            
            metrics = self._calculate_metrics(predictions, actuals)
            
            start_date = str(history_data.iloc[0]['日期']) if '日期' in history_data.columns else 'N/A'
            end_date = str(history_data.iloc[-1]['日期']) if '日期' in history_data.columns else 'N/A'
            
            result = BacktestResult(
                stock_code=stock_code,
                accuracy=metrics['accuracy'],
                precision=metrics['precision'],
                recall=metrics['recall'],
                f1_score=metrics['f1_score'],
                total_predictions=len(predictions),
                correct_predictions=metrics['correct_count'],
                up_predictions=metrics['up_count'],
                down_predictions=metrics['down_count'],
                neutral_predictions=metrics['neutral_count'],
                up_hit_rate=metrics['up_hit_rate'],
                down_hit_rate=metrics['down_hit_rate'],
                avg_confidence=metrics['avg_confidence'],
                backtest_period=(start_date, end_date),
                details=predictions
            )
            
            self.accuracy_history[stock_code] = {
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **metrics
            }
            
            print(f"[回测完成] {stock_code}: 准确率={metrics['accuracy']:.1%}, "
                  f"F1={metrics['f1_score']:.3f}, 样本数={len(predictions)}")
            
            return result
            
        except Exception as e:
            print(f"[错误] 回测执行失败 {stock_code}: {str(e)}")
            raise
    
    def _predict_single_day(self, train_data: pd.DataFrame, 
                           test_point: pd.Series) -> Optional[Dict]:
        """基于训练数据预测单日方向"""
        try:
            latest = train_data.iloc[-1]
            
            signals = []
            score = 50
            
            ma5 = latest.get('MA5', 0)
            ma20 = latest.get('MA20', 0)
            close = latest.get('收盘', 0)
            
            if pd.notna(ma5) and pd.notna(ma20) and ma20 > 0:
                if close > ma5 > ma20:
                    score += 15
                    signals.append('均线多头排列')
                elif close < ma5 < ma20:
                    score -= 15
                    signals.append('均线空头排列')
                    
            macd = latest.get('MACD', 0)
            macd_signal = latest.get('MACD_signal', 0)
            if pd.notna(macd) and pd.notna(macd_signal):
                if macd > macd_signal:
                    score += 12
                    signals.append('MACD多头')
                else:
                    score -= 10
                    signals.append('MACD空头')
                    
            rsi6 = latest.get('RSI6', 50)
            if pd.notna(rsi6):
                if rsi6 < 30:
                    score += 10
                    signals.append('RSI超卖')
                elif rsi6 > 70:
                    score -= 10
                    signals.append('RSI超买')
                    
            volume_ratio = 0
            if '成交量' in train_data.columns and len(train_data) >= 20:
                avg_vol = train_data['成交量'].iloc[-20:].mean()
                current_vol = latest.get('成交量', 0)
                if avg_vol > 0:
                    volume_ratio = current_vol / avg_vol
                    if volume_ratio > 1.5:
                        score += 8 if score > 50 else -8
                        signals.append('放量')
                        
            bb_position = latest.get('BB_middle', 0)
            bb_upper = latest.get('BB_upper', 0)
            bb_lower = latest.get('BB_lower', 0)
            if pd.notna(bb_upper) and pd.notna(bb_lower) and (bb_upper - bb_lower) > 0:
                position = (close - bb_lower) / (bb_upper - bb_lower)
                if position < 0.2:
                    score += 8
                    signals.append('接近下轨')
                elif position > 0.8:
                    score -= 8
                    signals.append('接近上轨')
            
            score = max(10, min(90, score))
            
            if score >= 60:
                direction = '上涨'
                probability = min(0.85, 0.5 + (score - 50) / 100)
            elif score <= 40:
                direction = '下跌'
                probability = min(0.85, 0.5 + (50 - score) / 100)
            else:
                direction = '震荡'
                probability = 0.5
                
            if probability >= 0.75:
                confidence = '高'
            elif probability >= 0.55:
                confidence = '中'
            else:
                confidence = '低'
            
            return {
                'direction': direction,
                'probability': probability,
                'confidence': confidence,
                'score': score,
                'signals': signals[:5],
                'volume_ratio': volume_ratio
            }
            
        except Exception as e:
            print(f"[警告] 单日预测失败: {str(e)}")
            return None
    
    def _determine_actual_direction(self, data: pd.DataFrame, index: int) -> Optional[str]:
        """确定实际涨跌方向"""
        try:
            if index >= len(data):
                return None
                
            current_close = data.iloc[index]['收盘']
            
            if index + 1 < len(data):
                next_close = data.iloc[index + 1]['收盘']
            else:
                return None
            
            if pd.isna(current_close) or pd.isna(next_close):
                return None
                
            change_pct = (next_close - current_close) / current_close * 100
            
            if change_pct > 0.3:
                return '上涨'
            elif change_pct < -0.3:
                return '下跌'
            else:
                return '震荡'
                
        except Exception as e:
            print(f"[警告] 确定实际方向失败: {str(e)}")
            return None
    
    def _calculate_metrics(self, predictions: List[Dict], actuals: List[str]) -> Dict:
        """计算回测评估指标"""
        if not predictions or not actuals:
            return {
                'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0,
                'f1_score': 0.0, 'correct_count': 0, 'up_count': 0,
                'down_count': 0, 'neutral_count': 0,
                'up_hit_rate': 0.0, 'down_hit_rate': 0.0,
                'avg_confidence': 0.0
            }
        
        correct_count = sum(1 for p, a in zip(predictions, actuals) if p['direction'] == a)
        
        up_preds = [(p, a) for p, a in zip(predictions, actuals) if p['direction'] == '上涨']
        down_preds = [(p, a) for p, a in zip(predictions, actuals) if p['direction'] == '下跌']
        neutral_preds = [p for p in predictions if p['direction'] == '震荡']
        
        up_hits = sum(1 for p, a in up_preds if a == '上涨') if up_preds else 0
        down_hits = sum(1 for p, a in down_preds if a == '下跌') if down_preds else 0
        
        tp = sum(1 for p, a in zip(predictions, actuals) if p['direction'] == '上涨' and a == '上涨')
        fp = sum(1 for p, a in zip(predictions, actuals) if p['direction'] == '上涨' and a != '上涨')
        fn = sum(1 for p, a in zip(predictions, actuals) if p['direction'] != '上涨' and a == '上涨')
        
        accuracy = correct_count / len(predictions) if predictions else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        confidences = [p.get('probability', 0.5) for p in predictions]
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        return {
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'correct_count': correct_count,
            'up_count': len(up_preds),
            'down_count': len(down_preds),
            'neutral_count': len(neutral_preds),
            'up_hit_rate': round(up_hits / len(up_preds), 4) if up_preds else 0.0,
            'down_hit_rate': round(down_hits / len(down_preds), 4) if down_preds else 0.0,
            'avg_confidence': round(avg_confidence, 4)
        }
    
    def get_accuracy_report(self, stock_code: str, days: int = 20) -> Dict:
        """获取历史准确率报告"""
        recent_predictions = [p for p in self.historical_predictions if p['stock_code'] == stock_code][-days:]
        
        if not recent_predictions:
            return {
                'stock_code': stock_code,
                'period': f'最近{days}天',
                'total_predictions': 0,
                'accuracy': 0.0,
                'up_accuracy': 0.0,
                'down_accuracy': 0.0,
                'confidence_distribution': {'高': 0, '中': 0, '低': 0},
                'message': '暂无历史预测记录'
            }
        
        correct = sum(1 for p in recent_predictions if p['predicted'] == p['actual'])
        
        up_preds = [p for p in recent_predictions if p['predicted'] == '上涨']
        down_preds = [p for p in recent_predictions if p['predicted'] == '下跌']
        
        up_correct = sum(1 for p in up_preds if p['actual'] == '上涨') if up_preds else 0
        down_correct = sum(1 for p in down_preds if p['actual'] == '下跌') if down_preds else 0
        
        confidence_dist = {'高': 0, '中': 0, '低': 0}
        for p in recent_predictions:
            conf = p.get('confidence', '中')
            if conf in confidence_dist:
                confidence_dist[conf] += 1
        
        return {
            'stock_code': stock_code,
            'period': f'最近{days}天',
            'total_predictions': len(recent_predictions),
            'correct_predictions': correct,
            'accuracy': round(correct / len(recent_predictions), 4) if recent_predictions else 0.0,
            'up_total': len(up_preds),
            'up_correct': up_correct,
            'up_accuracy': round(up_correct / len(up_preds), 4) if up_preds else 0.0,
            'down_total': len(down_preds),
            'down_correct': down_correct,
            'down_accuracy': round(down_correct / len(down_preds), 4) if down_preds else 0.0,
            'confidence_distribution': confidence_dist,
            'avg_probability': round(np.mean([p['probability'] for p in recent_predictions]), 4),
            'model_reliability': self._assess_model_reliability(correct / len(recent_predictions) if recent_predictions else 0)
        }
    
    def _assess_model_reliability(self, accuracy: float) -> str:
        """评估模型可靠性"""
        if accuracy >= 0.70:
            return '高可靠'
        elif accuracy >= 0.55:
            return '中等可靠'
        elif accuracy >= 0.45:
            return '低可靠'
        else:
            return '需改进'


class EnsemblePredictor:
    """
    多模型集成预测器
    
    整合4个子模型的预测结果：
    - 技术分析预测 (40%权重)：基于技术指标信号判断
    - 基本面预测 (30%权重)：基于估值和业绩判断
    - 市场情绪预测 (20%权重)：基于大盘和板块趋势
    - 历史模式匹配 (10%权重)：基于相似K线形态
    """
    
    def __init__(self):
        """初始化集成预测器"""
        self.ta = TechnicalAnalysis()
        self.ve = ValueEvaluation()
        self.backtest_engine = BacktestEngine()
        
        self.model_weights = {
            'technical': 0.40,
            'fundamental': 0.30,
            'market_sentiment': 0.20,
            'pattern_match': 0.10
        }
        
        self.confidence_thresholds = {
            'high': 0.72,
            'medium': 0.58,
            'low': 0.45
        }
    
    def predict(self, stock_code: str, technical_data: Dict, 
               fundamental_data: Dict, market_data: Dict) -> EnsemblePredictionResult:
        """
        执行集成预测
        
        参数:
            stock_code: 股票代码
            technical_data: 技术面数据字典
            fundamental_data: 基本面数据字典
            market_data: 市场数据字典（大盘指数、板块数据等）
            
        返回:
            EnsemblePredictionResult 集成预测结果
        """
        technical_result = self._technical_prediction(technical_data, stock_code)
        fundamental_result = self._fundamental_prediction(fundamental_data, stock_code)
        sentiment_result = self._market_sentiment_prediction(market_data)
        pattern_result = self._pattern_match_prediction(technical_data)
        
        ensemble_score = (
            technical_result['score'] * self.model_weights['technical'] +
            fundamental_result['score'] * self.model_weights['fundamental'] +
            sentiment_result['score'] * self.model_weights['market_sentiment'] +
            pattern_result['score'] * self.model_weights['pattern_match']
        )
        
        direction, probability = self._determine_direction_and_probability(
            ensemble_score, technical_result, fundamental_result, sentiment_result, pattern_result
        )
        
        confidence = self._calculate_confidence(probability, technical_result, fundamental_result)
        
        key_signals = self._aggregate_key_signals([
            technical_result['signals'],
            fundamental_result['signals'],
            sentiment_result['signals'],
            pattern_result['signals']
        ])
        
        stop_loss, take_profit = self._calculate_risk_levels(technical_data, probability, direction)
        position_size = self._recommend_position_size(probability, technical_result.get('risk_level', '中'))
        risk_level = self._assess_risk_level(technical_result, fundamental_result, sentiment_result)
        rating = self._determine_rating(probability, ensemble_score)
        
        expected_return_min, expected_return_max = self._estimate_expected_return(direction, probability, technical_data)
        
        stock_name = technical_data.get('name', '') or fundamental_data.get('name', '')
        
        return EnsemblePredictionResult(
            code=stock_code,
            name=stock_name,
            prediction_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            direction=direction,
            probability=round(probability, 4),
            confidence=confidence,
            expected_return_min=round(expected_return_min, 4),
            expected_return_max=round(expected_return_max, 4),
            key_signals=key_signals[:8],
            model_weights=self.model_weights.copy(),
            model_scores={
                'technical': round(technical_result['score'], 2),
                'fundamental': round(fundamental_result['score'], 2),
                'market_sentiment': round(sentiment_result['score'], 2),
                'pattern_match': round(pattern_result['score'], 2)
            },
            technical_score=round(technical_result['score'], 2),
            fundamental_score=round(fundamental_result['score'], 2),
            market_sentiment_score=round(sentiment_result['score'], 2),
            pattern_match_score=round(pattern_result['score'], 2),
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            risk_level=risk_level,
            rating=rating
        )
    
    def _technical_prediction(self, technical_data: Dict, stock_code: str) -> Dict:
        """技术分析预测（40%权重）"""
        signals = []
        score = 50
        
        try:
            if not technical_data or not isinstance(technical_data, dict):
                return {'score': 50.0, 'signals': ['技术数据缺失'], 'risk_level': '中'}
            
            indicators = technical_data.get('indicators', {})
            
            ma5 = indicators.get('MA5', 0)
            ma20 = indicators.get('MA20', 0)
            close = indicators.get('close', 0)
            
            if ma5 and ma20 and close:
                if close > ma5 > ma20:
                    score += 15
                    signals.append('MA金叉形成')
                elif close < ma5 < ma20:
                    score -= 12
                    signals.append('MA死叉形成')
                    
            macd = indicators.get('MACD', 0)
            macd_signal = indicators.get('MACD_signal', 0)
            macd_hist = indicators.get('MACD_histogram', 0)
            
            if macd and macd_signal:
                if macd > macd_signal and macd_hist > 0:
                    score += 14
                    signals.append('MACD柱状图转正')
                elif macd < macd_signal and macd_hist < 0:
                    score -= 10
                    signals.append('MACD柱状图转负')
            
            rsi6 = indicators.get('RSI6', 50)
            if rsi6:
                if rsi6 < 30:
                    score += 10
                    signals.append('RSI超卖区')
                elif rsi6 > 70:
                    score -= 8
                    signals.append(f'RSI接近超买({rsi6:.0f})')
            
            volume_ratio = indicators.get('volume_ratio', 1.0)
            if volume_ratio > 2.0:
                score += 8 if score > 50 else -5
                signals.append('放量突破')
            elif volume_ratio < 0.5:
                signals.append('缩量整理')
                
            kdj_k = indicators.get('K', 50)
            kdj_d = indicators.get('D', 50)
            if kdj_k and kdj_d:
                if kdj_k > kdj_d and kdj_k < 30:
                    score += 7
                    signals.append('KDJ低位金叉')
                    
            bb_position = indicators.get('bb_position', 0.5)
            if bb_position < 0.2:
                score += 6
                signals.append('接近布林下轨')
            elif bb_position > 0.8:
                score -= 5
                signals.append('接近布林上轨')
            
            volatility = indicators.get('volatility', 0.03)
            risk_level = '高' if volatility > 0.05 else '中' if volatility > 0.02 else '低'
            
            score = max(20, min(90, score))
            
        except Exception as e:
            print(f"[警告] 技术预测计算异常: {str(e)}")
            signals.append('技术指标计算异常')
        
        return {
            'score': score,
            'signals': signals[:6],
            'risk_level': risk_level if 'risk_level' in dir() else '中'
        }
    
    def _fundamental_prediction(self, fundamental_data: Dict, stock_code: str) -> Dict:
        """基本面预测（30%权重）"""
        signals = []
        score = 50
        
        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                return {'score': 50.0, 'signals': ['基本面数据缺失']}
            
            valuation = fundamental_data.get('valuation', {})
            profitability = fundamental_data.get('profitability', {})
            growth = fundamental_data.get('growth', {})
            
            pe_ratio = valuation.get('pe_ratio', 0)
            industry_pe = valuation.get('industry_avg_pe', 15)
            
            if pe_ratio > 0 and industry_pe > 0:
                pe_ratio_vs_industry = pe_ratio / industry_pe
                if pe_ratio_vs_industry < 0.8:
                    score += 15
                    signals.append(f'PE低估({pe_ratio:.1f}x)')
                elif pe_ratio_vs_industry > 1.3:
                    score -= 10
                    signals.append(f'PE偏高({pe_ratio:.1f}x)')
            
            roe = profitability.get('roe', 0)
            if roe >= 15:
                score += 12
                signals.append(f'ROE优秀(+{roe:.1f}%)')
            elif roe >= 10:
                score += 6
                signals.append(f'ROE良好({roe:.1f}%)')
            elif roe > 0 and roe < 8:
                score -= 5
                signals.append(f'ROE偏低({roe:.1f}%)')
            
            revenue_growth = growth.get('revenue_growth_yoy', 0)
            profit_growth = growth.get('profit_growth_yoy', 0)
            
            if profit_growth > 20:
                score += 10
                signals.append(f'业绩预增(+{profit_growth:.1f}%)')
            elif profit_growth > 10:
                score += 6
                signals.append(f'业绩增长(+{profit_growth:.1f}%)')
            elif profit_growth < -10:
                score -= 12
                signals.append(f'业绩下滑({profit_growth:.1f}%)')
            
            debt_ratio = fundamental_data.get('financial_health', {}).get('debt_ratio', 50)
            if debt_ratio > 75:
                score -= 8
                signals.append(f'负债率偏高({debt_ratio:.0f}%)')
            elif debt_ratio < 40:
                score += 5
                signals.append('负债率健康')
            
            score = max(25, min(95, score))
            
        except Exception as e:
            print(f"[警告] 基本面预测计算异常: {str(e)}")
            signals.append('基本面数据计算异常')
        
        return {'score': score, 'signals': signals[:5]}
    
    def _market_sentiment_prediction(self, market_data: Dict) -> Dict:
        """市场情绪预测（20%权重）"""
        signals = []
        score = 50
        
        try:
            if not market_data or not isinstance(market_data, dict):
                return {'score': 50.0, 'signals': ['市场数据缺失']}
            
            index_change = market_data.get('index_change_pct', 0)
            sector_change = market_data.get('sector_change_pct', 0)
            north_fund_flow = market_data.get('north_fund_flow', 0)
            
            if index_change > 1.0:
                score += 10
                signals.append('大盘强势')
            elif index_change > 0.3:
                score += 5
                signals.append('大盘偏强')
            elif index_change < -1.0:
                score -= 10
                signals.append('大盘弱势')
            elif index_change < -0.3:
                score -= 5
                signals.append('大盘偏弱')
            
            if sector_change > 2.0:
                score += 8
                signals.append('板块领涨')
            elif sector_change < -2.0:
                score -= 6
                signals.append('板块走弱')
            
            if north_fund_flow > 10:
                score += 7
                signals.append('北向资金大幅流入')
            elif north_fund_flow > 0:
                score += 4
                signals.append('北向资金净流入')
            elif north_fund_flow < -10:
                score -= 6
                signals.append('北向资金流出')
            
            market_sentiment_score = market_data.get('sentiment_score', 50)
            if market_sentiment_score > 70:
                score += 5
                signals.append('市场情绪高涨')
            elif market_sentiment_score < 30:
                score -= 5
                signals.append('市场情绪低迷')
            
            score = max(20, min(85, score))
            
        except Exception as e:
            print(f"[警告] 市场情绪预测计算异常: {str(e)}")
            signals.append('市场数据计算异常')
        
        return {'score': score, 'signals': signals[:4]}
    
    def _pattern_match_prediction(self, technical_data: Dict) -> Dict:
        """历史模式匹配预测（10%权重）"""
        signals = []
        score = 50
        
        try:
            if not technical_data or 'indicators' not in technical_data:
                return {'score': 50.0, 'signals': ['模式匹配数据不足']}
            
            indicators = technical_data['indicators']
            
            close = indicators.get('close', 0)
            ma5 = indicators.get('MA5', 0)
            ma20 = indicators.get('MA20', 0)
            volume_ratio = indicators.get('volume_ratio', 1.0)
            
            pattern_score = 0
            
            if close and ma20 and close > ma20 and volume_ratio > 1.5:
                pattern_score += 20
                signals.append('放量突破形态')
            
            if ma5 and ma20:
                ma_diff_pct = abs(ma5 - ma20) / ma20 * 100 if ma20 else 0
                if ma_diff_pct < 1 and volume_ratio < 0.8:
                    pattern_score += 15
                    signals.append('均线粘合形态')
            
            rsi6 = indicators.get('RSI6', 50)
            if 35 <= rsi6 <= 45 and volume_ratio > 1.2:
                pattern_score += 12
                signals.append('超卖反弹形态')
            
            macd_hist = indicators.get('MACD_histogram', 0)
            prev_macd_hist = indicators.get('prev_MACD_histogram', 0)
            if macd_hist and prev_macd_hist and macd_hist > 0 > prev_macd_hist:
                pattern_score += 18
                signals.append('MACD底背离形态')
            
            score = 50 + pattern_score * 0.4
            score = max(30, min(80, score))
            
        except Exception as e:
            print(f"[警告] 模式匹配预测计算异常: {str(e)}")
            signals.append('模式识别异常')
        
        return {'score': score, 'signals': signals[:3]}
    
    def _determine_direction_and_probability(self, ensemble_score: float,
                                           technical: Dict,
                                           fundamental: Dict,
                                           sentiment: Dict,
                                           pattern: Dict) -> Tuple[str, float]:
        """确定最终方向和概率"""
        if ensemble_score >= 62:
            direction = '上涨'
            base_prob = 0.65 + (ensemble_score - 62) * 0.012
        elif ensemble_score <= 42:
            direction = '下跌'
            base_prob = 0.65 + (42 - ensemble_score) * 0.012
        else:
            direction = '震荡'
            base_prob = 0.52
        
        tech_bias = (technical['score'] - 50) / 100
        fund_bias = (fundamental['score'] - 50) / 150
        sent_bias = (sentiment['score'] - 50) / 200
        
        adjustment = tech_bias * 0.4 + fund_bias * 0.3 + sent_bias * 0.2
        
        probability = base_prob + adjustment
        probability = max(0.50, min(0.88, probability))
        
        if direction == '震荡':
            probability = min(probability, 0.60)
        
        return direction, round(probability, 4)
    
    def _calculate_confidence(self, probability: float, 
                            technical: Dict, 
                            fundamental: Dict) -> str:
        """计算综合置信度"""
        score_alignment = abs(technical['score'] - fundamental['score'])
        
        if probability >= self.confidence_thresholds['high'] and score_alignment < 15:
            return '高'
        elif probability >= self.confidence_thresholds['medium']:
            return '中'
        else:
            return '低'
    
    def _aggregate_key_signals(self, signal_groups: List[List[str]]) -> List[str]:
        """聚合所有子模型的关键信号"""
        all_signals = []
        for group in signal_groups:
            all_signals.extend(group)
        
        priority_keywords = [
            '放量突破', 'MACD金叉', 'MA金叉', 'PE低估',
            'ROE优秀', '业绩预增', '北向资金', '底背离'
        ]
        
        prioritized = []
        normal = []
        
        for signal in all_signals:
            if any(kw in signal for kw in priority_keywords):
                if signal not in prioritized:
                    prioritized.append(signal)
            else:
                if signal not in normal:
                    normal.append(signal)
        
        return prioritized[:4] + normal[:4]
    
    def _calculate_risk_levels(self, technical_data: Dict, 
                             probability: float, 
                             direction: str) -> Tuple[float, float]:
        """基于ATR计算动态止损止盈位"""
        try:
            atr = technical_data.get('indicators', {}).get('ATR', 0)
            close = technical_data.get('indicators', {}).get('close', 0)
            
            if atr and close:
                atr_pct = atr / close * 100
                
                if probability >= 0.72:
                    stop_loss_mult = 2.0 if direction == '上涨' else 2.5
                    take_profit_mult = 4.0 if direction == '上涨' else 3.5
                elif probability >= 0.58:
                    stop_loss_mult = 3.0
                    take_profit_mult = 3.0
                else:
                    stop_loss_mult = 4.0
                    take_profit_mult = 2.5
                
                stop_loss = -min(7.0, max(3.0, atr_pct * stop_loss_mult))
                take_profit = min(15.0, max(5.0, atr_pct * take_profit_mult))
                
                return round(stop_loss, 2), round(take_profit, 2)
            
        except Exception as e:
            print(f"[警告] 风险水平计算异常: {str(e)}")
        
        if probability >= 0.70:
            return -4.0, 9.0
        elif probability >= 0.55:
            return -5.0, 7.0
        else:
            return -6.0, 5.0
    
    def _recommend_position_size(self, probability: float, 
                                risk_level: str) -> str:
        """推荐仓位大小"""
        if probability >= 0.75 and risk_level == '低':
            return '重仓(70-90%)'
        elif probability >= 0.68:
            return '较重仓(50-70%)'
        elif probability >= 0.58:
            return '中等仓位(30-50%)'
        elif probability >= 0.48:
            return '轻仓(10-30%)'
        else:
            return '观望或空仓(<10%)'
    
    def _assess_risk_level(self, technical: Dict, 
                          fundamental: Dict, 
                          sentiment: Dict) -> str:
        """评估综合风险等级"""
        risk_factors = []
        
        tech_risk = technical.get('risk_level', '中')
        vol = technical.get('volatility', 0.03)
        
        if tech_risk == '高' or vol > 0.05:
            risk_factors.append(('tech', 2))
        elif tech_risk == '中' or vol > 0.03:
            risk_factors.append(('tech', 1))
        
        debt = fundamental.get('debt_ratio', 50)
        if debt > 75:
            risk_factors.append(('fund', 2))
        elif debt > 60:
            risk_factors.append(('fund', 1))
        
        idx_chg = sentiment.get('index_change', 0)
        if idx_chg < -2:
            risk_factors.append(('market', 2))
        elif idx_chg < -0.5:
            risk_factors.append(('market', 1))
        
        total_risk = sum(r[1] for r in risk_factors)
        
        if total_risk >= 5:
            return '高'
        elif total_risk >= 3:
            return '中高'
        elif total_risk >= 1:
            return '中'
        else:
            return '低'
    
    def _determine_rating(self, probability: float, ensemble_score: float) -> str:
        """确定投资评级"""
        combined = probability * 0.6 + (ensemble_score / 100) * 0.4
        
        if combined >= self.rating_system['strong_buy'][0]:
            name = self.rating_system['strong_buy'][1]
            stars = self.rating_system['strong_buy'][2]
        elif combined >= self.rating_system['buy'][0]:
            name = self.rating_system['buy'][1]
            stars = self.rating_system['buy'][2]
        elif combined >= self.rating_system['neutral'][0]:
            name = self.rating_system['neutral'][1]
            stars = self.rating_system['neutral'][2]
        elif combined >= self.rating_system['avoid'][0]:
            name = self.rating_system['avoid'][1]
            stars = self.rating_system['avoid'][2]
        else:
            name = self.rating_system['strong_avoid'][1]
            stars = self.rating_system['strong_avoid'][2]
        
        return f"{name} {stars}"
    
    def _estimate_expected_return(self, direction: str, 
                                 probability: float,
                                 technical_data: Dict) -> Tuple[float, float]:
        """估算预期收益区间"""
        base_return = {
            '上涨': (0.01, 0.06),
            '下跌': (-0.06, -0.01),
            '震荡': (-0.02, 0.02)
        }.get(direction, (-0.02, 0.02))
        
        prob_adjustment = (probability - 0.5) * 0.08
        
        min_ret = base_return[0] + prob_adjustment * 0.5
        max_ret = base_return[1] + prob_adjustment * 1.2
        
        vol = technical_data.get('indicators', {}).get('volatility', 0.03)
        vol_range = vol * 2
        
        min_ret = min_ret - vol_range * 0.3
        max_ret = max_ret + vol_range * 0.5
        
        return round(min_ret, 4), round(max_ret, 4)