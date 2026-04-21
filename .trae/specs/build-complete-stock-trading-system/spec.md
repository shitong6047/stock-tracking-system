# A股智能炒股系统规格

## Why
当前系统仅具备基础的股票跟踪和简单预测功能，无法满足实际投资决策需求。需要构建一个完整的A股智能炒股系统，能够：
1. **自动选股**：从全A股市场筛选出最具潜力的1支股票
2. **精准分析**：对指定股票进行深度技术面和基本面分析
3. **可靠预测**：基于历史数据验证的预测模型，提供涨跌概率和置信度
4. **实用建议**：给出明确的买入/卖出信号和风险提示

## What Changes
- 新增**市场扫描模块**：自动扫描A股市场，筛选优质标的
- 增强**分析引擎**：整合技术分析和基本面分析的多因子模型
- 升级**预测算法**：引入历史回测验证机制，提高预测准确率
- 完善**报告系统**：生成包含买卖建议和风险评估的完整报告
- 优化**用户交互**：支持命令行参数配置和多种运行模式

## Impact
- Affected specs: 全系统升级（数据获取、分析、预测、报告）
- Affected code: 
  - `src/main.py` - 主程序架构重构
  - `src/data_acquisition.py` - 增加市场扫描功能
  - `src/technical_analysis.py` - 增强技术指标计算
  - `src/value_evaluation.py` - 完善基本面分析
  - `src/prediction_model.py` - 引入历史验证机制
  - `src/report_generator.py` (新建) - 专业报告生成

---

## ADDED Requirements

### Requirement 1: A股市场智能扫描
The system SHALL automatically scan the entire A-share market to identify the most promising stock for next-day trading.

#### Scenario 1.1: Market-wide screening
- **WHEN** user runs system in "screen" mode without specifying stocks
- **THEN** system SHALL scan all A-share stocks (Shanghai + Shenzhen main boards)
- **AND** apply multi-factor scoring algorithm to rank stocks
- **AND** return top 1 stock with highest probability of rising next day
- **AND** provide detailed analysis report for selected stock

#### Scenario 1.2: Technical indicators integration
- **WHEN** scanning market data
- **THEN** system SHALL calculate key technical indicators:
  - Moving averages (MA5, MA10, MA20, MA60)
  - MACD with signal line and histogram
  - RSI (6, 12, 24 periods)
  - KDJ stochastic oscillator
  - Bollinger Bands (upper, middle, lower)
  - Volume analysis (OBV, turnover rate)

#### Scenario 1.3: Fundamental analysis factors
- **WHEN** evaluating stock quality
- **THEN** system SHALL consider fundamental metrics:
  - P/E ratio and P/B ratio comparison with industry average
  - Revenue growth rate (YoY, QoQ)
  - Net profit margin trends
  - ROE and ROA performance
  - Debt-to-equity ratio assessment
  - Cash flow health indicators

### Requirement 2: 指定股票深度分析
The system SHALL provide comprehensive analysis for stocks specified in "股票.txt".

