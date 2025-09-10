"""
CRUD (Create, Read, Update, Delete) operations for the application.
"""
from .user import (
    get_user,
    get_user_by_email,
    get_users,
    create_user,
    update_user,
    authenticate,
    is_active,
    is_superuser
)

# Make the CRUD operations available at the package level
__all__ = [
    'get_user',
    'get_user_by_email',
    'get_users',
    'create_user',
    'update_user',
    'authenticate',
    'is_active',
    'is_superuser'
]
