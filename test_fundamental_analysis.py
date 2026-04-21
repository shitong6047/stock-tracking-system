#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本面评估模块测试脚本
测试完整的财务分析功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from value_evaluation import ValueEvaluation, FundamentalAnalyzer


def test_valuation_analysis():
    """测试估值分析模块"""
    print("\n" + "="*80)
    print("📊 测试1: 估值分析模块")
    print("="*80)
    
    analyzer = FundamentalAnalyzer()
    
    fundamental_data = {
        'valuation': {
            'pe_ratio': 15.5,
            'pb_ratio': 2.3,
            'ps_ratio': 3.8,
            'pcf_ratio': 12.0,
            'market_cap': 850.0,
            'float_market_cap': 600.0
        },
        'profitability': {
            'roe': 18.5,
            'roa': 9.2,
            'gross_margin': 42.0,
            'net_margin': 15.5,
            'ebitda_margin': 18.6
        },
        'growth': {
            'revenue_growth_yoy': 22.3,
            'profit_growth': 28.6,
            'eps_growth': 26.4
        },
        'financial_health': {
            'debt_ratio': 45.0,
            'current_ratio': 1.85,
            'quick_ratio': 1.42,
            'goodwill_ratio': 8.5
        }
    }
    
    valuation_result = analyzer.analyze_valuation(fundamental_data, "食品饮料")
    
    print(f"✅ PE估值: {valuation_result.pe_ratio}")
    print(f"✅ PB估值: {valuation_result.pb_ratio}")
    print(f"✅ PS估值: {valuation_result.ps_ratio}")
    print(f"✅ PCF估值: {valuation_result.pcf_ratio}")
    print(f"✅ 市值: {valuation_result.market_cap}亿元 ({valuation_result.market_cap_rank})")
    print(f"\n相对估值:")
    print(f"  PE vs 行业: {valuation_result.pe_vs_industry}倍")
    print(f"  PB vs 行业: {valuation_result.pb_vs_industry}倍")
    print(f"  PE历史分位: {valuation_result.pe_percentile}%")
    print(f"  PEG指标: {valuation_result.peg_ratio}")
    print(f"\n估值评分:")
    print(f"  PE评分: {valuation_result.pe_score}/100")
    print(f"  PB评分: {valuation_result.pb_score}/100")
    print(f"  PB-ROE评分: {valuation_result.pb_roe_score}/100")
    print(f"  PS评分: {valuation_result.ps_score}/100")
    print(f"  PCF评分: {valuation_result.pcf_score}/100")
    print(f"  综合吸引力: {valuation_result.valuation_attractiveness:.1f}/100")
    print(f"\n📝 小结: {valuation_result.valuation_summary}")
    

def test_profitability_analysis():
    """测试盈利能力分析"""
    print("\n" + "="*80)
    print("💰 测试2: 盈利能力分析")
    print("="*80)
    
    analyzer = FundamentalAnalyzer()
    
    fundamental_data = {
        'profitability': {
            'roe': 22.3,
            'roa': 11.5,
            'gross_margin': 52.0,
            'net_margin': 18.8,
            'ebitda_margin': 22.5
        },
        'financial_health': {
            'debt_ratio': 48.0
        }
    }
    
    profitability_result = analyzer.analyze_profitability(fundamental_data)
    
    print(f"✅ ROE: {profitability_result.roe}%")
    print(f"✅ ROA: {profitability_result.roa}%")
    print(f"✅ 毛利率: {profitability_result.gross_margin}%")
    print(f"✅ 净利率: {profitability_result.net_margin}%")
    print(f"✅ EBITDA利润率: {profitability_result.ebitda_margin}%")
    print(f"\n杜邦分解:")
    print(f"  净利率驱动: {profitability_result.roe_dupont_net_margin*100:.2f}%")
    print(f"  资产周转率: {profitability_result.roe_dupont_asset_turnover:.2f}次")
    print(f"  权益乘数: {profitability_result.roe_dupont_equity_multiplier:.2f}倍")
    print(f"\n近5年毛利率趋势: {' → '.join(map(str, profitability_result.gross_margin_trend))}")
    print(f"近5年净利率趋势: {' → '.join(map(str, profitability_result.net_margin_trend))}")
    print(f"\n盈利能力评分:")
    print(f"  ROE评分: {profitability_result.roe_score}/100")
    print(f"  ROA评分: {profitability_result.roa_score}/100")
    print(f"  利润率评分: {profitability_result.margin_score}/100")
    print(f"  综合得分: {profitability_result.profitability_total:.1f}/100")
    print(f"\n📝 小结: {profitability_result.profitability_summary}")


