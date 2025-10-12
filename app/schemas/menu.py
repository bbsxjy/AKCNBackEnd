"""
Menu permission schemas
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MenuItem(BaseModel):
    """Menu item schema."""
    id: str
    name: str
    title: str
    path: str
    icon: str
    order: int
    enabled: bool = True
    badge: Optional[str] = None
    badge_type: Optional[str] = None  # success/warning/danger/info

    model_config = ConfigDict(from_attributes=True)


class MenuGroup(BaseModel):
    """Menu group schema."""
    id: str
    title: str
    order: int
    items: List[MenuItem]

    model_config = ConfigDict(from_attributes=True)


class MenuPermissionsResponse(BaseModel):
    """Menu permissions response schema."""
    user_role: str
    menu_groups: List[MenuGroup]

    model_config = ConfigDict(from_attributes=True)
