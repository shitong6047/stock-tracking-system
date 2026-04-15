"""
测试模块
功能：测试各模块功能
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime

from file_parser import FileParser
from data_acquisition import DataAcquisition
from technical_analysis import TechnicalAnalysis
from value_evaluation import ValueEvaluation
from prediction_model import PredictionModel


class TestFileParser(unittest.TestCase):
    """文件解析模块测试"""
    
    def setUp(self):
        self.parser = FileParser()
        self.test_csv = 'test_tracking.csv'
        self.test_json = 'test_tracking.json'
        
        self.parser.create_sample_file(self.test_csv, 'csv')
        self.parser.create_sample_file(self.test_json, 'json')
    
    def tearDown(self):
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        if os.path.exists(self.test_json):
            os.remove(self.test_json)
    
    def test_parse_csv(self):
        """测试CSV解析"""
        result = self.parser.parse_file(self.test_csv)
        self.assertTrue(result['success'])
        self.assertEqual(result['parsed'], 3)
        self.assertEqual(len(result['data']), 3)
    
    def test_parse_json(self):
        """测试JSON解析"""
        result = self.parser.parse_file(self.test_json)
        self.assertTrue(result['success'])
        self.assertEqual(result['parsed'], 3)
        self.assertEqual(len(result['data']), 3)
    
    def test_validate_stock_code(self):
        """测试股票代码验证"""
        self.assertTrue(self.parser.validate_stock_code('000001'))
        self.assertTrue(self.parser.validate_stock_code('600519'))
        self.assertTrue(self.parser.validate_stock_code('300750'))
        self.assertFalse(self.parser.validate_stock_code('123456'))
        self.assertFalse(self.parser.validate_stock_code('abc'))
        self.assertFalse(self.parser.validate_stock_code(''))
    
    def test_invalid_file(self):
        """测试无效文件"""
        result = self.parser.parse_file('nonexistent.csv')
        self.assertFalse(result['success'])


class TestTechnicalAnalysis(unittest.TestCase):
    """技术分析模块测试"""
    
    def setUp(self):
        self.ta = TechnicalAnalysis()
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        self.test_df = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(10, 15, 100),
            'close': np.random.uniform(10, 15, 100),
            'high': np.random.uniform(12, 16, 100),
            'low': np.random.uniform(8, 12, 100),
            'volume': np.random.randint(1000000, 5000000, 100)
        })
        
        self.test_df['close'] = self.test_df['close'].cumsum() / 10 + 10
    
    def test_calculate_ma(self):
        """测试均线计算"""
        df = self.ta.calculate_ma(self.test_df)
        self.assertIn('MA5', df.columns)
        self.assertIn('MA10', df.columns)
        self.assertIn('MA20', df.columns)
    
    def test_calculate_macd(self):
        """测试MACD计算"""
        df = self.ta.calculate_macd(self.test_df)
        self.assertIn('DIF', df.columns)
        self.assertIn('DEA', df.columns)
        self.assertIn('MACD', df.columns)
    
    def test_calculate_kdj(self):
        """测试KDJ计算"""
        df = self.ta.calculate_kdj(self.test_df)
        self.assertIn('K', df.columns)
        self.assertIn('D', df.columns)
        self.assertIn('J', df.columns)
    
    def test_calculate_rsi(self):
        """测试RSI计算"""
        df = self.ta.calculate_rsi(self.test_df)
        self.assertIn('RSI6', df.columns)
        self.assertIn('RSI12', df.columns)
    
    def test_identify_trend(self):
        """测试趋势识别"""
        df = self.ta.calculate_all_indicators(self.test_df)
        trend = self.ta.identify_trend(df)
        
        self.assertIn('trend', trend)
        self.assertIn('strength', trend)
        self.assertIn('score', trend)
        self.assertGreaterEqual(trend['strength'], 0)
        self.assertLessEqual(trend['strength'], 100)
    
    def test_detect_signals(self):
        """测试信号检测"""
        df = self.ta.calculate_all_indicators(self.test_df)
        signals = self.ta.detect_signals(df)
        
        self.assertIsInstance(signals, list)
    
    def test_get_technical_score(self):
        """测试技术评分"""
        df = self.ta.calculate_all_indicators(self.test_df)
        score = self.ta.get_technical_score(df)
        
        self.assertIn('score', score)
        self.assertIn('trend', score)
        self.assertIn('evaluation', score)
        self.assertGreaterEqual(score['score'], 0)
        self.assertLessEqual(score['score'], 100)


class TestValueEvaluation(unittest.TestCase):
    """价值评估模块测试"""
    
    def setUp(self):
        self.ve = ValueEvaluation()
        
        self.sample_financial = {
            'pe_ratio': 12,
            'pb_ratio': 1.2,
            'roe': 15,
            'dividend_yield': 3.5,
            'revenue_growth': 25,
            'profit_growth': 30,
            'debt_ratio': 40
        }
    
    def test_calculate_financial_score(self):
        """测试财务评分"""
        result = self.ve.calculate_financial_score(self.sample_financial)
        
        self.assertIn('total_score', result)
        self.assertIn('item_scores', result)
        self.assertIn('grade', result)
        self.assertGreaterEqual(result['total_score'], 0)
        self.assertLessEqual(result['total_score'], 100)
    
    def test_calculate_intrinsic_value(self):
        """测试内在价值计算"""
        value = self.ve.calculate_intrinsic_value(eps=2.0, growth_rate=0.1)
        self.assertIsNotNone(value)
        self.assertGreater(value, 0)
    
    def test_calculate_deviation(self):
        """测试偏离度计算"""
        deviation = self.ve.calculate_deviation(10, 12)
        self.assertAlmostEqual(deviation, -16.67, places=1)
    
    def test_calculate_safety_margin(self):
        """测试安全边际计算"""
        margin = self.ve.calculate_safety_margin(10, 12)
        self.assertAlmostEqual(margin, 16.67, places=1)
    
    def test_evaluate_stock(self):
        """测试综合评估"""
        result = self.ve.evaluate_stock(
            code='000001',
            name='测试股票',
            financial_data=self.sample_financial,
            current_price=15
        )
        
        self.assertEqual(result.code, '000001')
        self.assertEqual(result.name, '测试股票')
        self.assertGreaterEqual(result.financial_score, 0)


class TestPredictionModel(unittest.TestCase):
    """预测模型模块测试"""
    
    def test_prediction_result_structure(self):
        """测试预测结果结构"""
        from prediction_model import PredictionResult
        
        result = PredictionResult(
            code='000001',
            name='平安银行',
            prediction_time='2026-04-15 10:00:00',
            direction='上涨',
            probability=0.65,
            confidence='中',
            technical_score=70,
            value_score=60,
            sentiment_score=55,
            macro_score=50,
            total_score=62,
            key_signals=['MACD金叉'],
            risk_warning='投资有风险'
        )
        
        self.assertEqual(result.code, '000001')
        self.assertEqual(result.direction, '上涨')
        self.assertEqual(result.probability, 0.65)


def run_quick_test():
    """快速测试（不依赖网络）"""
    print("=" * 60)
    print("快速测试（离线模块）")
    print("=" * 60)
    
    print("\n[测试1] 文件解析模块")
    parser = FileParser()
    parser.create_sample_file('quick_test.csv', 'csv')
    result = parser.parse_file('quick_test.csv')
    print(f"  CSV解析: {'通过' if result['success'] else '失败'}")
    print(f"  解析数量: {result['parsed']}")
    os.remove('quick_test.csv')
    
    print("\n[测试2] 技术分析模块")
    ta = TechnicalAnalysis()
    test_df = pd.DataFrame({
        'close': [10 + i * 0.1 for i in range(100)],
        'high': [11 + i * 0.1 for i in range(100)],
        'low': [9 + i * 0.1 for i in range(100)]
    })
    df = ta.calculate_all_indicators(test_df)
    score = ta.get_technical_score(df)
    print(f"  指标计算: 通过")
    print(f"  技术评分: {score['score']}")
    print(f"  趋势判断: {score['trend']['trend']}")
    
    print("\n[测试3] 价值评估模块")
    ve = ValueEvaluation()
    financial = {
        'pe_ratio': 15,
        'pb_ratio': 1.5,
        'roe': 12,
        'dividend_yield': 3,
        'revenue_growth': 20,
        'profit_growth': 25
    }
    result = ve.calculate_financial_score(financial)
    print(f"  财务评分: {result['total_score']:.1f}")
    print(f"  评级: {result['grade']}")
    
    print("\n" + "=" * 60)
    print("快速测试完成")
    print("=" * 60)


def run_online_test():
    """在线测试（需要网络）"""
    print("=" * 60)
    print("在线测试（需要网络连接）")
    print("=" * 60)
    
    print("\n[测试1] 数据获取模块")
    data_acq = DataAcquisition()
    
    print("  获取实时行情...")
    realtime = data_acq.get_stock_realtime('000001')
    if realtime:
        print(f"  股票名称: {realtime['name']}")
        print(f"  最新价: {realtime['latest_price']}")
        print("  实时数据获取: 通过")
    else:
        print("  实时数据获取: 失败（可能是非交易时间）")
    
    print("\n[测试2] 预测模型模块")
    model = PredictionModel()
    
    print("  执行预测...")
    result = model.predict('000001', data_acq)
    if result:
        print(f"  预测方向: {result.direction}")
        print(f"  预测概率: {result.probability}")
        print(f"  综合得分: {result.total_score}")
        print("  预测功能: 通过")
    else:
        print("  预测功能: 失败")
    
    print("\n" + "=" * 60)
    print("在线测试完成")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='股票系统测试')
    parser.add_argument('--quick', action='store_true', help='运行快速离线测试')
    parser.add_argument('--online', action='store_true', help='运行在线测试')
    parser.add_argument('--unit', action='store_true', help='运行单元测试')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_test()
    elif args.online:
        run_online_test()
    elif args.unit:
        unittest.main(argv=[''], verbosity=2, exit=True)
    else:
        print("请选择测试模式:")
        print("  --quick  : 快速离线测试")
        print("  --online : 在线测试（需要网络）")
        print("  --unit   : 单元测试")
