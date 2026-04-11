"""
校园生活圈 - 失物招领路由
处理失物招领的 CRUD 操作与状态管理
"""
from flask import Blueprint, request, jsonify, current_app

from ext import db
from models import LostFound
from utils import login_required
from common.file_utils import allowed_file, save_uploaded_file
from common.pagination import parse_pagination_params, calculate_offset, build_pagination_response
from common.response import success_response, error_response
from common.query_utils import escape_like_pattern
from config import Config

import os
import uuid

lost_bp = Blueprint("lost", __name__)


@lost_bp.route("", methods=["POST"])
@login_required
def create_lost(user_id):
    """
    发布失物 / 招领信息（需要登录）
    支持 multipart/form-data 格式上传图片
    """
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    record_type = request.form.get("type", "").strip().upper()
    location = request.form.get("location", "").strip()
    contact = request.form.get("contact", "").strip()

    # 获取图片文件
    file = request.files.get('image')

    # 基础校验
    missing_fields = []
    if not title:
        missing_fields.append("title")
    if not record_type:
        missing_fields.append("type")
    if not location:
        missing_fields.append("location")
    if not contact:
        missing_fields.append("contact")

    if missing_fields:
        return error_response(f"缺少必要字段: {', '.join(missing_fields)}", 400)

    if record_type not in {"LOST", "FOUND"}:
        return error_response("type 只允许为 LOST 或 FOUND", 400)

    # 处理图片上传
    image_filename = None
    if file and file.filename:
        image_filename = save_uploaded_file(file)

    # 根据类型设置初始状态
    initial_status = "未找回" if record_type == "LOST" else "未认领"

    record = LostFound(
        owner_id=user_id,
        title=title,
        description=description or None,
        type=record_type,
        location=location,
        contact=contact,
        status=initial_status,
        image=image_filename
    )

    try:
        db.session.add(record)
        db.session.commit()
        return success_response({'id': record.id}, '发布成功', 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发布失物招领失败: {e}")
        return error_response('发布失败，请稍后重试', 500)


@lost_bp.route("", methods=["GET"])
def list_lost():
    """
    获取失物 / 招领列表（公开）

    支持的查询参数：
    - keyword: 按标题模糊搜索
    - type: 类型过滤（LOST/FOUND）
    - status: 状态过滤
    - page: 页码（从 1 开始，默认 1）
    - page_size: 每页条数（默认 20，最大 100）
    """
    keyword = (request.args.get("keyword", "") or "").strip()
    type_ = (request.args.get("type", "") or "").strip().upper()
    status = (request.args.get("status", "") or "").strip()

    page, page_size = parse_pagination_params(request)

    query = LostFound.query

    if keyword:
        escaped_keyword = escape_like_pattern(keyword)
        query = query.filter(LostFound.title.like(f"%{escaped_keyword}%", escape='\\'))

    if type_:
        query = query.filter_by(type=type_)

    if status:
        query = query.filter_by(status=status)

    total = query.count()

    items = (
        query.order_by(LostFound.created_at.desc())
        .offset(calculate_offset(page, page_size))
        .limit(page_size)
        .all()
    )

    result = [item.to_dict() for item in items]

    return jsonify(build_pagination_response(result, total, page, page_size))


@lost_bp.route("/my", methods=["GET"])
@login_required
def get_my_posts(user_id):
    """
    获取当前用户发布的失物招领（需登录）

    支持分页参数
    """
    page, page_size = parse_pagination_params(request)

    query = LostFound.query.filter_by(owner_id=user_id)
    total = query.count()

    records = (
        query.order_by(LostFound.created_at.desc())
        .offset(calculate_offset(page, page_size))
        .limit(page_size)
        .all()
    )

    result = [record.to_dict() for record in records]

    return jsonify(build_pagination_response(result, total, page, page_size))


@lost_bp.route("/<int:post_id>", methods=["GET"])
def get_lost(post_id):
    """
    获取单个失物/招领详情（公开）
    """
    record = LostFound.query.get(post_id)

    if not record:
        return error_response("信息不存在", 404)

    return jsonify({"success": True, "item": record.to_dict()})


@lost_bp.route("/<int:post_id>", methods=["PUT"])
@login_required
def update_post(user_id, post_id):
    """
    更新失物招领信息（仅发布者可操作）

    可更新字段：title, description, location, contact
    """
    record = LostFound.query.get(post_id)

    if not record:
        return error_response("信息不存在", 404)

    if record.owner_id != user_id:
        return error_response("无权限修改", 403)

    data = request.get_json(silent=True) or {}

    # 更新字段
    if 'title' in data:
        record.title = data['title'].strip()
    if 'description' in data:
        record.description = data['description']
    if 'location' in data:
        record.location = data['location'].strip()
    if 'contact' in data:
        record.contact = data['contact'].strip()

    try:
        db.session.commit()
        return jsonify({"success": True, "message": "更新成功", "item": record.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新失物招领失败: {e}")
        return error_response("更新失败，请稍后重试", 500)


@lost_bp.route("/<int:post_id>/status", methods=["PUT"])
@login_required
def update_status(user_id, post_id):
    """
    更新失物招领状态（需要登录且为发布者）
    """
    record = LostFound.query.get(post_id)

    if not record:
        return error_response("信息不存在", 404)

    if record.owner_id != user_id:
        return error_response("无权限修改", 403)

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()

    if not new_status:
        return error_response("状态不能为空", 400)

    if record.type == "LOST":
        valid_statuses = {"未找回", "已找回", "已放弃"}
    else:  # FOUND
        valid_statuses = {"未认领", "已认领"}

    if new_status not in valid_statuses:
        return error_response(f"无效的状态，允许的状态为: {', '.join(valid_statuses)}", 400)

    record.status = new_status

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "状态更新成功",
            "status": new_status
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新状态失败: {e}")
        return error_response("更新失败，请稍后重试", 500)


@lost_bp.route('/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(user_id, post_id):
    """
    删除失物招领（仅发布者可操作）
    """
    post = LostFound.query.get(post_id)

    if not post:
        return error_response("信息不存在", 404)

    if post.owner_id != user_id:
        return error_response("无权删除此信息", 403)

    try:
        # 可选：删除关联的图片文件
        # if post.image:
        #     delete_uploaded_file(post.image)

        db.session.delete(post)
        db.session.commit()
        return jsonify({"success": True, "message": "删除成功"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除失物招领失败: {e}")
        return error_response("删除失败，请稍后重试", 500)