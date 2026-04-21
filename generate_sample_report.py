#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本面评估模块示例 - 生成完整分析报告
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from value_evaluation import ValueEvaluation


def main():
    print("\n正在生成完整的基本面分析报告...\n")
    
    ve = ValueEvaluation()
    
    sample_data = {
        'valuation': {
            'pe_ratio': 18.5,
            'pb_ratio': 2.8,
            'ps_ratio': 4.2,
            'pcf_ratio': 14.0,
            'market_cap': 850.5,
            'float_market_cap': 620.3
        },
        'profitability': {
            'roe': 19.2,
            'roa': 9.6,
            'gross_margin': 46.8,
            'net_margin': 15.3,
            'ebitda_margin': 18.4
        },
        'growth': {
            'revenue_growth_yoy': 23.5,
            'profit_growth': 29.8,
            'eps_growth': 27.2
        },
        'financial_health': {
            'debt_ratio': 44.5,
            'current_ratio': 1.82,
            'quick_ratio': 1.45,
            'goodwill_ratio': 8.8,
            'interest_expense': 180.0,
            'operating_cashflow': 1250.0,
            'receivable_days': 52.0,
            'inventory_days': 65.0
        }
    }
    
    report = ve.generate_fundamental_analysis_report(
        stock_code="000001",
        stock_name="平安银行",
        fundamental_data=sample_data,
        industry="银行"
    )
    
    print(report)
    
    output_file = "sample_fundamental_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"\n✅ 报告已保存到: {output_file}")


if __name__ == "__main__":
    main()
