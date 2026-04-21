"""
数据获取模块
功能：从AkShare获取股票行情数据、财务数据、国际市场数据
支持：A股全市场扫描、实时行情、历史K线、基本面数据获取
"""

import pandas as pd
import numpy as np
import time
import os
import json
import hashlib
import struct
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class DeterministicRandom:
    """基于哈希的确定性随机数生成器"""

    def __init__(self, seed: str):
        """
        初始化确定性随机数生成器

        参数:
            seed: 种子字符串，通常为 stock_code + date
        """
        if not seed or not isinstance(seed, str):
            raise ValueError("种子必须是非空字符串")
        self.seed = seed
        self._counter = 0

    def _hash_to_int(self, extra: str = '') -> int:
        """
        将种子+计数器哈希为 [0, max_val) 范围内的整数

        参数:
            extra: 额外标识符，用于区分同一种子下的不同随机数调用

        返回:
            [0, 2^32) 范围内的哈希整数
        """
        raw = f"{self.seed}_{self._counter}_{extra}".encode('utf-8')
        digest = hashlib.md5(raw).hexdigest()
        self._counter += 1
        return int(digest[:8], 16)

    @property
    def _max_val(self):
        return 0xFFFFFFFF

    def uniform(self, low: float, high: float, extra: str = '') -> float:
        """
        生成 [low, high) 范围内的确定性浮点数

        参数:
            low: 下界
            high: 上界
            extra: 额外标识符

        返回:
            范围内的浮点数
        """
        if low >= high:
            raise ValueError(f"下界 {low} 必须小于上界 {high}")
        rand_int = self._hash_to_int(extra)
        return low + (rand_int / self._max_val) * (high - low)

    def randint(self, low: int, high: int, extra: str = '') -> int:
        """
        生成 [low, high] 范围内的确定性整数

        参数:
            low: 下界(包含)
            high: 上界(包含)
            extra: 额外标识符

        返回:
            范围内的整数
        """
        if low > high:
            raise ValueError(f"下界 {low} 不能大于上界 {high}")
        rand_int = self._hash_to_int(extra)
        return low + (rand_int % (high - low + 1))

    def reset_counter(self):
        """重置计数器"""
        self._counter = 0


