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
            评分结果
        """
        scores = {}
        details = []
        
        pe = financial_data.get('pe_ratio', 0)
        if pe > 0:
            if pe < self.pe_threshold:
                scores['pe'] = 100
                details.append(f'PE({pe:.1f})低于{self.pe_threshold}，估值合理')
            elif pe < self.pe_threshold * 1.5:
                scores['pe'] = 70
                details.append(f'PE({pe:.1f})适中')
            else:
                scores['pe'] = max(0, 100 - (pe - self.pe_threshold) * 5)
                details.append(f'PE({pe:.1f})偏高')
        else:
            scores['pe'] = 50
            details.append('PE数据缺失')
        
        pb = financial_data.get('pb_ratio', 0)
        if pb > 0:
            if pb < self.pb_threshold:
                scores['pb'] = 100
                details.append(f'PB({pb:.2f})低于{self.pb_threshold}，破净或接近破净')
            elif pb < self.pb_threshold * 2:
                scores['pb'] = 70
                details.append(f'PB({pb:.2f})适中')
            else:
                scores['pb'] = max(0, 100 - (pb - self.pb_threshold) * 20)
                details.append(f'PB({pb:.2f})偏高')
        else:
            scores['pb'] = 50
            details.append('PB数据缺失')
        
        roe = financial_data.get('roe', 0)
        if roe > 0:
            if roe > self.roe_threshold:
                scores['roe'] = 100
                details.append(f'ROE({roe:.1f}%)高于{self.roe_threshold}%，盈利能力强')
            elif roe > self.roe_threshold * 0.5:
                scores['roe'] = 70
                details.append(f'ROE({roe:.1f}%)适中')
            else:
                scores['roe'] = max(0, roe / self.roe_threshold * 100)
                details.append(f'ROE({roe:.1f}%)偏低')
        else:
            scores['roe'] = 50
            details.append('ROE数据缺失')
        
        dividend = financial_data.get('dividend_yield', 0)
        if dividend > 0:
            if dividend > self.dividend_threshold:
                scores['dividend'] = 100
                details.append(f'股息率({dividend:.2f}%)高于{self.dividend_threshold}%')
            else:
                scores['dividend'] = dividend / self.dividend_threshold * 100
                details.append(f'股息率({dividend:.2f}%)')
        else:
            scores['dividend'] = 30
            details.append('无股息或数据缺失')
        
        revenue_growth = financial_data.get('revenue_growth', 0)
        if revenue_growth != 0:
            if revenue_growth > self.growth_threshold:
                scores['revenue_growth'] = 100
                details.append(f'营收增速({revenue_growth:.1f}%)高于{self.growth_threshold}%')
            elif revenue_growth > 0:
                scores['revenue_growth'] = revenue_growth / self.growth_threshold * 100
                details.append(f'营收增速({revenue_growth:.1f}%)')
            else:
                scores['revenue_growth'] = 0
                details.append(f'营收负增长({revenue_growth:.1f}%)')
        else:
            scores['revenue_growth'] = 50
            details.append('营收增速数据缺失')
        
        profit_growth = financial_data.get('profit_growth', 0)
        if profit_growth != 0:
            if profit_growth > self.growth_threshold:
                scores['profit_growth'] = 100
                details.append(f'利润增速({profit_growth:.1f}%)高于{self.growth_threshold}%')
            elif profit_growth > 0:
                scores['profit_growth'] = profit_growth / self.growth_threshold * 100
                details.append(f'利润增速({profit_growth:.1f}%)')
            else:
                scores['profit_growth'] = 0
                details.append(f'利润负增长({profit_growth:.1f}%)')
        else:
            scores['profit_growth'] = 50
            details.append('利润增速数据缺失')
        
        total_score = sum(scores[k] * self.weights[k] for k in self.weights)
        
        return {
            'total_score': total_score,
            'item_scores': scores,
            'details': details,
            'grade': self._get_grade(total_score)
        }
    
    def _get_grade(self, score: float) -> str:
        """获取评级"""
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        else:
            return 'D'
    
    def calculate_intrinsic_value(self, eps: float, growth_rate: float,
                                   discount_rate: float = None) -> Optional[float]:
        """
        计算内在价值（简化DCF模型）
        
        参数:
            eps: 每股收益
            growth_rate: 增长率
            discount_rate: 折现率
            
        返回:
            内在价值
        """
        if discount_rate is None:
            discount_rate = self.discount_rate
        
        if eps <= 0:
            return None
        
        growth_rate = growth_rate / 100 if abs(growth_rate) > 1 else growth_rate
        
        if growth_rate >= discount_rate:
            return eps * 20
        
        intrinsic_value = eps * (1 + growth_rate) / (discount_rate - growth_rate)
        
        return max(intrinsic_value, 0)
    
    def calculate_deviation(self, current_price: float, 
                           intrinsic_value: float) -> float:
        """
        计算价格偏离度
        
        参数:
            current_price: 当前价格
            intrinsic_value: 内在价值
            
        返回:
            偏离度（正数表示高估，负数表示低估）
        """
        if intrinsic_value <= 0:
            return 0
        
        return (current_price - intrinsic_value) / intrinsic_value * 100
    
    def calculate_safety_margin(self, current_price: float, 
                                intrinsic_value: float) -> float:
        """
        计算安全边际
        
        参数:
            current_price: 当前价格
            intrinsic_value: 内在价值
            
        返回:
            安全边际（正数表示有安全边际）
        """
        if intrinsic_value <= 0:
            return 0
        
        return (intrinsic_value - current_price) / intrinsic_value * 100
    
    def evaluate_stock(self, code: str, name: str, 
                       financial_data: Dict, 
                       current_price: float) -> ValueAssessment:
        """
        综合评估股票价值
        
        参数:
            code: 股票代码
            name: 股票名称
            financial_data: 财务数据
            current_price: 当前价格
            
        返回:
            价值评估结果
        """
        financial_result = self.calculate_financial_score(financial_data)
        
        eps = financial_data.get('eps', 0)
        if eps <= 0:
            eps = current_price / max(financial_data.get('pe_ratio', 0), 1) if financial_data.get('pe_ratio', 0) > 0 else 0
        
        growth_rate = financial_data.get('profit_growth', 10)
        intrinsic_value = self.calculate_intrinsic_value(eps, growth_rate)
        
        if intrinsic_value and intrinsic_value > 0:
            deviation = self.calculate_deviation(current_price, intrinsic_value)
            safety_margin = self.calculate_safety_margin(current_price, intrinsic_value)
        else:
            deviation = 0
            safety_margin = 0
        
        evaluation = self._generate_evaluation(financial_result, deviation, safety_margin)
        risk_warning = self._generate_risk_warning(financial_data, deviation)
        
        return ValueAssessment(
            code=code,
            name=name,
            financial_score=financial_result['total_score'],
            intrinsic_value=intrinsic_value,
            current_price=current_price,
            deviation=deviation,
            safety_margin=safety_margin,
            evaluation=evaluation,
            risk_warning=risk_warning
        )
    
    def _generate_evaluation(self, financial_result: Dict, 
                            deviation: float, safety_margin: float) -> str:
        """生成评估结论"""
        parts = []
        
        grade = financial_result['grade']
        score = financial_result['total_score']
        
        if grade in ['A', 'B+']:
            parts.append(f'财务状况优秀(评分{score:.0f}，{grade}级)')
        elif grade == 'B':
            parts.append(f'财务状况良好(评分{score:.0f}，{grade}级)')
        else:
            parts.append(f'财务状况一般(评分{score:.0f}，{grade}级)')
        
        if deviation < -30:
            parts.append('显著低估')
        elif deviation < -10:
            parts.append('低估')
        elif deviation < 10:
            parts.append('估值合理')
        elif deviation < 30:
            parts.append('偏高')
        else:
            parts.append('显著高估')
        
        if safety_margin > 30:
            parts.append('安全边际高')
        elif safety_margin > 10:
            parts.append('有一定安全边际')
        elif safety_margin > 0:
            parts.append('安全边际较小')
        else:
            parts.append('无安全边际')
        
        return '，'.join(parts)
    
    def _generate_risk_warning(self, financial_data: Dict, deviation: float) -> str:
        """生成风险提示"""
        warnings = []
        
        pe = financial_data.get('pe_ratio', 0)
        if pe > 50:
            warnings.append('PE过高，估值风险大')
        elif pe > 30:
            warnings.append('PE偏高，注意估值风险')
        
        roe = financial_data.get('roe', 0)
        if roe < 5:
            warnings.append('ROE较低，盈利能力弱')
        
        debt_ratio = financial_data.get('debt_ratio', 0)
        if debt_ratio > 70:
            warnings.append('资产负债率高，财务风险大')
        elif debt_ratio > 60:
            warnings.append('资产负债率偏高')
        
        if deviation > 50:
            warnings.append('价格显著高于内在价值')
        
        if not warnings:
            warnings.append('投资有风险，决策需谨慎')
        
        return '；'.join(warnings)
    
    def get_value_score(self, financial_data: Dict, current_price: float) -> Dict:
        """
        获取价值投资评分（用于预测模型）
        
        参数:
            financial_data: 财务数据
            current_price: 当前价格
            
        返回:
            价值评分结果
        """
        financial_result = self.calculate_financial_score(financial_data)
        
        eps = financial_data.get('eps', 0)
        if eps <= 0:
            eps = current_price / max(financial_data.get('pe_ratio', 0), 1) if financial_data.get('pe_ratio', 0) > 0 else 0
        
        growth_rate = financial_data.get('profit_growth', 10)
        intrinsic_value = self.calculate_intrinsic_value(eps, growth_rate)
        
        if intrinsic_value and intrinsic_value > 0:
            deviation = self.calculate_deviation(current_price, intrinsic_value)
            safety_margin = self.calculate_safety_margin(current_price, intrinsic_value)
        else:
            deviation = 0
            safety_margin = 0
        
        value_score = financial_result['total_score']
        
        if deviation < -20:
            value_score += 20
        elif deviation < -10:
            value_score += 10
        elif deviation > 20:
            value_score -= 20
        elif deviation > 10:
            value_score -= 10
        
        value_score = max(0, min(100, value_score))
        
        return {
            'score': value_score,
            'financial_score': financial_result['total_score'],
            'deviation': deviation,
            'safety_margin': safety_margin,
            'grade': financial_result['grade'],
            'details': financial_result['details']
        }


if __name__ == "__main__":
    from data_acquisition import DataAcquisition
    
    print("=" * 50)
    print("测试价值评估模块")
    print("=" * 50)
    
    data_acq = DataAcquisition()
    ve = ValueEvaluation()
    
    code = "000001"
    print(f"\n获取股票 {code} 数据:")
    
    realtime = data_acq.get_stock_realtime(code)
    financial = data_acq.get_stock_financial_indicator(code)
    
    if realtime and financial:
        print(f"\n实时行情:")
        print(f"  价格: {realtime['latest_price']}")
        print(f"  PE: {realtime['pe_ratio']}")
        print(f"  PB: {realtime['pb_ratio']}")
        
        print(f"\n财务指标:")
        for key, value in financial.items():
            print(f"  {key}: {value}")
        
        financial_data = {
            'pe_ratio': realtime['pe_ratio'],
            'pb_ratio': realtime['pb_ratio'],
            'roe': financial.get('roe', 0),
            'dividend_yield': 2.5,
            'revenue_growth': 10,
            'profit_growth': 15,
            'debt_ratio': financial.get('debt_ratio', 0)
        }
        
        print(f"\n财务评分:")
        score_result = ve.calculate_financial_score(financial_data)
        print(f"  总分: {score_result['total_score']:.1f}")
        print(f"  等级: {score_result['grade']}")
        for detail in score_result['details']:
            print(f"    - {detail}")
        
        print(f"\n综合评估:")
        assessment = ve.evaluate_stock(code, realtime['name'], financial_data, realtime['latest_price'])
        print(f"  评分: {assessment.financial_score:.1f}")
        print(f"  内在价值: {assessment.intrinsic_value:.2f}" if assessment.intrinsic_value else "  内在价值: 无法计算")
        print(f"  当前价格: {assessment.current_price:.2f}")
        print(f"  偏离度: {assessment.deviation:.1f}%")
        print(f"  安全边际: {assessment.safety_margin:.1f}%")
        print(f"  评估: {assessment.evaluation}")
        print(f"  风险提示: {assessment.risk_warning}")