#### Scenario 2.1: File parsing enhancement
- **WHEN** user provides "股票.txt" file
- **THEN** system SHALL parse all valid 6-digit stock codes
- **AND** skip invalid codes with clear error messages
- **AND** support comments (lines starting with #) and empty lines

#### Scenario 2.2: Multi-dimensional analysis
- **WHEN** analyzing specified stocks
- **THEN** system SHALL generate detailed reports including:
  - Current price position relative to moving averages
  - Recent trend direction and strength
  - Support/resistance levels identification
  - Volume-price relationship analysis
  - Key technical signal summary (bullish/bearish)
  - Fundamental health score (0-100)

#### Scenario 2.3: Historical pattern recognition
- **WHEN** analyzing stock history
- **THEN** system SHALL identify similar historical patterns
- **AND** calculate probability distribution of next-day outcomes
- **AND** highlight significant price levels and events

### Requirement 3: 可靠的预测模型
The prediction model SHALL be validated through historical backtesting.

#### Scenario 3.1: Historical validation mechanism
- **WHEN** generating predictions
- **THEN** system SHALL use last N days (configurable, default 60) as training window
- **AND** validate model accuracy on recent M days (configurable, default 20)
- **AND** report historical accuracy metrics:
  - Overall prediction accuracy (% correct direction)
  - Precision for "up" predictions
  - Recall for actual "up" movements
  - F1-score for balanced evaluation

#### Scenario 3.2: Probability-based predictions
- **WHEN** predicting next-day movement
- **THEN** system SHALL output:
  - Direction: 上涨(Up) / 下跌(Down) / 震荡(Sideways)
  - Probability: Confidence level (0.0 - 1.0)
  - Expected return range: Min / Max / Most likely
  - Key supporting signals: List of 3-5 most influential factors
  - Risk level: Low / Medium / High based on volatility

#### Scenario 3.3: Model ensemble approach
- **WHEN** calculating final prediction
- **THEN** system SHALL combine multiple models:
  - Technical analysis model (weight: 40%)
  - Fundamental analysis model (weight: 30%)
  - Market sentiment model (weight: 20%)
  - Historical pattern matching (weight: 10%)
- **AND** adjust weights dynamically based on recent model performance

### Requirement 4: 实用交易建议
The system SHALL provide actionable trading recommendations with risk warnings.

#### Scenario 4.1: Buy/Sell/Hold signals
- **WHEN** generating trading advice
- **THEN** system SHALL clearly state:
  - **Strong Buy**: Probability > 70%, multiple confirmations, low risk
  - **Buy**: Probability 55-70%, positive signals outweigh negative
  - **Hold**: Probability 45-55%, unclear direction, wait for confirmation
  - **Sell**: Probability < 45%, bearish signals dominant
  - **Strong Sell**: Probability < 30%, high risk of decline
- **AND** include recommended entry/exit price levels
- **AND** suggest position sizing (percentage of portfolio)

#### Scenario 4.2: Risk assessment and warnings
- **WHEN** providing recommendations
- **THEN** system SHALL highlight risks:
  - Market-level risks: Index trends, sector rotation, macro events
  - Stock-specific risks: Volatility spikes, unusual volume, news impact
  - Model uncertainty: Low confidence due to conflicting signals
  - Stop-loss recommendation: Price level to limit losses (-3% to -7%)
  - Take-profit target: Realistic upside target (+5% to +15%)

#### Scenario 4.3: Time-sensitive advice validity
- **WHEN** generating predictions
- **THEN** system SHALL specify:
  - Prediction timestamp (when analysis was run)
  - Validity period (next trading day only)
  - Recommended review time (before market open/close)
  - Conditions that would invalidate the prediction

### Requirement 5: 专业报告输出
The system SHALL generate professional-grade analysis reports in multiple formats.

#### Scenario 5.1: Console output format
- **WHEN** running in terminal
- **THEN** display formatted report with:
  - Clear section headers and visual separators
  - Color-coded signals (green=buy, red=sell, yellow=hold)
  - Key metrics highlighted with ★ markers
  - Summary at top with details below

#### Scenario 5.2: File export capability
- **WHEN** user requests saved reports
- **THEN** generate files in:
  - Markdown (.md): For documentation and sharing
  - JSON (.json): For programmatic access
  - CSV (.csv): For spreadsheet analysis
- **AND** save to configurable output directory (default: ./reports/)
- **AND** include timestamp in filename for version control

#### Scenario 5.3: Report content structure
Each report SHALL contain:
```
═══════════════════════════════════════════════════
  📊 A股智能分析报告
  生成时间: 2026-04-16 15:30:00
  分析模式: [市场扫描/指定分析]
═══════════════════════════════════════════════════

【★ 核心推荐】
🎯 最佳标的: 601988 中国银行
📈 预测方向: 上涨 | 概率: 72.5%
💰 操作建议: ★★★★☆ 强烈推荐买入
⚠️  风险等级: 中等 | 止损: -5% | 目标: +8%

【技术面分析】
✅ MA金叉形成 (MA5上穿MA20)
✅ MACD柱状图转正
⚠️ RSI接近超买区(68)
📊 综合技术评分: 78/100

【基本面分析】
✅ PE(5.8x)低于行业平均(12.3x)
✅ ROE持续改善(+15% YoY)
⚠️ 负债率略高(85%)
📊 综合基本面评分: 82/100

【历史验证】
📈 近20日预测准确率: 75%
📈 上涨预测命中率: 80%
📈 模型置信度: 高

【关键信号】
1. 放量突破60日均线
2. 北向资金连续3日净流入
3. 行业政策利好预期
4. 季报业绩预增公告

【风险提示】
⚠️ 大盘震荡风险
⚠️ 银行板块轮动加速
⚠️ 利率变动敏感度高

═══════════════════════════════════════════════════
免责声明：本报告仅供参考，不构成投资建议...
═══════════════════════════════════════════════════
```

---

## MODIFIED Requirements

### Requirement: 数据获取模块扩展
Modified `DataAcquisition` class to support:
- Batch market data retrieval for all A-shares
- Real-time quote streaming for monitored stocks
- Historical data caching with TTL (Time-To-Live)
- Fallback mechanisms when primary data source fails
- Rate limiting to avoid API throttling

### Requirement: 技术分析引擎增强
Modified `TechnicalAnalysis` class to include:
- Additional indicators: ADX, CCI, Williams %R, Ichimoku Cloud
- Multi-timeframe analysis (daily, weekly, monthly)
- Signal strength quantification (weak/moderate/strong)
- Pattern recognition (head-shoulders, double-top, etc.)
- Trend classification (uptrend/downtrend/sideways)

### Requirement: 基本面评估完善
Modified `ValueEvaluation` class to incorporate:
- Industry peer comparison benchmarks
- Financial statement quality scoring
- Management efficiency metrics
- Growth sustainability assessment
- Valuation model (DCF, DDM) estimates

---

## REMOVED Requirements

### Requirement: 简单随机模拟
**Reason**: Random data generation is unsuitable for real investment decisions
**Migration**: Replace with deterministic algorithms using real or simulated-but-realistic market data

---

## Validation Criteria

### Functional Testing
- [ ] Market scan mode successfully identifies top candidate from full A-share universe
- [ ] Specified stock analysis generates comprehensive multi-dimensional report
- [ ] Predictions include historical accuracy metrics (>65% baseline target)
- [ ] Trading recommendations are clear and actionable
- [ ] Risk warnings are prominent and specific

### Accuracy Validation
- [ ] Backtesting on 6-month historical data shows >60% directional accuracy
- [ ] Top-1 selection beats random selection by >15%
- [ ] Probability calibration: 70% predicted ≈ 70% actual occurrence
- [ ] No systematic bias in over/under-prediction

### Performance Requirements
- [ ] Full market scan completes within 120 seconds (3000+ stocks)
- [ ] Single stock analysis completes within 5 seconds
- [ ] Report generation adds <2 seconds overhead
- [ ] Memory usage stays under 500MB during operation

### User Experience
- [ ] Clear command-line interface with helpful error messages
- [ ] Output is readable in both terminal and file formats
- [ ] Configuration options documented and easy to modify
- [ ] Graceful handling of network failures and missing data

---

## Configuration Options

System SHALL support configuration via:
1. Command-line arguments (highest priority)
2. Environment variables (medium priority)
3. Config file `config.json` (lowest priority, defaults)

Key parameters:
```json
{
  "mode": "screen|analyze|both",
  "input_file": "股票.txt",
  "output_dir": "./reports/",
  "scan_scope": "all|main_board|csi300|csi500",
  "top_n": 1,
  "lookback_days": 60,
  "validation_days": 20,
  "risk_tolerance": "low|medium|high",
  "min_confidence": 0.55,
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.08
}
```
