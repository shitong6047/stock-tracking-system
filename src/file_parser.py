"""
文件解析模块
功能：解析股票跟踪预测文件，支持CSV、JSON和TXT格式
"""

import os
import json
import csv
import chardet
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
import re


class FileParser:
    """股票跟踪预测文件解析器"""
    
    # 股票代码格式常量
    STOCK_CODE_PATTERN = re.compile(r'^\d{6}$')
    STOCK_CODE_LENGTH = 6
    A_STOCK_RANGE = (1, 999999)
    
    def __init__(self, whitelist: Optional[Set[str]] = None, blacklist: Optional[Set[str]] = None):
        """
        初始化文件解析器
        
        参数:
            whitelist: 白名单，仅允许的股票代码集合（None表示不限制）
            blacklist: 黑名单，禁止的股票代码集合（None表示不限制）
        """
        self.required_fields = ['code', 'name']
        self.optional_fields = ['date', 'status', 'notes']
        
        # 白名单/黑名单机制
        self.whitelist = whitelist if whitelist is not None else set()
        self.blacklist = blacklist if blacklist is not None else set()
        self._whitelist_enabled = len(self.whitelist) > 0
        self._blacklist_enabled = len(self.blacklist) > 0
    
    def validate_stock_code(self, code: str, line_num: int = 0) -> Tuple[bool, str, str]:
        """
        验证股票代码的有效性
        
        参数:
            code: 待验证的股票代码
            line_num: 行号（用于错误消息）
            
        返回:
            元组 (是否有效, 错误原因, 建议修正方案)
        """
        if not code or not isinstance(code, str):
            return False, '代码为空或类型错误', '请提供有效的6位数字股票代码'
        
        code = code.strip()
        
        # 检查1：格式验证 - 必须是6位纯数字
        if not self.STOCK_CODE_PATTERN.match(code):
            # 分析具体错误原因
            if len(code) == 0:
                return False, '代码为空字符串', '请输入6位数字的股票代码，如：000001、600519'
            elif len(code) != self.STOCK_CODE_LENGTH:
                return (
                    False,
                    f'代码长度错误：期望{self.STOCK_CODE_LENGTH}位，实际{len(code)}位',
                    f'请确保代码为{self.STOCK_CODE_LENGTH}位数字。当前代码"{code}"长度为{len(code)}位，'
                    f'建议检查是否遗漏了前导零（如"1"应为"000001"）或包含多余字符'
                )
            elif not code.isdigit():
                non_digit_chars = [c for c in code if not c.isdigit()]
                return (
                    False,
                    f'代码包含非数字字符: {set(non_digit_chars)}',
                    f'股票代码应仅包含数字字符(0-9)。当前代码"{code}"中包含非法字符{set(non_digit_chars)}，'
                    f'建议移除非数字字符后重试'
                )
            else:
                return False, '格式不符合要求', '请使用标准的6位A股代码格式（如000001-999999）'
        
        # 检查2：A股范围验证（000001-999999）
        try:
            code_num = int(code)
            min_code, max_code = self.A_STOCK_RANGE
            if code_num < min_code or code_num > max_code:
                return (
                    False,
                    f'代码超出A股有效范围({min_code}-{max_code})',
                    f'A股代码范围应在{min_code:06d}到{max_code:06d}之间，当前代码{code}超出此范围，'
                    f'请确认是否为有效的A股代码'
                )
        except ValueError:
            return False, '无法转换为数字', '请确认代码为有效的数字格式'
        
        # 检查3：黑名单检查
        if self._blacklist_enabled and code in self.blacklist:
            return (
                False,
                f'代码{code}在黑名单中',
                f'该股票代码已被加入黑名单禁止使用。如需使用，请先从黑名单中移除'
            )
        
        # 检查4：白名单检查
        if self._whitelist_enabled and code not in self.whitelist:
            whitelist_sample = list(self.whitelist)[:3]
            return (
                False,
                f'代码{code}不在白名单中',
                f'当前已启用白名单模式，仅允许以下范围内的代码：{whitelist_sample}'
                f'{"..." if len(self.whitelist) > 3 else ""}。请将{code}添加到白名单后重试'
            )
        
        # 所有检查通过
        return True, '', ''
    
    def add_to_whitelist(self, codes: List[str]) -> None:
        """
        添加代码到白名单
        
        参数:
            codes: 要添加的代码列表
        """
        for code in codes:
            if code and isinstance(code, str):
                code = code.strip()
                # 仅进行基本格式验证（6位数字），不检查黑白名单状态
                if self.STOCK_CODE_PATTERN.match(code):
                    self.whitelist.add(code)
        self._whitelist_enabled = len(self.whitelist) > 0
    
    def add_to_blacklist(self, codes: List[str]) -> None:
        """
        添加代码到黑名单
        
        参数:
            codes: 要添加的代码列表
        """
        for code in codes:
            if code and isinstance(code, str):
                code = code.strip()
                # 仅进行基本格式验证（6位数字），不检查黑白名单状态
                if self.STOCK_CODE_PATTERN.match(code):
                    self.blacklist.add(code)
        self._blacklist_enabled = len(self.blacklist) > 0
    
    def remove_from_whitelist(self, codes: List[str]) -> None:
        """从白名单移除代码"""
        for code in codes:
            self.whitelist.discard(code.strip())
        self._whitelist_enabled = len(self.whitelist) > 0
    
    def remove_from_blacklist(self, codes: List[str]) -> None:
        """从黑名单移除代码"""
        for code in codes:
            self.blacklist.discard(code.strip())
        self._blacklist_enabled = len(self.blacklist) > 0
    
    def get_validation_stats(self) -> Dict:
        """
        获取验证配置统计信息
        
        返回:
            配置信息字典
        """
        return {
            'whitelist_enabled': self._whitelist_enabled,
            'blacklist_enabled': self._blacklist_enabled,
            'whitelist_count': len(self.whitelist),
            'blacklist_count': len(self.blacklist),
            'whitelist_codes': sorted(list(self.whitelist))[:10],
            'blacklist_codes': sorted(list(self.blacklist))[:10]
        }
    
    def parse_file(self, file_path: str) -> Dict:
        """
        自动识别文件格式并解析
        
        参数:
            file_path: 文件路径
            
        返回:
            解析结果字典
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'data': [],
                'error': f'文件不存在: {file_path}'
            }
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            return self.parse_csv(file_path)
        elif ext == '.json':
            return self.parse_json(file_path)
        elif ext == '.txt':
            return self.parse_txt(file_path)
        else:
            return {
                'success': False,
                'data': [],
                'error': f'不支持的文件格式: {ext}'
            }
    
    def parse_txt(self, file_path: str) -> Dict:
        """
        解析TXT文件（每行一个股票代码）
        
        参数:
            file_path: 文件路径
            
        返回:
            解析结果字典
        """
        try:
            # 检测文件编码
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'
            
            # 读取TXT文件
            stocks = []
            with open(file_path, 'r', encoding=encoding) as f:
                for line_num, line in enumerate(f, 1):
                    stock = self._parse_txt_line(line.strip(), line_num)
                    if stock:
                        stocks.append(stock)
            
            return {
                'success': True,
                'data': stocks,
                'format': 'txt',
                'total_count': len(stocks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'error': f'TXT解析失败: {str(e)}'
            }
    
    def _parse_txt_line(self, line: str, line_num: int) -> Optional[Dict]:
        """
        解析TXT文件的一行（带严格验证）
        
        参数:
            line: 行内容
            line_num: 行号
            
        返回:
            股票字典或None
        """
        try:
            # 跳过空行和注释行
            if not line or line.startswith('#'):
                return None
            
            # 提取股票代码
            code = self._extract_code(line)
            
            if not code:
                print(
                    f"[错误] 第{line_num}行: 无法识别股票代码\n"
                    f"  └─ 原始内容: \"{line}\"\n"
                    f"  └─ 原因: 无法从该行提取有效的股票代码\n"
                    f"  └─ 建议: 请确保每行只包含一个6位数字的股票代码（如：000001、600519）"
                )
                return None
            
            # 执行严格的股票代码验证
            is_valid, error_reason, suggestion = self.validate_stock_code(code, line_num)
            
            if not is_valid:
                print(
                    f"[错误] 第{line_num}行: 股票代码验证失败\n"
                    f"  └─ 原始代码: \"{code}\"\n"
                    f"  └─ 无效原因: {error_reason}\n"
                    f"  └─ 建议修正: {suggestion}"
                )
                return None
            
            # 从代码推断股票名称（使用常见股票映射）
            name = self._get_stock_name(code)
            
            stock = {
                'code': code,
                'name': name,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'active',
                'notes': ''
            }
            
            return stock
            
        except Exception as e:
            print(
                f"[错误] 第{line_num}行: 解析过程发生异常\n"
                f"  └─ 原始内容: \"{line}\"\n"
                f"  └─ 异常类型: {type(e).__name__}\n"
                f"  └─ 异常信息: {str(e)}\n"
                f"  └─ 建议: 请检查该行格式是否符合要求或联系技术支持"
            )
            return None
    
    def _get_stock_name(self, code: str) -> str:
        """
        根据股票代码获取股票名称（带未知代码智能提示）
        
        参数:
            code: 股票代码
            
        返回:
            股票名称
        """
        if not code or not isinstance(code, str):
            return '未知股票'
        
        # 常见股票代码映射
        stock_names = {
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
        
        # 查找已知股票名称
        known_name = stock_names.get(code)
        
        if known_name:
            return known_name
        
        # 未知代码的智能识别与提示
        code_prefix = code[:3] if len(code) >= 3 else code[:1]
        
        # 根据代码前缀推断市场类型
        market_info = {
            '000': '(深市主板)',
            '001': '(深市主板)',
            '002': '(中小板)',
            '003': '(中小板)',
            '300': '(创业板)',
            '301': '(创业板)',
            '600': '(沪市主板)',
            '601': '(沪市主板)',
            '603': '(沪市主板)',
            '605': '(沪市主板)',
            '688': '(科创板)',
            '689': '(科创板)'
        }
        
        market_hint = market_info.get(code_prefix, '(未知市场)')
        
        return f'待确认股票{code}{market_hint}'
    
    def parse_csv(self, file_path: str) -> Dict:
        """
        解析CSV文件
        
        参数:
            file_path: 文件路径
            
        返回:
            解析结果字典
        """
        try:
            # 检测文件编码
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'
            
            # 读取CSV文件
            stocks = []
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    stock = self._parse_row(row, row_num)
                    if stock:
                        stocks.append(stock)
            
            return {
                'success': True,
                'data': stocks,
                'format': 'csv',
                'total_count': len(stocks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'error': f'CSV解析失败: {str(e)}'
            }
    
    def parse_json(self, file_path: str) -> Dict:
        """
        解析JSON文件
        
        参数:
            file_path: 文件路径
            
        返回:
            解析结果字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks = []
            
            # 支持多种JSON格式
            if isinstance(data, dict):
                if 'stocks' in data:
                    stocks_data = data['stocks']
                elif 'data' in data:
                    stocks_data = data['data']
                else:
                    stocks_data = [data]
            elif isinstance(data, list):
                stocks_data = data
            else:
                return {
                    'success': False,
                    'data': [],
                    'error': '不支持的JSON格式'
                }
            
            for idx, item in enumerate(stocks_data):
                stock = self._parse_row(item, idx + 1)
                if stock:
                    stocks.append(stock)
            
            return {
                'success': True,
                'data': stocks,
                'format': 'json',
                'total_count': len(stocks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'error': f'JSON解析失败: {str(e)}'
            }
    
    def _parse_row(self, row: Dict, row_num: int) -> Optional[Dict]:
        """
        解析单行数据（带严格验证）
        
        参数:
            row: 行数据
            row_num: 行号
            
        返回:
            股票字典或None
        """
        try:
            # 提取股票代码和名称
            code = self._extract_code(row.get('code') or row.get('股票代码') or row.get('symbol'))
            name = row.get('name') or row.get('股票名称') or row.get('stock_name') or ''
            
            if not code:
                print(
                    f"[错误] 第{row_num}行: 缺少必要字段 - 股票代码\n"
                    f"  └─ 原始数据: {row}\n"
                    f"  └─ 原因: 未找到有效的股票代码字段（code/股票代码/symbol）\n"
                    f"  └─ 建议: 请确保每行包含'code'、'股票代码'或'symbol'字段"
                )
                return None
            
            # 执行严格的股票代码验证
            is_valid, error_reason, suggestion = self.validate_stock_code(code, row_num)
            
            if not is_valid:
                print(
                    f"[错误] 第{row_num}行: 股票代码验证失败\n"
                    f"  └─ 原始代码: \"{code}\"\n"
                    f"  └─ 无效原因: {error_reason}\n"
                    f"  └─ 建议修正: {suggestion}"
                )
                return None
            
            if not name or not str(name).strip():
                print(
                    f"[警告] 第{row_num}行: 股票名称为空\n"
                    f"  └─ 股票代码: {code}\n"
                    f"  └─ 原因: 未找到有效的股票名称字段或值为空\n"
                    f"  └─ 处理: 将使用自动推断的名称"
                )
                name = self._get_stock_name(code)
            
            # 构建股票信息
            stock = {
                'code': code,
                'name': name.strip(),
                'date': row.get('date') or row.get('日期') or datetime.now().strftime('%Y-%m-%d'),
                'status': row.get('status') or row.get('状态') or 'active',
                'notes': row.get('notes') or row.get('备注') or ''
            }
            
            # 添加可选字段
            for field in self.optional_fields:
                if field in row:
                    stock[field] = row[field]
            
            return stock
            
        except Exception as e:
            print(
                f"[错误] 第{row_num}行: 解析过程发生异常\n"
                f"  └─ 原始数据: {row}\n"
                f"  └─ 异常类型: {type(e).__name__}\n"
                f"  └─ 异常信息: {str(e)}\n"
                f"  └─ 建议: 请检查该行数据格式是否符合要求或联系技术支持"
            )
            return None
    
    def _extract_code(self, code: str) -> str:
        """
        提取股票代码
        
        参数:
            code: 原始代码
            
        返回:
            标准化股票代码
        """
        if not code:
            return ''
        
        # 移除空格和特殊字符
        code = str(code).strip().upper()
        
        # 移除股票后缀
        code = re.sub(r'\.(SH|SZ|HK)$', '', code)
        
        # 确保是6位数字（A股）
        if len(code) == 6 and code.isdigit():
            return code
        
        # 处理其他格式
        code = re.sub(r'[^\d]', '', code)
        
        return code
    
    def create_sample_file(self, file_path: str, format_type: str = 'csv'):
        """
        创建示例文件
        
        参数:
            file_path: 文件路径
            format_type: 文件格式 (csv/json/txt)
        """
        sample_stocks = [
            {'code': '000001', 'name': '平安银行', 'date': '2024-01-01', 'status': 'active', 'notes': '银行股'},
            {'code': '600519', 'name': '贵州茅台', 'date': '2024-01-01', 'status': 'active', 'notes': '白酒龙头'},
            {'code': '000002', 'name': '万科A', 'date': '2024-01-01', 'status': 'active', 'notes': '房地产'},
            {'code': '000858', 'name': '五粮液', 'date': '2024-01-01', 'status': 'active', 'notes': '白酒'},
            {'code': '600036', 'name': '招商银行', 'date': '2024-01-01', 'status': 'active', 'notes': '银行'}
        ]
        
        if format_type == 'csv':
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['code', 'name', 'date', 'status', 'notes'])
                writer.writeheader()
                writer.writerows(sample_stocks)
        
        elif format_type == 'json':
            data = {
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stocks': sample_stocks
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        elif format_type == 'txt':
            with open(file_path, 'w', encoding='utf-8') as f:
                for stock in sample_stocks:
                    f.write(f"{stock['code']}\n")
        
        print(f"[创建] 示例{format_type.upper()}文件已创建: {file_path}")
    
    def validate_file(self, file_path: str) -> Dict:
        """
        验证文件格式
        
        参数:
            file_path: 文件路径
            
        返回:
            验证结果字典
        """
        result = self.parse_file(file_path)
        
        if not result['success']:
            return result
        
        # 检查必要字段
        missing_fields = []
        for stock in result['data']:
            for field in self.required_fields:
                if field not in stock or not stock[field]:
                    missing_fields.append(field)
        
        if missing_fields:
            return {
                'success': False,
                'data': [],
                'error': f'缺少必要字段: {set(missing_fields)}'
            }
        
        return {
            'success': True,
            'data': result['data'],
            'format': result['format'],
            'total_count': result['total_count'],
            'validation': '文件格式验证通过'
        }
    
    def export_to_format(self, stocks: List[Dict], output_path: str, format_type: str = 'csv'):
        """
        导出数据到指定格式
        
        参数:
            stocks: 股票列表
            output_path: 输出路径
            format_type: 输出格式
        """
        if format_type == 'csv':
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['code', 'name', 'date', 'status', 'notes'])
                writer.writeheader()
                writer.writerows(stocks)
        
        elif format_type == 'json':
            data = {
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(stocks),
                'stocks': stocks
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        elif format_type == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for stock in stocks:
                    f.write(f"{stock['code']}\n")
        
        print(f"[导出] 已导出 {len(stocks)} 只股票到 {output_path}")
