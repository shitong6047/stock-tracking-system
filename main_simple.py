"""
股票跟踪预测系统 - 简化版本
功能：基于模拟数据的股票跟踪与预测系统
"""

import os
import sys
import json
import csv
import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from file_parser import FileParser
from technical_analysis import TechnicalAnalysis
from value_evaluation import ValueEvaluation


class MockDataAcquisition:
    """模拟数据获取类（用于演示）"""
    
    def __init__(self):
        self.base_prices = {
            '000001': 12.5,  # 平安银行
            '600519': 1800,  # 贵州茅台
            '000858': 150,   # 五粮液
            '600036': 35,    # 招商银行
            '000002': 25,    # 万科A
        }
    
    def get_stock_realtime(self, code: str) -> Optional[Dict]:
        """获取模拟实时数据"""
        base_price = self.base_prices.get(code, 10)
        
        # 生成随机波动
        change_pct = random.uniform(-5, 5)
        change_amount = base_price * change_pct / 100
        
        return {
            'code': code,
            'name': self._get_stock_name(code),
            'latest_price': round(base_price + change_amount, 2),
            'change_pct': round(change_pct, 2),
            'change_amount': round(change_amount, 2),
            'volume': random.randint(1000000, 5000000),
            'amount': round((base_price + change_amount) * random.randint(1000000, 5000000), 0),
            'turnover_rate': round(random.uniform(0.5, 10), 2),
            'pe_ratio': round(random.uniform(5, 30), 1),
            'pb_ratio': round(random.uniform(0.5, 3), 2),
            'open': round(base_price + random.uniform(-1, 1), 2),
            'high': round(base_price + random.uniform(0, 3), 2),
            'low': round(base_price + random.uniform(-3, 0), 2),
            'prev_close': base_price
        }
    
    def get_stock_history(self, code: str, days: int = 120) -> Optional[Dict]:
        """获取模拟历史数据"""
        base_price = self.base_prices.get(code, 10)
        
        dates = []
        prices = []
        volumes = []
        
        current_price = base_price
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # 生成价格序列
            change = random.uniform(-0.05, 0.05)
            current_price = current_price * (1 + change)
            prices.append(round(current_price, 2))
            
            volumes.append(random.randint(1000000, 5000000))
        
        return {
            'date': dates,
            'close': prices,
            'open': [round(p * random.uniform(0.98, 1.02), 2) for p in prices],
            'high': [round(p * random.uniform(1.01, 1.05), 2) for p in prices],
            'low': [round(p * random.uniform(0.95, 0.99), 2) for p in prices],
            'volume': volumes
        }
    
    def get_stock_financial_indicator(self, code: str) -> Optional[Dict]:
        """获取模拟财务数据"""
        return {
            'code': code,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'pe_ratio': round(random.uniform(8, 25), 1),
            'pb_ratio': round(random.uniform(0.8, 2.5), 2),
            'roe': round(random.uniform(10, 20), 1),
            'roa': round(random.uniform(5, 15), 1),
            'gross_margin': round(random.uniform(30, 60), 1),
            'net_margin': round(random.uniform(10, 30), 1),
            'debt_ratio': round(random.uniform(30, 70), 1),
            'current_ratio': round(random.uniform(1, 3), 2),
            'quick_ratio': round(random.uniform(0.8, 2), 2)
        }
    
    def get_batch_realtime(self, codes: List[str]) -> Dict[str, Dict]:
        """批量获取实时数据"""
        return {code: self.get_stock_realtime(code) for code in codes}
    
    def _get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        names = {
            '000001': '平安银行',
            '600519': '贵州茅台',
            '000858': '五粮液',
            '600036': '招商银行',
            '000002': '万科A'
        }
        return names.get(code, f'股票{code}')