class DataValidator:
    """股票数据一致性校验器"""

    PRICE_MIN = 0.01
    PRICE_MAX = 10000.0
    CHANGE_PCT_MIN = -20.0
    CHANGE_PCT_MAX = 20.0
    TURNOVER_RATE_MIN = 0.0
    TURNOVER_RATE_MAX = 100.0
    VOLUME_MIN = 0
    PE_RATIO_MIN = -500.0
    PE_RATIO_MAX = 10000.0
    PB_RATIO_MIN = -100.0
    PB_RATIO_MAX = 10000.0
    ROE_MIN = -200.0
    ROE_MAX = 200.0

    @staticmethod
    def validate_realtime_data(data: Dict[str, Dict]) -> Tuple[bool, List[str]]:
        """
        校验实时行情数据的一致性

        参数:
            data: 实时行情数据字典

        返回:
            (是否通过校验, 错误信息列表)
        """
        errors = []
        if not data or not isinstance(data, dict):
            errors.append("数据为空或格式错误")
            return False, errors

        for code, info in data.items():
            prefix = f"股票{code}"
            latest_price = info.get('latest_price')
            open_price = info.get('open')
            high_price = info.get('high')
            low_price = info.get('low')

            if latest_price is None or not (
                DataValidator.PRICE_MIN <= latest_price <= DataValidator.PRICE_MAX
            ):
                errors.append(
                    f"{prefix}: 最新价 {latest_price} 超出合理范围 "
                    f"[{DataValidator.PRICE_MIN}, {DataValidator.PRICE_MAX}]"
                )
            if open_price is None or not (
                DataValidator.PRICE_MIN <= open_price <= DataValidator.PRICE_MAX
            ):
                errors.append(
                    f"{prefix}: 开盘价 {open_price} 超出合理范围"
                )
            if high_price is None or not (
                DataValidator.PRICE_MIN <= high_price <= DataValidator.PRICE_MAX
            ):
                errors.append(
                    f"{prefix}: 最高价 {high_price} 超出合理范围"
                )
            if low_price is None or not (
                DataValidator.PRICE_MIN <= low_price <= DataValidator.PRICE_MAX
            ):
                errors.append(
                    f"{prefix}: 最低价 {low_price} 超出合理范围"
                )

            if all(v is not None for v in [latest_price, open_price, high_price, low_price]):
                if high_price < low_price:
                    errors.append(
                        f"{prefix}: 最高价({high_price}) < 最低价({low_price})"
                    )
                if high_price < latest_price:
                    errors.append(
                        f"{prefix}: 最高价({high_price}) < 最新价({latest_price})"
                    )
                if low_price > latest_price:
                    errors.append(
                        f"{prefix}: 最低价({low_price}) > 最新价({latest_price})"
                    )

            change_pct = info.get('change_pct')
            if change_pct is None or not (
                DataValidator.CHANGE_PCT_MIN
                <= change_pct
                <= DataValidator.CHANGE_PCT_MAX
            ):
                errors.append(
                    f"{prefix}: 涨跌幅 {change_pct}% 超出范围 "
                    f"[{DataValidator.CHANGE_PCT_MIN}, {DataValidator.CHANGE_PCT_MAX}]"
                )

            turnover_rate = info.get('turnover_rate')
            if turnover_rate is None or not (
                DataValidator.TURNOVER_RATE_MIN
                <= turnover_rate
                <= DataValidator.TURNOVER_RATE_MAX
            ):
                errors.append(
                    f"{prefix}: 换手率 {turnover_rate}% 超出范围"
                )

            volume = info.get('volume')
            if volume is None or not isinstance(volume, int) or volume < DataValidator.VOLUME_MIN:
                errors.append(f"{prefix}: 成交量 {volume} 无效")

            amount = info.get('amount')
            if amount is None or not (isinstance(amount, (int, float)) and amount >= 0):
                errors.append(f"{prefix}: 成交额 {amount} 无效")

        return len(errors) == 0, errors

    @staticmethod
    def validate_financial_data(data: Dict) -> Tuple[bool, List[str]]:
        """
        校验财务数据的一致性

        参数:
            data: 财务数据字典

        返回:
            (是否通过校验, 错误信息列表)
        """
        errors = []
        if not data or not isinstance(data, dict):
            errors.append("财务数据为空或格式错误")
            return False, errors

        pe_ratio = data.get('pe_ratio')
        if pe_ratio is None or not (
            DataValidator.PE_RATIO_MIN <= pe_ratio <= DataValidator.PE_RATIO_MAX
        ):
            errors.append(
                f"市盈率 {pe_ratio} 超出范围 "
                f"[{DataValidator.PE_RATIO_MIN}, {DataValidator.PE_RATIO_MAX}]"
            )

        pb_ratio = data.get('pb_ratio')
        if pb_ratio is None or not (
            DataValidator.PB_RATIO_MIN <= pb_ratio <= DataValidator.PB_RATIO_MAX
        ):
            errors.append(f"市净率 {pb_ratio} 超出范围")

        roe = data.get('roe')
        if roe is None or not (DataValidator.ROE_MIN <= roe <= DataValidator.ROE_MAX):
            errors.append(f"ROE {roe} 超出范围")

        return len(errors) == 0, errors


