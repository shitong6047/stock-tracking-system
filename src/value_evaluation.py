"""
价值评估模块
功能：分析财务指标、计算估值、评估价格偏离度
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValueAssessment:
    """价值评估结果"""
    code: str
    name: str
    financial_score: float
    intrinsic_value: Optional[float]
    current_price: float
    deviation: float
    safety_margin: float
    evaluation: str
    risk_warning: str


class ValueEvaluation:
    """价值评估类"""
    
    def __init__(self):
        self.pe_threshold = 15
        self.pb_threshold = 1.5
        self.roe_threshold = 12
        self.dividend_threshold = 3
        self.growth_threshold = 20
        self.discount_rate = 0.1
        
        self.weights = {
            'pe': 0.20,
            'pb': 0.15,
            'roe': 0.25,
            'dividend': 0.15,
            'revenue_growth': 0.15,
            'profit_growth': 0.10
        }
    
    def calculate_financial_score(self, financial_data: Dict) -> Dict:
        """
        计算财务指标评分
        
        参数:
            financial_data: 财务数据字典
            
        返回:
            财务评分结果
        """
        scores = {}
        
        # PE评分
        pe_ratio = financial_data.get('pe_ratio', 0)
        if pe_ratio > 0:
            pe_score = max(0, min(100, (self.pe_threshold / pe_ratio) * 100))
            scores['pe_score'] = pe_score
        else:
            scores['pe_score'] = 50
        
        # PB评分
        pb_ratio = financial_data.get('pb_ratio', 0)
        if pb_ratio > 0:
            pb_score = max(0, min(100, (self.pb_threshold / pb_ratio) * 100))
            scores['pb_score'] = pb_score
        else:
            scores['pb_score'] = 50
        
        # ROE评分
        roe = financial_data.get('roe', 0)
        roe_score = min(100, max(0, roe * 10))
        scores['roe_score'] = roe_score
        
        # 股息率评分
        dividend_yield = financial_data.get('dividend_yield', 0)
        dividend_score = min(100, dividend_yield * 10)
        scores['dividend_score'] = dividend_score
        
        # 营收增长评分
        revenue_growth = financial_data.get('revenue_growth', 0)
        revenue_score = min(100, max(0, revenue_growth * 5))
        scores['revenue_score'] = revenue_score
        
        # 净利润增长评分
        profit_growth = financial_data.get('profit_growth', 0)
        profit_score = min(100, max(0, profit_growth * 5))
        scores['profit_score'] = profit_score
        
        # 加权总分
        total_score = sum(scores[key] * self.weights.get(key.replace('_score', ''), 0) 
                         for key in scores.keys() if key.endswith('_score'))
        
        scores['total_score'] = total_score
        
        return scores
    
    def calculate_intrinsic_value(self, financial_data: Dict, current_price: float) -> Optional[float]:
        """
        计算内在价值
        
        参数:
            financial_data: 财务数据
            current_price: 当前价格
            
        返回:
            内在价值
        """
        try:
            # 简单的DCF模型计算
            eps = financial_data.get('eps', 0)
            if eps <= 0:
                return None
            
            # 预期增长率
            growth_rate = financial_data.get('profit_growth', 0) / 100
            
            # 计算未来5年现金流
            future_cash_flows = []
            for year in range(1, 6):
                future_eps = eps * ((1 + growth_rate) ** year)
                future_cash_flows.append(future_eps)
            
            # 折现到现值
            intrinsic_value = sum(cf / ((1 + self.discount_rate) ** year) 
                                for year, cf in enumerate(future_cash_flows, 1))
            
            # 终值计算
            terminal_value = future_cash_flows[-1] * (1 + growth_rate * 0.5) / (self.discount_rate - growth_rate * 0.5)
            intrinsic_value += terminal_value / ((1 + self.discount_rate) ** 5)
            
            return intrinsic_value
            
        except Exception as e:
            print(f"[错误] 计算内在价值失败: {str(e)}")
            return None
    
    def assess_value(self, stock_code: str, stock_name: str, 
                    financial_data: Dict, current_price: float) -> ValueAssessment:
        """
        综合价值评估
        
        参数:
            stock_code: 股票代码
            stock_name: 股票名称
            financial_data: 财务数据
            current_price: 当前价格
            
        返回:
            价值评估结果
        """
        # 计算财务评分
        scores = self.calculate_financial_score(financial_data)
        financial_score = scores['total_score']
        
        # 计算内在价值
        intrinsic_value = self.calculate_intrinsic_value(financial_data, current_price)
        
        # 计算价格偏离度
        if intrinsic_value and intrinsic_value > 0:
            deviation = (current_price - intrinsic_value) / intrinsic_value * 100
            safety_margin = (intrinsic_value - current_price) / intrinsic_value * 100
        else:
            deviation = 0
            safety_margin = 0
        
        # 评估结果
        if financial_score >= 80:
            evaluation = "价值被低估"
            risk_warning = "低风险"
        elif financial_score >= 60:
            evaluation = "价值合理"
            risk_warning = "中等风险"
        elif financial_score >= 40:
            evaluation = "价值略高"
            risk_warning = "中等风险"
        else:
            evaluation = "价值被高估"
            risk_warning = "高风险"
        
        # 根据偏离度调整评估
        if deviation < -20:
            evaluation = "价值严重低估"
            risk_warning = "低风险"
        elif deviation > 20:
            evaluation = "价值严重高估"
            risk_warning = "高风险"
        
        return ValueAssessment(
            code=stock_code,
            name=stock_name,
            financial_score=financial_score,
            intrinsic_value=intrinsic_value,
            current_price=current_price,
            deviation=deviation,
            safety_margin=safety_margin,
            evaluation=evaluation,
            risk_warning=risk_warning
        )
    
    def get_industry_comparison(self, stock_assessment: ValueAssessment, 
                              industry_avg: Dict) -> Dict:
        """
        行业对比分析
        
        参数:
            stock_assessment: 股票评估结果
            industry_avg: 行业平均水平
            
        返回:
            对比分析结果
        """
        comparison = {
            'code': stock_assessment.code,
            'name': stock_assessment.name,
            'vs_industry_pe': 'above' if stock_assessment.financial_score > industry_avg.get('avg_pe_score', 50) else 'below',
            'vs_industry_pb': 'above' if stock_assessment.financial_score > industry_avg.get('avg_pb_score', 50) else 'below',
            'vs_industry_roe': 'above' if stock_assessment.financial_score > industry_avg.get('avg_roe_score', 50) else 'below',
            'relative_value': 'undervalued' if stock_assessment.deviation < -10 else 'overvalued' if stock_assessment.deviation > 10 else 'fair'
        }
        
        return comparison
    
    def generate_value_report(self, assessments: List[ValueAssessment]) -> str:
        """
        生成价值评估报告
        
        参数:
            assessments: 评估结果列表
            
        返回:
            报告文本
        """
        report = []
        report.append("=" * 80)
        report.append("价值评估报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # 统计信息
        undervalued = [a for a in assessments if a.evaluation == "价值被低估"]
        fairly_valued = [a for a in assessments if a.evaluation == "价值合理"]
        overvalued = [a for a in assessments if a.evaluation == "价值被高估"]
        
        report.append(f"被低估股票: {len(undervalued)}只")
        report.append(f"合理估值股票: {len(fairly_valued)}只")
        report.append(f"被高估股票: {len(overvalued)}只")
        report.append("")
        
        # 详细分析
        if undervalued:
            report.append("【价值被低估股票】")
            report.append("-" * 80)
            for assessment in sorted(undervalued, key=lambda x: x.financial_score, reverse=True):
                report.append(f"{assessment.code} {assessment.name}")
                report.append(f"  财务评分: {assessment.financial_score:.1f}")
                if assessment.intrinsic_value:
                    report.append(f"  内在价值: ¥{assessment.intrinsic_value:.2f}")
                report.append(f"  当前价格: ¥{assessment.current_price:.2f}")
                report.append(f"  安全边际: {assessment.safety_margin:.1f}%")
                report.append(f"  风险等级: {assessment.risk_warning}")
                report.append("")
        
        if overvalued:
            report.append("【价值被高估股票】")
            report.append("-" * 80)
            for assessment in sorted(overvalued, key=lambda x: x.financial_score):
                report.append(f"{assessment.code} {assessment.name}")
                report.append(f"  财务评分: {assessment.financial_score:.1f}")
                if assessment.intrinsic_value:
                    report.append(f"  内在价值: ¥{assessment.intrinsic_value:.2f}")
                report.append(f"  当前价格: ¥{assessment.current_price:.2f}")
                report.append(f"  价格偏离: {assessment.deviation:.1f}%")
                report.append(f"  风险等级: {assessment.risk_warning}")
                report.append("")
        
        report.append("=" * 80)
        report.append("风险提示: 价值评估仅供参考，投资有风险，决策需谨慎。")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def update_thresholds(self, pe_threshold: float, pb_threshold: float, 
                         roe_threshold: float, dividend_threshold: float):
        """
        更新评估阈值
        
        参数:
            pe_threshold: PE阈值
            pb_threshold: PB阈值
            roe_threshold: ROE阈值
            dividend_threshold: 股息率阈值
        """
        self.pe_threshold = pe_threshold
        self.pb_threshold = pb_threshold
        self.roe_threshold = roe_threshold
        self.dividend_threshold = dividend_threshold
        
        print(f"[更新] 评估阈值已更新: PE={pe_threshold}, PB={pb_threshold}, ROE={roe_threshold}, 股息率={dividend_threshold}%")
    
    def get_evaluation_summary(self, assessments: List[ValueAssessment]) -> Dict:
        """
        获取评估汇总
        
        参数:
            assessments: 评估结果列表
            
        返回:
            汇总信息
        """
        if not assessments:
            return {}
        
        avg_score = sum(a.financial_score for a in assessments) / len(assessments)
        avg_deviation = sum(a.deviation for a in assessments) / len(assessments)
        
        risk_distribution = {
            'low_risk': len([a for a in assessments if a.risk_warning == '低风险']),
            'medium_risk': len([a for a in assessments if a.risk_warning == '中等风险']),
            'high_risk': len([a for a in assessments if a.risk_warning == '高风险'])
        }
        
        return {
            'total_stocks': len(assessments),
            'avg_financial_score': avg_score,
            'avg_deviation': avg_deviation,
            'risk_distribution': risk_distribution,
            'best_value': max(assessments, key=lambda x: x.financial_score),
            'worst_value': min(assessments, key=lambda x: x.financial_score)
        }