#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股智能炒股系统 - 主程序
功能：支持全市场扫描选股、个股分析预测、配置管理、日志系统
版本: 3.0.0
"""

import os
import sys
import json
import csv
import argparse
import signal
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

try:
    from loguru import logger
except ImportError:
    import logging as logger
    logger.basicConfig(level=logging.INFO)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_parser import FileParser
from data_acquisition import DataAcquisition
from technical_analysis import TechnicalAnalysis
from value_evaluation import ValueEvaluation
from prediction_model import PredictionModel
from global_news import GlobalNewsCollector
from database import SupabaseStorage


class ConfigManager:
    """配置管理器 - 支持三级配置：命令行 > 环境变量 > config.json"""
    
    DEFAULT_CONFIG = {
        "data_dir": "./data",
        "report_dir": "./reports",
        "log_dir": "./logs",
        "scope": "csi300",
        "top_n": 10,
        "lookback_days": 60,
        "risk_tolerance": "medium",
        "prediction_threshold": 0.6,
        "enable_database": True,
        "enable_news": True,
        "log_level": "INFO",
        "log_rotation": "500 MB",
        "log_retention": "7 days",
        "screen_filters": {
            "min_market_cap": 50,
            "max_pe_ratio": 100,
            "min_turnover_rate": 1.0,
            "exclude_st": True,
            "exclude_new_stock_days": 60
        },
        "prediction_params": {
            "feature_window": 20,
            "model_type": "ensemble",
            "confidence_weight": 0.7
        }
    }
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config.json'
        )
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置（从文件和环境变量）"""
        self.config = self.DEFAULT_CONFIG.copy()
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self._deep_merge(self.config, file_config)
                logger.success(f"配置文件加载成功: {self.config_path}")
            except Exception as e:
                logger.warning(f"配置文件加载失败，使用默认配置: {e}")
        
        env_mappings = {
            'DATA_DIR': 'data_dir',
            'REPORT_DIR': 'report_dir',
            'LOG_DIR': 'log_dir',
            'SUPABASE_URL': 'supabase_url',
            'SUPABASE_KEY': 'supabase_key',
            'LOG_LEVEL': 'log_level'
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.environ.get(env_key)
            if env_value:
                self.config[config_key] = env_value
    
    def _deep_merge(self, base: Dict, override: Dict):
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        参数:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
            
        返回:
            配置值
        """
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置项（通常由命令行参数覆盖）
        
        参数:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save_default_config(self, path: str = None):
        """
        保存默认配置模板到文件
        
        参数:
            path: 保存路径
        """
        save_path = path or self.config_path
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        logger.info(f"默认配置模板已保存到: {save_path}")
    
    def to_dict(self) -> Dict:
        """返回配置字典"""
        return self.config.copy()


class LogManager:
    """日志管理器 - 统一日志系统"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LogManager._initialized:
            return
        LogManager._initialized = True
        self.logger = logger
    
    def setup(self, log_dir: str = './logs', level: str = 'INFO', 
              rotation: str = '500 MB', retention: str = '7 days'):
        """
        初始化日志系统
        
        参数:
            log_dir: 日志目录
            level: 日志级别
            rotation: 日志轮转大小
            retention: 日志保留时间
        """
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"stock_system_{datetime.now().strftime('%Y%m%d')}.log")
        
        self.logger.remove()
        
        self.logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True
        )
        
        self.logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8"
        )
        
        self.logger.info(f"日志系统初始化完成，日志文件: {log_file}")
    
    def get_logger(self):
        """获取logger实例"""
        return self.logger


