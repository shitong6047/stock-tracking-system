# 股票跟踪预测系统

基于多因子模型的股票跟踪与次日涨跌预测系统。

## 功能特性

- **文件解析**: 支持CSV和JSON格式的股票跟踪预测文件
- **数据获取**: 从AkShare获取实时行情、历史K线、财务指标
- **技术分析**: 计算MA、MACD、KDJ、RSI、BOLL等技术指标
- **价值评估**: 财务评分、估值计算、安全边际分析
- **预测模型**: 多因子模型预测次日涨跌
- **报告生成**: 自动生成预测报告和汇总报告

## 目录结构

```
缅A/
├── main.py                  # 主程序入口
├── file_parser.py           # 文件解析模块
├── data_acquisition.py      # 数据获取模块
├── technical_analysis.py    # 技术分析模块
├── value_evaluation.py      # 价值评估模块
├── prediction_model.py      # 预测模型模块
├── test_system.py           # 测试模块
├── requirements.txt         # 依赖库
├── PRD_股票选股跟踪系统.md   # 产品需求文档
├── 技术规格说明文档.md       # 技术规格说明
├── data/                    # 数据目录
│   ├── cache/              # 缓存目录
│   ├── stock_pool.json     # 股票池
│   └── stock_tracking_log.csv  # 跟踪日志
├── models/                  # 模型目录
└── reports/                 # 报告目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 创建股票跟踪预测文件

创建CSV格式文件 `stock_tracking.csv`:
```csv
股票代码,股票名称,关注日期,跟踪状态,备注
000001,平安银行,2026-04-15,跟踪中,银行龙头
600519,贵州茅台,2026-04-15,跟踪中,白酒龙头
```

或JSON格式文件 `stock_tracking.json`:
```json
{
  "stocks": [
    {"code": "000001", "name": "平安银行", "date": "2026-04-15", "status": "跟踪中"},
    {"code": "600519", "name": "贵州茅台", "date": "2026-04-15", "status": "跟踪中"}
  ]
}
```

### 2. 运行系统

```bash
# 完整运行（跟踪+预测）
python main.py -f stock_tracking.json

# 仅跟踪行情
python main.py -f stock_tracking.json -m track

# 仅预测
python main.py -f stock_tracking.json -m predict

# 创建示例文件
python main.py --create-sample
```

### 3. 运行测试

```bash
# 快速离线测试
python test_system.py --quick

# 在线测试（需要网络）
python test_system.py --online

# 单元测试
python test_system.py --unit
```

## 输出文件

### stock_pool.json
股票池配置文件，保存选股结果。

### stock_tracking_log.csv
跟踪日志，记录每次跟踪的股票行情数据。

### reports/
预测报告目录，包含每只股票的详细预测结果和汇总报告。

## 预测因子

| 因子类别 | 权重 | 说明 |
|---------|------|------|
| 技术因子 | 35% | 趋势强度、MACD信号、KDJ信号等 |
| 价值因子 | 30% | PE、PB、ROE、股息率等 |
| 情绪因子 | 20% | 涨跌幅、换手率等 |
| 宏观因子 | 15% | 国际市场数据 |

## 风险提示

- 本系统仅供参考，不构成投资建议
- 预测准确率目标为55%以上，无法保证更高准确率
- 仅支持A股市场
- 投资有风险，决策需谨慎

## 技术栈

- Python 3.8+
- AkShare: 股票数据获取
- Pandas: 数据处理
- NumPy: 数值计算
- XGBoost: 机器学习模型
- Matplotlib: 可视化
