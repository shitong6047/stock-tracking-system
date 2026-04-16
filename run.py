#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票跟踪预测系统 - 运行脚本
功能：启动股票跟踪预测系统
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main_simple import SimpleStockTrackingSystem, create_sample_tracking_file
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票跟踪预测系统')
    parser.add_argument('-f', '--file', type=str, help='股票跟踪预测文件路径')
    parser.add_argument('-m', '--mode', type=str, default='all', 
                       choices=['track', 'predict', 'all'],
                       help='运行模式: track(仅跟踪), predict(仅预测), all(全部)')
    parser.add_argument('--create-sample', action='store_true', 
                       help='创建示例股票跟踪预测文件')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_tracking_file()
        return
    
    system = SimpleStockTrackingSystem()
    system.run(file_path=args.file, mode=args.mode)

if __name__ == "__main__":
    main()