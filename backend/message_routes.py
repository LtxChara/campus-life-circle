'''
3.0版本新增：站内信,发送、回复、删除、关联三类事件,显示发送、回复人
'''
from flask import Blueprint, request, jsonify, current_app
from ext import db
from models import Message
from utils import login_required

message_bp = Blueprint('message', __name__)

# 发送留言
@message_bp.route('', methods=['POST'])
@login_required
def send_message(user_id):
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    post_id = data.get('post_id')  # 失物招领ID
    item_id = data.get('item_id')  # 二手商品ID

    if not content or not receiver_id:
        return jsonify({'success': False, 'message': '内容和接收者不能为空'}), 400

    sender_id = user_id

    if int(sender_id) == int(receiver_id):
        return jsonify({'success': False, 'message': '不能给自己留言哦'}), 400

    new_msg = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        post_id=post_id,
        item_id=item_id
    )

    try:
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({'success': True, 'message': '留言发送成功'}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发送消息失败: {e}")
        return jsonify({'success': False, 'message': '发送失败，请稍后重试'}), 500

# 获取我的收件箱
@message_bp.route('/inbox', methods=['GET'])
@login_required
def get_inbox(user_id):  # 接收 user_id
    # 查询所有发给我的消息，按时间倒序
    msgs = Message.query.filter_by(receiver_id=user_id)\
        .order_by(Message.created_at.desc()).all()
    
    return jsonify({
        "success": True, 
        "messages": [m.to_dict() for m in msgs]
    }), 200

@message_bp.route('/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(user_id, message_id):
    # 查找消息
    msg = Message.query.get(message_id)

    if not msg:
        return jsonify({'success': False, 'message': '消息不存在'}), 404

    # 安全检查：只有接收者（或发送者）才能删除
    if msg.receiver_id != user_id and msg.sender_id != user_id:
        return jsonify({'success': False, 'message': '无权删除此消息'}), 403

    try:
        db.session.delete(msg)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除消息失败: {e}")
        return jsonify({'success': False, 'message': '删除失败，请稍后重试'}), 500


@message_bp.route('/<int:message_id>/read', methods=['PUT'])
@login_required
def mark_message_read(user_id, message_id):
    # 标记消息为已读（仅接收者可操作）
    msg = Message.query.get(message_id)

    if not msg:
        return jsonify({'success': False, 'message': '消息不存在'}), 404

    # 只有接收者可以标记已读
    if msg.receiver_id != user_id:
        return jsonify({'success': False, 'message': '无权限操作'}), 403

    msg.is_read = True

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '已标记为已读'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"标记已读失败: {e}")
        return jsonify({'success': False, 'message': '操作失败'}), 500


@message_bp.route('/read-all', methods=['PUT'])
@login_required
def mark_all_messages_read(user_id):
    # 标记所有消息为已读
    try:
        # 更新所有未读消息
        Message.query.filter_by(receiver_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True, 'message': '已全部标记为已读'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量标记已读失败: {e}")
        return jsonify({'success': False, 'message': '操作失败'}), 500


@message_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count(user_id):
    # 获取未读消息数量
    count = Message.query.filter_by(receiver_id=user_id, is_read=False).count()

    return jsonify({
        "success": True,
        "unread_count": count
    })


@message_bp.route('/sent', methods=['GET'])
@login_required
def get_sent_messages(user_id):
    # 获取已发送的消息列表（发件箱）
    msgs = Message.query.filter_by(sender_id=user_id)\
        .order_by(Message.created_at.desc()).all()

    return jsonify({
        "success": True,
        "messages": [m.to_dict() for m in msgs]
    })