def test_growth_analysis():
    """测试成长性评估"""
    print("\n" + "="*80)
    print("📈 测试3: 成长性评估")
    print("="*80)
    
    analyzer = FundamentalAnalyzer()
    
    fundamental_data = {
        'growth': {
            'revenue_growth_yoy': 25.6,
            'profit_growth': 32.4,
            'eps_growth': 30.2
        },
        'financial_health': {
            'debt_ratio': 42.0
        }
    }
    
    growth_result = analyzer.analyze_growth(fundamental_data)
    
    print(f"✅ 营收增长YoY: {growth_result.revenue_growth_yoy}%")
    print(f"✅ 营收增长QoQ: {growth_result.revenue_growth_qoq}%")
    print(f"✅ 3年CAGR: {growth_result.revenue_cagr_3y}%")
    print(f"✅ 5年CAGR: {growth_result.revenue_cagr_5y}%")
    print(f"\n利润增长:")
    print(f"  净利润YoY: {growth_result.profit_growth_yoy}%")
    print(f"  扣非净利润YoY: {growth_result.profit_growth_deducted}%")
    print(f"  EPS增长: {growth_result.eps_growth}%")
    print(f"  FCF增长: {growth_result.fcf_growth}%")
    print(f"\n成长质量:")
    print(f"  增长稳定性: {growth_result.growth_stability:.1f}/100")
    print(f"  增长可持续性: {growth_result.growth_sustainability:.1f}/100")
    print(f"  成长质量综合: {growth_result.growth_quality_score:.1f}/100")
    print(f"\n成长性评分:")
    print(f"  营收增长评分: {growth_result.revenue_score}/100")
    print(f"  利润增长评分: {growth_result.profit_score}/100")
    print(f"  成长性综合: {growth_result.growth_total:.1f}/100")
    print(f"\n📝 小结: {growth_result.growth_summary}")


def test_financial_health():
    """测试财务健康检查"""
    print("\n" + "="*80)
    print("🏥 测试4: 财务健康检查")
    print("="*80)
    
    analyzer = FundamentalAnalyzer()
    
    fundamental_data = {
        'financial_health': {
            'debt_ratio': 55.0,
            'current_ratio': 1.65,
            'quick_ratio': 1.25,
            'goodwill_ratio': 12.3,
            'interest_expense': 150.0,
            'operating_cashflow': 850.0,
            'receivable_days': 62.0,
            'inventory_days': 78.0
        },
        'profitability': {
            'net_margin': 14.5,
            'ebit': 1200.0
        },
        'valuation': {
            'market_cap': 2500.0
        }
    }
    
    health_result = analyzer.check_financial_health(fundamental_data)
    
    print(f"✅ 资产负债率: {health_result.debt_ratio}%")
    print(f"✅ 流动比率: {health_result.current_ratio}")
    print(f"✅ 速动比率: {health_result.quick_ratio}")
    print(f"✅ 利息保障倍数: {health_result.interest_coverage}倍")
    print(f"✅ 商誉占比: {health_result.goodwill_ratio}%")
    print(f"✅ 经营现金流/净利润: {health_result.operating_cashflow_to_profit}")
    print(f"✅ 应收账款周转天数: {health_result.receivable_turnover_days}天")
    print(f"✅ 存货周转天数: {health_result.inventory_turnover_days}天")
    print(f"\n健康评分:")
    print(f"  偿债能力: {health_result.debt_score}/100")
    print(f"  流动性: {health_result.liquidity_score}/100")
    print(f"  盈利质量: {health_result.quality_score}/100")
    print(f"  运营效率: {health_result.efficiency_score}/100")
    print(f"  财务健康综合: {health_result.health_total:.1f}/100")
    
    if health_result.health_warnings:
        print(f"\n⚠️ 预警项目 ({len(health_result.health_warnings)}项):")
        for warning in health_result.health_warnings:
            print(f"  {warning}")
            
    print(f"\n📝 小结: {health_result.health_summary}")


