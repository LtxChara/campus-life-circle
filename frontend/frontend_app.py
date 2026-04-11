import os
from datetime import timedelta
from flask import Flask
from views import bp  # 导入定义前端路由的蓝图

app = Flask(__name__, template_folder='templates', static_folder='static')

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问cookie
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False，生产环境应设为True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 会话2小时后过期

# 图片服务基础URL配置
app.config['IMAGE_BASE_URL'] = os.environ.get('IMAGE_BASE_URL') or 'http://127.0.0.1:5000'
app.config['DEFAULT_IMAGE'] = 'https://via.placeholder.com/600x400?text=Campus+Life'

# Jinja2模板上下文处理器：提供全局函数
@app.context_processor
def utility_processor():
    def get_image_url(path, type='default'):
        """获取完整图片URL"""
        if not path:
            defaults = {
                'goods': 'https://via.placeholder.com/600x400?text=二手商品',
                'lost': 'https://via.placeholder.com/600x400?text=失物招领',
                'default': app.config['DEFAULT_IMAGE']
            }
            return defaults.get(type, defaults['default'])
        if path.startswith('http://') or path.startswith('https://'):
            return path
        return f"{app.config['IMAGE_BASE_URL']}/{path}"
    return dict(get_image_url=get_image_url)

# 注册前端蓝图（不指定 url_prefix，直接使用根路径）
app.register_blueprint(bp)

if __name__ == '__main__':
    # 运行应用（假定后端API运行在5000端口，这里前端使用另一个端口）
    app.run(host='0.0.0.0', port=5001, debug=True)
