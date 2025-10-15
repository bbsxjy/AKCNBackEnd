"""
CMDB数据导入脚本
快速从Excel文件导入CMDB系统目录数据
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.cmdb_import_service import CMDBImportService
from app.db.session import AsyncSessionLocal


async def import_cmdb_data(excel_path: str, replace_existing: bool = False):
    """
    导入CMDB数据

    Args:
        excel_path: Excel文件路径
        replace_existing: 是否替换现有数据
    """
    print(f"{'='*60}")
    print("CMDB系统目录数据导入")
    print(f"{'='*60}")
    print(f"Excel文件: {excel_path}")
    print(f"替换模式: {'是' if replace_existing else '否（增量导入）'}")
    print(f"{'='*60}\n")

    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"❌ 错误: 文件不存在 - {excel_path}")
        return False

    async with AsyncSessionLocal() as db:
        try:
            print("📥 开始导入数据...\n")

            result = await CMDBImportService.import_from_excel(
                db,
                file_path=excel_path,
                replace_existing=replace_existing
            )

            # 打印导入结果
            print(f"{'='*60}")
            print("✅ 导入完成!")
            print(f"{'='*60}")

            print("\n📊 导入统计:")
            print(f"  总行数: {result['total_rows']}")
            print(f"  耗时: {result['duration_seconds']:.2f} 秒")

            print("\n📋 L2应用:")
            print(f"  ✓ 导入: {result['l2_applications']['imported']} 条")
            print(f"  ⊘ 跳过: {result['l2_applications']['skipped']} 条")
            print(f"  ✗ 错误: {result['l2_applications']['errors']} 条")

            print("\n📋 156L1系统:")
            print(f"  ✓ 导入: {result['l1_156_systems']['imported']} 条")
            print(f"  ⊘ 跳过: {result['l1_156_systems']['skipped']} 条")
            print(f"  ✗ 错误: {result['l1_156_systems']['errors']} 条")

            print("\n📋 87L1系统:")
            print(f"  ✓ 导入: {result['l1_87_systems']['imported']} 条")
            print(f"  ⊘ 跳过: {result['l1_87_systems']['skipped']} 条")
            print(f"  ✗ 错误: {result['l1_87_systems']['errors']} 条")

            print(f"\n{'='*60}\n")

            return True

        except Exception as e:
            print(f"\n❌ 导入失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def show_statistics():
    """显示当前CMDB数据统计"""
    from app.services.cmdb_query_service import CMDBQueryService

    async with AsyncSessionLocal() as db:
        stats = await CMDBQueryService.get_statistics(db)

        print(f"{'='*60}")
        print("📊 CMDB数据统计")
        print(f"{'='*60}")
        print(f"\nL2应用总数: {stats['l2_applications']['total']}")
        print(f"156L1系统总数: {stats['l1_156_systems']['total']}")
        print(f"87L1系统总数: {stats['l1_87_systems']['total']}")

        if stats['l2_applications']['by_status']:
            print(f"\nL2应用状态分布:")
            for status, count in stats['l2_applications']['by_status'].items():
                if status:  # 跳过None
                    print(f"  - {status}: {count}")

        if stats['l2_applications']['by_management_level']:
            print(f"\nL2应用管理级别分布:")
            for level, count in stats['l2_applications']['by_management_level'].items():
                if level:  # 跳过None
                    print(f"  - {level}: {count}")

        print(f"\n{'='*60}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='CMDB系统目录数据导入工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 增量导入（默认）
  python import_cmdb_data.py "C:\\path\\to\\excel.xlsx"

  # 完全替换现有数据
  python import_cmdb_data.py "C:\\path\\to\\excel.xlsx" --replace

  # 查看当前统计
  python import_cmdb_data.py --stats
        """
    )

    parser.add_argument(
        'excel_path',
        nargs='?',
        help='Excel文件路径'
    )
    parser.add_argument(
        '--replace',
        action='store_true',
        help='替换现有数据（默认为增量导入）'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='显示当前CMDB数据统计'
    )

    args = parser.parse_args()

    # 显示统计
    if args.stats:
        asyncio.run(show_statistics())
        return

    # 导入数据
    if not args.excel_path:
        parser.print_help()
        return

    success = asyncio.run(import_cmdb_data(
        args.excel_path,
        replace_existing=args.replace
    ))

    if success:
        print("💡 提示: 使用 --stats 参数查看导入后的统计信息")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
