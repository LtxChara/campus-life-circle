"""
校园生活圈 - 响应格式化工具
统一API响应格式
"""
from typing import Any, Optional
from flask import jsonify


def success_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = 200
) -> tuple:
    """
    构建成功响应

    Args:
        data: 返回的数据（字典或列表）
        message: 成功消息
        status_code: HTTP状态码

    Returns:
        tuple: (响应对象, 状态码)
    """
    response = {"success": True, "message": message}

    if data is not None:
        if isinstance(data, dict):
            # 如果是字典，合并到响应中
            response.update(data)
        elif isinstance(data, list):
            # 如果是列表，作为 items 字段
            response["items"] = data
        else:
            # 其他类型，作为 data 字段
            response["data"] = data

    return jsonify(response), status_code


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None
) -> tuple:
    """
    构建错误响应

    Args:
        message: 错误消息
        status_code: HTTP状态码
        error_code: 错误代码（可选）

    Returns:
        tuple: (响应对象, 状态码)
    """
    response = {"success": False, "message": message}

    if error_code:
        response["error_code"] = error_code

    return jsonify(response), status_code


def paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "查询成功"
) -> tuple:
    """
    构建分页响应

    Args:
        items: 数据列表
        total: 总条数
        page: 当前页码
        page_size: 每页条数
        message: 成功消息

    Returns:
        tuple: (响应对象, 状态码)
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return jsonify({
        "success": True,
        "message": message,
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }), 200


def created_response(
    data: Any = None,
    message: str = "创建成功"
) -> tuple:
    """
    构建创建成功响应（HTTP 201）

    Args:
        data: 返回的数据
        message: 成功消息

    Returns:
        tuple: (响应对象, 状态码)
    """
    return success_response(data, message, 201)


def deleted_response(message: str = "删除成功") -> tuple:
    """
    构建删除成功响应

    Args:
        message: 成功消息

    Returns:
        tuple: (响应对象, 状态码)
    """
    return jsonify({"success": True, "message": message}), 200


def not_found_response(message: str = "资源不存在") -> tuple:
    """
    构建资源不存在响应（HTTP 404）

    Args:
        message: 错误消息

    Returns:
        tuple: (响应对象, 状态码)
    """
    return error_response(message, 404, "NOT_FOUND")


def unauthorized_response(message: str = "未授权") -> tuple:
    """
    构建未授权响应（HTTP 401）

    Args:
        message: 错误消息

    Returns:
        tuple: (响应对象, 状态码)
    """
    return error_response(message, 401, "UNAUTHORIZED")


def forbidden_response(message: str = "无权限") -> tuple:
    """
    构建禁止访问响应（HTTP 403）

    Args:
        message: 错误消息

    Returns:
        tuple: (响应对象, 状态码)
    """
    return error_response(message, 403, "FORBIDDEN")