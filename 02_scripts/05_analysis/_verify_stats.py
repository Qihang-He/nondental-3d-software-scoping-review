# -*- coding: utf-8 -*-
"""_verify_stats.py —— 计算核验结果的比例与精确 95% 置信区间（Clopper-Pearson）"""
from scipy.stats import beta

N_A = 200
N_B = 100
FALSE_EXCL = 1            # 抽样核验确认的漏排（编号 33）
PENDING = 1               # 待全文核验（编号 55）
REASON_ERR = 6            # 原因标签错误：104/153/157/23/117/137


def ci(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


def upper(k, n, alpha=0.05):
    return 1.0 if k >= n else beta.ppf(1 - alpha, k + 1, n - k)


print('== 样本 A（1,939 条被排除记录中分层随机抽取 200 条）==')
lo, hi = ci(FALSE_EXCL, N_A)
print('确认漏排 %d/%d = %.2f%%；精确 95%% CI = %.2f%%–%.2f%%'
      % (FALSE_EXCL, N_A, FALSE_EXCL / N_A * 100, lo * 100, hi * 100))
print('推断全部 1,939 条被排除记录中漏排数约为 %.1f 条（95%% CI %.1f–%.1f）'
      % (FALSE_EXCL / N_A * 1939, lo * 1939, hi * 1939))
if PENDING:
    print('另有 %d 条待全文核验（编号 55），未计入分子' % PENDING)
    print('  若该条亦为漏排，则漏排率 = %.2f%%（95%% CI %.2f%%–%.2f%%）'
          % ((FALSE_EXCL + PENDING) / N_A * 100, *[x * 100 for x in ci(FALSE_EXCL + PENDING, N_A)]))
    print('  仅取最不利情形（2/200）的上限 = %.2f%%' % (upper(FALSE_EXCL + PENDING, N_A) * 100))

print()
print('== 排除原因标签准确度 ==')
lo, hi = ci(REASON_ERR, N_A)
print('原因标签错误 %d/%d = %.1f%%；精确 95%% CI = %.1f%%–%.1f%%'
      % (REASON_ERR, N_A, REASON_ERR / N_A * 100, lo * 100, hi * 100))
print('即原因标签准确率 ≈ %.1f%%（95%% CI %.1f%%–%.1f%%）'
      % (100 - REASON_ERR / N_A * 100, (1 - hi) * 100, (1 - lo) * 100))

print()
print('== 样本 B（566 条纳入记录中随机抽取 100 条）==')
print('不符合纳入标准 0/%d = 0%%；单侧 95%% 上限 = %.2f%%' % (N_B, upper(0, N_B) * 100))
print('推断全部 566 条纳入记录中错误纳入数上限 ≈ %.1f 条' % (upper(0, N_B) * 566))
