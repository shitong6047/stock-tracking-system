# 股票跟踪预测系统 - 使用说明

## 系统功能

### 1. 股票池管理
- 支持多种文件格式：CSV、JSON、TXT
- 自动识别股票代码和名称
- 股票池保存到Supabase数据库或本地文件

### 2. 实时行情跟踪
- 批量获取股票实时行情数据
- 实时价格、涨跌幅、成交量、换手率等
- 异常提醒：涨幅>5%、跌幅>3%、量比>2倍

### 3. 国际消息面采集
- 采集全球金融市场新闻
- 分析市场情绪影响（乐观/悲观）
- 计算净影响值

### 4. 股票预测模型
- 多因子预测模型
- 技术面分析（MA、MACD、KDJ、RSI、布林带）
- 价值评估（PE、PB、ROE、DCF）
- 市场消息面影响分析
- 预测结果保存到本地文件

### 5. 数据库存储
- Supabase数据库集成
- 文件存储降级方案
- 支持股票池、跟踪日志、预测结果、国际新闻存储

## 运行环境

- Python版本：3.7.0
- 操作系统：Windows

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置文件

### .env 文件（可选）

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

如果未配置Supabase，系统会自动使用文件存储模式。

## 使用方法

### 1. 创建示例股票池文件

```bash
python.exe src/main.py --create-sample
```

### 2. 运行完整系统（跟踪+预测）

```bash
python.exe src/main.py -f data/stock_pool.txt
```

### 3. 仅跟踪股票行情

```bash
python.exe src/main.py -f data/stock_pool.txt -m track
```

### 4. 仅预测股票涨跌

```bash
python.exe src/main.py -f data/stock_pool.txt -m predict
```

## 文件结构

```
缅A/
├── src/                      # 源代码目录
│   ├── main.py              # 主程序入口
│   ├── file_parser.py       # 文件解析模块
│   ├── data_acquisition.py  # 数据获取模块
│   ├── technical_analysis.py # 技术分析模块
│   ├── value_evaluation.py  # 价值评估模块
│   ├── prediction_model.py  # 预测模型模块
│   ├── global_news.py       # 国际新闻采集模块
│   └── database.py          # 数据库存储模块
├── data/                     # 数据目录
│   ├── cache/               # 缓存文件
│   ├── stock_pool.json      # 股票池文件
│   ├── stock_tracking_log.csv # 跟踪日志
│   ├── global_news.json     # 国际新闻
│   └── *.json               # 预测结果
├── reports/                  # 报告目录
│   └── summary_*.txt        # 汇总报告
├── .env                      # 环境配置（可选）
├── requirements.txt          # 依赖包列表
└── README.md                 # 说明文档
```

## 数据存储

### Supabase存储（已配置）
- stock_pool: 股票池数据
- stock_tracking_log: 跟踪日志
- predictions: 预测结果
- global_news: 国际新闻

### 文件存储（降级方案）
- data/stock_pool.json
- data/stock_tracking_log.csv
- data/prediction_*.json
- data/global_news.json

## 异常提醒

系统会在以下情况触发提醒：
- 涨幅超过5%
- 跌幅超过3%
- 成交量翻倍（量比>2）
- 价格突破近期高低点

## 风险提示

本系统仅供参考，不构成投资建议。投资有风险，决策需谨慎。
