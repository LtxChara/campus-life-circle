"""
校园生活圈 - 工具模块
"""
from .file_utils import allowed_file, save_uploaded_file
from .pagination import parse_pagination_params, build_pagination_response
from .response import success_response, error_response, paginated_response
from .errors import APIError, ValidationError, AuthenticationError, PermissionError, NotFoundError
from .query_utils import escape_like_pattern

__all__ = [
    # 文件工具
    'allowed_file',
    'save_uploaded_file',
    # 分页工具
    'parse_pagination_params',
    'build_pagination_response',
    # 响应工具
    'success_response',
    'error_response',
    'paginated_response',
    # 错误类
    'APIError',
    'ValidationError',
    'AuthenticationError',
    'PermissionError',
    'NotFoundError',
    # 查询工具
    'escape_like_pattern',
]