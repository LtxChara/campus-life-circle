"""
校园生活圈 - 分页工具
处理分页参数解析和响应构建
"""
from typing import Tuple, Any
from flask import request
from config import Config


def parse_pagination_params(req=None) -> Tuple[int, int]:
    """
    从请求中解析分页参数

    Args:
        req: Flask request 对象，默认使用当前请求

    Returns:
        Tuple[int, int]: (page, page_size)
    """
    if req is None:
        req = request

    try:
        page = int(req.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = int(req.args.get("page_size", Config.DEFAULT_PAGE_SIZE))
    except (ValueError, TypeError):
        page_size = Config.DEFAULT_PAGE_SIZE

    # 确保参数在有效范围内
    page = max(page, 1)
    page_size = max(1, min(page_size, Config.MAX_PAGE_SIZE))

    return page, page_size


def calculate_offset(page: int, page_size: int) -> int:
    """
    计算数据库查询的偏移量

    Args:
        page: 页码（从1开始）
        page_size: 每页条数

    Returns:
        int: 偏移量
    """
    return (page - 1) * page_size


def build_pagination_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    success: bool = True
) -> dict:
    """
    构建标准分页响应

    Args:
        items: 数据列表
        total: 总条数
        page: 当前页码
        page_size: 每页条数
        success: 是否成功

    Returns:
        dict: 分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return {
        "success": success,
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }