#### 代码结构
目录规范，所有代码文件（.py）都放在`src/`目录下，数据文件（.csv）放在`data/`目录下。
运行时，确保在项目根目录下执行，python src/main.py
顶层模块为`main.py`，负责初始化项目、调用其他模块、处理异常。
其他模块（如`StockTracker.py`、`DataPipeline.py`）负责具体功能实现，不直接与用户交互。
顶层目录下不包含任何其他文件或目录，仅包含`src/`和`data/`目录及说明文件和运行脚本信息，不存放.py文件。
说明文件（如`README.md`、`LICENSE`）放在项目根目录下，运行脚本（如`run.sh`）放在`/scripts/`目录下。