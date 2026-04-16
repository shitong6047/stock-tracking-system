#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析工具 - 运行脚本
功能：读取股票编码文件，生成分析报告
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stock_analyzer import StockAnalyzer
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票分析工具')
    parser.add_argument('-f', '--file', type=str, 
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
    
    if not args.file:
        print("[错误] 请指定股票编码文件路径")
        print("使用方法: python analyze_stocks.py -f 股票.txt")
        print("或创建示例文件: python analyze_stocks.py --create-sample")
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