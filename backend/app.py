import os
from flask import Flask
from flask_cors import CORS
from ext import db, bcrypt
from config import Config
from common.errors import register_error_handlers


def create_app():
    app = Flask(__name__)

    # 从配置类加载配置
    app.config.from_object(Config)

    # 确保上传目录存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # 初始化扩展
    # CORS配置 - 限制允许的来源
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://127.0.0.1:5001", "http://localhost:5001"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    db.init_app(app)
    bcrypt.init_app(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 先导入 models，让 SQLAlchemy 知道有哪些表
    from models import User, SecondHandItem, LostFound, Message

    # 然后在 app 上下文中创建所有表
    with app.app_context():
        db.create_all()

    # 再注册蓝图
    from auth_routes import auth_bp
    from item_routes import item_bp
    from lost_routes import lost_bp
    from search_routes import search_bp
    from message_routes import message_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(item_bp, url_prefix="/api/secondhand")
    app.register_blueprint(lost_bp, url_prefix="/api/lostfound")
    app.register_blueprint(search_bp, url_prefix="/api")
    app.register_blueprint(message_bp, url_prefix="/api/messages")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

