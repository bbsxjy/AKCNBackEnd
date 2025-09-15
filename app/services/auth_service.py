"""
Authentication Service for SSO Integration
"""

import jwt
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError


class AuthService:
    """Service for handling SSO authentication and authorization."""
    
    def __init__(self):
        """Initialize auth service."""
        self.sso_config = {
            "issuer": settings.SSO_ISSUER,
            "client_id": settings.SSO_CLIENT_ID,
            "client_secret": settings.SSO_CLIENT_SECRET,
            "redirect_uri": settings.SSO_REDIRECT_URI,
            "token_endpoint": settings.SSO_TOKEN_ENDPOINT,
            "userinfo_endpoint": settings.SSO_USERINFO_ENDPOINT
        }
        self.jwt_secret = settings.SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)
        
    async def validate_sso_token(self, token: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Validate SSO token and extract user information.
        
        Performance requirement: <100ms response time
        """
        try:
            # Decode and verify JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": True}
            )
            
            # Verify issuer
            if payload.get("iss") != self.sso_config["issuer"]:
                raise AuthenticationError("Invalid token issuer")
            
            # Extract user information
            user_info = {
                "employee_id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "department": payload.get("department"),
                "role": payload.get("role")
            }
            
            return user_info
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    async def create_or_update_user(
        self,
        db: AsyncSession,
        sso_data: Dict[str, Any]
    ) -> User:
        """Create or update user from SSO data."""
        # Check if user exists
        result = await db.execute(
            select(User).where(User.employee_id == sso_data["employee_id"])
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.email = sso_data["email"]
            user.full_name = sso_data["name"]
            user.team = sso_data["department"]
            user.role = self.map_sso_role_to_system_role(sso_data["role"])
            user.last_login = datetime.utcnow()
        else:
            # Create new user
            user = User(
                employee_id=sso_data["employee_id"],
                email=sso_data["email"],
                full_name=sso_data["name"],
                team=sso_data["department"],
                role=self.map_sso_role_to_system_role(sso_data["role"]),
                is_active=True,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            db.add(user)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    def map_sso_role_to_system_role(self, sso_role: str) -> str:
        """Map SSO role to system RBAC role."""
        role_mapping = {
            "admin": "Admin",
            "manager": "Manager",
            "developer": "Editor",
            "analyst": "Editor",
            "viewer": "Viewer",
            "guest": "Viewer"
        }
        return role_mapping.get(sso_role.lower(), "Viewer")
    
    async def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create internal JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + self.token_expiry
        
        payload = {
            "sub": str(user.id),
            "employee_id": user.employee_id,
            "email": user.email,
            "role": user.role,
            "team": user.team,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    async def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify internal access token."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    async def create_refresh_token(self, user: User) -> str:
        """Create refresh token for token renewal."""
        expire = datetime.utcnow() + timedelta(days=30)
        
        payload = {
            "sub": str(user.id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> str:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": True}
            )
            
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Get user
            result = await db.execute(
                select(User).where(User.id == int(payload["sub"]))
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Create new access token
            return await self.create_access_token(user)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Refresh token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid refresh token")
    
    def check_permission(
        self,
        user: User,
        resource: str,
        action: str
    ) -> bool:
        """Check if user has permission for resource and action."""
        # Define permission matrix
        permissions = {
            "Admin": {
                "applications": ["create", "read", "update", "delete"],
                "subtasks": ["create", "read", "update", "delete"],
                "reports": ["create", "read", "export"],
                "users": ["create", "read", "update", "delete", "manage"],
                "audit": ["read", "export"],
                "notifications": ["create", "read", "manage"]
            },
            "Manager": {
                "applications": ["create", "read", "update"],
                "subtasks": ["create", "read", "update"],
                "reports": ["create", "read", "export"],
                "users": ["read"],
                "audit": ["read"],
                "notifications": ["create", "read"]
            },
            "Editor": {
                "applications": ["create", "read", "update"],
                "subtasks": ["create", "read", "update"],
                "reports": ["read", "view"],
                "users": ["read"],
                "audit": ["read"],
                "notifications": ["read"]
            },
            "Viewer": {
                "applications": ["read", "view"],
                "subtasks": ["read", "view"],
                "reports": ["read", "view"],
                "users": [],
                "audit": [],
                "notifications": ["read"]
            }
        }
        
        user_permissions = permissions.get(user.role, {})
        resource_permissions = user_permissions.get(resource, [])
        
        return action in resource_permissions
    
    def check_team_permission(
        self,
        user: User,
        entity: Any
    ) -> bool:
        """Check if user has permission to access team-specific entity."""
        # Admin can access all
        if user.role == "Admin":
            return True
        
        # Manager can access their team's data
        if user.role == "Manager":
            if hasattr(entity, "responsible_team"):
                return entity.responsible_team == user.team
        
        # Editor can access assigned entities
        if user.role == "Editor":
            if hasattr(entity, "responsible_person"):
                return entity.responsible_person == user.full_name
        
        return False
    
    async def create_session(
        self,
        db: AsyncSession,
        user: User,
        ip_address: str,
        user_agent: str
    ) -> str:
        """Create user session in Redis."""
        # In production, this would create a Redis session
        # For now, return a session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store session metadata (mock)
        session_data = {
            "user_id": user.id,
            "employee_id": user.employee_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        return session_id
    
    async def validate_session(
        self,
        db: AsyncSession,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Validate session from Redis."""
        # In production, this would check Redis
        # Mock implementation
        if session_id:
            return {
                "valid": True,
                "user_id": 1,
                "last_activity": datetime.utcnow().isoformat()
            }
        return None
    
    async def logout(
        self,
        db: AsyncSession,
        session_id: str
    ) -> bool:
        """Logout user and invalidate session."""
        # In production, delete from Redis
        # Mock implementation
        await db.commit()
        return True
    
    async def exchange_code_for_token(self, code: str) -> str:
        """Exchange authorization code for SSO token."""
        # In production, call SSO token endpoint
        # Mock implementation
        return "mock_sso_token"
    
    async def process_sso_callback(
        self,
        db: AsyncSession,
        code: str
    ) -> Dict[str, Any]:
        """Process SSO callback and create user session."""
        # Exchange code for token
        sso_token = await self.exchange_code_for_token(code)
        
        # Validate token and get user info
        user_info = await self.validate_sso_token(sso_token)
        
        # Create or update user
        user = await self.create_or_update_user(db, user_info)
        
        # Create tokens
        access_token = await self.create_access_token(user)
        refresh_token = await self.create_refresh_token(user)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }
    
    async def log_authentication_event(
        self,
        db: AsyncSession,
        user: User,
        event_type: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[str] = None
    ):
        """Log authentication events for audit."""
        # This would integrate with audit service
        # Mock implementation
        from app.services.audit_service import AuditService
        
        audit_service = AuditService()
        await audit_service.create_auth_log(
            db=db,
            user_id=user.id,
            event_type=event_type,
            success=success,
            ip_address=ip_address,
            details=details
        )
    
    def _verify_jwt_signature(self, token: str) -> bool:
        """Verify JWT signature."""
        try:
            jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_signature": True, "verify_exp": False}
            )
            return True
        except:
            return False
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret key."""
        return self.jwt_secret


# Singleton instance
auth_service = AuthService()