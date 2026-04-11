from flask import Blueprint, request, jsonify

from ext import db, bcrypt
from models import User
from utils import login_required, generate_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    用户注册
    请求 JSON 示例：
    {
        "username": "小明",
        "student_id": "20250001",
        "email": "test@example.com",
        "password": "123456"
    }
    """
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    student_id = (data.get("student_id") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password")
    
    # 确保 password 是字符串类型，不能是 None
    if password is None:
        password = ""
    else:
        password = str(password).strip()

    # 基础校验
    missing_fields = []
    if not username:
        missing_fields.append("username")
    if not student_id:
        missing_fields.append("student_id")
    if not email:
        missing_fields.append("email")
    if not password:
        missing_fields.append("password")

    if missing_fields:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"缺少必要字段: {', '.join(missing_fields)}",
                }
            ),
            400,
        )

    # 学号 / 邮箱是否已存在
    if User.query.filter_by(student_id=student_id).first():
        return (
            jsonify({"success": False, "message": "学号已注册"}),
            409,
        )

    if User.query.filter_by(email=email).first():
        return (
            jsonify({"success": False, "message": "邮箱已注册"}),
            409,
        )

    # 生成密码哈希（确保 password 不为空）
    if not password:
        return (
            jsonify({"success": False, "message": "密码不能为空"}),
            400,
        )
    
    try:
        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    except Exception as e:
        return (
            jsonify({"success": False, "message": f"密码加密失败: {str(e)}"}),
            500,
        )

    user = User(
        username=username,
        student_id=student_id,
        email=email,
        password_hash=pw_hash,
    )
    db.session.add(user)
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": "注册成功",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "student_id": user.student_id,
                    "email": user.email,
                },
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    用户登录
    请求 JSON 示例：
    {
        "student_id": "20250001",
        "password": "123456"
    }
    """
    data = request.get_json(silent=True) or {}

    student_id = (data.get("student_id") or "").strip()
    password = data.get("password") or ""

    if not student_id or not password:
        return (
            jsonify({"success": False, "message": "学号和密码均为必填项"}),
            400,
        )

    user = User.query.filter_by(student_id=student_id).first()
    # 统一返回模糊错误信息，防止用户枚举攻击
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return (
            jsonify({"success": False, "message": "学号或密码错误"}),
            401,
        )

    token = generate_token(user.id)

    return jsonify(
        {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "student_id": user.student_id,
                "email": user.email,
            },
        }
    )


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user(user_id):
    """
    获取当前登录用户信息

    需要在请求头中携带 Token：
    Authorization: Bearer <token>

    返回当前登录用户的详细信息
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "用户不存在"
        }), 404

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "student_id": user.student_id,
            "email": user.email,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M")
        }
    })