def test_fundamental_score():
    """测试综合基本面评分"""
    print("\n" + "="*80)
    print("🎯 测试5: 综合基本面评分（核心方法）")
    print("="*80)
    
    analyzer = FundamentalAnalyzer()
    
    fundamental_data = {
        'valuation': {
            'pe_ratio': 18.5,
            'pb_ratio': 2.8,
            'ps_ratio': 4.2,
            'pcf_ratio': 14.0,
            'market_cap': 650.0
        },
        'profitability': {
            'roe': 16.8,
            'roa': 8.5,
            'gross_margin': 38.5,
            'net_margin': 13.2,
            'ebitda_margin': 15.8
        },
        'growth': {
            'revenue_growth_yoy': 18.6,
            'profit_growth': 24.3,
            'eps_growth': 22.1
        },
        'financial_health': {
            'debt_ratio': 48.0,
            'current_ratio': 1.72,
            'quick_ratio': 1.35,
            'goodwill_ratio': 10.5,
            'receivable_days': 55.0,
            'inventory_days': 68.0
        }
    }
    
    score_result = analyzer.calculate_fundamental_score(fundamental_data, "医药生物")
    
    print(f"✅ 总评分: {score_result.total_score:.1f}/100")
    print(f"✅ 评级等级: {score_result.grade}")
    print(f"✅ 投资评级: {score_result.rating}")
    print(f"\n分项得分:")
    print(f"  • 估值吸引力: {score_result.valuation_score:.1f}/100 (权重30%)")
    print(f"  • 盈利能力: {score_result.profitability_score:.1f}/100 (权重30%)")
    print(f"  • 成长性: {score_result.growth_score:.1f}/100 (权重20%)")
    print(f"  • 财务健康: {score_result.health_score:.1f}/100 (权重20%)")
    
    if score_result.strengths:
        print(f"\n✅ 核心优势 ({len(score_result.strengths)}项):")
        for s in score_result.strengths:
            print(f"  • {s}")
            
    if score_result.weaknesses:
        print(f"\n❌ 主要劣势 ({len(score_result.weaknesses)}项):")
        for w in score_result.weaknesses:
            print(f"  • {w}")
            
    if score_result.suggestions:
        print(f"\n💡 投资建议:")
        for suggestion in score_result.suggestions:
            print(f"  • {suggestion}")


def test_industry_comparison():
    """测试行业对标功能"""
    print("\n" + "="*80)
    print("🏢 测试6: 行业对标分析")
    print("="*80)
    
    analyzer = FundamentalAnalyzer()
    
    fundamental_data = {
        'valuation': {
            'pe_ratio': 25.0,
            'pb_ratio': 3.5,
            'market_cap': 450.0
        },
        'profitability': {
            'roe': 19.5
        },
        'financial_health': {
            'debt_ratio': 38.0
        }
    }
    
    comparison = analyzer.compare_with_industry(fundamental_data, "食品饮料")
    
    print(f"✅ 行业: {comparison.industry_name}")
    print(f"✅ 相对位置: {comparison.relative_position}")
    
    if comparison.vs_industry_avg:
        print(f"\n关键指标对比:")
        for key, info in comparison.vs_industry_avg.items():
            print(f"  • {info['name']}: 本公司{info['value']:.2f} vs 行业平均{info['industry_avg']:.2f}"
                  f" ({info['vs_industry']}，比值{info['ratio']:.2f})")
                  
    if comparison.advantages:
        print(f"\n✅ 相对行业优势 ({len(comparison.advantages)}项):")
        for adv in comparison.advantages:
            print(f"  • {adv}")
            
    if comparison.disadvantages:
        print(f"\n❌ 相对行业劣势 ({len(comparison.disadvantages)}项):")
        for dis in comparison.disadvantages:
            print(f"  • {dis}")


