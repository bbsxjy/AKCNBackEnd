#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import sys

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

# 读取Excel
df = pd.read_excel(r'C:\Users\Administrator\Desktop\TrackerBuilder\需求.xlsx')

print("=== CMDB系统目录需求文档 ===\n")

for idx, row in df.iterrows():
    print(f"\n【需求 {int(row.iloc[0])}】")
    print(f"问题: {row.iloc[1]}")
    print(f"回答: {row.iloc[2]}")
    print("-" * 80)
