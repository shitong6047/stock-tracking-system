#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.database import SupabaseStorage

def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("数据库连接测试")
    print("=" * 60)
    
    print("\n[步骤1] 加载环境变量...")
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    database_url = os.environ.get('DATABASE_URL')
    
    print(f"  SUPABASE_URL: {supabase_url}")
    print(f"  SUPABASE_KEY: {supabase_key}")
    print(f"  DATABASE_URL: {database_url}")
    
    print("\n[步骤2] 初始化数据库存储...")
    storage = SupabaseStorage()
    
    if storage.is_connected:
        print("✓ 已连接到数据库")
    else:
        print("⚠ 使用文件存储模式（未配置数据库）")
    
    print("\n[步骤3] 测试保存股票池...")
    test_stocks = [
        {'code': '601988', 'name': '中国银行', 'date': '2024-04-16'},
        {'code': '601929', 'name': '吉视传媒', 'date': '2024-04-16'},
        {'code': '601919', 'name': '中远海控', 'date': '2024-04-16'}
    ]
    
    result = storage.save_stock_pool(test_stocks)
    print(f"  保存结果: {'成功' if result else '失败'}")
    
    print("\n[步骤4] 测试保存跟踪日志...")
    test_log = {
        'timestamp': '2024-04-16 15:00:00',
        'stock_code': '601988',
        'stock_name': '中国银行',
        'latest_price': 3.50,
        'price_change_pct': 1.20,
        'volume': 1000000,
        'tracking_note': '正常跟踪'
    }
    
    result = storage.save_tracking_log([test_log])
    print(f"  保存结果: {'成功' if result else '失败'}")
    
    print("\n[步骤5] 测试保存预测结果...")
    test_prediction = {
        'code': '601988',
        'name': '中国银行',
        'direction': '上涨',
        'probability': 0.65,
        'confidence': '中等',
        'total_score': 85,
        'key_signals': ['MA5上穿MA10', 'MACD金叉'],
        'risk_warning': '市场波动风险'
    }
    
    result = storage.save_prediction(test_prediction)
    print(f"  保存结果: {'成功' if result else '失败'}")
    
    print("\n[步骤6] 测试保存国际新闻...")
    test_news = [
        {
            'title': '测试新闻',
            'summary': '这是一条测试新闻',
            'pub_time': '2024-04-16 15:00:00',
            'source': '测试来源',
            'url': 'http://test.com',
            'impact': '乐观',
            'impact_score': 0.5
        }
    ]
    
    result = storage.save_global_news(test_news)
    print(f"  保存结果: {'成功' if result else '失败'}")
    
    print("\n" + "=" * 60)
    print("数据库连接测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_database_connection()