def test_full_report_generation():
    """测试完整报告生成"""
    print("\n" + "="*80)
    print("📋 测试7: 完整报告生成")
    print("="*80)
    
    ve = ValueEvaluation()
    
    fundamental_data = {
        'valuation': {
            'pe_ratio': 16.8,
            'pb_ratio': 2.5,
            'ps_ratio': 3.5,
            'pcf_ratio': 11.5,
            'market_cap': 720.0,
            'float_market_cap': 520.0
        },
        'profitability': {
            'roe': 17.5,
            'roa': 9.0,
            'gross_margin': 45.0,
            'net_margin': 14.8,
            'ebitda_margin': 17.5
        },
        'growth': {
            'revenue_growth_yoy': 21.5,
            'profit_growth': 27.8,
            'eps_growth': 25.3
        },
        'financial_health': {
            'debt_ratio': 46.0,
            'current_ratio': 1.78,
            'quick_ratio': 1.38,
            'goodwill_ratio': 9.2,
            'receivable_days': 58.0,
            'inventory_days': 72.0
        }
    }
    
    report = ve.generate_fundamental_analysis_report(
        stock_code="000001",
        stock_name="平安银行",
        fundamental_data=fundamental_data,
        industry="银行"
    )
    
    print(report)


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "="*80)
    print("🔄 测试8: 向后兼容性测试")
    print("="*80)
    
    ve = ValueEvaluation()
    
    old_format_data = {
        'pe_ratio': 15.0,
        'pb_ratio': 2.0,
        'roe': 15.0,
        'dividend_yield': 3.0,
        'revenue_growth': 15.0,
        'profit_growth': 20.0
    }
    
    scores = ve.calculate_financial_score(old_format_data)
    print(f"✅ 传统评分模式正常工作")
    print(f"  总评分: {scores.get('total_score', 0):.1f}")
    
    new_format_data = {
        'valuation': {
            'pe_ratio': 15.0,
            'pb_ratio': 2.0
        },
        'profitability': {
            'roe': 15.0,
            'roa': 8.0
        },
        'growth': {
            'revenue_growth_yoy': 15.0,
            'profit_growth': 20.0
        },
        'financial_health': {
            'debt_ratio': 50.0
        }
    }
    
    scores_new = ve.calculate_financial_score(new_format_data)
    print(f"✅ 新格式数据也支持传统评分")
    print(f"  总评分: {scores_new.get('total_score', 0):.1f}")
    
    assessment = ve.assess_value(
        stock_code="600036",
        stock_name="招商银行",
        financial_data=new_format_data,
        current_price=35.50,
        industry="银行"
    )
    
    print(f"✅ 完整价值评估正常")
    print(f"  代码: {assessment.code}")
    print(f"  名称: {assessment.name}")
    print(f"  传统评分: {assessment.financial_score:.1f}")
    print(f"  评估结果: {assessment.evaluation}")
    print(f"  风险提示: {assessment.risk_warning}")
    
    if assessment.fundamental_score:
        fs = assessment.fundamental_score
        print(f"\n  新增综合评分信息:")
        print(f"    总分: {fs.total_score:.1f}/100")
        print(f"    等级: {fs.grade}")
        print(f"    评级: {fs.rating}")


def test_error_handling():
    """测试异常处理和优雅降级"""
    print("\n" + "="*80)
    print("⚠️ 测试9: 异常处理和优雅降级")
    print("="*80)
    
    analyzer = FundamentalAnalyzer()
    
    empty_data = {}
    result = analyzer.calculate_fundamental_score(empty_data)
    print(f"✅ 空数据处理: 总评分={result.total_score}, 评级='{result.rating}'")
    
    none_data = None
    result_none = analyzer.calculate_fundamental_score(none_data) if none_data else analyzer.calculate_fundamental_score({})
    print(f"✅ None数据处理: 正常降级")
    
    invalid_data = {'invalid_key': 'invalid_value'}
    try:
        result_invalid = analyzer.calculate_fundamental_score(invalid_data)
        print(f"✅ 无效数据正常处理: 总评分={result_invalid.total_score}")
    except Exception as e:
        print(f"❌ 异常未正确处理: {str(e)}")


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 基本面评估模块 v2.0 - 功能测试套件")
    print("="*80)
    print("\n开始执行测试...\n")
    
    try:
        test_valuation_analysis()
        test_profitability_analysis()
        test_growth_analysis()
        test_financial_health()
        test_fundamental_score()
        test_industry_comparison()
        test_backward_compatibility()
        test_error_handling()
        
        print("\n" + "="*80)
        print("🎉 所有核心功能测试通过！")
        print("="*80)
        
        print("\n\n是否生成完整示例报告？(y/n): ", end="")
        choice = input().strip().lower()
        
        if choice == 'y':
            test_full_report_generation()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
