"""Analyze Excel data to find long columns causing truncation errors"""
import pandas as pd

def analyze_excel_lengths():
    df = pd.read_excel('sysmap.xlsx')
    print(f'Total columns: {len(df.columns)}')
    print(f'Total rows: {len(df)}')

    print('\n' + '='*80)
    print('Column maximum lengths:')
    print('='*80)

    long_columns = []

    for col in df.columns:
        if df[col].dtype == 'object':
            # Get max length for string columns
            max_len = df[col].astype(str).str.len().max()
            if max_len > 200:  # Flag columns longer than typical String(200)
                long_columns.append((col, max_len))
                print(f'⚠️  {col}: {max_len} chars (EXCEEDS TYPICAL LIMIT)')
            elif max_len > 100:
                print(f'   {col}: {max_len} chars')

    print('\n' + '='*80)
    print('PROBLEMATIC COLUMNS (likely causing truncation):')
    print('='*80)
    for col, length in sorted(long_columns, key=lambda x: x[1], reverse=True):
        print(f'{col}: {length} chars')
        # Find which rows have the longest values
        col_lengths = df[col].astype(str).str.len()
        long_rows = col_lengths[col_lengths > 200].index.tolist()
        if len(long_rows) <= 5:
            print(f'  Long values in rows: {long_rows}')
        else:
            print(f'  Long values in {len(long_rows)} rows')
        print()

if __name__ == "__main__":
    analyze_excel_lengths()