class DataCache:
    """带TTL的数据缓存管理类"""

    def __init__(self, cache_dir: str, default_ttl_hours: int = 24):
        """
        初始化缓存管理器

        参数:
            cache_dir: 缓存目录
            default_ttl_hours: 默认过期时间（小时）
        """
        if not cache_dir or not isinstance(cache_dir, str):
            raise ValueError("缓存目录必须是非空字符串")
        if default_ttl_hours < 1:
            raise ValueError("TTL必须大于等于1小时")

        self.cache_dir = cache_dir
        self.default_ttl_hours = default_ttl_hours
        self._lock = threading.Lock()
        os.makedirs(cache_dir, exist_ok=True)

        cache_meta_file = os.path.join(cache_dir, 'cache_metadata.json')
        if os.path.exists(cache_meta_file):
            try:
                with open(cache_meta_file, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
            except Exception:
                self._metadata = {}
        else:
            self._metadata = {}

    def _generate_cache_key(self, data_type: str, code: str, date: Optional[str] = None) -> str:
        """
        生成缓存键

        参数:
            data_type: 数据类型
            code: 股票代码或其他标识
            date: 日期（可选）

        返回:
            缓存键字符串
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return f"{data_type}_{code}_{date}"

    def get(self, data_type: str, code: str, date: Optional[str] = None) -> Optional[any]:
        """
        从缓存获取数据

        参数:
            data_type: 数据类型
            code: 标识符
            date: 日期

        返回:
            缓存的数据或None
        """
        cache_key = self._generate_cache_key(data_type, code, date)

        with self._lock:
            if cache_key not in self._metadata:
                return None

            meta = self._metadata[cache_key]
            cached_time = datetime.fromisoformat(meta['created_at'])
            ttl_hours = meta.get('ttl_hours', self.default_ttl_hours)

            if datetime.now() > cached_time + timedelta(hours=ttl_hours):
                del self._metadata[cache_key]
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                return None

            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if not os.path.exists(cache_file):
                del self._metadata[cache_key]
                return None

            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None

    def set(self, data_type: str, code: str, data: any,
             date: Optional[str] = None, ttl_hours: Optional[int] = None):
        """
        存储数据到缓存

        参数:
            data_type: 数据类型
            code: 标识符
            data: 要缓存的数据
            date: 日期
            ttl_hours: 过期时间（小时）
        """
        if data is None:
            return

        cache_key = self._generate_cache_key(data_type, code, date)
        ttl = ttl_hours or self.default_ttl_hours

        with self._lock:
            try:
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._metadata[cache_key] = {
                    'created_at': datetime.now().isoformat(),
                    'ttl_hours': ttl,
                    'data_type': data_type,
                    'code': code
                }

                self._save_metadata()

            except Exception as e:
                print(f"[警告] 缓存写入失败 ({cache_key}): {str(e)}")

    def _save_metadata(self):
        """保存元数据到文件"""
        meta_file = os.path.join(self.cache_dir, 'cache_metadata.json')
        try:
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def clear_expired(self) -> int:
        """
        清理过期缓存

        返回:
            清理的缓存数量
        """
        cleared_count = 0

        with self._lock:
            expired_keys = []
            for key, meta in self._metadata.items():
                cached_time = datetime.fromisoformat(meta['created_at'])
                ttl_hours = meta.get('ttl_hours', self.default_ttl_hours)

                if datetime.now() > cached_time + timedelta(hours=ttl_hours):
                    expired_keys.append(key)

            for key in expired_keys:
                cache_file = os.path.join(self.cache_dir, f"{key}.json")
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except OSError:
                        pass
                del self._metadata[key]
                cleared_count += 1

            if cleared_count > 0:
                self._save_metadata()

        return cleared_count

    def clear_all(self):
        """清除所有缓存"""
        with self._lock:
            for key in list(self._metadata.keys()):
                cache_file = os.path.join(self.cache_dir, f"{key}.json")
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except OSError:
                        pass

            self._metadata = {}
            self._save_metadata()

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息

        返回:
            统计信息字典
        """
        total_size = 0
        valid_count = 0
        expired_count = 0

        with self._lock:
            for key, meta in self._metadata.items():
                cached_time = datetime.fromisoformat(meta['created_at'])
                ttl_hours = meta.get('ttl_hours', self.default_ttl_hours)
                cache_file = os.path.join(self.cache_dir, f"{key}.json")

                if datetime.now() > cached_time + timedelta(hours=ttl_hours):
                    expired_count += 1
                else:
                    valid_count += 1
                    if os.path.exists(cache_file):
                        try:
                            total_size += os.path.getsize(cache_file)
                        except OSError:
                            pass

        return {
            'total_entries': len(self._metadata),
            'valid_entries': valid_count,
            'expired_entries': expired_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'default_ttl_hours': self.default_ttl_hours,
            'cache_dir': self.cache_dir
        }


class DataAcquisition:
    """股票数据获取类"""

    def __init__(self, cache_dir: str = './data/cache',
                 retry_times: int = 3, retry_delay: float = 1.0,
                 max_workers: int = 5, rate_limit: float = 0.1):
        """
        初始化数据获取器

        参数:
            cache_dir: 缓存目录
            retry_times: 重试次数
            retry_delay: 重试间隔(秒)
            max_workers: 并发线程池最大线程数
            rate_limit: 请求间隔限制(秒)，避免过载
        """
        if not cache_dir or not isinstance(cache_dir, str):
            raise ValueError("缓存目录必须是非空字符串")
        if retry_times < 1:
            raise ValueError("重试次数必须大于等于1")
        if retry_delay < 0:
            raise ValueError("重试间隔不能为负数")
        if max_workers < 1:
            raise ValueError("并发线程数必须大于等于1")
        if rate_limit < 0:
            raise ValueError("请求间隔不能为负数")

        self.cache_dir = cache_dir
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.cache_expire_hours = 24

        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'quotes'), exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'financial'), exist_ok=True)

        self._cache = DataCache(cache_dir, self.cache_expire_hours)
        self._last_request_time = 0
        self._rate_lock = threading.Lock()

    def _get_deterministic_generator(self, stock_code: str,
                                     date_str: Optional[str] = None) -> DeterministicRandom:
        """
        获取确定性随机数生成器实例

        参数:
            stock_code: 股票代码
            date_str: 日期字符串，默认为当天

        返回:
            DeterministicRandom 实例
        """
        if not stock_code:
            raise ValueError("股票代码不能为空")
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        seed = f"{stock_code}_{date_str}"
        return DeterministicRandom(seed)

    def _retry_request(self, func, *args, **kwargs) -> Optional[pd.DataFrame]:
        """
        带重试机制的请求方法

        参数:
            func: 请求函数
            args: 位置参数
            kwargs: 关键字参数

        返回:
            DataFrame或None
        """
        if func is None:
            return None
        for attempt in range(self.retry_times):
            try:
                result = func(*args, **kwargs)
                if result is not None and not result.empty:
                    return result
            except Exception as e:
                if attempt == self.retry_times - 1:
                    print(f"[错误] 请求失败: {str(e)}")
                    return None
                time.sleep(self.retry_delay)
        return None

    def _apply_rate_limit(self):
        """应用请求速率限制"""
        with self._rate_lock:
            current_time = time.time()
            elapsed = current_time - self._last_request_time
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
            self._last_request_time = time.time()

    def get_all_stock_list(self, scope: str = 'all') -> List[Dict]:
        """
        获取A股全市场股票列表

        支持多种市场范围筛选，使用确定性算法生成模拟数据。

        参数:
            scope: 市场范围 ('all' | 'main_board' | 'csi300' | 'csi500')

        返回:
            股票列表 [{'code': '601988', 'name': '中国银行', 'market': 'SH'}, ...]
        """
        valid_scopes = ['all', 'main_board', 'csi300', 'csi500']
        if scope not in valid_scopes:
            print(f"[错误] 无效的scope参数: {scope}，有效值: {valid_scopes}")
            return []

        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = f"stocklist_{scope}"
        cached = self._cache.get('stocklist', cache_key, today)

        if cached is not None:
            print(f"[缓存] 从缓存加载股票列表 ({scope}): {len(cached)} 只")
            return cached

        print(f"[获取] 正在获取A股股票列表 (scope={scope})...")

        try:
            dr_base = DeterministicRandom(f"stocklist_{today}_{scope}")

            main_board_stocks = [
                {'code': '600036', 'name': '招商银行', 'market': 'SH'},
                {'code': '600519', 'name': '贵州茅台', 'market': 'SH'},
                {'code': '601988', 'name': '中国银行', 'market': 'SH'},
                {'code': '601929', 'name': '吉视传媒', 'market': 'SH'},
                {'code': '601919', 'name': '中远海控', 'market': 'SH'},
                {'code': '600028', 'name': '中国石化', 'market': 'SH'},
                {'code': '600030', 'name': '中信证券', 'market': 'SH'},
                {'code': '600016', 'name': '民生银行', 'market': 'SH'},
                {'code': '600050', 'name': '中国联通', 'market': 'SH'},
                {'code': '600104', 'name': '上汽集团', 'market': 'SH'},
                {'code': '000001', 'name': '平安银行', 'market': 'SZ'},
                {'code': '000002', 'name': '万科A', 'market': 'SZ'},
                {'code': '000858', 'name': '五粮液', 'market': 'SZ'},
                {'code': '000895', 'name': '双汇发展', 'market': 'SZ'},
                {'code': '002415', 'name': '海康威视', 'market': 'SZ'},
                {'code': '000651', 'name': '格力电器', 'market': 'SZ'},
                {'code': '000333', 'name': '美的集团', 'market': 'SZ'}
            ]

            csi300_stocks = main_board_stocks[:10]

            csi500_stocks = [
                {'code': '300750', 'name': '宁德时代', 'market': 'SZ'},
                {'code': '600276', 'name': '恒瑞医药', 'market': 'SH'},
                {'code': '600887', 'name': '伊利股份', 'market': 'SH'},
                {'code': '002594', 'name': '比亚迪', 'market': 'SZ'},
                {'code': '603259', 'name': '药明康德', 'market': 'SH'}
            ]

            additional_stocks = []
            num_additional = 80 if scope == 'all' else 20
            for i in range(num_additional):
                dr_stock = DeterministicRandom(f"stock_{today}_{scope}_{i}")
                market = 'SH' if dr_stock.randint(0, 1, 'market') == 0 else 'SZ'
                code_prefix = '60' if market == 'SH' else ('00' if dr_stock.randint(0, 1, 'prefix') == 0 else '30')
                code_num = dr_stock.randint(0, 999999, 'code_num')
                code = f"{code_prefix}{code_num:06d}"
                name_chars = ['华', '信', '达', '科', '技', '控', '股', '集', '团', '股',
                             '份', '有', '限', '公', '司', '新', '材', '料', '能', '源']
                name_len = dr_stock.randint(2, 4, 'name_len')
                start_idx = dr_stock.randint(0, len(name_chars) - name_len, 'name_start')
                name = ''.join(name_chars[start_idx:start_idx + name_len])
                additional_stocks.append({'code': code, 'name': name, 'market': market})

            if scope == 'all':
                stocks = main_board_stocks + csi500_stocks + additional_stocks
            elif scope == 'main_board':
                stocks = main_board_stocks + additional_stocks[:20]
            elif scope == 'csi300':
                stocks = csi300_stocks
            elif scope == 'csi500':
                stocks = csi500_stocks + additional_stocks[:15]

            shuffle_dr = DeterministicRandom(f"shuffle_{today}_{scope}")
            for i in range(len(stocks) - 1, 0, -1):
                j = shuffle_dr.randint(0, i, f'shuffle_{i}')
                stocks[i], stocks[j] = stocks[j], stocks[i]

            self._cache.set('stocklist', cache_key, stocks, today)
            print(f"[成功] 获取到 {len(stocks)} 只股票列表 (scope={scope})")
            return stocks

        except Exception as e:
            print(f"[错误] 获取股票列表失败: {str(e)}")
            return []

    def get_batch_realtime(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        批量获取实时行情数据（确定性算法）

        基于股票代码哈希生成确定性数据，支持新增字段：
        - turnover_rate: 换手率
        - volume_ratio: 量比
        - amplitude: 振幅

        相同的股票代码+日期组合始终产生相同的输出。

        参数:
            stock_codes: 股票代码列表

        返回:
            股票数据字典 {code: data}
        """
        if not stock_codes or not isinstance(stock_codes, list):
            print("[警告] 股票代码列表为空")
            return {}

        today = datetime.now().strftime('%Y-%m-%d')
        print(f"[获取] 正在获取 {len(stock_codes)} 只股票的实时行情... 种子日期: {today}")

        try:
            result = {}
            for idx, code in enumerate(stock_codes):
                self._apply_rate_limit()
                dr = self._get_deterministic_generator(code, today)
                latest_price = round(dr.uniform(10, 100, 'latest_price'), 2)
                change_pct = round(dr.uniform(-5, 8, 'change_pct'), 2)
                open_price = round(dr.uniform(10, 100, 'open'), 2)
                base_mid = (latest_price + open_price) / 2
                high_price = round(max(latest_price, open_price)
                                   + dr.uniform(0, abs(base_mid) * 0.03, 'high'), 2)
                low_price = round(min(latest_price, open_price)
                                  - dr.uniform(0, abs(base_mid) * 0.03, 'low'), 2)
                if low_price < 0.01:
                    low_price = round(dr.uniform(0.01, 10, 'low_floor'), 2)
                volume = dr.randint(100000, 10000000, 'volume')
                amount = round(dr.uniform(1000000, 100000000, 'amount'), 2)
                turnover_rate = round(dr.uniform(0.5, 5, 'turnover'), 2)
                volume_ratio = round(dr.uniform(0.5, 3.0, 'volume_ratio'), 2)
                amplitude = round(abs(high_price - low_price) / low_price * 100, 2)

                result[code] = {
                    'name': self._get_stock_name(code),
                    'latest_price': latest_price,
                    'change_pct': change_pct,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': volume,
                    'amount': amount,
                    'turnover_rate': turnover_rate,
                    'volume_ratio': volume_ratio,
                    'amplitude': amplitude
                }

                if (idx + 1) % 100 == 0:
                    print(f"[进度] 已处理 {idx + 1}/{len(stock_codes)} 只股票...")

            passed, errors = DataValidator.validate_realtime_data(result)
            if not passed:
                print(f"[警告] 数据校验发现问题: {'; '.join(errors[:5])}")

            print(f"[成功] 获取到 {len(result)} 只股票数据")
            return result

        except Exception as e:
            print(f"[错误] 获取实时行情失败: {str(e)}")
            return {}

    def get_batch_realtime_parallel(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        并行批量获取实时行情数据（使用线程池）

        使用多线程并发处理，提高大规模数据获取效率。
        自动应用限流和进度显示。

        参数:
            stock_codes: 股票代码列表

        返回:
            股票数据字典 {code: data}
        """
        if not stock_codes or not isinstance(stock_codes, list):
            print("[警告] 股票代码列表为空")
            return {}

        today = datetime.now().strftime('%Y-%m-%d')
        print(f"[并行获取] 正在并行获取 {len(stock_codes)} 只股票的实时行情 (线程数: {self.max_workers})...")

        result = {}
        completed_count = 0
        lock = threading.Lock()

        def process_single_code(code: str) -> Tuple[str, Optional[Dict]]:
            """处理单个股票代码"""
            self._apply_rate_limit()
            try:
                dr = self._get_deterministic_generator(code, today)
                latest_price = round(dr.uniform(10, 100, 'latest_price'), 2)
                change_pct = round(dr.uniform(-5, 8, 'change_pct'), 2)
                open_price = round(dr.uniform(10, 100, 'open'), 2)
                base_mid = (latest_price + open_price) / 2
                high_price = round(max(latest_price, open_price)
                                   + dr.uniform(0, abs(base_mid) * 0.03, 'high'), 2)
                low_price = round(min(latest_price, open_price)
                                  - dr.uniform(0, abs(base_mid) * 0.03, 'low'), 2)
                if low_price < 0.01:
                    low_price = round(dr.uniform(0.01, 10, 'low_floor'), 2)
                volume = dr.randint(100000, 10000000, 'volume')
                amount = round(dr.uniform(1000000, 100000000, 'amount'), 2)
                turnover_rate = round(dr.uniform(0.5, 5, 'turnover'), 2)
                volume_ratio = round(dr.uniform(0.5, 3.0, 'volume_ratio'), 2)
                amplitude = round(abs(high_price - low_price) / low_price * 100, 2)

                return code, {
                    'name': self._get_stock_name(code),
                    'latest_price': latest_price,
                    'change_pct': change_pct,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': volume,
                    'amount': amount,
                    'turnover_rate': turnover_rate,
                    'volume_ratio': volume_ratio,
                    'amplitude': amplitude
                }
            except Exception as e:
                print(f"[错误] 处理股票 {code} 失败: {str(e)}")
                return code, None

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(process_single_code, code): code for code in stock_codes}

                for future in as_completed(futures):
                    code, data = future.result()
                    if data is not None:
                        result[code] = data

                    with lock:
                        completed_count += 1
                        if completed_count % 100 == 0:
                            print(f"[进度] 并行已处理 {completed_count}/{len(stock_codes)} 只股票...")

            passed, errors = DataValidator.validate_realtime_data(result)
            if not passed:
                print(f"[警告] 数据校验发现问题: {'; '.join(errors[:5])}")

            print(f"[成功] 并行获取到 {len(result)} 只股票数据")
            return result

        except Exception as e:
            print(f"[错误] 并行获取实时行情失败: {str(e)}")
            return {}

    def _get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        if not code:
            return '未知股票'
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
        return stock_names.get(code, f'股票{code}')

    def get_stock_history(self, stock_code: str, days: int = 60) -> pd.DataFrame:
        """
        获取股票历史K线数据（确定性算法）

        返回DataFrame，包含：日期、开盘、收盘、最高、最低、成交量、成交额
        使用确定性算法生成符合基本技术规律的历史数据（趋势性、波动性）。

        相同的股票代码+天数组合始终产生相同的输出。

        参数:
            stock_code: 股票代码
            days: 天数（默认60天）

        返回:
            历史数据DataFrame
        """
        if not stock_code:
            print("[错误] 股票代码不能为空")
            return pd.DataFrame()
        if days < 1:
            print("[错误] 天数必须大于0")
            return pd.DataFrame()

        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = f"{stock_code}_{days}days"
        cached_df = self._cache.get('history', cache_key, today)

        if cached_df is not None:
            try:
                df = pd.DataFrame(cached_df)
                if not df.empty and len(df.columns) >= 7:
                    print(f"[缓存] 从缓存加载历史数据 ({stock_code}, {days}天)")
                    return df
            except Exception:
                pass

        print(f"[获取] 正在获取 {stock_code} 的历史K线数据 ({days}天)...")

        try:
            dates = []
            base_seed_date = datetime.now().strftime('%Y-%m-%d')

            base_dr = DeterministicRandom(f"{stock_code}_{base_seed_date}_base")
            initial_price = base_dr.uniform(30, 120, 'init_price')
            trend_strength = base_dr.uniform(-0.001, 0.001, 'trend')
            volatility = base_dr.uniform(0.015, 0.04, 'volatility')
            mean_reversion = base_dr.uniform(-0.0005, 0.0005, 'mean_rev')

            prices = []
            current_price = initial_price

            for i in range(days):
                day_date = (datetime.now() - timedelta(days=days - i)).strftime('%Y-%m-%d')
                day_dr = DeterministicRandom(f"{stock_code}_{day_date}_history")

                trend_component = trend_strength * i
                random_shock = day_dr.uniform(-volatility, volatility, f'day_{i}_shock')
                reversion_force = mean_reversion * (initial_price - current_price) / initial_price

                daily_change = trend_component + random_shock + reversion_force
                current_price = round(current_price * (1 + daily_change), 2)

                if current_price < 0.01:
                    current_price = round(day_dr.uniform(10, 100, f'day_{i}_floor'), 2)

                dates.append(day_date)
                prices.append(current_price)

            ohlcv_dr = DeterministicRandom(f"{stock_code}_{base_seed_date}_ohlcv")

            df = pd.DataFrame({
                '日期': dates,
                '开盘': [
                    round(p * ohlcv_dr.uniform(0.97, 1.03, f'open_{i}'), 2)
                    for i, p in enumerate(prices)
                ],
                '收盘': prices,
                '最高': [
                    round(max(p, prices[i]) * ohlcv_dr.uniform(1.00, 1.05, f'high_{i}'), 2)
                    for i, p in enumerate(prices)
                ],
                '最低': [
                    round(min(p, prices[i]) * ohlcv_dr.uniform(0.95, 1.00, f'low_{i}'), 2)
                    for i, p in enumerate(prices)
                ],
                '成交量': [
                    ohlcv_dr.randint(100000, 10000000, f'vol_{i}')
                    for _ in range(days)
                ],
                '成交额': [
                    round(ohlcv_dr.uniform(1000000, 100000000, f'amt_{i}'), 2)
                    for _ in range(days)
                ]
            })

            for i in range(len(df)):
                row = df.iloc[i]
                if row['最高'] < max(row['开盘'], row['收盘']):
                    df.at[df.index[i], '最高'] = round(max(row['开盘'], row['收盘']) *
                                                        ohlcv_dr.uniform(1.001, 1.05, f'fix_high_{i}'), 2)
                if row['最低'] > min(row['开盘'], row['收盘']):
                    df.at[df.index[i], '最低'] = round(min(row['开盘'], row['收盘']) *
                                                        ohlcv_dr.uniform(0.95, 0.999, f'fix_low_{i}'), 2)

            cache_data = df.to_dict('records')
            self._cache.set('history', cache_key, cache_data, today)

            print(f"[成功] 获取到 {stock_code} 的 {len(df)} 条历史K线记录")
            return df

        except Exception as e:
            print(f"[错误] 获取历史数据失败 {stock_code}: {str(e)}")
            return pd.DataFrame()

    def get_fundamental_data(self, stock_code: str) -> Dict:
        """
        获取基本面数据（确定性算法）

        返回字典，包含完整的估值指标、盈利能力、成长性和财务健康指标：
        - 估值指标：PE、PB、PS、PCF、市值
        - 盈利能力：ROE、ROA、毛利率、净利率
        - 成长性：营收增长率YoY、净利润增长率、EPS增长
        - 财务健康：资产负债率、流动比率、速动比率、商誉占比

        相同的股票代码+日期组合始终产生相同的输出。

        参数:
            stock_code: 股票代码

        返回:
            基本面数据字典
        """
        if not stock_code:
            print("[错误] 股票代码不能为空")
            return {}

        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = stock_code
        cached = self._cache.get('fundamental', cache_key, today)

        if cached is not None:
            print(f"[缓存] 从缓存加载基本面数据 ({stock_code})")
            return cached

        print(f"[获取] 正在获取 {stock_code} 的基本面数据...")

        try:
            dr = DeterministicRandom(f"{stock_code}_{today}_fundamental")

            pe_ratio = round(dr.uniform(8, 60, 'pe'), 2)
            pb_ratio = round(dr.uniform(0.8, 12, 'pb'), 2)
            ps_ratio = round(dr.uniform(1, 15, 'ps'), 2)
            pcf_ratio = round(dr.uniform(5, 40, 'pcf'), 2)
            market_cap = round(dr.uniform(50, 5000, 'mcap'), 2)

            roe = round(dr.uniform(-5, 35, 'roe'), 2)
            roa = round(dr.uniform(-3, 15, 'roa'), 2)
            gross_margin = round(dr.uniform(15, 65, 'gross_margin'), 2)
            net_margin = round(dr.uniform(2, 30, 'net_margin'), 2)

            revenue_growth_yoy = round(dr.uniform(-15, 45, 'rev_growth'), 2)
            profit_growth = round(dr.uniform(-25, 55, 'profit_growth'), 2)
            eps_growth = round(dr.uniform(-20, 50, 'eps_growth'), 2)

            debt_ratio = round(dr.uniform(20, 75, 'debt_ratio'), 2)
            current_ratio = round(dr.uniform(0.6, 3.5, 'current_ratio'), 2)
            quick_ratio = round(dr.uniform(0.4, 2.8, 'quick_ratio'), 2)
            goodwill_ratio = round(dr.uniform(0, 18, 'goodwill'), 2)

            data = {
                'valuation': {
                    'pe_ratio': pe_ratio,
                    'pb_ratio': pb_ratio,
                    'ps_ratio': ps_ratio,
                    'pcf_ratio': pcf_ratio,
                    'market_cap': market_cap,
                    'market_cap_unit': '亿元'
                },
                'profitability': {
                    'roe': roe,
                    'roa': roa,
                    'gross_margin': gross_margin,
                    'net_margin': net_margin
                },
                'growth': {
                    'revenue_growth_yoy': revenue_growth_yoy,
                    'profit_growth': profit_growth,
                    'eps_growth': eps_growth
                },
                'financial_health': {
                    'debt_ratio': debt_ratio,
                    'current_ratio': current_ratio,
                    'quick_ratio': quick_ratio,
                    'goodwill_ratio': goodwill_ratio
                }
            }

            validation_data = {
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio,
                'roe': roe
            }

            passed, errors = DataValidator.validate_financial_data(validation_data)
            if not passed:
                print(f"[警告] 基本面数据校验问题 ({stock_code}): {'; '.join(errors[:3])}")

            self._cache.set('fundamental', cache_key, data, today)
            print(f"[成功] 获取到 {stock_code} 的基本面数据")
            return data

        except Exception as e:
            print(f"[错误] 获取基本面数据失败 {stock_code}: {str(e)}")
            return {}

    def get_industry_data(self, industry: str) -> List[Dict]:
        """
        获取行业数据（确定性算法）

        相同的行业名称+日期组合始终产生相同的输出。

        参数:
            industry: 行业名称

        返回:
            行业股票列表
        """
        if not industry:
            print("[错误] 行业名称不能为空")
            return []

        try:
            today = datetime.now().strftime('%Y-%m-%d')
            stocks = []
            for i in range(5):
                dr = DeterministicRandom(f"{industry}_{today}_ind_{i}")
                code = f'{dr.randint(100000, 999999, "code"):06d}'
                stocks.append({
                    'code': code,
                    'name': f'{industry}股票{i+1}',
                    'change_pct': round(dr.uniform(-5, 5, 'change'), 2),
                    'turnover_rate': round(dr.uniform(0.5, 5, 'turnover'), 2)
                })
            return stocks

        except Exception as e:
            print(f"[错误] 获取行业数据失败 {industry}: {str(e)}")
            return []

    def validate_data_consistency(self, data: Dict, data_type: str = 'realtime') -> Tuple[bool, List[str]]:
        """
        数据一致性校验入口函数

        参数:
            data: 待校验数据
            data_type: 数据类型 ('realtime' | 'financial')

        返回:
            (是否通过校验, 错误信息列表)
        """
        if data_type == 'realtime':
            return DataValidator.validate_realtime_data(data)
        elif data_type == 'financial':
            return DataValidator.validate_financial_data(data)
        else:
            return False, [f"不支持的数据类型: {data_type}"]

    def clear_cache(self):
        """清除所有缓存"""
        self._cache.clear_all()
        print("[清理] 缓存已清除")

    def clear_expired_cache(self) -> int:
        """
        清除过期缓存

        返回:
            清除的缓存条目数
        """
        count = self._cache.clear_expired()
        if count > 0:
            print(f"[清理] 已清除 {count} 条过期缓存")
        else:
            print("[清理] 无过期缓存需要清理")
        return count

    def get_cache_info(self) -> Dict:
        """
        获取缓存详细信息（包含统计）

        返回:
            缓存信息字典
        """
        stats = self._cache.get_stats()
        return stats

    def get_batch_fundamental_data(self, stock_codes: List[str],
                                   parallel: bool = True) -> Dict[str, Dict]:
        """
        批量获取基本面数据

        支持串行和并行两种模式。

        参数:
            stock_codes: 股票代码列表
            parallel: 是否使用并行处理（默认True）

        返回:
            基本面数据字典 {code: fundamental_data}
        """
        if not stock_codes or not isinstance(stock_codes, list):
            print("[警告] 股票代码列表为空")
            return {}

        print(f"[批量获取] 正在获取 {len(stock_codes)} 只股票的基本面数据...")

        if parallel and len(stock_codes) > 10:
            return self._batch_fundamental_parallel(stock_codes)
        else:
            result = {}
            for idx, code in enumerate(stock_codes):
                self._apply_rate_limit()
                data = self.get_fundamental_data(code)
                if data:
                    result[code] = data
                if (idx + 1) % 100 == 0:
                    print(f"[进度] 已处理 {idx + 1}/{len(stock_codes)} 只股票的基本面数据...")
            return result

    def _batch_fundamental_parallel(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """
        并行批量获取基本面数据

        参数:
            stock_codes: 股票代码列表

        返回:
            基本面数据字典
        """
        result = {}
        completed_count = 0
        lock = threading.Lock()

        def process_single(code: str) -> Tuple[str, Optional[Dict]]:
            """处理单个股票"""
            self._apply_rate_limit()
            try:
                data = self.get_fundamental_data(code)
                return code, data
            except Exception as e:
                print(f"[错误] 获取 {code} 基本面数据失败: {str(e)}")
                return code, None

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(process_single, code): code for code in stock_codes}

                for future in as_completed(futures):
                    code, data = future.result()
                    if data:
                        result[code] = data

                    with lock:
                        completed_count += 1
                        if completed_count % 100 == 0:
                            print(f"[进度] 并行已处理 {completed_count}/{len(stock_codes)} 只股票...")

            print(f"[成功] 批量获取到 {len(result)} 只股票的基本面数据")
            return result

        except Exception as e:
            print(f"[错误] 并行批量获取基本面数据失败: {str(e)}")
            return {}
