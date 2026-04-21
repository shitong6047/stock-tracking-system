"""
专业报告生成器 v1.0
功能：生成专业级A股分析报告，支持控制台输出和多格式导出

包含：
- ReportGenerator 核心类
- 控制台美化报告模板
- 交易建议引擎（五档评级、动态止损止盈、仓位管理）
- 多格式导出（Markdown/JSON/CSV）
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import os


@dataclass
class ReportConfig:
    """报告配置类"""
    output_dir: str = './reports'
    include_disclaimer: bool = True
    max_signals_display: int = 8
    console_width: int = 80
    encoding: str = 'utf-8'


class ReportGenerator:
    """
    专业级A股分析报告生成器
    
    功能特性：
    - 美观的控制台输出（带emoji和表格）
    - 完整的Markdown格式报告
    - 结构化JSON数据导出
    - CSV批量对比表格
    - 智能交易建议引擎
    """
    
    def __init__(self, config: Optional[ReportConfig] = None):
        """
        初始化报告生成器
        
        参数:
            config: 报告配置对象（可选）
        """
        self.config = config or ReportConfig()
        
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        self.rating_system = {
            'strong_buy': {'name': '强烈推荐买入', 'stars': '★★★★★', 
                          'color': '\033[92m', 'position': '70-90%'},
            'buy': {'name': '推荐买入', 'stars': '★★★★☆', 
                   'color': '\033[94m', 'position': '50-70%'},
            'neutral': {'name': '中性观望', 'stars': '★★★☆☆', 
                       'color': '\033[93m', 'position': '30-50%'},
            'avoid': {'name': '谨慎回避', 'stars': '★★☆☆☆', 
                     'color': '\033[91m', 'position': '10-30%'},
            'strong_avoid': {'name': '强烈回避', 'stars': '★☆☆☆☆', 
                            'color': '\033[91m', 'position': '<10%'}
        }
    
    def generate_console_report(self, prediction_result: Any, 
                               analysis_data: Dict) -> str:
        """
        生成控制台美化报告
        
        参数:
            prediction_result: 预测结果对象（EnsemblePredictionResult或PredictionResult）
            analysis_data: 分析数据字典（包含技术面、基本面等详细数据）
            
        返回:
            格式化的报告字符串
        """
        try:
            if not prediction_result:
                return "⚠️ 无预测结果，无法生成报告"
            
            lines = []
            width = self.config.console_width
            
            pred_time = getattr(prediction_result, 'prediction_time', 
                              datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            lines.append("═" * width)
            lines.append(f"  📊 A股智能分析报告")
            lines.append(f"  生成时间: {pred_time}")
            
            mode = analysis_data.get('analysis_mode', '市场扫描')
            lines.append(f"  分析模式: [{mode}]")
            lines.append("═" * width)
            lines.append("")
            
            code = getattr(prediction_result, 'code', '')
            name = getattr(prediction_result, 'name', '')
            direction = getattr(prediction_result, 'direction', '未知')
            probability = getattr(prediction_result, 'probability', 0)
            confidence = getattr(prediction_result, 'confidence', '中')
            
            rating = getattr(prediction_result, 'rating', '待定')
            stop_loss = getattr(prediction_result, 'stop_loss', 0)
            take_profit = getattr(prediction_result, 'take_profit', 0)
            risk_level = getattr(prediction_result, 'risk_level', '中')
            position_size = getattr(prediction_result, 'position_size', '中等仓位(30-50%)')
            
            prob_pct = probability * 100
            
            lines.append("【★ 核心推荐】")
            lines.append(f"🎯 最佳标的: {code} {name}")
            lines.append(f"📈 预测方向: {direction} | 概率: {prob_pct:.1f}%")
            lines.append(f"💰 操作建议: {rating}")
            lines.append(f"⚠️  风险等级: {risk_level} | 止损: {stop_loss:.1f}% | 目标: {+take_profit:.1f}%")
            lines.append(f"📊 建议仓位: {position_size}")
            lines.append("")
            
            technical_data = analysis_data.get('technical_analysis', {})
            fundamental_data = analysis_data.get('fundamental_analysis', {})
            
            tech_score = getattr(prediction_result, 'technical_score', 
                               technical_data.get('score', 50))
            fund_score = getattr(prediction_result, 'fundamental_score',
                               fundamental_data.get('score', 50))
            
            lines.append("【技术面分析】")
            tech_signals = self._format_signals(
                technical_data.get('signals', []),
                getattr(prediction_result, 'key_signals', [])
            )
            for signal in tech_signals[:5]:
                lines.append(signal)
            lines.append(f"📊 综合技术评分: {tech_score:.0f}/100")
            lines.append("")
            
            lines.append("【基本面分析】")
            fund_signals = fundamental_data.get('key_points', [])
            if fund_signals:
                for point in fund_signals[:4]:
                    lines.append(point)
            else:
                pe_ratio = fundamental_data.get('pe_ratio', 0)
                roe = fundamental_data.get('roe', 0)
                debt_ratio = fundamental_data.get('debt_ratio', 50)
                
                if pe_ratio and pe_ratio > 0:
                    industry_pe = fundamental_data.get('industry_avg_pe', 15)
                    if industry_pe and pe_ratio < industry_pe * 0.85:
                        lines.append(f"✅ PE({pe_ratio:.1f}x)低于行业平均({industry_pe:.1f}x)")
                    elif industry_pe and pe_ratio > industry_pe * 1.2:
                        lines.append(f"⚠️ PE({pe_ratio:.1f}x)高于行业平均({industry_pe:.1f}x)")
                
                if roe and roe >= 12:
                    lines.append(f"✅ ROE持续改善(+{roe:.1f}% YoY)")
                elif roe and roe > 0:
                    lines.append(f"📊 ROE为{roe:.1f}%")
                    
                if debt_ratio and debt_ratio > 75:
                    lines.append(f"⚠️ 负债率略高({debt_ratio:.0f}%)")
                elif debt_ratio and debt_ratio <= 45:
                    lines.append("✅ 负债率健康")
            
            lines.append(f"📊 综合基本面评分: {fund_score:.0f}/100")
            lines.append("")
            
            accuracy_report = analysis_data.get('accuracy_report', {})
            if accuracy_report:
                lines.append("【历史验证】")
                acc = accuracy_report.get('accuracy', 0)
                up_acc = accuracy_report.get('up_accuracy', 0)
                down_acc = accuracy_report.get('down_accuracy', 0)
                reliability = accuracy_report.get('model_reliability', '未知')
                
                lines.append(f"📈 近20日预测准确率: {acc*100:.1f}%")
                lines.append(f"📈 上涨预测命中率: {up_acc*100:.1f}%")
                lines.append(f"📈 下跌预测命中率: {down_acc*100:.1f}%")
                lines.append(f"📈 模型置信度: {reliability}")
                lines.append("")
            
            key_signals = getattr(prediction_result, 'key_signals', [])
            if key_signals:
                lines.append("【关键信号】")
                for i, signal in enumerate(key_signals[:6], 1):
                    lines.append(f"{i}. {signal}")
                lines.append("")
            
            risk_warnings = analysis_data.get('risk_warnings', [])
            if risk_warnings:
                lines.append("【风险提示】")
                for warning in risk_warnings[:4]:
                    lines.append(f"⚠️ {warning}")
                lines.append("")
            
            lines.append("═" * width)
            if self.config.include_disclaimer:
                lines.append("免责声明：本报告仅供参考，不构成投资建议...")
                lines.append("投资有风险，决策需谨慎")
            lines.append("═" * width)
            
            return "\n".join(lines)
            
        except Exception as e:
            print(f"[错误] 控制台报告生成失败: {str(e)}")
            return f"❌ 报告生成异常: {str(e)}"
    
    def _format_signals(self, tech_signals: List[str], 
                       pred_signals: List[str]) -> List[str]:
        """格式化信号列表"""
        formatted = []
        
        all_signals = list(set(tech_signals + pred_signals))
        
        positive_keywords = ['金叉', '突破', '超卖', '低估', '优秀', '增长', '流入']
        negative_keywords = ['死叉', '超买', '偏高', '下滑', '流出', '风险']
        
        for signal in all_signals[:8]:
            is_positive = any(kw in signal for kw in positive_keywords)
            is_negative = any(kw in signal for kw in negative_keywords)
            
            if is_positive:
                formatted.append(f"✅ {signal}")
            elif is_negative:
                formatted.append(f"⚠️ {signal}")
            else:
                formatted.append(f"📌 {signal}")
        
        return formatted
    
    def generate_markdown_report(self, prediction_result: Any,
                                analysis_data: Dict,
                                output_path: Optional[str] = None) -> str:
        """
        生成Markdown格式报告
        
        参数:
            prediction_result: 预测结果对象
            analysis_data: 分析数据字典
            output_path: 输出路径（可选，默认自动生成）
            
        返回:
            报告文件路径
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"report_{timestamp}.md"
                output_path = os.path.join(self.config.output_dir, filename)
            
            md_lines = []
            
            pred_time = getattr(prediction_result, 'prediction_time',
                              datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            md_lines.append("# A股智能分析报告\n")
            md_lines.append(f"- **生成时间**: {pred_time}\n")
            
            mode = analysis_data.get('analysis_mode', '市场扫描')
            md_lines.append(f"- **分析模式**: {mode}\n")
            
            code = getattr(prediction_result, 'code', '')
            name = getattr(prediction_result, 'name', '')
            direction = getattr(prediction_result, 'direction', '未知')
            probability = getattr(prediction_result, 'probability', 0)
            confidence = getattr(prediction_result, 'confidence', '中')
            
            rating = getattr(prediction_result, 'rating', '待定')
            stop_loss = getattr(prediction_result, 'stop_loss', 0)
            take_profit = getattr(prediction_result, 'take_profit', 0)
            risk_level = getattr(prediction_result, 'risk_level', '中')
            
            md_lines.append("\n## ★ 核心推荐\n")
            md_lines.append(f"| 项目 | 详情 |")
            md_lines.append(f"|------|------|")
            md_lines.append(f"| **最佳标的** | {code} {name} |")
            md_lines.append(f"| **预测方向** | {direction} |")
            md_lines.append(f"| **概率** | {probability*100:.1f}% |")
            md_lines.append(f"| **置信度** | {confidence} |")
            md_lines.append(f"| **操作建议** | {rating} |")
            md_lines.append(f"| **风险等级** | {risk_level} |")
            md_lines.append(f"| **止损位** | {stop_loss:.1f}% |")
            md_lines.append(f"| **目标位** | {+take_profit:.1f}% |\n")
            
            tech_score = getattr(prediction_result, 'technical_score', 50)
            fund_score = getattr(prediction_result, 'fundamental_score', 50)
            
            md_lines.append("## 技术面分析\n")
            md_lines.append(f"**综合评分**: {tech_score:.0f}/100\n")
            
            tech_signals = getattr(prediction_result, 'key_signals', [])
            if tech_signals:
                md_lines.append("**关键信号**:\n")
                for signal in tech_signals[:6]:
                    md_lines.append(f"- {signal}\n")
            
            md_lines.append("\n## 基本面分析\n")
            md_lines.append(f"**综合评分**: {fund_score:.0f}/100\n")
            
            fundamental_data = analysis_data.get('fundamental_analysis', {})
            if fundamental_data:
                pe_ratio = fundamental_data.get('pe_ratio', 0)
                roe = fundamental_data.get('roe', 0)
                debt_ratio = fundamental_data.get('debt_ratio', 50)
                
                md_lines.append("| 指标 | 数值 | 评价 |")
                md_lines.append("|------|------|------|")
                
                if pe_ratio:
                    md_lines.append(f"| PE(TTM) | {pe_ratio:.2f}x | {'低估' if pe_ratio < 15 else '合理' if pe_ratio < 25 else '偏高'} |")
                if roe:
                    md_lines.append(f"| ROE | {roe:.1f}% | {'优秀' if roe >= 15 else '良好' if roe >= 10 else '一般'} |")
                if debt_ratio:
                    md_lines.append(f"| 资产负债率 | {debt_ratio:.1f}% | {'健康' if debt_ratio < 50 else '偏高' if debt_ratio < 70 else '需关注'} |")
                md_lines.append("")
            
            model_scores = getattr(prediction_result, 'model_scores', None)
            if model_scores:
                md_lines.append("\n## 模型权重与得分\n")
                md_lines.append("| 模型 | 权重 | 得分 |")
                md_lines.append("|------|------|------|")
                
                weights = getattr(prediction_result, 'model_weights', {})
                for model_name, score in model_scores.items():
                    weight = weights.get(model_name, 0)
                    model_label = {
                        'technical': '技术分析',
                        'fundamental': '基本面',
                        'market_sentiment': '市场情绪',
                        'pattern_match': '模式匹配'
                    }.get(model_name, model_name)
                    
                    md_lines.append(f"| {model_label} | {weight*100:.0f}% | {score:.1f}/100 |")
                md_lines.append("")
            
            accuracy_report = analysis_data.get('accuracy_report', {})
            if accuracy_report:
                md_lines.append("## 历史验证\n")
                md_lines.append(f"- **近20日准确率**: {accuracy_report.get('accuracy', 0)*100:.1f}%\n")
                md_lines.append(f"- **上涨命中率**: {accuracy_report.get('up_accuracy', 0)*100:.1f}%\n")
                md_lines.append(f"- **下跌命中率**: {accuracy_report.get('down_accuracy', 0)*100:.1f}%\n")
                md_lines.append(f"- **模型可靠性**: {accuracy_report.get('model_reliability', '未知')}\n")
            
            risk_warnings = analysis_data.get('risk_warnings', [])
            if risk_warnings:
                md_lines.append("\n## ⚠️ 风险提示\n")
                for warning in risk_warnings:
                    md_lines.append(f"- {warning}\n")
            
            md_lines.append("\n---\n")
            if self.config.include_disclaimer:
                md_lines.append("**免责声明**: 本报告基于量化模型生成，仅供参考，不构成投资建议。\n")
                md_lines.append("投资有风险，决策需谨慎。\n")
            
            report_content = "\n".join(md_lines)
            
            with open(output_path, 'w', encoding=self.config.encoding) as f:
                f.write(report_content)
            
            print(f"[保存] Markdown报告已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[错误] Markdown报告生成失败: {str(e)}")
            raise
    
    def generate_json_report(self, prediction_result: Any,
                            output_path: Optional[str] = None) -> str:
        """
        生成JSON格式报告
        
        参数:
            prediction_result: 预测结果对象
            output_path: 输出路径（可选，默认自动生成）
            
        返回:
            JSON文件路径
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"report_{timestamp}.json"
                output_path = os.path.join(self.config.output_dir, filename)
            
            result_dict = {
                'code': getattr(prediction_result, 'code', ''),
                'name': getattr(prediction_result, 'name', ''),
                'prediction_time': getattr(prediction_result, 'prediction_time', ''),
                'direction': getattr(prediction_result, 'direction', ''),
                'probability': getattr(prediction_result, 'probability', 0),
                'confidence': getattr(prediction_result, 'confidence', ''),
                'rating': getattr(prediction_result, 'rating', ''),
                'expected_return_min': getattr(prediction_result, 'expected_return_min', 0),
                'expected_return_max': getattr(prediction_result, 'expected_return_max', 0),
                'key_signals': getattr(prediction_result, 'key_signals', []),
                'stop_loss': getattr(prediction_result, 'stop_loss', 0),
                'take_profit': getattr(prediction_result, 'take_profit', 0),
                'position_size': getattr(prediction_result, 'position_size', ''),
                'risk_level': getattr(prediction_result, 'risk_level', ''),
                'model_weights': getattr(prediction_result, 'model_weights', {}),
                'model_scores': getattr(prediction_result, 'model_scores', {}),
                'technical_score': getattr(prediction_result, 'technical_score', 0),
                'fundamental_score': getattr(prediction_result, 'fundamental_score', 0),
                'market_sentiment_score': getattr(prediction_result, 'market_sentiment_score', 0),
                'pattern_match_score': getattr(prediction_result, 'pattern_match_score', 0),
                'generated_at': datetime.now().isoformat()
            }
            
            with open(output_path, 'w', encoding=self.config.encoding) as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            print(f"[保存] JSON报告已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[错误] JSON报告生成失败: {str(e)}")
            raise
    
    def generate_csv_summary(self, predictions_list: List[Any],
                           output_path: Optional[str] = None) -> str:
        """
        生成CSV汇总表
        
        参数:
            predictions_list: 预测结果列表
            output_path: 输出路径（可选，默认自动生成）
            
        返回:
            CSV文件路径
        """
        try:
            if not predictions_list:
                raise ValueError("预测列表不能为空")
            
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"summary_{timestamp}.csv"
                output_path = os.path.join(self.config.output_dir, filename)
            
            rows = []
            for pred in predictions_list:
                row = {
                    '股票代码': getattr(pred, 'code', ''),
                    '股票名称': getattr(pred, 'name', ''),
                    '预测方向': getattr(pred, 'direction', ''),
                    '概率': f"{getattr(pred, 'probability', 0)*100:.1f}%",
                    '置信度': getattr(pred, 'confidence', ''),
                    '操作建议': getattr(pred, 'rating', ''),
                    '止损位(%)': getattr(pred, 'stop_loss', 0),
                    '目标位(%)': getattr(pred, 'take_profit', 0),
                    '风险等级': getattr(pred, 'risk_level', ''),
                    '建议仓位': getattr(pred, 'position_size', ''),
                    '技术评分': getattr(pred, 'technical_score', 0),
                    '基本面评分': getattr(pred, 'fundamental_score', 0),
                    '关键信号': '|'.join(getattr(pred, 'key_signals', [])[:3]),
                    '预测时间': getattr(pred, 'prediction_time', '')
                }
                rows.append(row)
            
            df = pd.DataFrame(rows)
            
            df_sorted = df.sort_values(by=['概率'], ascending=False, key=lambda x: x.str.rstrip('%').astype(float))
            
            df_sorted.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"[保存] CSV汇总表已保存到: {output_path} (共{len(predictions_list)}条记录)")
            return output_path
            
        except Exception as e:
            print(f"[错误] CSV汇总表生成失败: {str(e)}")
            raise
    
    def generate_trading_advice(self, prediction_result: Any,
                               analysis_data: Dict) -> Dict:
        """
        生成完整交易建议（集成在报告中使用）
        
        包含：
        - 五档评级系统
        - 动态止损止盈计算
        - 仓位管理建议
        - 风险评估矩阵
        
        参数:
            prediction_result: 预测结果对象
            analysis_data: 分析数据字典
            
        返回:
            交易建议字典
        """
        try:
            probability = getattr(prediction_result, 'probability', 0.5)
            direction = getattr(prediction_result, 'direction', '震荡')
            risk_level = getattr(prediction_result, 'risk_level', '中')
            
            combined_score = probability * 0.6
            tech_score = getattr(prediction_result, 'technical_score', 50) / 100 * 0.4
            final_score = combined_score + tech_score
            
            if final_score >= 0.78:
                rating_key = 'strong_buy'
            elif final_score >= 0.68:
                rating_key = 'buy'
            elif final_score >= 0.55:
                rating_key = 'neutral'
            elif final_score >= 0.42:
                rating_key = 'avoid'
            else:
                rating_key = 'strong_avoid'
            
            rating_info = self.rating_system[rating_key]
            
            atr = analysis_data.get('atr', 0)
            volatility = analysis_data.get('volatility', 0.03)
            
            base_stop_loss = 3.0 + (1 - probability) * 4
            base_take_profit = 5.0 + probability * 8
            
            vol_adjustment = volatility / 0.03
            stop_loss = min(7.0, max(3.0, base_stop_loss * vol_adjustment))
            take_profit = min(15.0, max(5.0, base_take_profit * vol_adjustment))
            
            if direction == '下跌':
                stop_loss = abs(stop_loss)
                take_profit = abs(take_profit)
            
            position_map = {
                'strong_buy': ('高概率机会', '70-90%', '可考虑加仓'),
                'buy': ('较好机会', '50-70%', '分批建仓'),
                'neutral': ('观望为主', '30-50%', '持有或小幅调整'),
                'avoid': ('谨慎对待', '10-30%', '减仓或观望'),
                'strong_avoid': ('高风险', '<10%', '避免介入')
            }
            
            pos_advice = position_map[rating_key]
            
            risk_factors = []
            risk_score = 0
            
            tech_risk = getattr(prediction_result, 'technical_score', 50)
            if tech_risk < 40:
                risk_factors.append('技术面偏弱')
                risk_score += 2
            elif tech_risk < 55:
                risk_factors.append('技术面一般')
                risk_score += 1
            
            fund_risk = getattr(prediction_result, 'fundamental_score', 50)
            if fund_risk < 40:
                risk_factors.append('基本面堪忧')
                risk_score += 2
            elif fund_risk < 55:
                risk_factors.append('基本面一般')
                risk_score += 1
            
            market_trend = analysis_data.get('market_trend', '中性')
            if market_trend == '弱势':
                risk_factors.append('大盘环境不佳')
                risk_score += 2
            elif market_trend == '震荡':
                risk_factors.append('大盘震荡')
                risk_score += 1
            
            sector_trend = analysis_data.get('sector_trend', '中性')
            if sector_trend == '走弱':
                risk_factors.append('板块趋势向下')
                risk_score += 1
            
            if volatility > 0.05:
                risk_factors.append(f'高波动率({volatility*100:.1f}%)')
                risk_score += 1
            
            if risk_score >= 5:
                overall_risk = '高'
            elif risk_score >= 3:
                overall_risk = '中高'
            elif risk_score >= 1:
                overall_risk = '中'
            else:
                overall_risk = '低'
            
            advice = {
                'rating': {
                    'level': rating_key,
                    'name': rating_info['name'],
                    'stars': rating_info['stars'],
                    'score': round(final_score, 3)
                },
                'entry_strategy': {
                    'suggested_action': rating_info['name'],
                    'urgency': pos_advice[0],
                    'position_size': pos_advice[1],
                    'execution_method': pos_advice[2]
                },
                'risk_management': {
                    'stop_loss_pct': round(-stop_loss, 2) if direction == '上涨' else round(stop_loss, 2),
                    'take_profit_pct': round(take_profit, 2) if direction == '上涨' else round(-take_profit, 2),
                    'risk_reward_ratio': round(take_profit / stop_loss, 2) if stop_loss > 0 else 0,
                    'max_position_loss': round(stop_loss * 0.8, 2)
                },
                'position_sizing': {
                    'recommended_range': pos_advice[1],
                    'single_stock_max': '总资金5%' if overall_risk == '高' else '总资金8%',
                    'portfolio_diversification': '至少分散到5-8只不同板块个股'
                },
                'risk_assessment': {
                    'overall_level': overall_risk,
                    'risk_score': risk_score,
                    'risk_factors': risk_factors,
                    'main_concerns': risk_factors[:3]
                },
                'timing_advice': self._generate_timing_advice(direction, probability, risk_level),
                'monitoring_points': self._generate_monitoring_points(prediction_result, analysis_data)
            }
            
            return advice
            
        except Exception as e:
            print(f"[警告] 交易建议生成异常: {str(e)}")
            return {'error': str(e)}
    
    def _generate_timing_advice(self, direction: str, 
                               probability: float,
                               risk_level: str) -> Dict:
        """生成时机建议"""
        timing = {}
        
        if direction == '上涨':
            if probability >= 0.75:
                timing['best_entry'] = '回调至支撑位时入场'
                timing['patience'] = '可等待1-2个交易日确认'
                timing['urgency'] = '中等偏高'
            elif probability >= 0.60:
                timing['best_entry'] = '可在当前价位附近逐步建仓'
                timing['patience'] = '可分2-3批买入'
                timing['urgency'] = '中等'
            else:
                timing['best_entry'] = '等待更明确信号'
                timing['patience'] = '建议观察3-5个交易日'
                timing['urgency'] = '不急'
        elif direction == '下跌':
            timing['best_entry'] = '不建议此时入场'
            timing['action'] = '如已持仓，考虑减仓'
            timing['urgency'] = '根据止损位执行'
        else:
            timing['best_entry'] = '保持观望'
            timing['strategy'] = '等待方向明朗后再做决定'
            timing['urgency'] = '低'
        
        if risk_level == '高':
            timing['additional_caution'] = '当前风险较高，务必设置严格止损'
        elif risk_level == '低':
            timing['opportunity_note'] = '风险可控，可适当增加仓位'
        
        return timing
    
    def _generate_monitoring_points(self, prediction_result: Any,
                                   analysis_data: Dict) -> List[str]:
        """生成监控要点"""
        points = []
        
        direction = getattr(prediction_result, 'direction', '震荡')
        stop_loss = getattr(prediction_result, 'stop_loss', -5)
        
        points.append(f"股价触及止损位({stop_loss:+.1f}%)时严格执行止损")
        
        if direction == '上涨':
            points.append("关注成交量变化，缩量上涨需警惕")
            points.append("监控关键技术位是否有效突破")
            points.append("注意获利盘回吐压力")
        elif direction == '下跌':
            points.append("观察是否出现企稳信号")
            points.append("关注是否有利空消息进一步发酵")
        
        key_signals = getattr(prediction_result, 'key_signals', [])
        if '放量突破' in str(key_signals):
            points.append("确认突破有效性，防止假突破")
        if 'MACD' in str(key_signals):
            points.append("持续跟踪MACD指标变化")
        
        market_trend = analysis_data.get('market_trend', '')
        if market_trend:
            points.append(f"留意大盘趋势变化（当前：{market_trend}）")
        
        news_alerts = analysis_data.get('news_alerts', [])
        if news_alerts:
            points.append(f"关注重要消息：{news_alerts[0]}")
        
        return points[:6]
    
    def batch_generate_reports(self, predictions_list: List[Any],
                             analysis_data_list: List[Dict],
                             formats: List[str] = ['console']) -> Dict[str, List[str]]:
        """
        批量生成报告
        
        参数:
            predictions_list: 预测结果列表
            analysis_data_list: 对应的分析数据列表
            formats: 要生成的格式列表（console/markdown/json/csv）
            
        返回:
            字典：{format_type: [file_paths]}
        """
        results = {fmt: [] for fmt in formats}
        
        if len(predictions_list) != len(analysis_data_list):
            raise ValueError("预测列表和分析数据列表长度不一致")
        
        for i, (pred, analysis) in enumerate(zip(predictions_list, analysis_data_list)):
            try:
                if 'console' in formats:
                    console_report = self.generate_console_report(pred, analysis)
                    results['console'].append(console_report)
                
                if 'markdown' in formats:
                    md_path = self.generate_markdown_report(pred, analysis)
                    results['markdown'].append(md_path)
                
                if 'json' in formats:
                    json_path = self.generate_json_report(pred)
                    results['json'].append(json_path)
                    
            except Exception as e:
                code = getattr(pred, 'code', f'unknown_{i}')
                print(f"[警告] 第{i+1}个样本({code})报告生成失败: {str(e)}")
        
        if 'csv' in formats and predictions_list:
            csv_path = self.generate_csv_summary(predictions_list)
            results['csv'].append(csv_path)
        
        total = len(predictions_list)
        success_count = len(results.get('markdown', results.get('json', results.get('console', []))))
        
        print(f"\n[完成] 批量报告生成完毕: 成功{success_count}/{total}个")
        
        for fmt, paths in results.items():
            if paths:
                print(f"  - {fmt.upper()}: {len(paths)}个文件")
        
        return results