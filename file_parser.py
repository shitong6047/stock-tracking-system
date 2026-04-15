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
        解析CSV格式文件
        
        参数:
            file_path: CSV文件路径
            
        返回:
            解析结果字典
        """
        try:
            encoding = self.auto_detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            data = []
            errors = []
            
            for i, row in enumerate(rows, start=2):
                stock = self._parse_row(row, i)
                if stock:
                    if stock.get('valid'):
                        data.append(stock)
                    else:
                        errors.append(stock.get('error'))
            
            return {
                'success': len(data) > 0,
                'data': data,
                'error': '; '.join(errors) if errors else None,
                'total': len(rows),
                'parsed': len(data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'error': f'CSV解析失败: {str(e)}'
            }
    
    def parse_json(self, file_path: str) -> Dict:
        """
        解析JSON格式文件
        
        参数:
            file_path: JSON文件路径
            
        返回:
            解析结果字典
        """
        try:
            encoding = self.auto_detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = json.load(f)
            
            if isinstance(content, dict) and 'stocks' in content:
                stocks = content['stocks']
            elif isinstance(content, list):
                stocks = content
            else:
                return {
                    'success': False,
                    'data': [],
                    'error': 'JSON格式不正确，需要包含stocks数组或直接为数组'
                }
            
            data = []
            errors = []
            
            for i, item in enumerate(stocks, start=1):
                stock = self._parse_dict(item, i)
                if stock:
                    if stock.get('valid'):
                        data.append(stock)
                    else:
                        errors.append(stock.get('error'))
            
            return {
                'success': len(data) > 0,
                'data': data,
                'error': '; '.join(errors) if errors else None,
                'total': len(stocks),
                'parsed': len(data)
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'data': [],
                'error': f'JSON解析失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'error': f'文件读取失败: {str(e)}'
            }
    
    def _parse_row(self, row: Dict, line_num: int) -> Optional[Dict]:
        """
        解析CSV行数据
        
        参数:
            row: CSV行数据
            line_num: 行号
            
        返回:
            解析后的股票数据
        """
        field_mapping = {
            '股票代码': 'code',
            '代码': 'code',
            'code': 'code',
            '股票名称': 'name',
            '名称': 'name',
            'name': 'name',
            '关注日期': 'date',
            '日期': 'date',
            'date': 'date',
            '跟踪状态': 'status',
            '状态': 'status',
            'status': 'status',
            '备注': 'notes',
            'notes': 'notes'
        }
        
        normalized = {}
        for key, value in row.items():
            key_lower = key.strip().lower()
            mapped_key = field_mapping.get(key_lower, key_lower)
            normalized[mapped_key] = value.strip() if isinstance(value, str) else value
        
        return self._validate_and_build(normalized, line_num)
    
    def _parse_dict(self, item: Dict, index: int) -> Optional[Dict]:
        """
        解析JSON字典数据
        
        参数:
            item: JSON字典
            index: 索引
            
        返回:
            解析后的股票数据
        """
        normalized = {
            'code': item.get('code') or item.get('股票代码') or item.get('代码'),
            'name': item.get('name') or item.get('股票名称') or item.get('名称'),
            'date': item.get('date') or item.get('关注日期') or item.get('日期'),
            'status': item.get('status') or item.get('跟踪状态') or item.get('状态'),
            'notes': item.get('notes') or item.get('备注')
        }
        
        return self._validate_and_build(normalized, index)
    
    def _validate_and_build(self, data: Dict, index: int) -> Optional[Dict]:
        """
        验证数据并构建结果
        
        参数:
            data: 标准化后的数据
            index: 索引/行号
            
        返回:
            验证后的股票数据
        """
        code = data.get('code')
        name = data.get('name')
        
        if not code:
            return {
                'valid': False,
                'error': f'第{index}条记录缺少股票代码'
            }
        
        if not self.validate_stock_code(str(code)):
            return {
                'valid': False,
                'error': f'第{index}条记录股票代码格式错误: {code}'
            }
        
        code = str(code).zfill(6)
        
        date_str = data.get('date')
        if date_str:
            try:
                if isinstance(date_str, str):
                    date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                else:
                    date = date_str
            except:
                date = datetime.now().strftime('%Y-%m-%d')
        else:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'valid': True,
            'code': code,
            'name': name or f'股票{code}',
            'date': date,
            'status': data.get('status') or '跟踪中',
            'notes': data.get('notes') or ''
        }
    
    def validate_stock_code(self, code: str) -> bool:
        """
        验证股票代码格式
        
        参数:
            code: 股票代码
            
        返回:
            是否有效
        """
        code = str(code).strip()
        
        if not code:
            return False
        
        if not re.match(r'^[0-9]{6}$', code.zfill(6)):
            return False
        
        prefix = code.zfill(6)[:2]
        valid_prefixes = ['00', '30', '60', '68', '12', '15', '18']
        
        return prefix in valid_prefixes
    
    def auto_detect_encoding(self, file_path: str) -> str:
        """
        自动检测文件编码
        
        参数:
            file_path: 文件路径
            
        返回:
            编码名称
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
        
        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        
        if encoding and encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
            return 'gbk'
        
        return encoding or 'utf-8'
    
    def create_sample_file(self, file_path: str, format_type: str = 'csv') -> bool:
        """
        创建示例文件
        
        参数:
            file_path: 文件路径
            format_type: 格式类型 (csv/json)
            
        返回:
            是否成功
        """
        try:
            sample_data = [
                {'code': '000001', 'name': '平安银行', 'date': '2026-04-15', 'status': '跟踪中', 'notes': '银行龙头'},
                {'code': '600519', 'name': '贵州茅台', 'date': '2026-04-15', 'status': '跟踪中', 'notes': '白酒龙头'},
                {'code': '000858', 'name': '五粮液', 'date': '2026-04-15', 'status': '已观察', 'notes': '白酒次龙头'}
            ]
            
            if format_type == 'csv':
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['code', 'name', 'date', 'status', 'notes'])
                    writer.writeheader()
                    writer.writerows(sample_data)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({'stocks': sample_data}, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"创建示例文件失败: {str(e)}")
            return False


if __name__ == "__main__":
    parser = FileParser()
    
    print("=" * 50)
    print("测试文件解析模块")
    print("=" * 50)
    
    parser.create_sample_file('sample_tracking.csv', 'csv')
    parser.create_sample_file('sample_tracking.json', 'json')
    
    print("\n解析CSV文件:")
    result = parser.parse_file('sample_tracking.csv')
    print(f"成功: {result['success']}")
    print(f"解析数量: {result['parsed']}/{result['total']}")
    for stock in result['data']:
        print(f"  {stock['code']} - {stock['name']}")
    
    print("\n解析JSON文件:")
    result = parser.parse_file('sample_tracking.json')
    print(f"成功: {result['success']}")
    print(f"解析数量: {result['parsed']}/{result['total']}")
    for stock in result['data']:
        print(f"  {stock['code']} - {stock['name']}")
    
    print("\n测试股票代码验证:")
    test_codes = ['000001', '600519', '300750', '123456', 'abc', '']
    for code in test_codes:
        valid = parser.validate_stock_code(code)
        print(f"  {code}: {'有效' if valid else '无效'}")
