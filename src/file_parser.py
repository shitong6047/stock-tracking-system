"""
文件解析模块
功能：解析股票跟踪预测文件，支持CSV和JSON格式
"""

import os
import json
import csv
import chardet
from typing import List, Dict, Optional
from datetime import datetime
import re


class FileParser:
    """股票跟踪预测文件解析器"""
    
    def __init__(self):
        self.required_fields = ['code', 'name']
        self.optional_fields = ['date', 'status', 'notes']
    
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
        else:
            return {
                'success': False,
                'data': [],
                'error': f'不支持的文件格式: {ext}'
            }
    
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
        解析单行数据
        
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
            
            if not code or not name:
                print(f"[警告] 第{row_num}行: 缺少必要字段 (code, name)")
                return None
            
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
            print(f"[警告] 第{row_num}行解析失败: {str(e)}")
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
            format_type: 文件格式 (csv/json)
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
        
        print(f"[导出] 已导出 {len(stocks)} 只股票到 {output_path}")