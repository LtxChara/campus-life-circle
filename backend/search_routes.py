"""
校园生活圈 - 统一搜索和浏览接口
支持二手商品、失物招领的混合搜索和随机浏览
"""
from flask import Blueprint, request, jsonify
import random

from ext import db
from models import SecondHandItem, LostFound
from common.pagination import parse_pagination_params, calculate_offset
from common.query_utils import escape_like_pattern
from config import Config

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["GET"])
def unified_search():
    """
    统一搜索接口（公开）

    支持的查询参数：
    - keyword: 搜索关键字（按标题搜索）
    - types: 类型过滤，逗号分隔（secondhand, lost, found）
    - page: 页码（默认1）
    - page_size: 每页条数（默认20，最大100）

    返回结果按照发布日期降序排列
    """
    keyword = (request.args.get("keyword", "") or "").strip()
    types_str = (request.args.get("types", "") or "").strip()

    page, page_size = parse_pagination_params(request)

    # 解析类型过滤
    selected_types = set()
    if types_str:
        for t in types_str.split(","):
            t = t.strip().lower()
            if t in {"secondhand", "lost", "found"}:
                selected_types.add(t)
    else:
        # 默认显示所有类型
        selected_types = {"secondhand", "lost", "found"}

    results = []
    total = 0

    # 转义搜索关键字
    escaped_keyword = escape_like_pattern(keyword) if keyword else ""

    # 查询二手商品
    if "secondhand" in selected_types:
        query = SecondHandItem.query
        if keyword:
            query = query.filter(
                SecondHandItem.title.like(f"%{escaped_keyword}%", escape='\\')
            )

        # 先获取总数用于分页计算
        secondhand_total = query.count()
        total += secondhand_total

        # 分页查询
        items = (
            query.order_by(SecondHandItem.created_at.desc())
            .offset(calculate_offset(page, page_size))
            .limit(page_size)
            .all()
        )

        for item in items:
            results.append({
                "id": item.id,
                "type": "secondhand",
                "title": item.title,
                "description": item.description,
                "price": item.price,
                "category": item.category,
                "status": item.status,
                "image": item.image,
                "created_at_str": item.created_at.strftime("%Y-%m-%d %H:%M"),
                "seller_id": item.seller_id,
            })

    # 查询失物招领
    if "lost" in selected_types or "found" in selected_types:
        query = LostFound.query
        if keyword:
            query = query.filter(
                LostFound.title.like(f"%{escaped_keyword}%", escape='\\')
            )

        # 根据选择的类型过滤
        type_filters = []
        if "lost" in selected_types:
            type_filters.append("LOST")
        if "found" in selected_types:
            type_filters.append("FOUND")

        if type_filters:
            query = query.filter(LostFound.type.in_(type_filters))

        lostfound_total = query.count()
        total += lostfound_total

        # 分页查询
        records = (
            query.order_by(LostFound.created_at.desc())
            .offset(calculate_offset(page, page_size))
            .limit(page_size)
            .all()
        )

        for record in records:
            results.append({
                "id": record.id,
                "type": "lostfound",
                "lostfound_type": record.type,
                "title": record.title,
                "description": record.description,
                "location": record.location,
                "contact": record.contact,
                "status": record.get_current_status(),
                "image": record.image,
                "created_at_str": record.created_at.strftime("%Y-%m-%d %H:%M"),
                "owner_id": record.owner_id,
            })

    # 按日期降序排序
    results.sort(key=lambda x: x["created_at_str"], reverse=True)

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return jsonify({
        "success": True,
        "items": results[:page_size],  # 确保返回数量不超过 page_size
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    })


@search_bp.route("/random", methods=["GET"])
def random_browse():
    """
    随机浏览接口（公开）

    支持的查询参数：
    - types: 类型过滤，逗号分隔（secondhand, lost, found）
    - count: 返回数量（默认20，最大50）

    随机返回指定类型的内容
    """
    types_str = (request.args.get("types", "") or "").strip()

    try:
        count = int(request.args.get("count", 20))
    except ValueError:
        count = 20

    count = max(1, min(count, 50))

    # 解析类型过滤
    selected_types = set()
    if types_str:
        for t in types_str.split(","):
            t = t.strip().lower()
            if t in {"secondhand", "lost", "found"}:
                selected_types.add(t)
    else:
        # 默认显示所有类型
        selected_types = {"secondhand", "lost", "found"}

    results = []

    # 获取二手商品（使用数据库随机排序，避免全量加载）
    if "secondhand" in selected_types:
        # 使用 RANDOM() 函数进行随机排序（SQLite）
        items = SecondHandItem.query.order_by(db.func.random()).limit(count).all()
        for item in items:
            results.append({
                "id": item.id,
                "type": "secondhand",
                "title": item.title,
                "description": item.description,
                "price": item.price,
                "category": item.category,
                "status": item.status,
                "image": item.image,
                "created_at_str": item.created_at.strftime("%Y-%m-%d %H:%M"),
                "seller_id": item.seller_id,
            })

    # 获取失物招领
    if "lost" in selected_types or "found" in selected_types:
        query = LostFound.query

        # 根据选择的类型过滤
        type_filters = []
        if "lost" in selected_types:
            type_filters.append("LOST")
        if "found" in selected_types:
            type_filters.append("FOUND")

        if type_filters:
            query = query.filter(LostFound.type.in_(type_filters))

        records = query.order_by(db.func.random()).limit(count).all()
        for record in records:
            results.append({
                "id": record.id,
                "type": "lostfound",
                "lostfound_type": record.type,
                "title": record.title,
                "description": record.description,
                "location": record.location,
                "contact": record.contact,
                "status": record.get_current_status(),
                "image": record.image,
                "created_at_str": record.created_at.strftime("%Y-%m-%d %H:%M"),
                "owner_id": record.owner_id,
            })

    # 随机打乱
    random.shuffle(results)

    # 取前 count 个
    random_results = results[:count]

    return jsonify({
        "success": True,
        "items": random_results,
        "count": len(random_results),
    })