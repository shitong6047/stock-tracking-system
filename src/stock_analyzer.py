#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析工具
功能：读取股票编码文件，生成包含股票名称、分析时间、备注信息和涨跌幅预测的分析报告
"""

import os
import json
import csv
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StockAnalysisResult:
    """股票分析结果"""
    code: str
    name: str
    analysis_time: str
    notes: str
    predicted_change: float
    confidence: str
    risk_level: str
    technical_signal: str
    recommendation: str
    price_range: Tuple[float, float]


class StockAnalyzer:
    """股票分析器"""
    
    def __init__(self, data_dir: str = './data'):
        """
        初始化股票分析器
        
        参数:
            data_dir: 数据目录
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 股票名称映射（A股常用股票）
        self.stock_names = {
            '000001': '平安银行',
            '000002': '万科A',
            '000858': '五粮液',
            '600036': '招商银行',
            '600519': '贵州茅台',
            '601988': '中国银行',
            '601929': '吉视传媒',
            '601919': '中远海控',
            '000895': '双汇发展',
            '002415': '海康威视',
            '300750': '宁德时代',
            '000651': '格力电器',
            '600276': '恒瑞医药',
            '600887': '伊利股份',
            '000333': '美的集团',
            '600030': '中信证券',
            '600016': '民生银行',
            '600028': '中国石化',
            '600050': '中国联通',
            '600104': '上汽集团'
        }
        
        # 备注信息模板
        self.notes_templates = {
            '银行': '关注业绩表现和资产质量',
            '白酒': '关注消费复苏和业绩增长',
            '房地产': '关注政策变化和销售情况',
            '保险': '关注投资收益和保费增长',
            '医药': '关注研发进展和医保政策',
            '科技': '关注技术突破和市场份额',
            '消费': '关注消费趋势和品牌价值',
            '能源': '关注价格波动和产能扩张',
            '制造': '关注订单情况和产能利用率',
            '公用事业': '关注政策稳定和分红能力'
        }
    
    def parse_stock_codes_file(self, file_path: str) -> List[str]:
        """
        解析股票编码文件
        
        参数:
            file_path: 股票编码文件路径
            
        返回:
            股票编码列表
        """
        stock_codes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 提取股票代码（支持多种格式）
                        code = self._extract_stock_code(line)
                        if code:
                            stock_codes.append(code)
                        else:
                            print(f"[警告] 第{line_num}行无法识别的股票编码: {line}")
        
        except FileNotFoundError:
            print(f"[错误] 文件不存在: {file_path}")
        except Exception as e:
            print(f"[错误] 读取文件失败: {str(e)}")
        
        return stock_codes
    
    def _extract_stock_code(self, text: str) -> Optional[str]:
        """
        从文本中提取股票代码
        
        参数:
            text: 输入文本
            
        返回:
            股票代码或None
        """
        import re
        
        # 移除空格和特殊字符
        text = text.strip().upper()
        
        # 移除股票后缀
        text = re.sub(r'\.(SH|SZ|HK)$', '', text)
        
        # 提取6位数字（A股）
        if len(text) == 6 and text.isdigit():
            return text
        
        # 处理其他格式，提取数字
        digits = re.sub(r'[^\d]', '', text)
        if len(digits) == 6:
            return digits
        
        return None
    
    def get_stock_info(self, stock_code: str) -> Dict:
        """
        获取股票信息
        
        参数:
            stock_code: 股票代码
            
        返回:
            股票信息字典
        """
        # 获取股票名称
        name = self.stock_names.get(stock_code, f'未知股票({stock_code})')
        
        # 确定股票类型
        stock_type = self._get_stock_type(name)
        
        # 生成备注信息
        notes = self.notes_templates.get(stock_type, '关注基本面变化')
        
        return {
            'code': stock_code,
            'name': name,
            'type': stock_type,
            'notes': notes
        }
    
    def _get_stock_type(self, stock_name: str) -> str:
        """
        根据股票名称确定股票类型
        
        参数:
            stock_name: 股票名称
            
        返回:
            股票类型
        """
        name_lower = stock_name.lower()
        
        if any(keyword in name_lower for keyword in ['银行', 'bank']):
            return '银行'
        elif any(keyword in name_lower for keyword in ['白酒', '酒', '茅台', '五粮液']):
            return '白酒'
        elif any(keyword in name_lower for keyword in ['房地产', '地产', '万科']):
            return '房地产'
        elif any(keyword in name_lower for keyword in ['保险', '保险']):
            return '保险'
        elif any(keyword in name_lower for keyword in ['医药', '药', '医疗']):
            return '医药'
        elif any(keyword in name_lower for keyword in ['科技', '技术', '电子', '通信']):
            return '科技'
        elif any(keyword in name_lower for keyword in ['消费', '零售', '商业', '食品']):
            return '消费'
        elif any(keyword in name_lower for keyword in ['能源', '石油', '煤炭', '电力']):
            return '能源'
        elif any(keyword in name_lower for keyword in ['制造', '工业', '汽车', '机械']):
            return '制造'
        elif any(keyword in name_lower for keyword in ['公用', '电力', '水务', '燃气']):
            return '公用事业'
        else:
            return '其他'
    
    def predict_stock_change(self, stock_code: str, stock_info: Dict) -> StockAnalysisResult:
        """
        预测股票涨跌幅
        
        参数:
            stock_code: 股票代码
            stock_info: 股票信息
            
        返回:
            分析结果
        """
        # 模拟预测逻辑（基于股票类型和随机因素）
        stock_type = stock_info['type']
        
        # 根据股票类型设置不同的预测参数
        type_params = {
            '银行': {'base_change': 0.02, 'volatility': 0.03},
            '白酒': {'base_change': 0.03, 'volatility': 0.05},
            '房地产': {'base_change': -0.01, 'volatility': 0.06},
            '保险': {'base_change': 0.01, 'volatility': 0.04},
            '医药': {'base_change': 0.02, 'volatility': 0.04},
            '科技': {'base_change': 0.04, 'volatility': 0.08},
            '消费': {'base_change': 0.02, 'volatility': 0.05},
            '能源': {'base_change': 0.01, 'volatility': 0.07},
            '制造': {'base_change': 0.01, 'volatility': 0.05},
            '公用事业': {'base_change': 0.01, 'volatility': 0.03},
            '其他': {'base_change': 0.01, 'volatility': 0.04}
        }
        
        params = type_params.get(stock_type, type_params['其他'])
        
        # 生成预测涨跌幅
        base_change = params['base_change']
        volatility = params['volatility']
        predicted_change = base_change + random.uniform(-volatility, volatility)
        
        # 确定置信度
        abs_change = abs(predicted_change)
        if abs_change < 0.02:
            confidence = '高'
        elif abs_change < 0.05:
            confidence = '中'
        else:
            confidence = '低'
        
        # 确定风险等级
        if abs_change < 0.03:
            risk_level = '低风险'
        elif abs_change < 0.06:
            risk_level = '中等风险'
        else:
            risk_level = '高风险'
        
        # 生成技术信号
        technical_signal = self._generate_technical_signal(predicted_change, stock_type)
        
        # 生成投资建议
        recommendation = self._generate_recommendation(predicted_change, confidence)
        
        # 计算价格区间
        current_price = random.uniform(10, 200)  # 模拟当前价格
        price_range = (
            round(current_price * (1 + predicted_change - 0.02), 2),
            round(current_price * (1 + predicted_change + 0.02), 2)
        )
        
        return StockAnalysisResult(
            code=stock_code,
            name=stock_info['name'],
            analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            notes=stock_info['notes'],
            predicted_change=round(predicted_change * 100, 2),  # 转换为百分比
            confidence=confidence,
            risk_level=risk_level,
            technical_signal=technical_signal,
            recommendation=recommendation,
            price_range=price_range
        )
    
    def _generate_technical_signal(self, predicted_change: float, stock_type: str) -> str:
        """
        生成技术信号
        
        参数:
            predicted_change: 预测涨跌幅
            stock_type: 股票类型
            
        返回:
            技术信号
        """
        if predicted_change > 0.05:
            return '强势上涨，突破阻力位'
        elif predicted_change > 0.02:
            return '温和上涨，均线多头排列'
        elif predicted_change > -0.02:
            return '震荡整理，观望为主'
        elif predicted_change > -0.05:
            return '弱势下跌，关注支撑位'
        else:
            return '深度下跌，风险较高'
    
    def _generate_recommendation(self, predicted_change: float, confidence: str) -> str:
        """
        生成投资建议
        
        参数:
            predicted_change: 预测涨跌幅
            confidence: 置信度
            
        返回:
            投资建议
        """
        if predicted_change > 0.05 and confidence in ['高', '中']:
            return '强烈买入'
        elif predicted_change > 0.02:
            return '买入'
        elif predicted_change > -0.02:
            return '持有'
        elif predicted_change > -0.05:
            return '卖出'
        else:
            return '强烈卖出'
    
    def analyze_stocks(self, file_path: str) -> List[StockAnalysisResult]:
        """
        分析股票
        
        参数:
            file_path: 股票编码文件路径
            
        返回:
            分析结果列表
        """
        print(f"🔍 开始分析股票文件: {file_path}")
        print("=" * 60)
        
        # 解析股票编码
        stock_codes = self.parse_stock_codes_file(file_path)
        
        if not stock_codes:
            print("[错误] 未找到有效的股票编码")
            return []
        
        print(f"✅ 找到 {len(stock_codes)} 只股票")
        
        results = []
        for i, stock_code in enumerate(stock_codes, 1):
            print(f"\n📊 正在分析第 {i}/{len(stock_codes)} 只股票...")
            
            # 获取股票信息
            stock_info = self.get_stock_info(stock_code)
            print(f"   股票: {stock_code} {stock_info['name']}")
            print(f"   类型: {stock_info['type']}")
            print(f"   备注: {stock_info['notes']}")
            
            # 预测涨跌幅
            result = self.predict_stock_change(stock_code, stock_info)
            results.append(result)
            
            print(f"   预测涨跌幅: {result.predicted_change:.2f}%")
            print(f"   置信度: {result.confidence}")
            print(f"   风险等级: {result.risk_level}")
            print(f"   技术信号: {result.technical_signal}")
            print(f"   投资建议: {result.recommendation}")
            print(f"   价格区间: ¥{result.price_range[0]:.2f} - ¥{result.price_range[1]:.2f}")
            
            # 模拟处理时间
            time.sleep(0.5)
        
        print(f"\n✅ 完成 {len(results)} 只股票的分析")
        return results
    
    def generate_analysis_report(self, results: List[StockAnalysisResult], 
                               output_format: str = 'json') -> str:
        """
        生成分析报告
        
        参数:
            results: 分析结果列表
            output_format: 输出格式 (json/csv/txt)
            
        返回:
            报告文件路径
        """
        if not results:
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            return self._generate_json_report(results, timestamp)
        elif output_format == 'csv':
            return self._generate_csv_report(results, timestamp)
        elif output_format == 'txt':
            return self._generate_txt_report(results, timestamp)
        else:
            return self._generate_json_report(results, timestamp)
    
    def _generate_json_report(self, results: List[StockAnalysisResult], timestamp: str) -> str:
        """
        生成JSON格式报告
        
        参数:
            results: 分析结果列表
            timestamp: 时间戳
            
        返回:
            报告文件路径
        """
        report_file = os.path.join(self.data_dir, f'stock_analysis_report_{timestamp}.json')
        
        report_data = {
            'report_type': '股票分析报告',
            'generate_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(results),
            'analysis_results': []
        }
        
        for result in results:
            report_data['analysis_results'].append({
                'stock_code': result.code,
                'stock_name': result.name,
                'analysis_time': result.analysis_time,
                'notes': result.notes,
                'predicted_change_pct': result.predicted_change,
                'confidence': result.confidence,
                'risk_level': result.risk_level,
                'technical_signal': result.technical_signal,
                'recommendation': result.recommendation,
                'price_range': result.price_range
            })
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return report_file
    
    def _generate_csv_report(self, results: List[StockAnalysisResult], timestamp: str) -> str:
        """
        生成CSV格式报告
        
        参数:
            results: 分析结果列表
            timestamp: 时间戳
            
        返回:
            报告文件路径
        """
        report_file = os.path.join(self.data_dir, f'stock_analysis_report_{timestamp}.csv')
        
        with open(report_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                '股票代码', '股票名称', '分析时间', '备注信息', '预测涨跌幅(%)',
                '置信度', '风险等级', '技术信号', '投资建议', '价格区间下限', '价格区间上限'
            ])
            
            for result in results:
                writer.writerow([
                    result.code,
                    result.name,
                    result.analysis_time,
                    result.notes,
                    result.predicted_change,
                    result.confidence,
                    result.risk_level,
                    result.technical_signal,
                    result.recommendation,
                    result.price_range[0],
                    result.price_range[1]
                ])
        
        return report_file
    
    def _generate_txt_report(self, results: List[StockAnalysisResult], timestamp: str) -> str:
        """
        生成文本格式报告
        
        参数:
            results: 分析结果列表
            timestamp: 时间戳
            
        返回:
            报告文件路径
        """
        report_file = os.path.join(self.data_dir, f'stock_analysis_report_{timestamp}.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("股票分析报告\n")
            f.write("=" * 80 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析股票数量: {len(results)} 只\n")
            f.write("\n")
            
            # 统计信息
            buy_count = len([r for r in results if r.recommendation in ['强烈买入', '买入']])
            sell_count = len([r for r in results if r.recommendation in ['强烈卖出', '卖出']])
            hold_count = len([r for r in results if r.recommendation == '持有'])
            
            f.write("汇总统计:\n")
            f.write(f"推荐买入: {buy_count} 只\n")
            f.write(f"推荐卖出: {sell_count} 只\n")
            f.write(f"建议持有: {hold_count} 只\n")
            f.write("\n")
            
            # 详细分析
            f.write("详细分析:\n")
            f.write("-" * 80 + "\n")
            
            for result in results:
                f.write(f"{result.code} {result.name}\n")
                f.write(f"  分析时间: {result.analysis_time}\n")
                f.write(f"  备注信息: {result.notes}\n")
                f.write(f"  预测涨跌幅: {result.predicted_change:.2f}%\n")
                f.write(f"  置信度: {result.confidence}\n")
                f.write(f"  风险等级: {result.risk_level}\n")
                f.write(f"  技术信号: {result.technical_signal}\n")
                f.write(f"  投资建议: {result.recommendation}\n")
                f.write(f"  价格区间: ¥{result.price_range[0]:.2f} - ¥{result.price_range[1]:.2f}\n")
                f.write("-" * 80 + "\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("风险提示: 本报告仅供参考，不构成投资建议。投资有风险，决策需谨慎。\n")
            f.write("=" * 80 + "\n")
        
        return report_file
    
    def create_sample_stock_file(self, file_path: str = '股票.txt'):
        """
        创建示例股票编码文件
        
        参数:
            file_path: 文件路径
        """
        sample_codes = [
            '000001',  # 平安银行
            '600519',  # 贵州茅台
            '000002',  # 万科A
            '000858',  # 五粮液
            '600036',  # 招商银行
            '# 这是注释行',
            '601988',  # 中国银行
            '601929',  # 吉视传媒
            '601919'   # 中远海控
        ]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for code in sample_codes:
                f.write(code + '\n')
        
        print(f"[创建] 示例股票编码文件已创建: {file_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票分析工具')
    parser.add_argument('-f', '--file', type=str, required=True, 
                       help='股票编码文件路径')
    parser.add_argument('-o', '--output', type=str, default='json',
                       choices=['json', 'csv', 'txt'],
                       help='输出格式 (默认: json)')
    parser.add_argument('--create-sample', action='store_true',
                       help='创建示例股票编码文件')
    
    args = parser.parse_args()
    
    analyzer = StockAnalyzer()
    
    if args.create_sample:
        analyzer.create_sample_stock_file()
        return
    
    # 分析股票
    results = analyzer.analyze_stocks(args.file)
    
    if results:
        # 生成报告
        report_file = analyzer.generate_analysis_report(results, args.output)
        print(f"\n📊 分析报告已生成: {report_file}")
        
        # 显示汇总信息
        print("\n📈 汇总信息:")
        buy_count = len([r for r in results if r.recommendation in ['强烈买入', '买入']])
        sell_count = len([r for r in results if r.recommendation in ['强烈卖出', '卖出']])
        hold_count = len([r for r in results if r.recommendation == '持有'])
        
        print(f"推荐买入: {buy_count} 只")
        print(f"推荐卖出: {sell_count} 只")
        print(f"建议持有: {hold_count} 只")
    else:
        print("[错误] 未生成分析报告")


if __name__ == "__main__":
    main()