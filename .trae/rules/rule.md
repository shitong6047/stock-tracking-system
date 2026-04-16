## 项目规范要求

### 文件输出规范
| 文件类型 | 文件名 | 格式说明 |
|---------|--------|---------|
| 跟踪日志 | `data/stock_tracking_log.csv` | CSV格式，支持Excel打开 |
| 选股池 | `data/stock_pool.json` | JSON格式，持久化存储 |

### 日志字段定义
- `timestamp`: 时间戳（ISO 8601格式）
- `stock_code`: 股票代码
- `stock_name`: 股票名称
- `latest_price`: 最新价
- `price_change_pct`: 涨跌幅（%）
- `volume`: 成交量
- `tracking_note`: 跟踪备注
- `alert_signal`: 异常信号标记

### 数据写入规则
- 写入模式：追加写入（`a`/`a+`），禁止覆盖历史数据
- 编码格式：UTF-8 with BOM（确保Excel中文无乱码）
- 目录结构：`data/` 目录统一存放输出文件

### 代码规范
#### 命名规范
| 类型 | 命名方式 | 示例 |
|-----|---------|------|
| 变量/函数 | 小写下划线 | `stock_code`, `fetch_data()` |
| 类名 | 大驼峰 | `StockTracker`, `DataPipeline` |
| 常量 | 全大写下划线 | `MAX_RETRY_COUNT`, `DATA_DIR` |

#### 代码结构

目录规范，所有代码文件（.py）都放在`src/`目录下，数据文件（.csv）放在`data/`目录下。
运行时，确保在项目根目录下执行，python src/main.py
顶层模块为`main.py`，负责初始化项目、调用其他模块、处理异常。
其他模块（如`StockTracker.py`、`DataPipeline.py`）负责具体功能实现，不直接与用户交互。
顶层目录下不包含任何其他文件或目录，仅包含`src/`和`data/`目录及说明文件和运行脚本信息，不存放.py文件。
说明文件（如`README.md`、`LICENSE`）放在项目根目录下，运行脚本（如`run.sh`）放在`/scripts/`目录下。