"""
Announcement service for announcement management operations
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate

logger = logging.getLogger(__name__)


class AnnouncementService:
    """Service for announcement operations."""

    @staticmethod
    async def get_announcements(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        is_pinned: Optional[bool] = None
    ) -> Tuple[List[Announcement], int]:
        """
        Get paginated list of announcements with filters.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status
            priority: Filter by priority
            is_pinned: Filter by pinned status

        Returns:
            Tuple of (announcements list, total count)
        """
        try:
            # Build base query with eager loading
            query = select(Announcement).options(
                selectinload(Announcement.created_by)
            )
            count_query = select(func.count()).select_from(Announcement)

            # Apply filters
            filters = []
            if status:
                filters.append(Announcement.status == status)
            if priority:
                filters.append(Announcement.priority == priority)
            if is_pinned is not None:
                filters.append(Announcement.is_pinned == is_pinned)

            if filters:
                query = query.where(*filters)
                count_query = count_query.where(*filters)

            # Get total count
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Order by: pinned first, then created_at desc
            query = query.order_by(
                Announcement.is_pinned.desc(),
                Announcement.created_at.desc()
            )

            # Execute query
            result = await db.execute(query)
            announcements = result.scalars().all()

            return list(announcements), total

        except Exception as e:
            logger.error(f"Error getting announcements: {e}")
            raise

    @staticmethod
    async def get_announcement_by_id(
        db: AsyncSession,
        announcement_id: int
    ) -> Optional[Announcement]:
        """Get announcement by ID with relationships."""
        try:
            query = select(Announcement).where(
                Announcement.id == announcement_id
            ).options(
                selectinload(Announcement.created_by)
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting announcement by ID {announcement_id}: {e}")
            raise

    @staticmethod
    async def create_announcement(
        db: AsyncSession,
        announcement_data: AnnouncementCreate,
        created_by_user: User
    ) -> Announcement:
        """
        Create a new announcement.

        Args:
            db: Database session
            announcement_data: Announcement creation data
            created_by_user: User creating the announcement

        Returns:
            Created announcement
        """
        try:
            # Set publish_date to now if not provided and status is published
            publish_date = announcement_data.publish_date
            if not publish_date and announcement_data.status == "published":
                publish_date = datetime.utcnow()

            # Create new announcement
            announcement = Announcement(
                title=announcement_data.title,
                content=announcement_data.content,
                priority=announcement_data.priority,
                status=announcement_data.status,
                created_by_user_id=created_by_user.id,
                is_pinned=announcement_data.is_pinned,
                publish_date=publish_date,
                expire_date=announcement_data.expire_date
            )
            db.add(announcement)
            await db.commit()
            await db.refresh(announcement)

            # Load relationships
            await db.refresh(announcement, ["created_by"])

            logger.info(f"Announcement created: {announcement.title} (ID: {announcement.id})")
            return announcement

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating announcement: {e}")
            raise

    @staticmethod
    async def update_announcement(
        db: AsyncSession,
        announcement_id: int,
        announcement_data: AnnouncementUpdate
    ) -> Optional[Announcement]:
        """
        Update announcement.

        Args:
            db: Database session
            announcement_id: Announcement ID to update
            announcement_data: Update data

        Returns:
            Updated announcement or None if not found
        """
        try:
            announcement = await AnnouncementService.get_announcement_by_id(
                db, announcement_id
            )
            if not announcement:
                return None

            # Update fields
            update_data = announcement_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "status" and value == "published" and not announcement.publish_date:
                    # Set publish_date if changing to published and not set
                    announcement.publish_date = datetime.utcnow()
                setattr(announcement, field, value)

            await db.commit()
            await db.refresh(announcement)
            logger.info(f"Announcement updated: {announcement.title} (ID: {announcement.id})")
            return announcement

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating announcement {announcement_id}: {e}")
            raise

    @staticmethod
    async def delete_announcement(db: AsyncSession, announcement_id: int) -> bool:
        """
        Delete an announcement.

        Args:
            db: Database session
            announcement_id: Announcement ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            announcement = await AnnouncementService.get_announcement_by_id(
                db, announcement_id
            )
            if not announcement:
                return False

            await db.delete(announcement)
            await db.commit()
            logger.info(f"Announcement deleted: {announcement.title} (ID: {announcement.id})")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting announcement {announcement_id}: {e}")
            raise

    @staticmethod
    async def toggle_pin(
        db: AsyncSession,
        announcement_id: int,
        is_pinned: bool
    ) -> Optional[Announcement]:
        """
        Toggle announcement pin status.

        Args:
            db: Database session
            announcement_id: Announcement ID
            is_pinned: Pin status

        Returns:
            Updated announcement or None if not found
        """
        try:
            announcement = await AnnouncementService.get_announcement_by_id(
                db, announcement_id
            )
            if not announcement:
                return None

            announcement.is_pinned = is_pinned
            await db.commit()
            await db.refresh(announcement)
            logger.info(f"Announcement pin toggled: {announcement.title} -> {is_pinned}")
            return announcement

        except Exception as e:
            await db.rollback()
            logger.error(f"Error toggling pin for announcement {announcement_id}: {e}")
            raise

    @staticmethod
    async def get_active_announcements(
        db: AsyncSession,
        limit: Optional[int] = 10
    ) -> List[Announcement]:
        """
        Get active announcements (published and not expired).

        Args:
            db: Database session
            limit: Maximum number of announcements to return

        Returns:
            List of active announcements
        """
        try:
            now = datetime.utcnow()
            query = select(Announcement).where(
                and_(
                    Announcement.status == "published",
                    Announcement.publish_date <= now,
                    or_(
                        Announcement.expire_date.is_(None),
                        Announcement.expire_date > now
                    )
                )
            ).options(
                selectinload(Announcement.created_by)
            ).order_by(
                Announcement.is_pinned.desc(),
                Announcement.created_at.desc()
            )

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting active announcements: {e}")
            raise

    @staticmethod
    async def get_pinned_announcements(db: AsyncSession) -> List[Announcement]:
        """
        Get all pinned active announcements.

        Args:
            db: Database session

        Returns:
            List of pinned active announcements
        """
        try:
            now = datetime.utcnow()
            query = select(Announcement).where(
                and_(
                    Announcement.status == "published",
                    Announcement.is_pinned == True,
                    Announcement.publish_date <= now,
                    or_(
                        Announcement.expire_date.is_(None),
                        Announcement.expire_date > now
                    )
                )
            ).options(
                selectinload(Announcement.created_by)
            ).order_by(
                Announcement.created_at.desc()
            )

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting pinned announcements: {e}")
            raise


announcement_service = AnnouncementService()
