from datetime import datetime, timedelta

from ext import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 方便通过 user.secondhand_items / user.lost_found_records 反查
    secondhand_items = db.relationship(
        "SecondHandItem", backref="seller", lazy=True, cascade="all, delete-orphan"
    )
    lost_found_records = db.relationship(
        "LostFound", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} student_id={self.student_id}>"


class SecondHandItem(db.Model):
    __tablename__ = "secondhand_items"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="在售", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 3.0版本新增,图片路径字段
    image = db.Column(db.String(255), nullable=True)

    # 复合索引：优化按卖家+时间查询
    __table_args__ = (
        db.Index('idx_seller_created', 'seller_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<SecondHandItem id={self.id} title={self.title!r}>"
    
    # 3.0版本新增,使用to_dict函数展示信息
    def to_dict(self):
        return {
            'id': self.id,
            'seller_id': self.seller_id,
            'seller_name': self.seller.username if self.seller else '未知卖家',
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'status': self.status,
            'image': self.image,  # 图片
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }


class LostFound(db.Model):
    __tablename__ = "lost_found"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # 取值示例：LOST / FOUND
    type = db.Column(db.String(10), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)

    # 2.0版本新增：针对失物的状态（未找回/已找回/已放弃）
    # 对于招领信息，此字段为：未认领/已认领
    status = db.Column(db.String(20), default="未找回", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 3.0版本新增,图片路径字段
    image = db.Column(db.String(255), nullable=True)

    # 复合索引：优化按发布者+时间查询、按类型+状态查询
    __table_args__ = (
        db.Index('idx_owner_created', 'owner_id', 'created_at'),
        db.Index('idx_type_status', 'type', 'status'),
    )

    def __repr__(self) -> str:
        return f"<LostFound id={self.id} type={self.type} title={self.title!r}>"
    
    def get_current_status(self):
        """
        获取当前状态，自动处理超过30天的失物
        """
        # 只对失物类型的记录进行自动过期判断
        if self.type == "LOST" and self.status == "未找回":
            # 计算发布时长
            days_passed = (datetime.utcnow() - self.created_at).days
            if days_passed > 30:
                # 超过30天自动标记为已放弃
                return "已放弃"
        return self.status
    
    # 3.0版本新增,使用to_dict函数展示信息
    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'owner_name': self.owner.username if self.owner else '未知用户',
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'location': self.location,
            'contact': self.contact,
            'status': self.get_current_status(),
            'image': self.image,  # 图片
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    # 发送者
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    # 接收者
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # 关联的失物招领帖子（可选）
    post_id = db.Column(db.Integer, db.ForeignKey("lost_found.id"), nullable=True)

    # 关联的二手商品（可选）
    item_id = db.Column(db.Integer, db.ForeignKey("secondhand_items.id"), nullable=True)

    content = db.Column(db.Text, nullable=False)  # 留言内容
    is_read = db.Column(db.Boolean, default=False, index=True)  # 是否已读
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 建立关系
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    post = db.relationship("LostFound", backref="messages")
    # 二手商品关系
    item = db.relationship("SecondHandItem", backref="messages")

    # 复合索引：优化收件箱查询（接收者+已读状态）
    __table_args__ = (
        db.Index('idx_receiver_read', 'receiver_id', 'is_read'),
    )

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} to {self.receiver_id}>"

    def to_dict(self):
        """转字典，方便API返回"""
        # 智能判断关联的是哪个标题
        link_title = '普通私信'
        if self.post:
            link_title = f"[失物] {self.post.title}"
        elif self.item:
            link_title = f"[二手] {self.item.title}"

        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'post_id': self.post_id,
            'item_id': self.item_id, # 返回 item_id
            'post_title': link_title, # 这里复用 post_title 字段给前端显示，省得改前端逻辑
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': self.is_read
        }