class StockTrackingSystem:
    """股票跟踪预测系统"""
    
    def __init__(self, data_dir: str = './data', report_dir: str = './reports'):
        """
        初始化系统
        
        参数:
            data_dir: 数据目录
            report_dir: 报告目录
        """
        self.data_dir = data_dir
        self.report_dir = report_dir
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(report_dir, exist_ok=True)
        
        self.parser = FileParser()
        self.data_acq = MockDataAcquisition()  # 使用模拟数据
        self.ta = TechnicalAnalysis()
        self.ve = ValueEvaluation()
        
        self.stock_pool_file = os.path.join(data_dir, 'stock_pool.json')
        self.tracking_log_file = os.path.join(data_dir, 'stock_tracking_log.csv')
    
    def load_stock_pool(self, file_path: str = None) -> List[Dict]:
        """
        加载股票池
        
        参数:
            file_path: 股票跟踪预测文件路径
            
        返回:
            股票列表
        """
        if file_path:
            result = self.parser.parse_file(file_path)
            if result['success']:
                stocks = result['data']
                self._save_stock_pool(stocks)
                return stocks
            else:
                print(f"[错误] {result['error']}")
                return []
        
        if os.path.exists(self.stock_pool_file):
            with open(self.stock_pool_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('stocks', [])
        
        return []
    
    def _save_stock_pool(self, stocks: List[Dict]):
        """
        保存股票池
        
        参数:
            stocks: 股票列表
        """
        data = {
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stocks': stocks
        }
        
        with open(self.stock_pool_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[保存] 股票池已保存到 {self.stock_pool_file}")
    
    def track_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        跟踪股票行情
        
        参数:
            stocks: 股票列表
            
        返回:
            跟踪结果列表
        """
        codes = [s['code'] for s in stocks]
        realtime_data = self.data_acq.get_batch_realtime(codes)
        
        tracking_results = []
        for stock in stocks:
            code = stock['code']
            if code in realtime_data:
                data = realtime_data[code]
                
                alert_signal = self._check_alert(data)
                
                result = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'stock_code': code,
                    'stock_name': data['name'],
                    'latest_price': data['latest_price'],
                    'change_pct': data['change_pct'],
                    'open_price': data.get('open', 0),
                    'high_price': data.get('high', 0),
                    'low_price': data.get('low', 0),
                    'volume': data['volume'],
                    'amount': data['amount'],
                    'turnover_rate': data['turnover_rate'],
                    'pe_ratio': data['pe_ratio'],
                    'dividend_yield': 0,
                    'tracking_note': '正常跟踪',
                    'alert_signal': alert_signal
                }
                
                tracking_results.append(result)
                
                if alert_signal:
                    print(f"[提醒] {code} {data['name']}: {alert_signal}")
        
        self._save_tracking_log(tracking_results)
        
        return tracking_results
    
    def _check_alert(self, data: Dict) -> str:
        """
        检查异常信号
        
        参数:
            data: 股票数据
            
        返回:
            异常信号描述
        """
        signals = []
        
        change_pct = data.get('change_pct', 0)
        if change_pct > 5:
            signals.append(f'涨幅{change_pct:.2f}%超过5%')
        elif change_pct < -3:
            signals.append(f'跌幅{abs(change_pct):.2f}%超过3%')
        
        turnover = data.get('turnover_rate', 0)
        if turnover > 10:
            signals.append(f'换手率{turnover:.2f}%超过10%')
        
        return '；'.join(signals) if signals else ''
    
    def _save_tracking_log(self, results: List[Dict]):
        """
        保存跟踪日志
        
        参数:
            results: 跟踪结果列表
        """
        file_exists = os.path.exists(self.tracking_log_file)
        
        with open(self.tracking_log_file, 'a', encoding='utf-8-sig', newline='') as f:
            fieldnames = [
                'timestamp', 'stock_code', 'stock_name', 'latest_price', 'change_pct',
                'open_price', 'high_price', 'low_price', 'volume', 'amount',
                'turnover_rate', 'pe_ratio', 'dividend_yield', 'tracking_note', 'alert_signal'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(results)
        
        print(f"[保存] 跟踪日志已追加到 {self.tracking_log_file}")
    
    def predict_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        预测股票次日涨跌
        
        参数:
            stocks: 股票列表
            
        返回:
            预测结果列表
        """
        predictions = []
        
        for stock in stocks:
            code = stock['code']
            print(f"\n正在预测 {code} {stock.get('name', '')}...")
            
            result = self._predict_stock(code)
            
            if result:
                predictions.append(result)
        
        return predictions
    
    def _predict_stock(self, code: str) -> Optional[Dict]:
        """
        预测单只股票
        
        参数:
            code: 股票代码
            
        返回:
            预测结果
        """
        realtime = self.data_acq.get_stock_realtime(code)
        if not realtime:
            return None
        
        hist_data = self.data_acq.get_stock_history(code, days=120)
        if not hist_data:
            return None
        
        # 技术分析
        hist_df = pd.DataFrame(hist_data)
        tech_result = self.ta.get_technical_score(hist_df)
        
        # 价值评估
        financial = self.data_acq.get_stock_financial_indicator(code)
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
        
        # 情绪因子
        sentiment_score = self._calculate_sentiment_score(realtime)
        
        # 宏观因子
        macro_score = 50
        
        # 综合评分
        total_score = (
            tech_result['score'] * 0.35 +
            value_result['score'] * 0.30 +
            sentiment_score * 0.20 +
            macro_score * 0.15
        )
        
        # 预测方向
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
        
        # 置信度
        if probability >= 0.7 or probability <= 0.3:
            confidence = '高'
        elif probability >= 0.6 or probability <= 0.4:
            confidence = '中'
        else:
            confidence = '低'
        
        # 关键信号
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
        
        return {
            'code': code,
            'name': realtime['name'],
            'direction': direction,
            'probability': round(probability, 2),
            'confidence': confidence,
            'technical_score': round(tech_result['score'], 1),
            'value_score': round(value_result['score'], 1),
            'sentiment_score': round(sentiment_score, 1),
            'macro_score': round(macro_score, 1),
            'total_score': round(total_score, 1),
            'key_signals': key_signals[:5],
            'risk_warning': risk_warning
        }
    
    def _calculate_sentiment_score(self, realtime: Dict) -> float:
        """计算情绪因子得分"""
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
    
    def _generate_risk_warning(self, realtime: Dict, tech_result: Dict, 
                               value_result: Dict) -> str:
        """生成风险提示"""
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
    
    def generate_summary_report(self, predictions: List[Dict]) -> str:
        """生成汇总报告"""
        report = []
        report.append("=" * 70)
        report.append("股票预测汇总报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        report.append("")
        
        up_stocks = [p for p in predictions if p['direction'] == '上涨']
        down_stocks = [p for p in predictions if p['direction'] == '下跌']
        neutral_stocks = [p for p in predictions if p['direction'] == '震荡']
        
        report.append(f"预测上涨: {len(up_stocks)}只")
        report.append(f"预测下跌: {len(down_stocks)}只")
        report.append(f"预测震荡: {len(neutral_stocks)}只")
        report.append("")
        
        if up_stocks:
            report.append("【看涨股票】")
            report.append("-" * 70)
            for p in sorted(up_stocks, key=lambda x: x['probability'], reverse=True):
                report.append(f"{p['code']} {p['name']}")
                report.append(f"  概率: {p['probability']*100:.1f}% | 置信度: {p['confidence']} | 得分: {p['total_score']}")
                report.append(f"  信号: {', '.join(p['key_signals'][:3])}")
                report.append("")
        
        if down_stocks:
            report.append("【看跌股票】")
            report.append("-" * 70)
            for p in sorted(down_stocks, key=lambda x: x['probability']):
                report.append(f"{p['code']} {p['name']}")
                report.append(f"  概率: {p['probability']*100:.1f}% | 置信度: {p['confidence']} | 得分: {p['total_score']}")
                report.append(f"  风险: {p['risk_warning']}")
                report.append("")
        
        report.append("=" * 70)
        report.append("风险提示: 本报告仅供参考，不构成投资建议。投资有风险，决策需谨慎。")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def run(self, file_path: str = None, mode: str = 'all'):
        """
        运行系统
        
        参数:
            file_path: 股票跟踪预测文件路径
            mode: 运行模式 (track/predict/all)
        """
        print("=" * 70)
        print("股票跟踪预测系统启动 (模拟数据版本)")
        print("=" * 70)
        
        print("\n[步骤1] 加载股票池...")
        stocks = self.load_stock_pool(file_path)
        
        if not stocks:
            print("[错误] 股票池为空，请检查股票跟踪预测文件")
            return
        
        print(f"[成功] 加载 {len(stocks)} 只股票")
        for s in stocks:
            print(f"  - {s['code']} {s['name']}")
        
        if mode in ['track', 'all']:
            print("\n[步骤2] 跟踪股票行情...")
            tracking_results = self.track_stocks(stocks)
            print(f"[成功] 跟踪 {len(tracking_results)} 只股票")
        
        if mode in ['predict', 'all']:
            print("\n[步骤3] 预测次日涨跌...")
            predictions = self.predict_stocks(stocks)
            
            print("\n[步骤4] 生成汇总报告...")
            report = self.generate_summary_report(predictions)
            print(report)
            
            report_file = os.path.join(self.report_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n[保存] 汇总报告已保存到 {report_file}")
        
        print("\n" + "=" * 70)
        print("系统运行完成")
        print("=" * 70)


def create_sample_tracking_file(file_path: str = 'stock_tracking.json'):
    """创建示例股票跟踪预测文件"""
    parser = FileParser()
    parser.create_sample_file(file_path.replace('.json', '.csv'), 'csv')
    parser.create_sample_file(file_path, 'json')
    print(f"[创建] 示例文件已创建: {file_path}")


def main():
    """主函数"""
    import argparse
    
    arg_parser = argparse.ArgumentParser(description='股票跟踪预测系统 (模拟数据版本)')
    arg_parser.add_argument('-f', '--file', type=str, help='股票跟踪预测文件路径')
    arg_parser.add_argument('-m', '--mode', type=str, default='all', 
                           choices=['track', 'predict', 'all'],
                           help='运行模式: track(仅跟踪), predict(仅预测), all(全部)')
    arg_parser.add_argument('--create-sample', action='store_true', 
                           help='创建示例股票跟踪预测文件')
    
    args = arg_parser.parse_args()
    
    if args.create_sample:
        create_sample_tracking_file()
        return
    
    system = StockTrackingSystem()
    system.run(file_path=args.file, mode=args.mode)


if __name__ == "__main__":
    main()