"""
Menu permission service for role-based menu access control
"""

import logging
from typing import List, Dict
from app.models.user import User
from app.schemas.menu import MenuItem, MenuGroup, MenuPermissionsResponse

logger = logging.getLogger(__name__)


class MenuService:
    """Service for menu permission operations."""

    # Define all available menu items
    ALL_MENU_ITEMS = {
        # Common features
        "dashboard": MenuItem(
            id="dashboard",
            name="Dashboard",
            title="仪表盘",
            path="/dashboard",
            icon="odometer",
            order=1,
            enabled=True
        ),
        "applications": MenuItem(
            id="applications",
            name="Applications",
            title="应用管理",
            path="/applications",
            icon="document",
            order=2,
            enabled=True
        ),
        "my-tasks": MenuItem(
            id="my-tasks",
            name="MyTasks",
            title="我的任务",
            path="/my-tasks",
            icon="user",
            order=3,
            enabled=True
        ),
        # Data management
        "import": MenuItem(
            id="import",
            name="Import",
            title="批量导入",
            path="/import",
            icon="upload",
            order=1,
            enabled=True
        ),
        "reports": MenuItem(
            id="reports",
            name="Reports",
            title="报表中心",
            path="/reports",
            icon="pie-chart",
            order=2,
            enabled=True
        ),
        # System management
        "user-management": MenuItem(
            id="user-management",
            name="UserManagement",
            title="用户管理",
            path="/user-management",
            icon="setting",
            order=1,
            enabled=True
        ),
        "announcements": MenuItem(
            id="announcements",
            name="Announcements",
            title="公告管理",
            path="/announcements",
            icon="bell-filled",
            order=2,
            enabled=True
        ),
        "audit": MenuItem(
            id="audit",
            name="Audit",
            title="审计日志",
            path="/audit",
            icon="search",
            order=3,
            enabled=True
        ),
        # Tools
        "mcp-agent": MenuItem(
            id="mcp-agent",
            name="MCPAgent",
            title="MCP助手",
            path="/mcp-agent",
            icon="chat-dot-round",
            order=1,
            enabled=True
        ),
    }

    # Role-based menu access configuration
    ROLE_MENU_CONFIG = {
        "admin": {
            "common": ["dashboard", "applications", "my-tasks"],
            "data-management": ["import", "reports"],
            "system-management": ["user-management", "announcements", "audit"],
            "tools": ["mcp-agent"],
        },
        "manager": {
            "common": ["dashboard", "applications", "my-tasks"],
            "data-management": ["import", "reports"],
            "system-management": ["announcements"],
            "tools": ["mcp-agent"],
        },
        "editor": {
            "common": ["dashboard", "applications", "my-tasks"],
            "tools": ["mcp-agent"],
        },
        "viewer": {
            "common": ["dashboard", "applications"],
            "tools": ["mcp-agent"],
        },
    }

    # Menu group definitions
    MENU_GROUP_TITLES = {
        "common": "常用功能",
        "data-management": "数据管理",
        "system-management": "系统管理",
        "tools": "辅助工具",
    }

    MENU_GROUP_ORDER = {
        "common": 1,
        "data-management": 2,
        "system-management": 3,
        "tools": 4,
    }

    @staticmethod
    def get_user_menu_permissions(user: User) -> MenuPermissionsResponse:
        """
        Get menu permissions for a user based on their role.

        Args:
            user: User object

        Returns:
            MenuPermissionsResponse with user role and accessible menu groups
        """
        try:
            # Get user role
            user_role = user.role
            if hasattr(user_role, 'value'):
                user_role = user_role.value

            # Get menu configuration for the role
            role_config = MenuService.ROLE_MENU_CONFIG.get(
                user_role,
                MenuService.ROLE_MENU_CONFIG["viewer"]  # Default to viewer if role not found
            )

            # Build menu groups
            menu_groups = []
            for group_id, menu_item_ids in role_config.items():
                # Get menu items for this group
                items = [
                    MenuService.ALL_MENU_ITEMS[item_id]
                    for item_id in menu_item_ids
                    if item_id in MenuService.ALL_MENU_ITEMS
                ]

                # Only add group if it has items
                if items:
                    menu_group = MenuGroup(
                        id=group_id,
                        title=MenuService.MENU_GROUP_TITLES.get(group_id, group_id),
                        order=MenuService.MENU_GROUP_ORDER.get(group_id, 999),
                        items=items
                    )
                    menu_groups.append(menu_group)

            # Sort groups by order
            menu_groups.sort(key=lambda x: x.order)

            logger.info(f"Generated menu permissions for user {user.username} with role {user_role}")

            return MenuPermissionsResponse(
                user_role=user_role,
                menu_groups=menu_groups
            )

        except Exception as e:
            logger.error(f"Error getting menu permissions for user {user.id}: {e}")
            # Return minimal viewer permissions on error
            return MenuPermissionsResponse(
                user_role="viewer",
                menu_groups=[
                    MenuGroup(
                        id="common",
                        title="常用功能",
                        order=1,
                        items=[MenuService.ALL_MENU_ITEMS["dashboard"]]
                    )
                ]
            )

    @staticmethod
    def check_menu_access(user: User, menu_item_id: str) -> bool:
        """
        Check if a user has access to a specific menu item.

        Args:
            user: User object
            menu_item_id: Menu item ID to check

        Returns:
            bool: True if user has access, False otherwise
        """
        try:
            # Get user role
            user_role = user.role
            if hasattr(user_role, 'value'):
                user_role = user_role.value

            # Get menu configuration for the role
            role_config = MenuService.ROLE_MENU_CONFIG.get(
                user_role,
                MenuService.ROLE_MENU_CONFIG["viewer"]
            )

            # Check if menu item is in any of the user's groups
            for menu_items in role_config.values():
                if menu_item_id in menu_items:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking menu access for user {user.id}: {e}")
            return False


menu_service = MenuService()
