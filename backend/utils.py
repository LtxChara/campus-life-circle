from functools import wraps

from flask import request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


def _get_serializer() -> URLSafeTimedSerializer:
    """获取序列化器，使用统一的SECRET_KEY"""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_token(user_id: int) -> str:
    """为给定用户生成带过期时间的 token。"""
    s = _get_serializer()
    return s.dumps({"user_id": user_id})


def verify_token(token: str, max_age: int = None) -> int | None:
    """校验 token，成功返回 user_id，失败/过期返回 None。"""
    if not token:
        return None

    # 使用配置中的过期时间
    if max_age is None:
        max_age = current_app.config.get('TOKEN_EXPIRATION', 7 * 24 * 3600)

    s = _get_serializer()
    try:
        data = s.loads(token, max_age=max_age)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None
    except Exception:
        # 兜底处理，避免异常泄漏到视图函数
        return None


def _extract_token_from_header() -> str | None:
    """
    从请求头里解析 token，支持两种写法：
    - Authorization: Bearer <token>
    - Authorization: <token>
    """
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header:
        return None

    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    return auth_header


def login_required(view_func):
    """
    登录校验装饰器。

    使用示例：

    @bp.route("/xxx", methods=["POST"])
    @login_required
    def create_xxx(user_id):
        ...
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = _extract_token_from_header()
        if not token:
            return jsonify({"success": False, "message": "未登录"}), 401

        user_id = verify_token(token)
        if not user_id:
            return jsonify({"success": False, "message": "登录已失效，请重新登录"}), 401

        # 把 user_id 透传给视图函数
        return view_func(user_id=user_id, *args, **kwargs)

    return wrapper
