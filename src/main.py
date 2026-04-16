#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票跟踪预测系统 - 主程序
功能：整合所有模块，提供完整的选股和预测功能
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_parser import FileParser
from data_acquisition import DataAcquisition
from technical_analysis import TechnicalAnalysis
from value_evaluation import ValueEvaluation
from prediction_model import PredictionModel
from global_news import GlobalNewsCollector
from database import SupabaseStorage


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
        self.data_acq = DataAcquisition(cache_dir=os.path.join(data_dir, 'cache'))
        self.ta = TechnicalAnalysis()
        self.ve = ValueEvaluation()
        self.model = PredictionModel(model_path=os.path.join(data_dir, 'models'))
        self.news_collector = GlobalNewsCollector()
        self.db_storage = SupabaseStorage()
        
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
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stocks': stocks
        }
        
        # 保存到Supabase（如果已配置）
        self.db_storage.save_stock_pool(stocks)
        
        # 同时保存到本地文件作为备份
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
                    'price_change_pct': data['change_pct'],
                    'volume': data['volume'],
                    'tracking_note': '正常跟踪',
                    'alert_signal': alert_signal
                }
                
                tracking_results.append(result)
                
                if alert_signal:
                    print(f"[提醒] {code} {data['name']}: {alert_signal}")
        
        # 保存到Supabase（如果已配置）
        self.db_storage.save_tracking_log(tracking_results)
        
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
        
        volume_ratio = data.get('volume_ratio', 1)
        if volume_ratio > 2:
            signals.append(f'量比{volume_ratio:.2f}超过2倍')
        
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
                'timestamp', 'stock_code', 'stock_name', 'latest_price', 
                'price_change_pct', 'volume', 'tracking_note', 'alert_signal'
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
        # 采集国际消息面数据
        print("\n[步骤3.0] 采集国际消息面数据...")
        global_news = self.news_collector.get_global_news(count=10)
        self.db_storage.save_global_news(global_news)
        
        # 分析国际消息面影响
        news_impact = self.news_collector.analyze_market_impact(global_news)
        print(f"  乐观新闻: {news_impact['positive_news_count']}条")
        print(f"  悲观新闻: {news_impact['negative_news_count']}条")
        print(f"  市场情绪: {news_impact['market_sentiment']}")
        
        predictions = []
        
        for stock in stocks:
            code = stock['code']
            print(f"\n正在预测 {code} {stock.get('name', '')}...")
            
            result = self.model.predict(code, self.data_acq)
            
            if result:
                # 整合国际消息面影响
                if news_impact['net_impact'] > 0:
                    result.probability += 0.05
                elif news_impact['net_impact'] < 0:
                    result.probability -= 0.05
                
                predictions.append({
                    'code': result.code,
                    'name': result.name,
                    'direction': result.direction,
                    'probability': result.probability,
                    'confidence': result.confidence,
                    'total_score': result.total_score,
                    'key_signals': result.key_signals,
                    'risk_warning': result.risk_warning
                })
                
                self.model.save_prediction(result, self.report_dir)
                self.db_storage.save_prediction(predictions[-1])
        
        return predictions
    
    def generate_summary_report(self, predictions: List[Dict]) -> str:
        """
        生成汇总报告
        
        参数:
            predictions: 预测结果列表
            
        返回:
            报告文本
        """
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
        print("股票跟踪预测系统启动")
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
    """
    创建示例股票跟踪预测文件
    
    参数:
        file_path: 文件路径
    """
    parser = FileParser()
    parser.create_sample_file(file_path.replace('.json', '.csv'), 'csv')
    parser.create_sample_file(file_path, 'json')
    print(f"[创建] 示例文件已创建: {file_path}")


def main():
    """主函数"""
    arg_parser = argparse.ArgumentParser(description='股票跟踪预测系统')
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
