"""
User service for user management operations
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations."""

    @staticmethod
    async def get_users(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """
        Get paginated list of users with filters.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of items per page
            role: Filter by role
            department: Filter by department
            is_active: Filter by active status
            search: Search in username, full_name, or email

        Returns:
            Tuple of (users list, total count)
        """
        try:
            # Build base query
            query = select(User)
            count_query = select(func.count()).select_from(User)

            # Apply filters
            filters = []
            if role:
                filters.append(User.role == role)
            if department:
                filters.append(User.department == department)
            if is_active is not None:
                filters.append(User.is_active == is_active)
            if search:
                search_filter = or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
                filters.append(search_filter)

            if filters:
                query = query.where(*filters)
                count_query = count_query.where(*filters)

            # Get total count
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Order by created_at desc
            query = query.order_by(User.created_at.desc())

            # Execute query
            result = await db.execute(query)
            users = result.scalars().all()

            return list(users), total

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            result = await db.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            raise

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            Created user

        Raises:
            IntegrityError: If username, email, or employee_id already exists
        """
        try:
            # Check if user already exists
            existing = await UserService.get_user_by_email(db, user_data.email)
            if existing:
                raise IntegrityError("User with this email already exists", None, None)

            existing = await UserService.get_user_by_username(db, user_data.username)
            if existing:
                raise IntegrityError("User with this username already exists", None, None)

            # Create new user
            user = User(
                sso_user_id=user_data.sso_user_id,
                employee_id=user_data.employee_id,
                username=user_data.username,
                full_name=user_data.full_name,
                email=user_data.email,
                department=user_data.department,
                team=user_data.team,
                role=UserRole(user_data.role),
                is_active=user_data.is_active
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"User created: {user.username} (ID: {user.id})")
            return user

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error creating user: {e}")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        user_data: UserUpdate
    ) -> Optional[User]:
        """
        Update user information.

        Args:
            db: Database session
            user_id: User ID to update
            user_data: Update data

        Returns:
            Updated user or None if not found
        """
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return None

            # Update fields
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "role" and value:
                    value = UserRole(value)
                setattr(user, field, value)

            await db.commit()
            await db.refresh(user)
            logger.info(f"User updated: {user.username} (ID: {user.id})")
            return user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """
        Delete a user.

        Args:
            db: Database session
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return False

            await db.delete(user)
            await db.commit()
            logger.info(f"User deleted: {user.username} (ID: {user.id})")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise

    @staticmethod
    async def update_user_role(
        db: AsyncSession,
        user_id: int,
        role: str
    ) -> Optional[User]:
        """Update user role."""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return None

            user.role = UserRole(role)
            await db.commit()
            await db.refresh(user)
            logger.info(f"User role updated: {user.username} -> {role}")
            return user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user role {user_id}: {e}")
            raise

    @staticmethod
    async def update_user_status(
        db: AsyncSession,
        user_id: int,
        is_active: bool
    ) -> Optional[User]:
        """Update user active status."""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return None

            user.is_active = is_active
            await db.commit()
            await db.refresh(user)
            logger.info(f"User status updated: {user.username} -> {'active' if is_active else 'inactive'}")
            return user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user status {user_id}: {e}")
            raise

    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: int) -> None:
        """Update user's last login time."""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if user:
                user.last_login_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            # Don't raise, as this is not critical

    @staticmethod
    async def batch_update_role(
        db: AsyncSession,
        user_ids: List[int],
        role: str,
        current_user_id: int
    ) -> Tuple[int, int, List[int]]:
        """
        Batch update user roles.

        Args:
            db: Database session
            user_ids: List of user IDs to update
            role: Target role
            current_user_id: ID of the user performing the operation (to prevent self-modification)

        Returns:
            Tuple of (success_count, failed_count, failed_ids)
        """
        success_count = 0
        failed_count = 0
        failed_ids = []

        try:
            for user_id in user_ids:
                # Prevent self-role change
                if user_id == current_user_id:
                    logger.warning(f"Skipping role update for current user {user_id}")
                    failed_count += 1
                    failed_ids.append(user_id)
                    continue

                try:
                    user = await UserService.get_user_by_id(db, user_id)
                    if user:
                        user.role = role
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(user_id)
                except Exception as e:
                    logger.error(f"Error updating role for user {user_id}: {e}")
                    failed_count += 1
                    failed_ids.append(user_id)

            await db.commit()
            logger.info(f"Batch role update completed: {success_count} succeeded, {failed_count} failed")
            return success_count, failed_count, failed_ids

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in batch role update: {e}")
            raise

    @staticmethod
    async def batch_update_department(
        db: AsyncSession,
        user_ids: List[int],
        department: str
    ) -> Tuple[int, int, List[int]]:
        """
        Batch update user departments.

        Args:
            db: Database session
            user_ids: List of user IDs to update
            department: Target department

        Returns:
            Tuple of (success_count, failed_count, failed_ids)
        """
        success_count = 0
        failed_count = 0
        failed_ids = []

        try:
            for user_id in user_ids:
                try:
                    user = await UserService.get_user_by_id(db, user_id)
                    if user:
                        user.department = department
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(user_id)
                except Exception as e:
                    logger.error(f"Error updating department for user {user_id}: {e}")
                    failed_count += 1
                    failed_ids.append(user_id)

            await db.commit()
            logger.info(f"Batch department update completed: {success_count} succeeded, {failed_count} failed")
            return success_count, failed_count, failed_ids

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in batch department update: {e}")
            raise

    @staticmethod
    async def batch_update_team(
        db: AsyncSession,
        user_ids: List[int],
        team: str
    ) -> Tuple[int, int, List[int]]:
        """
        Batch update user teams.

        Args:
            db: Database session
            user_ids: List of user IDs to update
            team: Target team

        Returns:
            Tuple of (success_count, failed_count, failed_ids)
        """
        success_count = 0
        failed_count = 0
        failed_ids = []

        try:
            for user_id in user_ids:
                try:
                    user = await UserService.get_user_by_id(db, user_id)
                    if user:
                        user.team = team
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(user_id)
                except Exception as e:
                    logger.error(f"Error updating team for user {user_id}: {e}")
                    failed_count += 1
                    failed_ids.append(user_id)

            await db.commit()
            logger.info(f"Batch team update completed: {success_count} succeeded, {failed_count} failed")
            return success_count, failed_count, failed_ids

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in batch team update: {e}")
            raise

    @staticmethod
    async def batch_update_status(
        db: AsyncSession,
        user_ids: List[int],
        is_active: bool,
        current_user_id: int
    ) -> Tuple[int, int, List[int]]:
        """
        Batch update user active status.

        Args:
            db: Database session
            user_ids: List of user IDs to update
            is_active: Target active status
            current_user_id: ID of the user performing the operation (to prevent self-deactivation)

        Returns:
            Tuple of (success_count, failed_count, failed_ids)
        """
        success_count = 0
        failed_count = 0
        failed_ids = []

        try:
            for user_id in user_ids:
                # Prevent self-deactivation
                if user_id == current_user_id and not is_active:
                    logger.warning(f"Skipping status update for current user {user_id}")
                    failed_count += 1
                    failed_ids.append(user_id)
                    continue

                try:
                    user = await UserService.get_user_by_id(db, user_id)
                    if user:
                        user.is_active = is_active
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(user_id)
                except Exception as e:
                    logger.error(f"Error updating status for user {user_id}: {e}")
                    failed_count += 1
                    failed_ids.append(user_id)

            await db.commit()
            logger.info(f"Batch status update completed: {success_count} succeeded, {failed_count} failed")
            return success_count, failed_count, failed_ids

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in batch status update: {e}")
            raise


user_service = UserService()
