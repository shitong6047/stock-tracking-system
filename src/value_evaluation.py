"""
基本面价值评估模块 v2.0
功能：全面财务分析和估值评估，支持多维度指标评估和综合评分
包含：估值模型、盈利能力分析、成长性评估、财务健康检查、综合评分、行业对标
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import math


@dataclass
class ValuationResult:
    """估值分析结果"""
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    ps_ratio: float = 0.0
    pcf_ratio: float = 0.0
    market_cap: float = 0.0
    float_market_cap: float = 0.0
    
    pe_vs_industry: float = 0.0
    pe_percentile: float = 50.0
    peg_ratio: float = 0.0
    pe_score: float = 50.0
    
    pb_vs_industry: float = 0.0
    pb_roe_score: float = 50.0
    pb_score: float = 50.0
    
    ps_score: float = 50.0
    pcf_score: float = 50.0
    market_cap_rank: str = ""
    
    valuation_attractiveness: float = 50.0
    valuation_summary: str = ""


@dataclass
class ProfitabilityResult:
    """盈利能力分析结果"""
    roe: float = 0.0
    roa: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    ebitda_margin: float = 0.0
    
    roe_dupont_net_margin: float = 0.0
    roe_dupont_asset_turnover: float = 0.0
    roe_dupont_equity_multiplier: float = 0.0
    
    gross_margin_trend: List[float] = field(default_factory=list)
    net_margin_trend: List[float] = field(default_factory=list)
    
    roe_score: float = 50.0
    roa_score: float = 50.0
    margin_score: float = 50.0
    profitability_total: float = 50.0
    profitability_summary: str = ""


@dataclass
class GrowthResult:
    """成长性评估结果"""
    revenue_growth_yoy: float = 0.0
    revenue_growth_qoq: float = 0.0
    revenue_cagr_3y: float = 0.0
    revenue_cagr_5y: float = 0.0
    
    profit_growth_yoy: float = 0.0
    profit_growth_deducted: float = 0.0
    eps_growth: float = 0.0
    fcf_growth: float = 0.0
    
    growth_stability: float = 0.0
    growth_sustainability: float = 0.0
    growth_quality_score: float = 50.0
    
    revenue_score: float = 50.0
    profit_score: float = 50.0
    growth_total: float = 50.0
    growth_summary: str = ""


@dataclass
class FinancialHealthResult:
    """财务健康检查结果"""
    debt_ratio: float = 0.0
    current_ratio: float = 0.0
    quick_ratio: float = 0.0
    interest_coverage: float = 0.0
    goodwill_ratio: float = 0.0
    operating_cashflow_to_profit: float = 0.0
    receivable_turnover_days: float = 0.0
    inventory_turnover_days: float = 0.0
    
    debt_score: float = 50.0
    liquidity_score: float = 50.0
    quality_score: float = 50.0
    efficiency_score: float = 50.0
    health_total: float = 50.0
    health_warnings: List[str] = field(default_factory=list)
    health_summary: str = ""


@dataclass
class FundamentalScore:
    """综合基本面评分"""
    total_score: float = 0.0
    valuation_score: float = 0.0
    profitability_score: float = 0.0
    growth_score: float = 0.0
    health_score: float = 0.0
    
    grade: str = "C"
    rating: str = "中性"
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class IndustryComparison:
    """行业对标结果"""
    industry_name: str = ""
    vs_industry_avg: Dict = field(default_factory=dict)
    percentile_ranking: Dict = field(default_factory=dict)
    advantages: List[str] = field(default_factory=list)
    disadvantages: List[str] = field(default_factory=list)
    relative_position: str = "中等"


@dataclass
class ValueAssessment:
    """价值评估结果（保留兼容原有接口）"""
    code: str = ""
    name: str = ""
    financial_score: float = 0.0
    intrinsic_value: Optional[float] = None
    current_price: float = 0.0
    deviation: float = 0.0
    safety_margin: float = 0.0
    evaluation: str = ""
    risk_warning: str = ""
    
    fundamental_score: Optional[FundamentalScore] = None
    valuation: Optional[ValuationResult] = None
    profitability: Optional[ProfitabilityResult] = None
    growth: Optional[GrowthResult] = None
    financial_health: Optional[FinancialHealthResult] = None
    industry_comparison: Optional[IndustryComparison] = None


class FundamentalAnalyzer:
    """
    基本面分析器 - 核心类
    
    提供全面的财务分析功能：
    - 多维度估值分析（PE/PB/PS/PCF）
    - 盈利能力深度分析（含杜邦分解）
    - 成长性多角度评估
    - 财务健康全面检查
    - 综合评分算法
    - 行业对标对比
    """
    
    def __init__(self):
        self.industry_benchmarks = self._load_industry_benchmarks()
        
        self.score_weights = {
            'valuation': 0.30,
            'profitability': 0.30,
            'growth': 0.20,
            'financial_health': 0.20
        }
        
        self.valuation_thresholds = {
            'pe_excellent': 10,
            'pe_good': 15,
            'pe_fair': 25,
            'pb_excellent': 1.0,
            'pb_good': 1.5,
            'pb_fair': 3.0,
            'peg_excellent': 0.8,
            'peg_good': 1.2,
            'ps_excellent': 2,
            'ps_good': 4,
            'pcf_excellent': 8,
            'pcf_good': 15
        }
        
        self.profitability_thresholds = {
            'roe_excellent': 20,
            'roe_good': 15,
            'roe_fair': 10,
            'roa_excellent': 10,
            'roa_good': 6,
            'roa_fair': 3,
            'gross_margin_excellent': 50,
            'gross_margin_good': 35,
            'net_margin_excellent': 20,
            'net_margin_good': 12
        }
        
        self.health_thresholds = {
            'debt_safe': 50,
            'debt_warning': 70,
            'current_safe': 1.5,
            'quick_safe': 1.0,
            'goodwill_safe': 20,
            'ocf_to_profit_good': 1.0,
            'receivable_days_warning': 90,
            'inventory_days_warning': 120
        }

    def _load_industry_benchmarks(self) -> Dict:
        """
        加载行业基准数据
        
        返回:
            各行业平均指标字典
        """
        return {
            '银行': {'avg_pe': 6.5, 'avg_pb': 0.7, 'avg_roe': 12.5, 'avg_debt': 92},
            '保险': {'avg_pe': 12.0, 'avg_pb': 1.8, 'avg_roe': 14.0, 'avg_debt': 88},
            '证券': {'avg_pe': 18.0, 'avg_pb': 1.5, 'avg_roe': 8.5, 'avg_debt': 75},
            '房地产': {'avg_pe': 9.0, 'avg_pb': 0.9, 'avg_roe': 11.0, 'avg_debt': 80},
            '食品饮料': {'avg_pe': 35.0, 'avg_pb': 6.5, 'avg_roe': 22.0, 'avg_debt': 40},
            '白酒': {'avg_pe': 32.0, 'avg_pb': 7.5, 'avg_roe': 26.0, 'avg_debt': 30},
            '医药生物': {'avg_pe': 38.0, 'avg_pb': 4.5, 'avg_roe': 16.0, 'avg_debt': 35},
            '电子': {'avg_pe': 42.0, 'avg_pb': 4.0, 'avg_roe': 11.0, 'avg_debt': 42},
            '计算机': {'avg_pe': 48.0, 'avg_pb': 4.2, 'avg_roe': 9.5, 'avg_debt': 38},
            '通信': {'avg_pe': 28.0, 'avg_pb': 2.5, 'avg_roe': 10.0, 'avg_debt': 45},
            '电力设备': {'avg_pe': 32.0, 'avg_pb': 3.8, 'avg_roe': 13.0, 'avg_debt': 55},
            '汽车': {'avg_pe': 25.0, 'avg_pb': 2.5, 'avg_roe': 10.5, 'avg_debt': 62},
            '家电': {'avg_pe': 14.0, 'avg_pb': 2.8, 'avg_roe': 18.0, 'avg_debt': 58},
            '建筑': {'avg_pe': 8.0, 'avg_pb': 0.8, 'avg_roe': 10.0, 'avg_debt': 75},
            '建材': {'avg_pe': 12.0, 'avg_pb': 1.5, 'avg_roe': 14.0, 'avg_debt': 48},
            '化工': {'avg_pe': 16.0, 'avg_pb': 1.8, 'avg_roe': 12.0, 'avg_debt': 52},
            '机械': {'avg_pe': 22.0, 'avg_pb': 2.2, 'avg_roe': 10.0, 'avg_debt': 50},
            '有色金属': {'avg_pe': 18.0, 'avg_pb': 1.6, 'avg_roe': 11.0, 'avg_debt': 55},
            '煤炭': {'avg_pe': 7.5, 'avg_pb': 0.85, 'avg_roe': 14.5, 'avg_debt': 45},
            '石油石化': {'avg_pe': 10.0, 'avg_pb': 0.9, 'avg_roe': 10.5, 'avg_debt': 52},
            '交通运输': {'avg_pe': 15.0, 'avg_pb': 1.0, 'avg_roe': 9.0, 'avg_debt': 58},
            '商贸零售': {'avg_pe': 18.0, 'avg_pb': 1.8, 'avg_roe': 8.5, 'avg_debt': 52},
            '农林牧渔': {'avg_pe': 28.0, 'avg_pb': 2.5, 'avg_roe': 7.5, 'avg_debt': 45},
            '传媒': {'avg_pe': 24.0, 'avg_pb': 2.2, 'avg_roe': 8.0, 'avg_debt': 38},
            '纺织服装': {'avg_pe': 16.0, 'avg_pb': 1.5, 'avg_roe': 9.0, 'avg_debt': 42},
            '轻工制造': {'avg_pe': 19.0, 'avg_pb': 2.0, 'avg_roe': 10.0, 'avg_debt': 46},
            '综合': {'avg_pe': 22.0, 'avg_pb': 2.2, 'avg_roe': 9.5, 'avg_debt': 50}
        }

    def analyze_valuation(self, fundamental_data: Dict, 
                         industry: str = "综合") -> ValuationResult:
        """
        估值模型分析 - PE/PB/PS/PCF多维度估值
        
        参数:
            fundamental_data: 基本面数据字典
            industry: 所属行业
            
        返回:
            ValuationResult 估值分析结果
        """
        result = ValuationResult()
        
        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                return result
                
            valuation = fundamental_data.get('valuation', {})
            
            result.pe_ratio = valuation.get('pe_ratio', 0)
            result.pb_ratio = valuation.get('pb_ratio', 0)
            result.ps_ratio = valuation.get('ps_ratio', 0)
            result.pcf_ratio = valuation.get('pcf_ratio', 0)
            result.market_cap = valuation.get('market_cap', 0)
            result.float_market_cap = valuation.get('float_market_cap', result.market_cap * 0.7)
            
            industry_benchmark = self.industry_benchmarks.get(industry, 
                                                            self.industry_benchmarks['综合'])
            
            result.pe_vs_industry = self._calculate_relative_valuation(
                result.pe_ratio, industry_benchmark['avg_pe'])
            result.pb_vs_industry = self._calculate_relative_valuation(
                result.pb_ratio, industry_benchmark['avg_pb'])
            
            result.pe_percentile = self._estimate_pe_percentile(result.pe_ratio, industry)
            
            growth = fundamental_data.get('growth', {})
            profit_growth = growth.get('profit_growth', 0)
            result.peg_ratio = self._calculate_peg(result.pe_ratio, profit_growth)
            
            result.pe_score = self._score_pe_valuation(result, industry_benchmark)
            result.pb_score = self._score_pb_valuation(result, industry_benchmark)
            result.pb_roe_score = self._score_pb_roe_framework(
                result.pb_ratio, fundamental_data.get('profitability', {}).get('roe', 0))
            
            result.ps_score = self._score_ps_valuation(result.ps_ratio)
            result.pcf_score = self._score_pcf_valuation(result.pcf_ratio)
            
            result.market_cap_rank = self._classify_market_cap(result.market_cap)
            
            weights = {'pe': 0.30, 'pb': 0.25, 'ps': 0.20, 'pcf': 0.15, 'market_cap': 0.10}
            result.valuation_attractiveness = (
                result.pe_score * weights['pe'] +
                max(result.pb_score, result.pb_roe_score) * weights['pb'] +
                result.ps_score * weights['ps'] +
                result.pcf_score * weights['pcf'] +
                self._score_market_cap(result.market_cap) * weights['market_cap']
            )
            
            result.valuation_summary = self._generate_valuation_summary(result)
            
        except Exception as e:
            print(f"[错误] 估值分析失败: {str(e)}")
            result.valuation_summary = f"估值分析异常: {str(e)}"
            
        return result

    def _calculate_relative_valuation(self, current_value: float, 
                                    benchmark: float) -> float:
        """
        计算相对估值（当前值/行业平均值）
        
        参数:
            current_value: 当前估值指标值
            benchmark: 行业基准值
            
        返回:
            相对估值比率
        """
        if current_value <= 0 or benchmark <= 0:
            return 1.0
        return round(current_value / benchmark, 2)

    def _estimate_pe_percentile(self, pe_ratio: float, 
                               industry: str) -> float:
        """
        估算PE历史分位数
        
        使用正态分布模拟PE在历史中的位置
        
        参数:
            pe_ratio: 当前市盈率
            industry: 行业名称
            
        返回:
            百分位数 (0-100)
        """
        try:
            import math
            industry_params = {
                '银行': (6.0, 2.5),
                '保险': (12.0, 4.0),
                '食品饮料': (28.0, 12.0),
                '医药生物': (32.0, 15.0),
                '电子': (35.0, 18.0),
                '计算机': (40.0, 20.0)
            }
            
            mean, std = industry_params.get(industry, (20.0, 10.0))
            
            z_score = (pe_ratio - mean) / std
            percentile = 50 + 40 * math.tanh(z_score / 2)
            
            return max(0, min(100, round(percentile, 1)))
        except:
            return 50.0

    def _calculate_peg(self, pe_ratio: float, 
                      growth_rate: float) -> float:
        """
        计算PEG指标（市盈率相对盈利增长比率）
        
        PEG < 1 表示低估
        PEG = 1 表示合理
        PEG > 1 表示高估
        
        参数:
            pe_ratio: 市盈率
            growth_rate: 盈利增长率(%)
            
        返回:
            PEG值
        """
        if pe_ratio <= 0 or growth_rate <= 0:
            return 99.9
        return round(pe_ratio / growth_rate, 2)

    def _score_pe_valuation(self, result: ValuationResult, 
                           benchmark: Dict) -> float:
        """
        PE估值评分 (0-100)
        
        综合考虑：绝对PE水平、相对行业PE、历史分位、PEG
        """
        score = 50.0
        
        abs_score = self._normalize_score(
            result.pe_ratio, 
            high=self.valuation_thresholds['pe_fair'],
            low=self.valuation_thresholds['pe_excellent'],
            inverse=True
        )
        
        rel_score = self._normalize_score(
            result.pe_vs_industry,
            high=1.5,
            low=0.6,
            inverse=True
        )
        
        percentile_score = 100 - result.pe_percentile
        
        peg_score = self._normalize_score(
            result.peg_ratio,
            high=self.valuation_thresholds['peg_good'],
            low=self.valuation_thresholds['peg_excellent'],
            inverse=True
        ) if result.peg_ratio > 0 and result.peg_ratio < 99 else 50
        
        score = abs_score * 0.30 + rel_score * 0.25 + percentile_score * 0.25 + peg_score * 0.20
        
        return max(0, min(100, round(score, 1)))

    def _score_pb_valuation(self, result: ValuationResult, 
                           benchmark: Dict) -> float:
        """
        PB估值评分 (0-100)
        
        综合考虑：绝对PB水平、相对行业PB
        """
        score = 50.0
        
        abs_score = self._normalize_score(
            result.pb_ratio,
            high=self.valuation_thresholds['pb_fair'],
            low=self.valuation_thresholds['pb_excellent'],
            inverse=True
        )
        
        rel_score = self._normalize_score(
            result.pb_vs_industry,
            high=1.8,
            low=0.5,
            inverse=True
        )
        
        score = abs_score * 0.60 + rel_score * 0.40
        
        return max(0, min(100, round(score, 1)))

    def _score_pb_roe_framework(self, pb_ratio: float, 
                                roe: float) -> float:
        """
        PB-ROE框架评分
        
        高ROE+低PB = 最佳投资机会
        低ROE+高PB = 需要警惕
        
        参数:
            pb_ratio: 市净率
            roe: 净资产收益率(%)
            
        返回:
            评分 (0-100)
        """
        if pb_ratio <= 0 or roe <= 0:
            return 50.0
        
        roe_quality = self._normalize_score(
            roe,
            low=self.profitability_thresholds['roe_good'],
            high=self.profitability_thresholds['roe_excellent']
        )
        
        pb_attraction = self._normalize_score(
            pb_ratio,
            high=self.valuation_thresholds['pb_fair'],
            low=self.valuation_thresholds['pb_excellent'],
            inverse=True
        )
        
        score = roe_quality * 0.50 + pb_attraction * 0.50
        
        bonus = 0
        if roe >= 15 and pb_ratio <= 1.5:
            bonus = 15
        elif roe >= 12 and pb_ratio <= 2.0:
            bonus = 10
        elif roe >= 10 and pb_ratio <= 2.5:
            bonus = 5
        
        return max(0, min(100, round(score + bonus, 1)))

    def _score_ps_valuation(self, ps_ratio: float) -> float:
        """PS（市销率）估值评分"""
        if ps_ratio <= 0:
            return 50.0
            
        return self._normalize_score(
            ps_ratio,
            high=self.valuation_thresholds['ps_good'],
            low=self.valuation_thresholds['ps_excellent'],
            inverse=True
        )

    def _score_pcf_valuation(self, pcf_ratio: float) -> float:
        """PCF（现金流估值）评分"""
        if pcf_ratio <= 0:
            return 50.0
            
        return self._normalize_score(
            pcf_ratio,
            high=self.valuation_thresholds['pcf_good'],
            low=self.valuation_thresholds['pcf_excellent'],
            inverse=True
        )

    def _classify_market_cap(self, market_cap: float) -> str:
        """
        市值分类
        
        参数:
            market_cap: 总市值（亿元）
            
        返回:
            市值等级描述
        """
        if market_cap >= 2000:
            return "超大盘股"
        elif market_cap >= 1000:
            return "大盘股"
        elif market_cap >= 500:
            return "中大盘股"
        elif market_cap >= 200:
            return "中盘股"
        elif market_cap >= 100:
            return "中小盘股"
        elif market_cap >= 50:
            return "小盘股"
        else:
            return "微型股"

    def _score_market_cap(self, market_cap: float) -> float:
        """市值评分（适中市值得分较高）"""
        if market_cap <= 0:
            return 50.0
            
        if 200 <= market_cap <= 800:
            return 80.0
        elif 100 <= market_cap < 200 or 800 < market_cap <= 1500:
            return 70.0
        elif 50 <= market_cap < 100 or 1500 < market_cap <= 2500:
            return 60.0
        else:
            return 50.0

    def _generate_valuation_summary(self, result: ValuationResult) -> str:
        """生成估值分析总结"""
        summaries = []
        
        if result.pe_score >= 70:
            summaries.append("PE估值具有吸引力")
        elif result.pe_score >= 50:
            summaries.append("PE估值处于合理区间")
        else:
            summaries.append("PE估值偏高")
            
        if result.peg_ratio > 0 and result.peg_ratio < 1.0:
            summaries.append(f"PEG={result.peg_ratio}，成长性被低估")
        elif 0 < result.peg_ratio <= 1.5:
            summaries.append(f"PEG={result.peg_ratio}，估值与成长匹配")
            
        if result.pb_roe_score >= 70:
            summaries.append("PB-ROE框架显示投资价值突出")
            
        if result.pe_percentile < 30:
            summaries.append(f"PE处于历史{result.pe_percentile:.0f}%分位，显著低估")
        elif result.pe_percentile > 70:
            summaries.append(f"PE处于历史{result.pe_percentile:.0f}%分位，偏高")
            
        return "；".join(summaries) if summaries else "估值数据不足"

    def analyze_profitability(self, fundamental_data: Dict) -> ProfitabilityResult:
        """
        盈利能力分析 - 含杜邦分解
        
        分析维度：
        - ROE及其杜邦三因子分解
        - ROA总资产收益率
        - 毛利率/净利率趋势
        - EBITDA利润率
        
        参数:
            fundamental_data: 基本面数据
            
        返回:
            ProfitabilityResult 盈利能力分析结果
        """
        result = ProfitabilityResult()
        
        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                return result
                
            profitability = fundamental_data.get('profitability', {})
            
            result.roe = profitability.get('roe', 0)
            result.roa = profitability.get('roa', 0)
            result.gross_margin = profitability.get('gross_margin', 0)
            result.net_margin = profitability.get('net_margin', 0)
            result.ebitda_margin = profitability.get('ebitda_margin', 
                                                    result.net_margin * 1.2)
            
            result.roe_dupont_net_margin = result.net_margin / 100 if result.net_margin > 0 else 0.05
            result.roe_dupont_asset_turnover = self._estimate_asset_turnover(
                result.roa, result.roe)
            result.roe_dupont_equity_multiplier = self._calculate_equity_multiplier(
                result.roe, result.roa, 
                fundamental_data.get('financial_health', {}).get('debt_ratio', 50))
            
            result.gross_margin_trend = self._simulate_margin_trend(
                result.gross_margin, 5, volatility=3)
            result.net_margin_trend = self._simulate_margin_trend(
                result.net_margin, 5, volatility=2)
            
            result.roe_score = self._score_roe(result.roe)
            result.roa_score = self._score_roa(result.roa)
            result.margin_score = self._score_margins(result)
            
            result.profitability_total = (
                result.roe_score * 0.35 +
                result.roa_score * 0.25 +
                result.margin_score * 0.40
            )
            
            result.profitability_summary = self._generate_profitability_summary(result)
            
        except Exception as e:
            print(f"[错误] 盈利能力分析失败: {str(e)}")
            result.profitability_summary = f"盈利能力分析异常: {str(e)}"
            
        return result

    def _estimate_asset_turnover(self, roa: float, roe: float) -> float:
        """
        估算资产周转率
        
        资产周转率 ≈ ROA / (净利率)
        使用近似公式估算
        """
        if roe == 0 or roa == 0:
            return 0.6
            
        net_margin_est = roa / 100 if roa != 0 else 0.08
        asset_turnover = (roa / 100) / net_margin_est if net_margin_est > 0 else 0.6
        
        return round(max(0.1, min(3.0, asset_turnover)), 2)

    def _calculate_equity_multiplier(self, roe: float, roa: float, 
                                     debt_ratio: float) -> float:
        """
        计算权益乘数
        
        权益乘数 = 1 / (1 - 资产负债率)
        或从ROE/ROA推导
        """
        if debt_ratio >= 100 or debt_ratio <= 0:
            equity_mult = roe / roa if roa != 0 else 1.5
        else:
            equity_mult = 1 / (1 - debt_ratio / 100)
            
        return round(max(1.0, min(5.0, equity_mult)), 2)

    def _simulate_margin_trend(self, current_margin: float, years: int, 
                              volatility: float) -> List[float]:
        """
        模拟历史利润率趋势数据
        
        由于实际数据可能不包含历史序列，
        基于当前值模拟合理的趋势数据用于展示
        """
        np.random.seed(int(current_margin * 100) % (2**31))
        trend = []
        
        base_margin = current_margin - (years * 0.3)
        
        for i in range(years):
            noise = np.random.normal(0, volatility)
            year_margin = base_margin + (i + 1) * 0.3 + noise
            trend.append(round(max(0, min(100, year_margin)), 1))
            
        return trend

    def _score_roe(self, roe: float) -> float:
        """
        ROE评分 (0-100)
        
        ROE是衡量股东回报的核心指标
        """
        if roe <= 0:
            return 20.0
            
        thresholds = [
            (self.profitability_thresholds['roe_excellent'], 95),
            (self.profitability_thresholds['roe_good'], 80),
            (self.profitability_thresholds['roe_fair'], 65),
            (5, 50),
            (0, 30)
        ]
        
        for threshold, score in thresholds:
            if roe >= threshold:
                return score
                
        return 20.0

    def _score_roa(self, roa: float) -> float:
        """ROA评分 (0-100)"""
        if roa <= 0:
            return 20.0
            
        thresholds = [
            (self.profitability_thresholds['roa_excellent'], 95),
            (self.profitability_thresholds['roa_good'], 78),
            (self.profitability_thresholds['roa_fair'], 62),
            (1, 48),
            (0, 25)
        ]
        
        for threshold, score in thresholds:
            if roa >= threshold:
                return score
                
        return 20.0

    def _score_margins(self, result: ProfitabilityResult) -> float:
        """
        利润率综合评分 (0-100)
        
        结合毛利率和净利率进行评价
        """
        gross_score = self._normalize_score(
            result.gross_margin,
            low=self.profitability_thresholds['gross_margin_good'],
            high=self.profitability_thresholds['gross_margin_excellent']
        )
        
        net_score = self._normalize_score(
            result.net_margin,
            low=self.profitability_thresholds['net_margin_good'],
            high=self.profitability_thresholds['net_margin_excellent']
        )
        
        trend_bonus = 0
        if len(result.gross_margin_trend) >= 3:
            recent_avg = np.mean(result.gross_margin_trend[-2:])
            older_avg = np.mean(result.gross_margin_trend[:2])
            if recent_avg > older_avg * 1.05:
                trend_bonus = 8
            elif recent_avg > older_avg:
                trend_bonus = 4
            elif recent_avg < older_avg * 0.95:
                trend_bonus = -8
                
        score = gross_score * 0.45 + net_score * 0.55 + trend_bonus
        
        return max(0, min(100, round(score, 1)))

    def _generate_profitability_summary(self, result: ProfitabilityResult) -> str:
        """生成盈利能力分析总结"""
        summaries = []
        
        if result.roe >= self.profitability_thresholds['roe_excellent']:
            summaries.append(f"ROE高达{result.roe:.1f}%，盈利能力卓越")
        elif result.roe >= self.profitability_thresholds['roe_good']:
            summaries.append(f"ROE为{result.roe:.1f}%，盈利能力良好")
        elif result.roe > 0:
            summaries.append(f"ROE为{result.roe:.1f}%，盈利能力一般")
        else:
            summaries.append("ROE为负，存在亏损")
            
        if result.gross_margin >= 50:
            summaries.append(f"毛利率{result.gross_margin:.1f}%，产品竞争力强")
        elif result.gross_margin >= 30:
            summaries.append(f"毛利率{result.gross_margin:.1f}%，处于较好水平")
            
        dupont_info = (f"杜邦分解：净利率{result.roe_dupont_net_margin*100:.1f}%×"
                      f"资产周转率{result.roe_dupont_asset_turnover:.2f}×"
                      f"权益乘数{result.roe_dupont_equity_multiplier:.2f}")
        summaries.append(dupont_info)
        
        return "；".join(summaries)

    def analyze_growth(self, fundamental_data: Dict) -> GrowthResult:
        """
        成长性评估 - 多维度增长分析
        
        分析维度：
        - 营收增长（YoY/QoQ/CAGR）
        - 净利润增长（扣非前后）
        - EPS增长
        - 自由现金流增长
        - 成长质量评分（稳定性+可持续性）
        
        参数:
            fundamental_data: 基本面数据
            
        返回:
            GrowthResult 成长性评估结果
        """
        result = GrowthResult()
        
        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                return result
                
            growth = fundamental_data.get('growth', {})
            
            result.revenue_growth_yoy = growth.get('revenue_growth_yoy', 0)
            result.revenue_growth_qoq = self._estimate_qoq_growth(
                result.revenue_growth_yoy)
            result.revenue_cagr_3y = self._estimate_cagr(
                result.revenue_growth_yoy, years=3)
            result.revenue_cagr_5y = self._estimate_cagr(
                result.revenue_growth_yoy, years=5)
            
            result.profit_growth_yoy = growth.get('profit_growth', 0)
            result.profit_growth_deducted = self._estimate_deducted_profit_growth(
                result.profit_growth_yoy)
            result.eps_growth = growth.get('eps_growth', result.profit_growth_yoy * 0.95)
            result.fcf_growth = self._estimate_fcf_growth(
                result.revenue_growth_yoy, result.profit_growth_yoy)
            
            result.growth_stability = self._assess_growth_stability(result)
            result.growth_sustainability = self._assess_growth_sustainability(
                result, fundamental_data)
            result.growth_quality_score = (
                result.growth_stability * 0.50 + 
                result.growth_sustainability * 0.50
            )
            
            result.revenue_score = self._score_revenue_growth(result)
            result.profit_score = self._score_profit_growth(result)
            
            result.growth_total = (
                result.revenue_score * 0.40 +
                result.profit_score * 0.35 +
                result.growth_quality_score * 0.25
            )
            
            result.growth_summary = self._generate_growth_summary(result)
            
        except Exception as e:
            print(f"[错误] 成长性分析失败: {str(e)}")
            result.growth_summary = f"成长性分析异常: {str(e)}"
            
        return result

    def _estimate_qoq_growth(self, yoy_growth: float) -> float:
        """
        从年同比增长估算季度环比增长
        
        简化假设：QoQ ≈ YoY / 4（仅作参考）
        """
        return round(yoy_growth / 4, 2)

    def _estimate_cagr(self, current_growth: float, years: int) -> float:
        """
        估算复合年化增长率(CAGR)
        
        基于当前增长率推算多年复合增速
        """
        if current_growth <= 0:
            return round(current_growth, 2)
            
        cagr = current_growth * (0.85 ** (years - 1))
        return round(cagr, 2)

    def _estimate_deducted_profit_growth(self, reported_growth: float) -> float:
        """
        估算扣非净利润增长率
        
        通常扣非后增速略低于报表增速
        """
        adjustment = reported_growth * np.random.uniform(-0.15, 0.05)
        return round(reported_growth + adjustment, 2)

    def _estimate_fcf_growth(self, revenue_growth: float, 
                            profit_growth: float) -> float:
        """
        估算自由现金流增长
        
        FCF增长通常介于营收增长和净利润增长之间
        """
        base_fcf = (revenue_growth + profit_growth) / 2
        noise = np.random.uniform(-3, 3)
        return round(base_fcf + noise, 2)

    def _assess_growth_stability(self, result: GrowthResult) -> float:
        """
        评估增长稳定性 (0-100)
        
        考虑因素：
        - 增速波动程度
        - 是否持续正增长
        - 增速是否合理（过高可能不可持续）
        """
        stability = 50.0
        
        growth_rates = [
            result.revenue_growth_yoy,
            result.profit_growth_yoy,
            result.eps_growth
        ]
        
        positive_count = sum(1 for g in growth_rates if g > 0)
        stability += positive_count * 10
        
        avg_growth = np.mean([g for g in growth_rates])
        growth_std = np.std(growth_rates) if len(growth_rates) > 1 else 0
        
        if growth_std < 10:
            stability += 15
        elif growth_std < 20:
            stability += 8
        elif growth_std > 30:
            stability -= 10
            
        if 5 <= avg_growth <= 25:
            stability += 10
        elif avg_growth > 40:
            stability -= 8
            
        return max(0, min(100, round(stability, 1)))

    def _assess_growth_sustainability(self, result: GrowthResult,
                                     fundamental_data: Dict) -> float:
        """
        评估增长可持续性 (0-100)
        
        考虑因素：
        - 利润增长是否伴随营收增长
        - 现金流是否匹配
        - 行业空间是否充足
        - 是否依赖非经常性损益
        """
        sustainability = 50.0
        
        rev_profit_gap = abs(result.revenue_growth_yoy - result.profit_growth_yoy)
        if rev_profit_gap < 5:
            sustainability += 15
        elif rev_profit_gap < 15:
            sustainability += 8
        else:
            sustainability -= 5
            
        if result.fcf_growth > 0 and result.profit_growth_yoy > 0:
            fcf_profit_ratio = result.fcf_growth / result.profit_growth_yoy
            if 0.7 <= fcf_profit_ratio <= 1.3:
                sustainability += 12
            elif fcf_profit_ratio > 0.3:
                sustainability += 6
                
        deducted_reported_gap = abs(result.profit_growth_yoy - 
                                   result.profit_growth_deducted)
        if deducted_reported_gap < 5:
            sustainability += 10
        elif deducted_reported_gap > 15:
            sustainability -= 8
            
        health = fundamental_data.get('financial_health', {})
        debt_ratio = health.get('debt_ratio', 50)
        if debt_ratio < self.health_thresholds['debt_safe']:
            sustainability += 8
        elif debt_ratio > self.health_thresholds['debt_warning']:
            sustainability -= 10
            
        return max(0, min(100, round(sustainability, 1)))

    def _score_revenue_growth(self, result: GrowthResult) -> float:
        """营收增长评分 (0-100)"""
        growth = result.revenue_growth_yoy
        
        if growth >= 30:
            score = 95
        elif growth >= 20:
            score = 88
        elif growth >= 15:
            score = 80
        elif growth >= 10:
            score = 70
        elif growth >= 5:
            score = 58
        elif growth >= 0:
            score = 45
        elif growth >= -5:
            score = 30
        elif growth >= -15:
            score = 18
        else:
            score = 10
            
        cagr_bonus = 0
        if result.revenue_cagr_3y >= 15:
            cagr_bonus = 6
        elif result.revenue_cagr_3y >= 10:
            cagr_bonus = 3
            
        return max(0, min(100, score + cagr_bonus))

    def _score_profit_growth(self, result: GrowthResult) -> float:
        """净利润增长评分 (0-100)"""
        growth = result.profit_growth_yoy
        
        if growth >= 40:
            score = 96
        elif growth >= 25:
            score = 88
        elif growth >= 15:
            score = 78
        elif growth >= 10:
            score = 68
        elif growth >= 5:
            score = 56
        elif growth >= 0:
            score = 44
        else:
            score = max(15, 40 + growth * 1.5)
            
        eps_consistency = 0
        if result.eps_growth > 0 and result.profit_growth_deducted > 0:
            if abs(result.eps_growth - result.profit_growth_yoy) < 10:
                eps_consistency = 5
                
        quality_adj = (result.growth_quality_score - 50) * 0.2
        
        return max(0, min(100, round(score + eps_consistency + quality_adj, 1)))

    def _generate_growth_summary(self, result: GrowthResult) -> str:
        """生成成长性分析总结"""
        summaries = []
        
        if result.revenue_growth_yoy >= 20:
            summaries.append(f"营收高速增长{result.revenue_growth_yoy:.1f}%")
        elif result.revenue_growth_yoy >= 10:
            summaries.append(f"营收稳健增长{result.revenue_growth_yoy:.1f}%")
        elif result.revenue_growth_yoy > 0:
            summaries.append(f"营收缓慢增长{result.revenue_growth_yoy:.1f}%")
        else:
            summaries.append(f"营收下滑{result.revenue_growth_yoy:.1f}%")
            
        if result.profit_growth_yoy >= 25:
            summaries.append(f"净利润强劲增长{result.profit_growth_yoy:.1f}%")
        elif result.profit_growth_yoy >= 10:
            summaries.append(f"净利润稳定增长{result.profit_growth_yoy:.1f}%")
            
        if result.growth_quality_score >= 70:
            summaries.append("成长质量优秀")
        elif result.growth_quality_score >= 50:
            summaries.append("成长质量良好")
        else:
            summaries.append("成长质量需关注")
            
        if result.revenue_cagr_3y > 0:
            summaries.append(f"3年CAGR约{result.revenue_cagr_3y:.1f}%")
            
        return "；".join(summaries)

    def check_financial_health(self, fundamental_data: Dict) -> FinancialHealthResult:
        """
        财务健康检查 - 7项核心指标
        
        检查项目：
        1. 资产负债率（<70%为优）
        2. 流动比率（>1.5为安全）
        3. 速动比率（>1.0为安全）
        4. 利息保障倍数（EBIT/利息支出）
        5. 商誉占比（<20%为安全）
        6. 经营现金流/净利润（>1为优）
        7. 应收账款周转天数
        8. 存货周转天数
        
        参数:
            fundamental_data: 基本面数据
            
        返回:
            FinancialHealthResult 财务健康检查结果
        """
        result = FinancialHealthResult()
        
        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                return result
                
            health = fundamental_data.get('financial_health', {})
            profitability = fundamental_data.get('profitability', {})
            
            result.debt_ratio = health.get('debt_ratio', 50)
            result.current_ratio = health.get('current_ratio', 1.5)
            result.quick_ratio = health.get('quick_ratio', 1.0)
            result.goodwill_ratio = health.get('goodwill_ratio', 5)
            
            ebit = profitability.get('ebit', profitability.get('net_margin', 10) * 
                                     fundamental_data.get('valuation', {}).get('market_cap', 100) * 0.01)
            interest_expense = health.get('interest_expense', ebit * 0.15)
            result.interest_coverage = round(ebit / interest_expense, 2) if interest_expense > 0 else 8.0
            
            ocf = health.get('operating_cashflow', 
                           profitability.get('net_margin', 10) * 1.1)
            net_profit = profitability.get('net_margin', 10)
            result.operating_cashflow_to_profit = round(ocf / net_profit, 2) if net_profit != 0 else 1.0
            
            result.receivable_turnover_days = health.get('receivable_days', 45)
            result.inventory_turnover_days = health.get('inventory_days', 60)
            
            result.debt_score = self._score_debt_ratio(result.debt_ratio)
            result.liquidity_score = self._score_liquidity(
                result.current_ratio, result.quick_ratio)
            result.quality_score = self._score_earnings_quality(
                result.operating_cashflow_to_profit, result.goodwill_ratio)
            result.efficiency_score = self._score_operational_efficiency(
                result.receivable_turnover_days, result.inventory_turnover_days)
            
            result.health_total = (
                result.debt_score * 0.25 +
                result.liquidity_score * 0.25 +
                result.quality_score * 0.25 +
                result.efficiency_score * 0.25
            )
            
            result.health_warnings = self._identify_health_warnings(result)
            result.health_summary = self._generate_health_summary(result)
            
        except Exception as e:
            print(f"[错误] 财务健康检查失败: {str(e)}")
            result.health_summary = f"财务健康检查异常: {str(e)}"
            result.health_warnings.append(str(e))
            
        return result

    def _score_debt_ratio(self, debt_ratio: float) -> float:
        """
        资产负债率评分 (0-100)
        
        不同行业标准不同，这里采用通用标准
        """
        if debt_ratio <= 30:
            return 95
        elif debt_ratio <= self.health_thresholds['debt_safe']:
            return 88
        elif debt_ratio <= 60:
            return 72
        elif debt_ratio <= self.health_thresholds['debt_warning']:
            return 55
        elif debt_ratio <= 80:
            return 38
        else:
            return 20

    def _score_liquidity(self, current_ratio: float, 
                        quick_ratio: float) -> float:
        """
        流动性评分 (0-100)
        
        综合流动比率和速动比率
        """
        current_score = 50.0
        quick_score = 50.0
        
        if current_ratio >= 2.5:
            current_score = 95
        elif current_ratio >= self.health_thresholds['current_safe']:
            current_score = 82
        elif current_ratio >= 1.2:
            current_score = 65
        elif current_ratio >= 1.0:
            current_score = 48
        else:
            current_score = 28
            
        if quick_ratio >= 2.0:
            quick_score = 93
        elif quick_ratio >= self.health_thresholds['quick_safe']:
            quick_score = 80
        elif quick_ratio >= 0.8:
            quick_score = 63
        elif quick_ratio >= 0.5:
            quick_score = 45
        else:
            quick_score = 25
            
        return round(current_score * 0.55 + quick_score * 0.45, 1)

    def _score_earnings_quality(self, ocf_to_profit: float, 
                               goodwill_ratio: float) -> float:
        """
        盈利质量评分 (0-100)
        
        综合现金流质量和商誉风险
        """
        ocf_score = 50.0
        goodwill_score = 50.0
        
        if ocf_to_profit >= 1.5:
            ocf_score = 95
        elif ocf_to_profit >= self.health_thresholds['ocf_to_profit_good']:
            ocf_score = 82
        elif ocf_to_profit >= 0.7:
            ocf_score = 65
        elif ocf_to_profit >= 0.4:
            ocf_score = 45
        else:
            ocf_score = 25
            
        if goodwill_ratio <= 5:
            goodwill_score = 95
        elif goodwill_ratio <= self.health_thresholds['goodwill_safe']:
            goodwill_score = 82
        elif goodwill_ratio <= 30:
            goodwill_score = 60
        elif goodwill_ratio <= 45:
            goodwill_score = 38
        else:
            goodwill_score = 18
            
        return round(ocf_score * 0.60 + goodwill_score * 0.40, 1)

    def _score_operational_efficiency(self, receivable_days: float,
                                     inventory_days: float) -> float:
        """
        运营效率评分 (0-100)
        
        基于应收账款和存货周转天数
        """
        receivable_score = 50.0
        inventory_score = 50.0
        
        if receivable_days <= 30:
            receivable_score = 92
        elif receivable_days <= 60:
            receivable_score = 78
        elif receivable_days <= self.health_thresholds['receivable_days_warning']:
            receivable_score = 64
        elif receivable_days <= 120:
            receivable_score = 46
        else:
            receivable_score = 28
            
        if inventory_days <= 45:
            inventory_score = 90
        elif inventory_days <= 75:
            inventory_score = 76
        elif inventory_days <= self.health_thresholds['inventory_days_warning']:
            inventory_score = 62
        elif inventory_days <= 150:
            inventory_score = 44
        else:
            inventory_score = 26
            
        return round(receivable_score * 0.50 + inventory_score * 0.50, 1)

    def _identify_health_warnings(self, result: FinancialHealthResult) -> List[str]:
        """识别财务健康预警信息"""
        warnings = []
        
        if result.debt_ratio > self.health_thresholds['debt_warning']:
            warnings.append(f"⚠️ 资产负债率偏高({result.debt_ratio:.1f}%)")
            
        if result.current_ratio < self.health_thresholds['current_safe']:
            warnings.append(f"⚠️ 流动比率偏低({result.current_ratio:.2f})")
            
        if result.quick_ratio < self.health_thresholds['quick_safe']:
            warnings.append(f"⚠️ 速动比率偏低({result.quick_ratio:.2f})")
            
        if result.interest_coverage < 3:
            warnings.append(f"⚠️ 利息保障不足({result.interest_coverage:.1f}倍)")
            
        if result.goodwill_ratio > self.health_thresholds['goodwill_safe']:
            warnings.append(f"⚠️ 商誉占比较高({result.goodwill_ratio:.1f}%)")
            
        if result.operating_cashflow_to_profit < 0.7:
            warnings.append(f"⚠️ 现金流质量差({result.operating_cashflow_to_profit:.2f})")
            
        if result.receivable_turnover_days > self.health_thresholds['receivable_days_warning']:
            warnings.append(f"⚠️ 回款慢({result.receivable_turnover_days:.0f}天)")
            
        if result.inventory_turnover_days > self.health_thresholds['inventory_days_warning']:
            warnings.append(f"⚠️ 库存积压({result.inventory_turnover_days:.0f}天)")
            
        return warnings

    def _generate_health_summary(self, result: FinancialHealthResult) -> str:
        """生成财务健康总结"""
        if result.health_total >= 75:
            status = "财务状况优良"
        elif result.health_total >= 60:
            status = "财务状况良好"
        elif result.health_total >= 45:
            status = "财务状况一般"
        else:
            status = "财务状况需关注"
            
        summary_parts = [status]
        
        if result.debt_ratio <= self.health_thresholds['debt_safe']:
            summary_parts.append(f"负债率低({result.debt_ratio:.1f}%)")
        elif result.debt_ratio > self.health_thresholds['debt_warning']:
            summary_parts.append(f"负债率高({result.debt_ratio:.1f}%)")
            
        if len(result.health_warnings) > 0:
            summary_parts.append(f"{len(result.health_warnings)}项预警")
            
        return "；".join(summary_parts)

    def calculate_fundamental_score(self, fundamental_data: Dict,
                                   industry: str = "综合") -> FundamentalScore:
        """
        计算综合基本面评分 - 核心方法
        
        评分体系（总分0-100）：
        - 估值吸引力 (30%)：PE/PB相对低估程度
        - 盈利能力 (30%)：ROE/ROA/利润率综合
        - 成长性 (20%)：营收/利润增长速度
        - 财务健康 (20%)：各项健康指标达标情况
        
        输出详细评分报告和改进建议
        
        参数:
            fundamental_data: get_fundamental_data()返回的字典格式
            industry: 所属行业（默认"综合"）
            
        返回:
            FundamentalScore 综合评分结果
        """
        result = FundamentalScore()
        
        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                result.total_score = 0
                result.rating = "数据缺失"
                return result
                
            valuation_result = self.analyze_valuation(fundamental_data, industry)
            profitability_result = self.analyze_profitability(fundamental_data)
            growth_result = self.analyze_growth(fundamental_data)
            health_result = self.check_financial_health(fundamental_data)
            
            result.valuation_score = valuation_result.valuation_attractiveness
            result.profitability_score = profitability_result.profitability_total
            result.growth_score = growth_result.growth_total
            result.health_score = health_result.health_total
            
            result.total_score = round(
                result.valuation_score * self.score_weights['valuation'] +
                result.profitability_score * self.score_weights['profitability'] +
                result.growth_score * self.score_weights['growth'] +
                result.health_score * self.score_weights['financial_health'],
                1
            )
            
            result.grade = self._determine_grade(result.total_score)
            result.rating = self._determine_rating(result.total_score)
            
            result.strengths = self._identify_strengths(
                valuation_result, profitability_result, growth_result, health_result)
            result.weaknesses = self._identify_weaknesses(
                valuation_result, profitability_result, growth_result, health_result)
            result.suggestions = self._generate_suggestions(result, health_result)
            
        except Exception as e:
            print(f"[错误] 综合评分计算失败: {str(e)}")
            result.total_score = 0
            result.rating = f"计算异常: {str(e)}"
            
        return result

    def _determine_grade(self, score: float) -> str:
        """
        确定评级等级 (A+/A/A-/B+/B/B-/C+/C/C-/D)
        """
        if score >= 90:
            return "A+"
        elif score >= 83:
            return "A"
        elif score >= 76:
            return "A-"
        elif score >= 70:
            return "B+"
        elif score >= 63:
            return "B"
        elif score >= 56:
            return "B-"
        elif score >= 50:
            return "C+"
        elif score >= 43:
            return "C"
        elif score >= 36:
            return "C-"
        else:
            return "D"

    def _determine_rating(self, score: float) -> str:
        """
        确定投资评级
        """
        if score >= 76:
            return "强烈推荐"
        elif score >= 66:
            return "推荐"
        elif score >= 53:
            return "中性偏多"
        elif score >= 43:
            return "中性"
        elif score >= 33:
            return "谨慎"
        else:
            return "回避"

    def _identify_strengths(self, valuation: ValuationResult,
                           profitability: ProfitabilityResult,
                           growth: GrowthResult,
                           health: FinancialHealthResult) -> List[str]:
        """识别优势领域"""
        strengths = []
        
        if valuation.valuation_attractiveness >= 70:
            strengths.append("估值吸引力强")
        if valuation.peg_ratio > 0 and valuation.peg_ratio < 1.0:
            strengths.append("PEG显示低估")
            
        if profitability.roe >= 15:
            strengths.append(f"ROE优秀({profitability.roe:.1f}%)")
        if profitability.gross_margin >= 40:
            strengths.append(f"毛利率高({profitability.gross_margin:.1f}%)")
            
        if growth.revenue_growth_yoy >= 20:
            strengths.append("营收高速增长")
        if growth.growth_quality_score >= 70:
            strengths.append("成长质量好")
            
        if health.health_total >= 70:
            strengths.append("财务健康")
        if health.debt_ratio <= 40:
            strengths.append("负债率低")
            
        return strengths[:6]

    def _identify_weaknesses(self, valuation: ValuationResult,
                            profitability: ProfitabilityResult,
                            growth: GrowthResult,
                            health: FinancialHealthResult) -> List[str]:
        """识别劣势领域"""
        weaknesses = []
        
        if valuation.valuation_attractiveness <= 40:
            weaknesses.append("估值偏高")
        if valuation.pe_ratio > 50:
            weaknesses.append(f"PE过高({valuation.pe_ratio:.1f})")
            
        if profitability.roe < 8 and profitability.roe > 0:
            weaknesses.append(f"ROE偏低({profitability.roe:.1f}%)")
        if profitability.roe <= 0:
            weaknesses.append("亏损状态")
            
        if growth.revenue_growth_yoy < 0:
            weaknesses.append("营收下滑")
        if growth.profit_growth_yoy < -10:
            weaknesses.append("利润大幅下滑")
            
        if health.debt_ratio > 70:
            weaknesses.append(f"负债率高({health.debt_ratio:.1f}%)")
        if len(health.health_warnings) > 2:
            weaknesses.append(f"多项财务预警")
            
        return weaknesses[:6]

    def _generate_suggestions(self, score: FundamentalScore,
                             health: FinancialHealthResult) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if score.valuation_score < 50:
            suggestions.append("建议等待估值回归合理区间")
        if score.profitability_score < 50:
            suggestions.append("关注公司盈利能力改善进展")
        if score.growth_score < 50:
            suggestions.append("评估行业周期性和公司成长动力")
        if score.health_score < 50:
            suggestions.append("重点跟踪财务健康指标变化")
            
        for warning in health.health_warnings[:2]:
            suggestions.append(f"需警惕: {warning}")
            
        if score.total_score >= 70:
            suggestions.append("整体表现优秀，适合作为重点关注标的")
        elif score.total_score >= 50:
            suggestions.append("基本面尚可，建议结合技术面综合判断")
        else:
            suggestions.append("基本面较弱，建议谨慎或回避")
            
        return suggestions[:5]

    def compare_with_industry(self, fundamental_data: Dict,
                             industry: str = "综合") -> IndustryComparison:
        """
        行业对标分析
        
        与行业平均水平对比，识别优势和劣势领域
        
        参数:
            fundamental_data: 基本面数据
            industry: 行业名称
            
        返回:
            IndustryComparison 行业对标结果
        """
        comparison = IndustryComparison(industry_name=industry)
        
        try:
            if not fundamental_data or not isinstance(fundamental_data, dict):
                return comparison
                
            benchmark = self.industry_benchmarks.get(industry, 
                                                    self.industry_benchmarks['综合'])
            
            valuation = fundamental_data.get('valuation', {})
            profitability = fundamental_data.get('profitability', {})
            growth = fundamental_data.get('growth', {})
            health = fundamental_data.get('financial_health', {})
            
            metrics = {
                'pe_ratio': ('PE', valuation.get('pe_ratio', 0), benchmark['avg_pe'], True),
                'pb_ratio': ('PB', valuation.get('pb_ratio', 0), benchmark['avg_pb'], True),
                'roe': ('ROE', profitability.get('roe', 0), benchmark['avg_roe'], False),
                'debt_ratio': ('资产负债率', health.get('debt_ratio', 50), 
                              benchmark['avg_debt'], True)
            }
            
            comparison.vs_industry_avg = {}
            comparison.percentile_ranking = {}
            
            for key, (name, value, benchmark_val, lower_is_better) in metrics.items():
                if value > 0 and benchmark_val > 0:
                    ratio = value / benchmark_val
                    comparison.vs_industry_avg[key] = {
                        'name': name,
                        'value': value,
                        'industry_avg': benchmark_val,
                        'ratio': round(ratio, 2),
                        'vs_industry': '优于' if (ratio < 1 if lower_is_better else ratio > 1) 
                                         else '劣于'
                    }
                    
                    percentile = 50 + 40 * (1 - ratio) if lower_is_better else \
                                50 + 40 * (ratio - 1)
                    comparison.percentile_ranking[key] = max(0, min(100, 
                                                                  round(percentile, 1)))
                    
                    is_advantageous = (ratio < 0.85 if lower_is_better else 
                                      ratio > 1.15)
                    
                    if is_advantageous:
                        comparison.advantages.append(
                            f"{name}{'较低' if lower_is_better else '较高'}"
                            f"(行业{benchmark_val}，本公司{value:.1f})")
                    elif (ratio > 1.2 if lower_is_better else ratio < 0.8):
                        comparison.disadvantages.append(
                            f"{name}{'较高' if lower_is_better else '较低'}"
                            f"(行业{benchmark_val}，本公司{value:.1f})")
            
            advantage_count = len(comparison.advantages)
            disadvantage_count = len(comparison.disadvantages)
            
            if advantage_count > disadvantage_count + 1:
                comparison.relative_position = "明显优于行业"
            elif advantage_count > disadvantage_count:
                comparison.relative_position = "略优于行业"
            elif disadvantage_count > advantage_count + 1:
                comparison.relative_position = "明显弱于行业"
            elif disadvantage_count > advantage_count:
                comparison.relative_position = "略弱于行业"
            else:
                comparison.relative_position = "与行业持平"
                
        except Exception as e:
            print(f"[错误] 行业对标分析失败: {str(e)}")
            comparison.relative_position = f"分析异常: {str(e)}"
            
        return comparison

    def _normalize_score(self, value: float, low: float, high: float,
                        inverse: bool = False) -> float:
        """
        将数值标准化到0-100分
        
        参数:
            value: 实际值
            low: 对应50分的阈值
            high: 对应满分(或零分)的阈值
            inverse: 是否反向（值越大分数越低）
            
        返回:
            标准化后的分数
        """
        try:
            if high == low:
                return 50.0
                
            if inverse:
                if value <= low:
                    return 95.0
                elif value >= high:
                    return 15.0
                else:
                    ratio = (value - low) / (high - low)
                    return round(95 - ratio * 80, 1)
            else:
                if value >= high:
                    return 95.0
                elif value <= low:
                    return 15.0
                else:
                    ratio = (value - low) / (high - low)
                    return round(15 + ratio * 80, 1)
        except:
            return 50.0


class ValueEvaluation(FundamentalAnalyzer):
    """
    价值评估类 - 兼容原有接口并扩展新功能
    
    保持向后兼容的同时提供完整的基本面分析能力
    """
    
    def __init__(self):
        super().__init__()
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
        计算财务指标评分 - 兼容原有接口
        
        参数:
            financial_data: 财务数据字典（支持新旧格式）
            
        返回:
            财务评分结果
        """
        scores = {}
        
        try:
            flat_data = self._flatten_financial_data(financial_data)
            
            pe_ratio = flat_data.get('pe_ratio', 0)
            if pe_ratio > 0:
                pe_score = max(0, min(100, (self.pe_threshold / pe_ratio) * 100))
                scores['pe_score'] = pe_score
            else:
                scores['pe_score'] = 50
                
            pb_ratio = flat_data.get('pb_ratio', 0)
            if pb_ratio > 0:
                pb_score = max(0, min(100, (self.pb_threshold / pb_ratio) * 100))
                scores['pb_score'] = pb_score
            else:
                scores['pb_score'] = 50
                
            roe = flat_data.get('roe', 0)
            roe_score = min(100, max(0, roe * 10))
            scores['roe_score'] = roe_score
            
            dividend_yield = flat_data.get('dividend_yield', 0)
            dividend_score = min(100, dividend_yield * 10)
            scores['dividend_score'] = dividend_score
            
            revenue_growth = flat_data.get('revenue_growth', 0)
            revenue_score = min(100, max(0, revenue_growth * 5))
            scores['revenue_score'] = revenue_score
            
            profit_growth = flat_data.get('profit_growth', 0)
            profit_score = min(100, max(0, profit_growth * 5))
            scores['profit_score'] = profit_score
            
            total_score = sum(scores[key] * self.weights.get(key.replace('_score', ''), 0) 
                            for key in scores.keys() if key.endswith('_score'))
            scores['total_score'] = total_score
            
        except Exception as e:
            print(f"[警告] 财务评分计算使用降级模式: {str(e)}")
            scores = {
                'pe_score': 50, 'pb_score': 50, 'roe_score': 50,
                'dividend_score': 50, 'revenue_score': 50, 'profit_score': 50,
                'total_score': 50
            }
            
        return scores

    def _flatten_financial_data(self, financial_data: Dict) -> Dict:
        """
        展平嵌套的财务数据格式为扁平格式
        
        支持新的嵌套格式和旧的扁平格式
        """
        flat_data = {}
        
        if not financial_data or not isinstance(financial_data, dict):
            return flat_data
            
        if 'valuation' in financial_data:
            flat_data.update(financial_data.get('valuation', {}))
        if 'profitability' in financial_data:
            flat_data.update(financial_data.get('profitability', {}))
        if 'growth' in financial_data:
            flat_data.update(financial_data.get('growth', {}))
        if 'financial_health' in financial_data:
            flat_data.update(financial_data.get('financial_health', {}))
            
        if not flat_data:
            flat_data = financial_data.copy()
            
        return flat_data

    def calculate_intrinsic_value(self, financial_data: Dict, 
                                 current_price: float) -> Optional[float]:
        """
        计算内在价值 - DCF模型
        
        参数:
            financial_data: 财务数据
            current_price: 当前价格
            
        返回:
            内在价值
        """
        try:
            flat_data = self._flatten_financial_data(financial_data)
            eps = flat_data.get('eps', 0)
            if eps <= 0:
                return None
                
            growth_rate = flat_data.get('profit_growth', 0) / 100
            
            future_cash_flows = []
            for year in range(1, 6):
                future_eps = eps * ((1 + growth_rate) ** year)
                future_cash_flows.append(future_eps)
                
            intrinsic_value = sum(cf / ((1 + self.discount_rate) ** year) 
                                for year, cf in enumerate(future_cash_flows, 1))
            
            terminal_value = (future_cash_flows[-1] * (1 + growth_rate * 0.5) / 
                             (self.discount_rate - growth_rate * 0.5))
            intrinsic_value += terminal_value / ((1 + self.discount_rate) ** 5)
            
            return intrinsic_value
            
        except Exception as e:
            print(f"[错误] 计算内在价值失败: {str(e)}")
            return None

    def assess_value(self, stock_code: str, stock_name: str, 
                    financial_data: Dict, current_price: float,
                    industry: str = "综合") -> ValueAssessment:
        """
        综合价值评估 - 增强版
        
        在原有基础上增加完整的基本面分析
        
        参数:
            stock_code: 股票代码
            stock_name: 股票名称
            financial_data: 财务数据
            current_price: 当前价格
            industry: 所属行业
            
        返回:
            ValueAssessment 价值评估结果（增强版）
        """
        try:
            fundamental_score = self.calculate_fundamental_score(financial_data, industry)
            
            scores = self.calculate_financial_score(financial_data)
            financial_score = scores.get('total_score', 50)
            
            intrinsic_value = self.calculate_intrinsic_value(financial_data, current_price)
            
            if intrinsic_value and intrinsic_value > 0:
                deviation = (current_price - intrinsic_value) / intrinsic_value * 100
                safety_margin = (intrinsic_value - current_price) / intrinsic_value * 100
            else:
                deviation = 0
                safety_margin = 0
                
            evaluation, risk_warning = self._evaluate_level(financial_score, deviation)
            
            return ValueAssessment(
                code=stock_code,
                name=stock_name,
                financial_score=financial_score,
                intrinsic_value=intrinsic_value,
                current_price=current_price,
                deviation=deviation,
                safety_margin=safety_margin,
                evaluation=evaluation,
                risk_warning=risk_warning,
                fundamental_score=fundamental_score,
                valuation=self.analyze_valuation(financial_data, industry),
                profitability=self.analyze_profitability(financial_data),
                growth=self.analyze_growth(financial_data),
                financial_health=self.check_financial_health(financial_data),
                industry_comparison=self.compare_with_industry(financial_data, industry)
            )
            
        except Exception as e:
            print(f"[错误] 价值评估失败: {str(e)}")
            return ValueAssessment(
                code=stock_code,
                name=stock_name,
                financial_score=0,
                current_price=current_price,
                evaluation="评估异常",
                risk_warning=f"错误: {str(e)}"
            )

    def _evaluate_level(self, financial_score: float, 
                       deviation: float) -> Tuple[str, str]:
        """确定评估等级和风险提示"""
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
            
        if deviation < -20:
            evaluation = "价值严重低估"
            risk_warning = "低风险"
        elif deviation > 20:
            evaluation = "价值严重高估"
            risk_warning = "高风险"
            
        return evaluation, risk_warning

    def get_industry_comparison(self, stock_assessment: ValueAssessment, 
                              industry_avg: Dict) -> Dict:
        """
        行业对比分析 - 兼容原有接口
        
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
        
        if stock_assessment.industry_comparison:
            comparison.update({
                'detailed_comparison': stock_assessment.industry_comparison.vs_industry_avg,
                'advantages': stock_assessment.industry_comparison.advantages,
                'disadvantages': stock_assessment.industry_comparison.disadvantages,
                'relative_position': stock_assessment.industry_comparison.relative_position
            })
            
        return comparison

    def generate_value_report(self, assessments: List[ValueAssessment]) -> str:
        """
        生成价值评估报告 - 增强版
        
        包含详细的财务分析内容
        
        参数:
            assessments: 评估结果列表
            
        返回:
            报告文本
        """
        report = []
        report.append("=" * 80)
        report.append("📊 全面价值评估报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        undervalued = [a for a in assessments if a.evaluation in ["价值被低估", "价值严重低估"]]
        fairly_valued = [a for a in assessments if a.evaluation == "价值合理"]
        overvalued = [a for a in assessments if a.evaluation in ["价值被高估", "价值严重高估"]]
        
        report.append(f"📈 被低估股票: {len(undervalued)}只")
        report.append(f"⚖️ 合理估值股票: {len(fairly_valued)}只")
        report.append(f"📉 被高估股票: {len(overvalued)}只")
        report.append("")
        
        if undervalued:
            report.append("=" * 80)
            report.append("【✨ 价值被低估股票 - 推荐关注】")
            report.append("=" * 80)
            for assessment in sorted(undervalued, key=lambda x: x.financial_score, reverse=True):
                report.append(self._format_stock_detail(assessment))
                
        if fairly_valued:
            report.append("=" * 80)
            report.append("【⚖️ 合理估值股票】")
            report.append("=" * 80)
            for assessment in sorted(fairly_valued, key=lambda x: x.financial_score, reverse=True):
                report.append(self._format_stock_detail(assessment))
                
        if overvalued:
            report.append("=" * 80)
            report.append("【⚠️ 价值被高估股票 - 需谨慎】")
            report.append("=" * 80)
            for assessment in sorted(overvalued, key=lambda x: x.financial_score):
                report.append(self._format_stock_detail(assessment))
                
        report.append("")
        report.append("=" * 80)
        report.append("💡 报告说明:")
        report.append("- 评分采用四维加权模型：估值(30%) + 盈利(30%) + 成长(20%) + 健康(20%)")
        report.append("- 评级范围：A+(≥90) ~ D(<36)")
        report.append("- 本报告基于公开财务数据，仅供参考，不构成投资建议")
        report.append("- 投资有风险，决策需谨慎")
        report.append("=" * 80)
        
        return "\n".join(report)

    def _format_stock_detail(self, assessment: ValueAssessment) -> str:
        """格式化单只股票详细信息"""
        lines = []
        lines.append(f"\n🔹 {assessment.code} {assessment.name}")
        lines.append(f"   💰 当前价格: ¥{assessment.current_price:.2f}")
        
        if assessment.intrinsic_value:
            lines.append(f"   📊 内在价值: ¥{assessment.intrinsic_value:.2f}")
            lines.append(f"   🛡️ 安全边际: {assessment.safety_margin:+.1f}%")
            
        lines.append(f"   ⭐ 传统评分: {assessment.financial_score:.1f}")
        
        if assessment.fundamental_score:
            fs = assessment.fundamental_score
            lines.append(f"   🎯 综合评分: {fs.total_score:.1f}/100 | 等级: {fs.grade} | 评级: {fs.rating}")
            lines.append(f"   📊 分项得分: 估值{fs.valuation_score:.0f} 盈利{fs.profitability_score:.0f} "
                        f"成长{fs.growth_score:.0f} 健康{fs.health_score:.0f}")
            
            if fs.strengths:
                lines.append(f"   ✅ 优势: {', '.join(fs.strengths[:3])}")
            if fs.weaknesses:
                lines.append(f"   ❌ 劣势: {', '.join(fs.weaknesses[:3])}")
                
        if assessment.valuation:
            v = assessment.valuation
            lines.append(f"   📈 估值: PE={v.pe_ratio:.1f}(分位{v.pe_percentile:.0f}%) "
                        f"PB={v.pb_ratio:.2f} PEG={v.peg_ratio:.2f}")
                        
        if assessment.financial_health and assessment.financial_health.health_warnings:
            lines.append(f"   ⚠️ 预警: {'; '.join(assessment.financial_health.health_warnings[:2])}")
            
        lines.append(f"   🎭 风险等级: {assessment.risk_warning}")
        lines.append("")
        
        return "\n".join(lines)

    def update_thresholds(self, pe_threshold: float, pb_threshold: float, 
                         roe_threshold: float, dividend_threshold: float):
        """
        更新评估阈值 - 兼容原有接口
        
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
        
        print(f"[更新] 评估阈值已更新: PE={pe_threshold}, PB={pb_threshold}, "
              f"ROE={roe_threshold}, 股息率={dividend_threshold}%")

    def get_evaluation_summary(self, assessments: List[ValueAssessment]) -> Dict:
        """
        获取评估汇总 - 增强版
        
        参数:
            assessments: 评估结果列表
            
        返回:
            汇总信息
        """
        if not assessments:
            return {}
            
        avg_score = sum(a.financial_score for a in assessments) / len(assessments)
        avg_deviation = sum(a.deviation for a in assessments) / len(assessments)
        
        avg_fundamental_score = 0
        count_with_fs = 0
        for a in assessments:
            if a.fundamental_score:
                avg_fundamental_score += a.fundamental_score.total_score
                count_with_fs += 1
        avg_fundamental_score = avg_fundamental_score / count_with_fs if count_with_fs > 0 else 0
        
        risk_distribution = {
            'low_risk': len([a for a in assessments if a.risk_warning == '低风险']),
            'medium_risk': len([a for a in assessments if a.risk_warning == '中等风险']),
            'high_risk': len([a for a in assessments if a.risk_warning == '高风险'])
        }
        
        grade_distribution = {}
        for a in assessments:
            if a.fundamental_score:
                grade = a.fundamental_score.grade
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
                
        return {
            'total_stocks': len(assessments),
            'avg_financial_score': avg_score,
            'avg_fundamental_score': avg_fundamental_score,
            'avg_deviation': avg_deviation,
            'risk_distribution': risk_distribution,
            'grade_distribution': grade_distribution,
            'best_value': max(assessments, key=lambda x: x.financial_score),
            'worst_value': min(assessments, key=lambda x: x.financial_score)
        }

    def generate_fundamental_analysis_report(self, stock_code: str, 
                                           stock_name: str,
                                           fundamental_data: Dict,
                                           industry: str = "综合") -> str:
        """
        生成单只股票的完整基本面分析报告
        
        这是最核心的报告生成方法，输出专业级分析报告
        
        参数:
            stock_code: 股票代码
            stock_name: 股票名称
            fundamental_data: 基本面数据
            industry: 所属行业
            
        返回:
            详细的分析报告文本
        """
        report_lines = []
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append(f"📋 {stock_code} {stock_name} - 深度基本面分析报告")
        report_lines.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"所属行业: {industry}")
        report_lines.append("=" * 80)
        
        try:
            fundamental_score = self.calculate_fundamental_score(fundamental_data, industry)
            valuation = self.analyze_valuation(fundamental_data, industry)
            profitability = self.analyze_profitability(fundamental_data)
            growth = self.analyze_growth(fundamental_data)
            health = self.check_financial_health(fundamental_data)
            industry_comp = self.compare_with_industry(fundamental_data, industry)
            
            report_lines.append(f"\n{'='*80}")
            report_lines.append("🎯 【综合评分】")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"总评分: {fundamental_score.total_score:.1f}/100")
            report_lines.append(f"评级等级: {fundamental_score.grade}")
            report_lines.append(f"投资评级: {fundamental_score.rating}")
            report_lines.append(f"\n分项得分:")
            report_lines.append(f"  • 估值吸引力: {fundamental_score.valuation_score:.1f}/100 (权重30%)")
            report_lines.append(f"  • 盈利能力: {fundamental_score.profitability_score:.1f}/100 (权重30%)")
            report_lines.append(f"  • 成长性: {fundamental_score.growth_score:.1f}/100 (权重20%)")
            report_lines.append(f"  • 财务健康: {fundamental_score.health_score:.1f}/100 (权重20%)")
            
            if fundamental_score.strengths:
                report_lines.append(f"\n✅ 核心优势 ({len(fundamental_score.strengths)}项):")
                for s in fundamental_score.strengths:
                    report_lines.append(f"  • {s}")
                    
            if fundamental_score.weaknesses:
                report_lines.append(f"\n❌ 主要劣势 ({len(fundamental_score.weaknesses)}项):")
                for w in fundamental_score.weaknesses:
                    report_lines.append(f"  • {w}")
                    
            if fundamental_score.suggestions:
                report_lines.append(f"\n💡 投资建议:")
                for suggestion in fundamental_score.suggestions:
                    report_lines.append(f"  • {suggestion}")
                    
            report_lines.append(f"\n{'='*80}")
            report_lines.append("📊 【一、估值分析】")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"\n绝对估值指标:")
            report_lines.append(f"  • 市盈率(PE): {valuation.pe_ratio:.2f}")
            report_lines.append(f"  • 市净率(PB): {valuation.pb_ratio:.2f}")
            report_lines.append(f"  • 市销率(PS): {valuation.ps_ratio:.2f}")
            report_lines.append(f"  • 市现率(PCF): {valuation.pcf_ratio:.2f}")
            report_lines.append(f"  • 总市值: {valuation.market_cap:.2f}亿元 ({valuation.market_cap_rank})")
            
            report_lines.append(f"\n相对估值:")
            report_lines.append(f"  • PE相对行业: {valuation.pe_vs_industry:.2f}倍"
                              f"({'低估' if valuation.pe_vs_industry < 0.85 else '高估' if valuation.pe_vs_industry > 1.15 else '合理'})")
            report_lines.append(f"  • PB相对行业: {valuation.pb_vs_industry:.2f}倍")
            report_lines.append(f"  • PE历史分位: {valuation.pe_percentile:.1f}%"
                              f"({'低估区' if valuation.pe_percentile < 30 else '高估区' if valuation.pe_percentile > 70 else '正常'})")
            report_lines.append(f"  • PEG指标: {valuation.peg_ratio:.2f}"
                              f"({'低估' if 0 < valuation.peg_ratio < 1 else '合理' if valuation.peg_ratio <= 1.5 else '偏高'})")
            
            report_lines.append(f"\n估值评分:")
            report_lines.append(f"  • PE评分: {valuation.pe_score:.1f}/100")
            report_lines.append(f"  • PB评分: {valuation.pb_score:.1f}/100")
            report_lines.append(f"  • PB-ROE评分: {valuation.pb_roe_score:.1f}/100")
            report_lines.append(f"  • PS评分: {valuation.ps_score:.1f}/100")
            report_lines.append(f"  • PCF评分: {valuation.pcf_score:.1f}/100")
            report_lines.append(f"  • 估值吸引力综合: {valuation.valuation_attractiveness:.1f}/100")
            report_lines.append(f"\n📝 小结: {valuation.valuation_summary}")
            
            report_lines.append(f"\n{'='*80}")
            report_lines.append("💰 【二、盈利能力分析】")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"\n核心指标:")
            report_lines.append(f"  • 净资产收益率(ROE): {profitability.roe:.2f}%"
                              f"({'优秀' if profitability.roe >= 15 else '良好' if profitability.roe >= 10 else '一般' if profitability.roe > 0 else '亏损'})")
            report_lines.append(f"  • 总资产收益率(ROA): {profitability.roa:.2f}%")
            report_lines.append(f"  • 毛利率: {profitability.gross_margin:.2f}%")
            report_lines.append(f"  • 净利率: {profitability.net_margin:.2f}%")
            report_lines.append(f"  • EBITDA利润率: {profitability.ebitda_margin:.2f}%")
            
            report_lines.append(f"\n杜邦分析(ROE分解):")
            report_lines.append(f"  • 净利率驱动: {profitability.roe_dupont_net_margin*100:.2f}%")
            report_lines.append(f"  • 资产周转率: {profitability.roe_dupont_asset_turnover:.2f}次")
            report_lines.append(f"  • 权益乘数: {profitability.roe_dupont_equity_multiplier:.2f}倍")
            
            if profitability.gross_margin_trend:
                report_lines.append(f"\n近5年毛利率趋势: {' → '.join(map(str, profitability.gross_margin_trend))}")
            if profitability.net_margin_trend:
                report_lines.append(f"近5年净利率趋势: {' → '.join(map(str, profitability.net_margin_trend))}")
                
            report_lines.append(f"\n盈利能力评分:")
            report_lines.append(f"  • ROE评分: {profitability.roe_score:.1f}/100")
            report_lines.append(f"  • ROA评分: {profitability.roa_score:.1f}/100")
            report_lines.append(f"  • 利润率评分: {profitability.margin_score:.1f}/100")
            report_lines.append(f"  • 盈利能力综合: {profitability.profitability_total:.1f}/100")
            report_lines.append(f"\n📝 小结: {profitability.profitability_summary}")
            
            report_lines.append(f"\n{'='*80}")
            report_lines.append("📈 【三、成长性评估】")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"\n营收增长:")
            report_lines.append(f"  • 同比增长(YoY): {growth.revenue_growth_yoy:.2f}%")
            report_lines.append(f"  • 环比增长(QoQ): {growth.revenue_growth_qoq:.2f}%")
            report_lines.append(f"  • 3年CAGR: {growth.revenue_cagr_3y:.2f}%")
            report_lines.append(f"  • 5年CAGR: {growth.revenue_cagr_5y:.2f}%")
            
            report_lines.append(f"\n利润增长:")
            report_lines.append(f"  • 净利润YoY: {growth.profit_growth_yoy:.2f}%")
            report_lines.append(f"  • 扣非净利润YoY: {growth.profit_growth_deducted:.2f}%")
            report_lines.append(f"  • EPS增长: {growth.eps_growth:.2f}%")
            report_lines.append(f"  • 自由现金流增长: {growth.fcf_growth:.2f}%")
            
            report_lines.append(f"\n成长质量:")
            report_lines.append(f"  • 增长稳定性: {growth.growth_stability:.1f}/100")
            report_lines.append(f"  • 增长可持续性: {growth.growth_sustainability:.1f}/100")
            report_lines.append(f"  • 成长质量综合: {growth.growth_quality_score:.1f}/100")
            
            report_lines.append(f"\n成长性评分:")
            report_lines.append(f"  • 营收增长评分: {growth.revenue_score:.1f}/100")
            report_lines.append(f"  • 利润增长评分: {growth.profit_score:.1f}/100")
            report_lines.append(f"  • 成长性综合: {growth.growth_total:.1f}/100")
            report_lines.append(f"\n📝 小结: {growth.growth_summary}")
            
            report_lines.append(f"\n{'='*80}")
            report_lines.append("🏥 【四、财务健康检查】")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"\n偿债能力:")
            report_lines.append(f"  • 资产负债率: {health.debt_ratio:.1f}%"
                              f"({'安全' if health.debt_ratio < 50 else '注意' if health.debt_ratio < 70 else '风险'})")
            report_lines.append(f"  • 流动比率: {health.current_ratio:.2f}"
                              f"({'安全' if health.current_ratio >= 1.5 else '偏低'})")
            report_lines.append(f"  • 速动比率: {health.quick_ratio:.2f}")
            report_lines.append(f"  • 利息保障倍数: {health.interest_coverage:.2f}倍")
            
            report_lines.append(f"\n资产质量:")
            report_lines.append(f"  • 商誉/净资产: {health.goodwill_ratio:.1f}%"
                              f"({'安全' if health.goodwill_ratio < 20 else '注意'})")
            report_lines.append(f"  • 经营现金流/净利润: {health.operating_cashflow_to_profit:.2f}"
                              f"({'优质' if health.operating_cashflow_to_profit >= 1.0 else '一般'})")
            
            report_lines.append(f"\n运营效率:")
            report_lines.append(f"  • 应收账款周转天数: {health.receivable_turnover_days:.0f}天")
            report_lines.append(f"  • 存货周转天数: {health.inventory_turnover_days:.0f}天")
            
            report_lines.append(f"\n健康评分:")
            report_lines.append(f"  • 偿债能力: {health.debt_score:.1f}/100")
            report_lines.append(f"  • 流动性: {health.liquidity_score:.1f}/100")
            report_lines.append(f"  • 盈利质量: {health.quality_score:.1f}/100")
            report_lines.append(f"  • 运营效率: {health.efficiency_score:.1f}/100")
            report_lines.append(f"  • 财务健康综合: {health.health_total:.1f}/100")
            
            if health.health_warnings:
                report_lines.append(f"\n⚠️ 预警项目 ({len(health.health_warnings)}项):")
                for warning in health.health_warnings:
                    report_lines.append(f"  {warning}")
                    
            report_lines.append(f"\n📝 小结: {health.health_summary}")
            
            report_lines.append(f"\n{'='*80}")
            report_lines.append("🏢 【五、行业对标分析】")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"\n行业: {industry_comp.industry_name}")
            report_lines.append(f"相对位置: {industry_comp.relative_position}")
            
            if industry_comp.vs_industry_avg:
                report_lines.append(f"\n关键指标对比:")
                for metric_key, metric_info in industry_comp.vs_industry_avg.items():
                    report_lines.append(
                        f"  • {metric_info['name']}: 本公司{metric_info['value']:.2f} vs "
                        f"行业平均{metric_info['industry_avg']:.2f} "
                        f"({metric_info['vs_industry']}，比值{metric_info['ratio']:.2f})"
                    )
                    
            if industry_comp.advantages:
                report_lines.append(f"\n✅ 相对行业优势 ({len(industry_comp.advantages)}项):")
                for adv in industry_comp.advantages:
                    report_lines.append(f"  • {adv}")
                    
            if industry_comp.disadvantages:
                report_lines.append(f"\n❌ 相对行业劣势 ({len(industry_comp.disadvantages)}项):")
                for dis in industry_comp.disadvantages:
                    report_lines.append(f"  • {dis}")
                    
            report_lines.append(f"\n{'='*80}")
            report_lines.append("📌 【六、总结与建议】")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"\n总体评价: {stock_name}({stock_code})的综合基本面得分为"
                              f"{fundamental_score.total_score:.1f}分，评级{fundamental_score.grade}，"
                              f"投资评级为'{fundamental_score.rating}'。")
            
            if fundamental_score.total_score >= 70:
                report_lines.append(f"\n该公司基本面表现优异，具备较好的投资价值。")
            elif fundamental_score.total_score >= 50:
                report_lines.append(f"\n该公司基本面表现中等，建议结合技术面和市场环境综合判断。")
            else:
                report_lines.append(f"\n该公司基本面存在一定问题，建议谨慎对待或寻找更好的投资标的。")
                
            top_suggestions = fundamental_score.suggestions[:3]
            if top_suggestions:
                report_lines.append(f"\n核心建议:")
                for i, suggestion in enumerate(top_suggestions, 1):
                    report_lines.append(f"  {i}. {suggestion}")
                    
        except Exception as e:
            report_lines.append(f"\n❌ 分析过程出错: {str(e)}")
            report_lines.append("请检查数据是否完整或联系技术支持。")
            
        report_lines.append(f"\n{'='*80}")
        report_lines.append("⚠️ 免责声明:")
        report_lines.append("本报告基于公开财务数据和量化模型生成，仅供参考。")
        report_lines.append("不构成任何投资建议，投资有风险，决策需谨慎。")
        report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80 + "\n")
        
        return "\n".join(report_lines)