class AStockTradingSystem:
    """
    A股智能炒股系统
    支持三种运行模式：
    - screen: 全市场扫描选股
    - analyze: 分析指定股票
    - both: 两者兼做
    """
    
    MODES = ['screen', 'analyze', 'both']
    SCOPES = ['all', 'csi300', 'csi500', 'sz50']
    RISK_LEVELS = ['low', 'medium', 'high']
    
    def __init__(self, config: ConfigManager = None):
        """
        初始化系统
        
        参数:
            config: 配置管理器实例
        """
        self.config = config or ConfigManager()
        
        data_dir = self.config.get('data_dir', './data')
        report_dir = self.config.get('report_dir', './reports')
        
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
        
        self.log_manager = LogManager()
        self.log_manager.setup(
            log_dir=self.config.get('log_dir', './logs'),
            level=self.config.get('log_level', 'INFO'),
            rotation=self.config.get('log_rotation', '500 MB'),
            retention=self.config.get('log_retention', '7 days')
        )
        
        self.logger = self.log_manager.get_logger()
        self.mode = 'both'
        self.scope = self.config.get('scope', 'csi300')
        self.top_n = self.config.get('top_n', 10)
        self.lookback_days = self.config.get('lookback_days', 60)
        self.risk_tolerance = self.config.get('risk_tolerance', 'medium')
        
        self.logger.info("=" * 70)
        self.logger.info("A股智能炒股系统启动")
        self.logger.info(f"运行模式: {self.mode}")
        self.logger.info(f"数据目录: {data_dir}")
        self.logger.info(f"报告目录: {report_dir}")
        self.logger.info("=" * 70)
    
    def load_stock_pool(self, file_path: str = None) -> List[Dict]:
        """
        加载股票池
        
        参数:
            file_path: 股票文件路径
            
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
                self.logger.error(f"文件解析失败: {result['error']}")
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
        
        try:
            self.db_storage.save_stock_pool(stocks)
        except Exception as e:
            self.logger.warning(f"保存到数据库失败: {e}")
        
        with open(self.stock_pool_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"股票池已保存到 {self.stock_pool_file}")
    
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
                    self.logger.warning(f"{code} {data['name']}: {alert_signal}")
        
        try:
            self.db_storage.save_tracking_log(tracking_results)
        except Exception as e:
            self.logger.warning(f"保存到数据库失败: {e}")
        
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
        
        self.logger.info(f"跟踪日志已追加到 {self.tracking_log_file}")
    
    def predict_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        预测股票次日涨跌
        
        参数:
            stocks: 股票列表
            
        返回:
            预测结果列表
        """
        self.logger.info("采集国际消息面数据...")
        global_news = self.news_collector.get_global_news(count=10)
        
        try:
            self.db_storage.save_global_news(global_news)
        except Exception as e:
            self.logger.warning(f"保存新闻到数据库失败: {e}")
        
        news_impact = self.news_collector.analyze_market_impact(global_news)
        self.logger.info(f"乐观新闻: {news_impact['positive_news_count']}条")
        self.logger.info(f"悲观新闻: {news_impact['negative_news_count']}条")
        self.logger.info(f"市场情绪: {news_impact['market_sentiment']}")
        
        predictions = []
        
        for stock in stocks:
            code = stock['code']
            self.logger.info(f"正在预测 {code} {stock.get('name', '')}...")
            
            result = self.model.predict(code, self.data_acq)
            
            if result:
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
                
                try:
                    self.db_storage.save_prediction(predictions[-1])
                except Exception as e:
                    self.logger.warning(f"保存预测到数据库失败: {e}")
        
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
    
    def screen_market(self) -> List[Dict]:
        """
        全市场扫描选股
        
        返回:
            选股结果列表
        """
        self.logger.info("\n[步骤1] 开始全市场扫描选股...")
        self.logger.info(f"扫描范围: {self.scope}")
        self.logger.info(f"筛选数量: Top {self.top_n}")
        
        try:
            scope_codes = self._get_scope_codes()
            
            all_stocks_data = []
            batch_size = 100
            
            for i in range(0, len(scope_codes), batch_size):
                batch = scope_codes[i:i + batch_size]
                self.logger.debug(f"正在获取第 {i//batch_size + 1} 批数据 ({len(batch)} 只股票)...")
                
                try:
                    batch_data = self.data_acq.get_batch_realtime(batch)
                    
                    for code, data in batch_data.items():
                        if self._passes_screen_filter(data):
                            stock_info = {
                                'code': code,
                                'name': data['name'],
                                'latest_price': data['latest_price'],
                                'change_pct': data['change_pct'],
                                'volume': data['volume'],
                                'turnover_rate': data.get('turnover_rate', 0),
                                'market_cap': data.get('market_cap', 0),
                                'pe_ratio': data.get('pe_ratio', 0),
                                'screen_score': self._calculate_screen_score(data)
                            }
                            all_stocks_data.append(stock_info)
                            
                except Exception as e:
                    self.logger.warning(f"批量获取数据失败: {e}")
                    continue
            
            sorted_stocks = sorted(all_stocks_data, 
                                 key=lambda x: x['screen_score'], 
                                 reverse=True)[:self.top_n]
            
            self._save_screen_results(sorted_stocks)
            
            self.logger.success(f"[完成] 全市场扫描完成，筛选出 {len(sorted_stocks)} 只优质股票")
            
            for idx, stock in enumerate(sorted_stocks, 1):
                self.logger.info(f"  {idx}. {stock['code']} {stock['name']} - "
                               f"评分: {stock['screen_score']:.2f} - "
                               f"涨幅: {stock['change_pct']:+.2f}%")
            
            return sorted_stocks
            
        except Exception as e:
            self.logger.error(f"全市场扫描失败: {e}")
            raise
    
    def _get_scope_codes(self) -> List[str]:
        """
        获取扫描范围的股票代码列表
        
        返回:
            股票代码列表
        """
        try:
            if self.scope == 'all':
                stock_list = self.data_acq.get_all_stock_list(scope='all')
            elif self.scope == 'csi300':
                stock_list = self.data_acq.get_all_stock_list(scope='csi300')
            elif self.scope == 'csi500':
                stock_list = self.data_acq.get_all_stock_list(scope='csi500')
            elif self.scope == 'sz50':
                stock_list = self.data_acq.get_all_stock_list(scope='sz50')
            else:
                stock_list = self.data_acq.get_all_stock_list(scope='all')
            
            codes = [stock['code'] for stock in stock_list]
            self.logger.info(f"获取到 {len(codes)} 只股票代码")
            return codes
            
        except Exception as e:
            self.logger.warning(f"获取{self.scope}成分股失败，使用全部A股: {e}")
            stock_list = self.data_acq.get_all_stock_list(scope='all')
            return [stock['code'] for stock in stock_list]
    
    def _passes_screen_filter(self, data: Dict) -> bool:
        """
        检查股票是否通过筛选条件
        
        参数:
            data: 股票实时数据
            
        返回:
            是否通过筛选
        """
        filters = self.config.get('screen_filters', {})
        
        name = data.get('name', '')
        if filters.get('exclude_st', True) and ('ST' in name or 'st' in name):
            return False
        
        market_cap = data.get('market_cap', 0)
        min_cap = filters.get('min_market_cap', 50)
        if market_cap > 0 and market_cap < min_cap * 1e8:
            return False
        
        pe_ratio = data.get('pe_ratio', 0)
        max_pe = filters.get('max_pe_ratio', 100)
        if pe_ratio > 0 and pe_ratio > max_pe:
            return False
        
        turnover_rate = data.get('turnover_rate', 0)
        min_turnover = filters.get('min_turnover_rate', 1.0)
        if turnover_rate > 0 and turnover_rate < min_turnover:
            return False
        
        return True
    
    def _calculate_screen_score(self, data: Dict) -> float:
        """
        计算选股评分
        
        参数:
            data: 股票实时数据
            
        返回:
            评分分数
        """
        score = 50.0
        
        change_pct = abs(data.get('change_pct', 0))
        if change_pct <= 3:
            score += 15
        elif change_pct <= 5:
            score += 10
        else:
            score += 5
        
        volume_ratio = data.get('volume_ratio', 1)
        if 1 <= volume_ratio <= 2:
            score += 15
        elif volume_ratio <= 3:
            score += 10
        else:
            score += 5
        
        turnover_rate = data.get('turnover_rate', 0)
        if 2 <= turnover_rate <= 8:
            score += 12
        elif turnover_rate <= 15:
            score += 8
        else:
            score += 4
        
        pe_ratio = data.get('pe_ratio', 0)
        if 10 <= pe_ratio <= 30:
            score += 8
        elif pe_ratio <= 50:
            score += 5
        
        return min(score, 100)
    
    def _save_screen_results(self, results: List[Dict]):
        """
        保存选股结果
        
        参数:
            results: 选股结果列表
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = os.path.join(
            self.report_dir, 
            f'screen_results_{timestamp}.json'
        )
        
        output_data = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scope': self.scope,
            'total_scanned': len(results),
            'top_n': self.top_n,
            'results': results
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"选股结果已保存到: {result_file}")
        
        if self.config.get('enable_database', True):
            try:
                self.db_storage.save_screen_results(output_data)
            except Exception as e:
                self.logger.warning(f"保存到数据库失败: {e}")
    
    def analyze_stocks(self, stocks: List[Dict]) -> Dict:
        """
        分析指定股票（包含跟踪和预测）
        
        参数:
            stocks: 股票列表
            
        返回:
            分析结果字典
        """
        self.logger.info(f"\n[步骤2] 开始分析 {len(stocks)} 只股票...")
        
        analysis_result = {
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tracking_results': [],
            'predictions': [],
            'summary': {}
        }
        
        try:
            tracking_results = self.track_stocks(stocks)
            analysis_result['tracking_results'] = tracking_results
            self.logger.success(f"[完成] 跟踪分析完成")
            
        except Exception as e:
            self.logger.error(f"跟踪分析失败: {e}")
            analysis_result['tracking_error'] = str(e)
        
        try:
            predictions = self.predict_stocks(stocks)
            analysis_result['predictions'] = predictions
            
            up_count = len([p for p in predictions if p['direction'] == '上涨'])
            down_count = len([p for p in predictions if p['direction'] == '下跌'])
            neutral_count = len([p for p in predictions if p['direction'] == '震荡'])
            
            analysis_result['summary'] = {
                'total': len(predictions),
                'up': up_count,
                'down': down_count,
                'neutral': neutral_count
            }
            
            self.logger.success(f"[完成] 预测分析完成 - 上涨:{up_count}, 下跌:{down_count}, 震荡:{neutral_count}")
            
        except Exception as e:
            self.logger.error(f"预测分析失败: {e}")
            analysis_result['prediction_error'] = str(e)
        
        report = self.generate_summary_report(predictions if 'predictions' in locals() else [])
        analysis_result['report_text'] = report
        
        self._save_analysis_report(analysis_result)
        
        return analysis_result
    
    def _save_analysis_report(self, result: Dict):
        """
        保存分析报告
        
        参数:
            result: 分析结果
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(
            self.report_dir,
            f'analysis_report_{timestamp}.json'
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        txt_report_file = os.path.join(
            self.report_dir,
            f'summary_{timestamp}.txt'
        )
        
        with open(txt_report_file, 'w', encoding='utf-8') as f:
            f.write(result.get('report_text', ''))
        
        self.logger.info(f"分析报告已保存到: {report_file}")
        self.logger.info(f"汇总报告已保存到: {txt_report_file}")
    
    def run(self, mode: str = 'both', file_path: str = None, **kwargs):
        """
        运行系统主流程
        
        参数:
            mode: 运行模式 (screen/analyze/both)
            file_path: 股票文件路径
            **kwargs: 其他参数
        """
        self.mode = mode
        
        if 'scope' in kwargs:
            self.scope = kwargs['scope']
        if 'top_n' in kwargs:
            self.top_n = kwargs['top_n']
        if 'lookback_days' in kwargs:
            self.lookback_days = kwargs['lookback_days']
        if 'risk_tolerance' in kwargs:
            self.risk_tolerance = kwargs['risk_tolerance']
        
        start_time = datetime.now()
        
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"开始执行 - 模式: {mode.upper()}")
        self.logger.info(f"{'='*70}")
        
        try:
            final_results = {'mode': mode, 'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S')}
            
            if mode in ['screen', 'both']:
                screen_results = self.screen_market()
                final_results['screen_results'] = screen_results
                
                if mode == 'both' and screen_results:
                    self.logger.info("\n[衔接] 对筛选出的股票进行深度分析...")
                    analysis_result = self.analyze_stocks(screen_results)
                    final_results['analysis'] = analysis_result
            
            if mode == 'analyze':
                stocks = self.load_stock_pool(file_path)
                
                if not stocks:
                    self.logger.error("股票池为空，请检查输入文件")
                    raise ValueError("股票池为空")
                
                self.logger.info(f"加载了 {len(stocks)} 只待分析股票")
                analysis_result = self.analyze_stocks(stocks)
                final_results['analysis'] = analysis_result
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            final_results['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
            final_results['duration_seconds'] = duration
            final_results['status'] = 'success'
            
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"系统运行完成 - 耗时: {duration:.2f}秒")
            self.logger.info(f"{'='*70}")
            
            return final_results
            
        except KeyboardInterrupt:
            self.logger.warning("\n用户中断操作")
            self._graceful_shutdown()
            raise
        except Exception as e:
            self.logger.error(f"系统运行出错: {e}", exc_info=True)
            self._handle_error(e)
            raise
    
    def _graceful_shutdown(self):
        """优雅关闭"""
        self.logger.info("正在优雅关闭系统...")
        self.logger.info("清理临时资源...")
        self.logger.info("系统已安全关闭")
    
    def _handle_error(self, error: Exception):
        """
        错误处理和优雅降级
        
        参数:
            error: 异常对象
        """
        error_msg = str(error)
        
        if "网络连接" in error_msg or "连接超时" in error_msg:
            self.logger.error("网络连接问题，请检查网络设置后重试")
        elif "数据获取" in error_msg:
            self.logger.error("数据源异常，可能为非交易时间或API限制")
        elif "文件" in error_msg:
            self.logger.error("文件操作失败，请检查文件路径和权限")
        elif "配置" in error_msg:
            self.logger.error("配置错误，请检查config.json或环境变量")
        else:
            self.logger.error(f"未知错误: {error_msg}")
            self.logger.error("建议查看详细日志获取更多信息")
        
        error_log_file = os.path.join(
            self.config.get('log_dir', './logs'),
            f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        with open(error_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now()}] 错误详情:\n")
            f.write(f"类型: {type(error).__name__}\n")
            f.write(f"消息: {error_msg}\n")
            f.write(f"模式: {self.mode}\n\n")


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数
    
    返回:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(
        description='A股智能炒股系统 v3.0 - 支持全市场扫描选股和个股分析预测',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 全市场扫描选股（沪深300）
  python src/main.py --mode screen --scope csi300 --top-n 10
  
  # 分析指定股票文件
  python src/main.py --mode analyze --file 股票.txt
  
  # 全市场扫描并深度分析
  python src/main.py --mode both --scope csi500 --top-n 5 --output ./reports/
  
  # 高风险偏好模式
  python src/main.py --mode both --risk-tolerance high --lookback-days 30
  
  # 向后兼容旧版命令
  python src/main.py -f 股票.txt -m predict
  python src/main.py --create-sample
"""
    )
    
    parser.add_argument(
        '-m', '--mode',
        type=str,
        default='both',
        choices=['screen', 'analyze', 'both', 'track', 'predict', 'all'],
        help='运行模式: screen(全市场扫描), analyze(分析指定), both(扫描+分析), '
             'track(仅跟踪), predict(仅预测), all(全部) [默认: both]'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        default=None,
        help='股票文件路径（analyze模式必需）'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出目录（覆盖配置文件的report_dir）'
    )
    
    parser.add_argument(
        '-s', '--scope',
        type=str,
        default=None,
        choices=['all', 'csi300', 'csi500', 'sz50'],
        help='扫描范围: all(全A股), csi300(沪深300), csi500(中证500), sz50(上证50)'
    )
    
    parser.add_argument(
        '-n', '--top-n',
        type=int,
        default=None,
        help='筛选股票数量 [默认: 10]'
    )
    
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=None,
        help='回溯天数用于技术分析 [默认: 60]'
    )
    
    parser.add_argument(
        '--risk-tolerance',
        type=str,
        default=None,
        choices=['low', 'medium', 'high'],
        help='风险偏好等级: low(保守), medium(均衡), high(激进)'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help='自定义配置文件路径'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default=None,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='日志级别 [默认: INFO]'
    )
    
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='创建示例股票文件'
    )
    
    parser.add_argument(
        '--init-config',
        action='store_true',
        help='生成默认配置文件模板'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s v3.0.0'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'analyze' and not args.file:
        parser.error("analyze模式需要指定股票文件 (--file/-f)")
    
    if args.mode in ['track', 'predict', 'all']:
        args.mode = {'track': 'analyze', 'predict': 'analyze', 'all': 'both'}[args.mode]
    
    return args


def create_sample_tracking_file(file_path: str = 'stock_tracking.csv'):
    """
    创建示例股票跟踪文件
    
    参数:
        file_path: 文件路径
    """
    parser = FileParser()
    parser.create_sample_file(file_path, 'csv')
    print(f"[创建] 示例文件已创建: {file_path}")


def main():
    """主函数入口"""
    args = parse_arguments()
    
    if args.create_sample:
        create_sample_tracking_file(args.file or 'stocks.csv')
        return
    
    try:
        config = ConfigManager(config_path=args.config)
        
        if args.init_config:
            config.save_default_config()
            print("[成功] 默认配置文件模板已生成: config.json")
            return
        
        if args.output:
            config.set('report_dir', args.output)
        if args.scope:
            config.set('scope', args.scope)
        if args.top_n is not None:
            config.set('top_n', args.top_n)
        if args.lookback_days is not None:
            config.set('lookback_days', args.lookback_days)
        if args.risk_tolerance:
            config.set('risk_tolerance', args.risk_tolerance)
        if args.log_level:
            config.set('log_level', args.log_level)
        
        system = AStockTradingSystem(config=config)
        
        result = system.run(
            mode=args.mode,
            file_path=args.file,
            scope=config.get('scope'),
            top_n=config.get('top_n'),
            lookback_days=config.get('lookback_days'),
            risk_tolerance=config.get('risk_tolerance')
        )
        
        if result.get('status') == 'success':
            print("\n✓ 系统运行成功完成！")
            print(f"  运行时长: {result.get('duration_seconds', 0):.2f}秒")
            print(f"  报告位置: {config.get('report_dir')}/")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n✗ 用户中断操作")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ 系统运行失败: {e}")
        print("  提示: 使用 --help 查看帮助信息")
        print("  详细日志请查看 logs/ 目录")
        sys.exit(1)


if __name__ == "__main__":
    main()
