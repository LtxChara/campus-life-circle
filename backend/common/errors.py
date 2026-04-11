"""
校园生活圈 - 错误处理
定义异常类和错误处理器
"""
from flask import jsonify, current_app


class APIError(Exception):
    """
    API错误基类
    所有自定义API异常都应继承此类
    """
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "success": False,
            "message": self.message,
            "error_code": self.error_code
        }


class ValidationError(APIError):
    """验证错误（HTTP 400）"""
    def __init__(self, message: str = "参数验证失败"):
        super().__init__(message, 400, "VALIDATION_ERROR")


class AuthenticationError(APIError):
    """认证错误（HTTP 401）"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, 401, "AUTHENTICATION_ERROR")


class PermissionError(APIError):
    """权限错误（HTTP 403）"""
    def __init__(self, message: str = "无权限执行此操作"):
        super().__init__(message, 403, "PERMISSION_ERROR")


class NotFoundError(APIError):
    """资源不存在错误（HTTP 404）"""
    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(message, 404, "NOT_FOUND")


class ConflictError(APIError):
    """冲突错误（HTTP 409）"""
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, 409, "CONFLICT")


class InternalError(APIError):
    """内部服务器错误（HTTP 500）"""
    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(message, 500, "INTERNAL_ERROR")


def handle_api_error(e: APIError) -> tuple:
    """
    处理 APIError 异常

    Args:
        e: APIError 实例

    Returns:
        tuple: (响应对象, 状态码)
    """
    return jsonify(e.to_dict()), e.status_code


def handle_generic_error(e: Exception) -> tuple:
    """
    处理通用异常
    生产环境不泄露错误细节

    Args:
        e: Exception 实例

    Returns:
        tuple: (响应对象, 状态码)
    """
    # 记录错误日志
    current_app.logger.error(f"未处理的异常: {type(e).__name__}: {e}")

    return jsonify({
        "success": False,
        "message": "服务器内部错误，请稍后重试",
        "error_code": "INTERNAL_ERROR"
    }), 500


def register_error_handlers(app):
    """
    注册错误处理器到Flask应用

    Args:
        app: Flask应用实例
    """
    app.register_error_handler(APIError, handle_api_error)
    # 注意：Exception处理器可能会干扰调试，根据需要启用
    # app.register_error_handler(Exception, handle_generic_error)