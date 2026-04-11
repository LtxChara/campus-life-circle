"""
校园生活圈 - 二手商品路由
处理二手商品的 CRUD 操作
"""
from flask import Blueprint, request, jsonify, current_app

from ext import db
from models import SecondHandItem
from utils import login_required
from common.file_utils import allowed_file, save_uploaded_file, delete_uploaded_file
from common.pagination import parse_pagination_params, calculate_offset, build_pagination_response
from common.response import success_response, error_response, paginated_response
from common.query_utils import escape_like_pattern, build_like_condition
from config import Config

# 图片上传
import os
import uuid

item_bp = Blueprint("item", __name__)


@item_bp.route("", methods=["POST"])
@login_required
def create_item(user_id):
    """
    发布二手商品（需登录）
    支持 multipart/form-data 格式上传图片
    """
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')

    # 获取图片文件
    file = request.files.get('image')

    if not title or not price:
        return error_response('标题和价格必填', 400)

    # 处理图片上传
    image_filename = None
    if file and file.filename:
        image_filename = save_uploaded_file(file)

    item = SecondHandItem(
        seller_id=user_id,
        title=title,
        description=description,
        price=float(price),
        image=image_filename
    )

    try:
        db.session.add(item)
        db.session.commit()
        return success_response({'id': item.id}, '发布成功', 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发布商品失败: {e}")
        return error_response('发布失败，请稍后重试', 500)


@item_bp.route("", methods=["GET"])
def list_items():
    """
    获取二手物品列表（公开）

    支持的查询参数：
    - keyword: 按标题模糊搜索
    - category: 分类过滤
    - status: 状态过滤
    - page: 页码（从 1 开始，默认 1）
    - page_size: 每页条数（默认 20，最大 100）
    """
    keyword = (request.args.get("keyword", "") or "").strip()
    category = (request.args.get("category", "") or "").strip()
    status = (request.args.get("status", "") or "").strip()

    page, page_size = parse_pagination_params(request)

    query = SecondHandItem.query

    if keyword:
        escaped_keyword = escape_like_pattern(keyword)
        query = query.filter(SecondHandItem.title.like(f"%{escaped_keyword}%", escape='\\'))

    if category:
        query = query.filter_by(category=category)

    if status:
        query = query.filter_by(status=status)

    total = query.count()

    items = (
        query.order_by(SecondHandItem.created_at.desc())
        .offset(calculate_offset(page, page_size))
        .limit(page_size)
        .all()
    )

    data = [item.to_dict() for item in items]

    return jsonify(build_pagination_response(data, total, page, page_size))


@item_bp.route("/my", methods=["GET"])
@login_required
def get_my_items(user_id):
    """
    获取当前用户发布的商品（需登录）

    支持分页参数
    """
    page, page_size = parse_pagination_params(request)

    query = SecondHandItem.query.filter_by(seller_id=user_id)
    total = query.count()

    items = (
        query.order_by(SecondHandItem.created_at.desc())
        .offset(calculate_offset(page, page_size))
        .limit(page_size)
        .all()
    )

    data = [item.to_dict() for item in items]

    return jsonify(build_pagination_response(data, total, page, page_size))


@item_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """
    获取单个二手物品详情（公开）
    """
    item = SecondHandItem.query.get(item_id)

    if not item:
        return error_response("商品不存在", 404)

    return jsonify({"success": True, "item": item.to_dict()})


@item_bp.route("/<int:item_id>", methods=["PUT"])
@login_required
def update_item(user_id, item_id):
    """
    更新商品信息（仅发布者可操作）

    可更新字段：title, description, price, category
    """
    item = SecondHandItem.query.get(item_id)

    if not item:
        return error_response("商品不存在", 404)

    if item.seller_id != user_id:
        return error_response("无权限修改此商品", 403)

    data = request.get_json(silent=True) or {}

    # 更新字段
    if 'title' in data:
        item.title = data['title'].strip()
    if 'description' in data:
        item.description = data['description']
    if 'price' in data:
        try:
            item.price = float(data['price'])
        except (ValueError, TypeError):
            return error_response("价格格式无效", 400)
    if 'category' in data:
        item.category = data['category']

    try:
        db.session.commit()
        return jsonify({"success": True, "message": "更新成功", "item": item.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新商品失败: {e}")
        return error_response("更新失败，请稍后重试", 500)


@item_bp.route("/<int:item_id>/status", methods=["PUT"])
@login_required
def update_item_status(user_id, item_id):
    """
    更新商品状态（仅发布者可操作）

    有效状态：在售, 已售, 已下架
    """
    item = SecondHandItem.query.get(item_id)

    if not item:
        return error_response("商品不存在", 404)

    if item.seller_id != user_id:
        return error_response("无权限修改此商品", 403)

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()

    valid_statuses = {"在售", "已售", "已下架"}
    if new_status not in valid_statuses:
        return error_response(f"无效状态，允许的状态: {', '.join(valid_statuses)}", 400)

    item.status = new_status

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "状态更新成功",
            "status": new_status
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新商品状态失败: {e}")
        return error_response("更新失败，请稍后重试", 500)


@item_bp.route('/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(user_id, item_id):
    """
    删除商品（仅发布者可操作）
    """
    item = SecondHandItem.query.get(item_id)

    if not item:
        return error_response("商品不存在", 404)

    if item.seller_id != user_id:
        return error_response("无权限删除此商品", 403)

    try:
        # 可选：删除关联的图片文件
        # if item.image:
        #     delete_uploaded_file(item.image)

        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "删除成功"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除商品失败: {e}")
        return error_response("删除失败，请稍后重试", 500)