"""
CMDB数据导入脚本
快速从Excel文件导入CMDB系统目录数据
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志 - 关闭SQLAlchemy的INFO级别日志（必须在导入之前）
import logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)

# 设置临时环境变量，关闭SQL echo
import os as _os
_os.environ['SILENCE_SQL'] = '1'

from app.services.cmdb_import_service import CMDBImportService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# 创建静默引擎（不echo SQL）
silent_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # 强制关闭SQL日志
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_timeout=30,
    connect_args={
        "server_settings": {"application_name": settings.APP_NAME + " - Import"},
        "command_timeout": 60,
        "timeout": 60,
    }
)

# 创建静默会话工厂
AsyncSessionLocal = async_sessionmaker(
    silent_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def import_cmdb_data(excel_path: str, replace_existing: bool = False, export_errors: bool = False):
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
        print(f"[ERROR] File not found - {excel_path}")
        return False

    async with AsyncSessionLocal() as db:
        try:
            print("Starting data import...\n")

            result = await CMDBImportService.import_from_excel(
                db,
                file_path=excel_path,
                replace_existing=replace_existing
            )

            # 打印导入结果
            print(f"{'='*60}")
            print("[SUCCESS] Import completed!")
            print(f"{'='*60}")

            print("\nImport Statistics:")
            print(f"  Total rows: {result['total_rows']}")
            print(f"  Duration: {result['duration_seconds']:.2f} seconds")

            print("\nL2 Applications:")
            print(f"  [+] Imported: {result['l2_applications']['imported']}")
            print(f"  [-] Skipped: {result['l2_applications']['skipped']}")
            print(f"  [X] Errors: {result['l2_applications']['errors']}")

            print("\n156L1 Systems:")
            print(f"  [+] Imported: {result['l1_156_systems']['imported']}")
            print(f"  [-] Skipped: {result['l1_156_systems']['skipped']}")
            print(f"  [X] Errors: {result['l1_156_systems']['errors']}")

            print("\n87L1 Systems:")
            print(f"  [+] Imported: {result['l1_87_systems']['imported']}")
            print(f"  [-] Skipped: {result['l1_87_systems']['skipped']}")
            print(f"  [X] Errors: {result['l1_87_systems']['errors']}")

            # 显示错误详情（如果有）
            if result['l2_applications']['errors'] > 0:
                print(f"\n{'='*60}")
                print(f"ERROR DETAILS - L2 Applications ({result['l2_applications']['errors']} errors)")
                print(f"{'='*60}")
                for i, err in enumerate(result['l2_applications']['error_details'][:20], 1):  # 只显示前20个
                    print(f"{i}. Row {err['row']}: {err['config_id']} - {err['name']}")
                    print(f"   Error: {err['error']}")

                if len(result['l2_applications']['error_details']) > 20:
                    print(f"\n... and {len(result['l2_applications']['error_details']) - 20} more errors")

            # 显示跳过详情（只显示前10个）
            if result['l2_applications']['skipped'] > 0:
                print(f"\n{'='*60}")
                print(f"SKIPPED - L2 Applications ({result['l2_applications']['skipped']} skipped)")
                print(f"{'='*60}")
                for i, skip in enumerate(result['l2_applications']['skipped_details'][:10], 1):
                    print(f"{i}. Row {skip['row']}: {skip['config_id']} - {skip['name']} ({skip['reason']})")

                if len(result['l2_applications']['skipped_details']) > 10:
                    print(f"... and {len(result['l2_applications']['skipped_details']) - 10} more skipped")

            if result['l1_156_systems']['skipped'] > 0 and len(result['l1_156_systems']['skipped_details']) <= 10:
                print(f"\n{'='*60}")
                print(f"SKIPPED - 156L1 Systems ({result['l1_156_systems']['skipped']} skipped)")
                print(f"{'='*60}")
                for i, skip in enumerate(result['l1_156_systems']['skipped_details'][:10], 1):
                    print(f"{i}. Row {skip['row']}: {skip['config_id']}")

            if result['l1_87_systems']['skipped'] > 0 and len(result['l1_87_systems']['skipped_details']) <= 10:
                print(f"\n{'='*60}")
                print(f"SKIPPED - 87L1 Systems ({result['l1_87_systems']['skipped']} skipped)")
                print(f"{'='*60}")
                for i, skip in enumerate(result['l1_87_systems']['skipped_details'][:10], 1):
                    print(f"{i}. Row {skip['row']}: {skip['config_id']}")

            print(f"\n{'='*60}\n")

            # 导出错误详情到文件（如果需要）
            if export_errors and result['l2_applications']['errors'] > 0:
                error_file = "import_errors.txt"
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write(f"CMDB Import Errors - {datetime.now()}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"Total Errors: {result['l2_applications']['errors']}\n\n")

                    for i, err in enumerate(result['l2_applications']['error_details'], 1):
                        f.write(f"{i}. Row {err['row']}: {err['config_id']} - {err['name']}\n")
                        f.write(f"   Error: {err['error']}\n\n")

                print(f"\n[INFO] Full error list exported to: {error_file}")

            # 如果有很多错误，提示可以导出到文件
            elif result['l2_applications']['errors'] > 20:
                print("\n[TIP] To export full error list to file, use --export-errors option")

            return True

        except Exception as e:
            print(f"\n[ERROR] Import failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def show_statistics():
    """显示当前CMDB数据统计"""
    from app.services.cmdb_query_service import CMDBQueryService

    async with AsyncSessionLocal() as db:
        stats = await CMDBQueryService.get_statistics(db)

        print(f"{'='*60}")
        print("CMDB Data Statistics")
        print(f"{'='*60}")
        print(f"\nL2 Applications Total: {stats['l2_applications']['total']}")
        print(f"156L1 Systems Total: {stats['l1_156_systems']['total']}")
        print(f"87L1 Systems Total: {stats['l1_87_systems']['total']}")

        if stats['l2_applications']['by_status']:
            print(f"\nL2 Applications by Status:")
            for status, count in stats['l2_applications']['by_status'].items():
                if status:  # Skip None
                    print(f"  - {status}: {count}")

        if stats['l2_applications']['by_management_level']:
            print(f"\nL2 Applications by Management Level:")
            for level, count in stats['l2_applications']['by_management_level'].items():
                if level:  # Skip None
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
    parser.add_argument(
        '--export-errors',
        action='store_true',
        help='导出完整错误列表到文件'
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
        replace_existing=args.replace,
        export_errors=args.export_errors
    ))

    if success:
        print("\n[TIP] Use --stats to view statistics after import")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
