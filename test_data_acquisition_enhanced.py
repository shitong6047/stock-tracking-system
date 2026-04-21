"""
数据获取模块增强功能测试
验证：股票列表、实时行情、历史K线、基本面数据、缓存、并发处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_acquisition import DataAcquisition
import pandas as pd


def test_get_all_stock_list():
    """测试A股全市场股票列表获取"""
    print("\n" + "="*60)
    print("测试1: A股全市场股票列表获取")
    print("="*60)

    da = DataAcquisition(cache_dir='./data/test_cache')

    for scope in ['all', 'main_board', 'csi300', 'csi500']:
        stocks = da.get_all_stock_list(scope=scope)
        print(f"\n✓ scope={scope}: 获取到 {len(stocks)} 只股票")

        if stocks:
            sample = stocks[0]
            print(f"  示例: {sample}")
            assert 'code' in sample, "缺少code字段"
            assert 'name' in sample, "缺少name字段"
            assert 'market' in sample, "缺少market字段"
            assert sample['market'] in ['SH', 'SZ'], f"无效market值: {sample['market']}"

    print("\n✅ 测试1通过: 股票列表获取正常")


def test_batch_realtime_enhanced():
    """测试增强的批量实时行情（新增字段）"""
    print("\n" + "="*60)
    print("测试2: 增强的批量实时行情（新增字段）")
    print("="*60)

    da = DataAcquisition(cache_dir='./data/test_cache')
    test_codes = ['600519', '000001', '601988', '300750', '000858']

    result = da.get_batch_realtime(test_codes)
    print(f"\n✓ 获取到 {len(result)} 只股票实时行情")

    for code, data in result.items():
        print(f"\n  {code} ({data['name']}):")
        print(f"    最新价: {data['latest_price']} | 涨跌幅: {data['change_pct']}%")
        print(f"    换手率: {data.get('turnover_rate')}% (新增)")
        print(f"    量比: {data.get('volume_ratio')} (新增)")
        print(f"    振幅: {data.get('amplitude')}% (新增)")

        required_fields = ['latest_price', 'change_pct', 'open', 'high', 'low',
                          'volume', 'amount', 'turnover_rate', 'volume_ratio', 'amplitude']
        for field in required_fields:
            assert field in data, f"缺少字段: {field}"

    print("\n✅ 测试2通过: 实时行情新增字段正常")


def test_stock_history_kline():
    """测试历史K线数据获取"""
    print("\n" + "="*60)
    print("测试3: 历史K线数据获取")
    print("="*60)

    da = DataAcquisition(cache_dir='./data/test_cache')

    df_30days = da.get_stock_history('600519', days=30)
    print(f"\n✓ 30天K线数据:")
    print(f"  形状: {df_30days.shape}")
    print(f"  列名: {list(df_30days.columns)}")
    print(f"\n  前3行数据:")
    print(df_30days.head(3).to_string(index=False))

    expected_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']
    for col in expected_columns:
        assert col in df_30days.columns, f"缺少列: {col}"

    df_60days = da.get_stock_history('600519', days=60)
    print(f"\n✓ 60天K线数据: {len(df_60days)} 条记录")

    assert len(df_60days) == 60, f"期望60条记录，实际{len(df_60days)}条"

    prices = df_60days['收盘'].values
    has_trend = abs(prices[-1] - prices[0]) > 1
    if has_trend:
        direction = "上涨" if prices[-1] > prices[0] else "下跌"
        print(f"  ✓ 数据具有趋势性 ({direction})")

    price_changes = []
    for i in range(1, len(prices)):
        change = abs(prices[i] - prices[i-1]) / prices[i-1]
        price_changes.append(change)
    avg_volatility = sum(price_changes) / len(price_changes)
    print(f"  ✓ 平均波动率: {avg_volatility:.4f}")

    print("\n✅ 测试3通过: 历史K线数据正常")


def test_fundamental_data_complete():
    """测试完整的基本面数据获取"""
    print("\n" + "="*60)
    print("测试4: 完整基本面数据获取")
    print("="*60)

    da = DataAcquisition(cache_dir='./data/test_cache')
    test_code = '600519'

    data = da.get_fundamental_data(test_code)
    print(f"\n✓ 获取到 {test_code} 的基本面数据:")

    categories = {
        'valuation': '估值指标',
        'profitability': '盈利能力',
        'growth': '成长性',
        'financial_health': '财务健康'
    }

    for category_key, category_name in categories.items():
        if category_key in data:
            print(f"\n  【{category_name}】")
            for key, value in data[category_key].items():
                print(f"    {key}: {value}")

    assert 'valuation' in data, "缺少估值指标"
    assert 'profitability' in data, "缺少盈利能力指标"
    assert 'growth' in data, "缺少成长性指标"
    assert 'financial_health' in data, "缺少财务健康指标"

    valuation = data['valuation']
    required_valuation = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'pcf_ratio', 'market_cap']
    for field in required_valuation:
        assert field in valuation, f"估值指标缺少: {field}"

    profitability = data['profitability']
    required_profit = ['roe', 'roa', 'gross_margin', 'net_margin']
    for field in required_profit:
        assert field in profitability, f"盈利能力指标缺少: {field}"

    growth = data['growth']
    required_growth = ['revenue_growth_yoy', 'profit_growth', 'eps_growth']
    for field in required_growth:
        assert field in growth, f"成长性指标缺少: {field}"

    health = data['financial_health']
    required_health = ['debt_ratio', 'current_ratio', 'quick_ratio', 'goodwill_ratio']
    for field in required_health:
        assert field in health, f"财务健康指标缺少: {field}"

    print("\n✅ 测试4通过: 基本面数据完整")


def test_cache_mechanism():
    """测试带TTL的缓存机制"""
    print("\n" + "="*60)
    print("测试5: 带TTL的缓存机制")
    print("="*60)

    da = DataAcquisition(cache_dir='./data/test_cache')

    print("\n--- 首次获取（写入缓存） ---")
    data1 = da.get_fundamental_data('000001')
    print(f"  获取数据完成")

    print("\n--- 第二次获取（应从缓存加载） ---")
    data2 = da.get_fundamental_data('000001')
    print(f"  从缓存加载数据完成")

    assert data1 == data2, "缓存数据不一致"

    cache_info = da.get_cache_info()
    print(f"\n✓ 缓存统计信息:")
    print(f"  总条目数: {cache_info['total_entries']}")
    print(f"  有效条目: {cache_info['valid_entries']}")
    print(f"  过期条目: {cache_info['expired_entries']}")
    print(f"  总大小: {cache_info['total_size_mb']} MB")
    print(f"  默认TTL: {cache_info['default_ttl_hours']} 小时")

    print("\n✅ 测试5通过: 缓存机制正常")


def test_parallel_processing():
    """测试并行批量处理"""
    print("\n" + "="*60)
    print("测试6: 并行批量处理优化")
    print("="*60)

    da = DataAcquisition(
        cache_dir='./data/test_cache',
        max_workers=3,
        rate_limit=0.01
    )

    test_codes = ['600519', '000001', '601988', '300750', '000858',
                  '600036', '002415', '000651', '600276', '600887']

    print("\n--- 并行获取实时行情 ---")
    parallel_result = da.get_batch_realtime_parallel(test_codes)
    print(f"  ✓ 并行获取到 {len(parallel_result)} 只股票数据")

    assert len(parallel_result) == len(test_codes), \
        f"期望{len(test_codes)}只，实际{len(parallel_result)}只"

    print("\n--- 批量获取基本面数据 ---")
    fundamental_result = da.get_batch_fundamental_data(test_codes[:5], parallel=True)
    print(f"  ✓ 批量获取到 {len(fundamental_result)} 只股票基本面数据")

    assert len(fundamental_result) == 5, f"期望5只，实际{len(fundamental_result)}只"

    print("\n✅ 测试6通过: 并行批量处理正常")


def test_deterministic_consistency():
    """测试确定性一致性"""
    print("\n" + "="*60)
    print("测试7: 确定性一致性验证")
    print("="*60)

    da1 = DataAcquisition(cache_dir='./data/test_cache')
    da2 = DataAcquisition(cache_dir='./data/test_cache')

    code = '600519'

    rt_data1 = da1.get_batch_realtime([code])
    rt_data2 = da2.get_batch_realtime([code])

    assert rt_data1[code]['latest_price'] == rt_data2[code]['latest_price'], \
        "实时行情数据不一致"
    assert rt_data1[code]['change_pct'] == rt_data2[code]['change_pct'], \
        "涨跌幅数据不一致"
    print("  ✓ 实时行情数据一致")

    hist1 = da1.get_stock_history(code, days=10)
    hist2 = da2.get_stock_history(code, days=10)

    assert hist1.equals(hist2), "历史K线数据不一致"
    print("  ✓ 历史K线数据一致")

    fund1 = da1.get_fundamental_data(code)
    fund2 = da2.get_fundamental_data(code)

    assert fund1 == fund2, "基本面数据不一致"
    print("  ✓ 基本面数据一致")

    print("\n✅ 测试7通过: 确定性一致性验证通过")


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("#  数据获取模块增强功能测试套件")
    print("#"*70)

    try:
        test_get_all_stock_list()
        test_batch_realtime_enhanced()
        test_stock_history_kline()
        test_fundamental_data_complete()
        test_cache_mechanism()
        test_parallel_processing()
        test_deterministic_consistency()

        print("\n" + "#"*70)
        print("#  🎉 所有测试通过！")
        print("#"*70)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
