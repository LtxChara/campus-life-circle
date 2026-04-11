"""
校园生活圈 - 统一配置管理
集中管理所有配置项，支持环境变量覆盖
"""
import os


class Config:
    """基础配置"""
    # 安全密钥 - 用于Token签名和Session加密
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campus-secret-key-dev'

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///campus.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JSON配置
    JSON_AS_ASCII = False  # 支持中文返回

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传 16MB

    # Token配置
    TOKEN_EXPIRATION = 7 * 24 * 3600  # Token有效期 7天 (秒)

    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # 允许的图片文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

    # 生产环境必须设置SECRET_KEY环境变量
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
        return key


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}