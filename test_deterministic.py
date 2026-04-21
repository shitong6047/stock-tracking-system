import sys
sys.path.insert(0, 'src')
from data_acquisition import DataAcquisition, DeterministicRandom

print('=== 测试1: DeterministicRandom 确定性 ===')
dr1 = DeterministicRandom('600519_2026-04-21')
vals1 = [round(dr1.uniform(10, 100), 4) for _ in range(5)]
print('  第一次调用:', vals1)

dr2 = DeterministicRandom('600519_2026-04-21')
vals2 = [round(dr2.uniform(10, 100), 4) for _ in range(5)]
print('  第二次调用:', vals2)
print('  确定性验证:', vals1 == vals2, '(应True)')

dr3 = DeterministicRandom('000001_2026-04-21')
vals3 = [round(dr3.uniform(10, 100), 4) for _ in range(5)]
print('  不同种子:  ', vals3)
print('  不同种子差异:', vals1 != vals3, '(应True)')

print()
print('=== 测试2: get_batch_realtime 确定性 ===')
da = DataAcquisition()
data1 = da.get_batch_realtime(['600519', '000001', '300750'])
data2 = da.get_batch_realtime(['600519', '000001', '300750'])
for code in data1:
    match = data1[code] == data2[code]
    print('  %s: 确定性=%s' % (code, match))

print()
print('=== 测试3: validate_data_consistency 校验 ===')
passed, errors = da.validate_data_consistency(data1, 'realtime')
err_msg = '; '.join(errors[:5]) if errors else '无'
print('  实时数据校验: passed=%s, errors=%s' % (passed, err_msg))

fin_data = da.get_financial_data('600519')
f_passed, f_errors = da.validate_data_consistency(fin_data, 'financial')
f_err_msg = '; '.join(f_errors[:3]) if f_errors else '无'
print('  财务数据校验: passed=%s, errors=%s' % (f_passed, f_err_msg))

print()
print('=== 测试4: get_stock_history 确定性 ===')
hist1 = da.get_stock_history('600519', days=5)
hist2 = da.get_stock_history('600519', days=5)
print('  历史数据一致性:', hist1.equals(hist2), '(应True)')
print(hist1.to_string(index=False))

print()
print('=== 测试5: get_industry_data 确定性 ===')
ind1 = da.get_industry_data('银行')
ind2 = da.get_industry_data('银行')
print('  行业数据一致性:', ind1 == ind2, '(应True)')
for s in ind1:
    print('   ', s)

print()
print('=== 全部测试完成 ===')
