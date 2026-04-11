from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
from functools import wraps

# 创建一个名为 'front' 的蓝图用于管理前端路由
bp = Blueprint('front', __name__)

# 后端REST API的基础URL，根据实际部署地址调整
API_BASE_URL = 'http://127.0.0.1:5000/api'

# 2.0版本：添加代理路由，用于前端访问搜索和随机接口
@bp.route('/api/search')
def proxy_search():
    """代理搜索请求到后端"""
    import requests
    keyword = request.args.get('keyword', '')
    types = request.args.get('types', '')
    page = request.args.get('page', 1)
    
    try:
        resp = requests.get(
            f"{API_BASE_URL}/search",
            params={'keyword': keyword, 'types': types, 'page': page}
        )
        return resp.json(), resp.status_code
    except Exception as e:
        return {'success': False, 'message': '搜索服务不可用'}, 500

@bp.route('/api/random')
def proxy_random():
    """代理随机浏览请求到后端"""
    import requests
    types = request.args.get('types', '')
    count = request.args.get('count', 20)
    
    try:
        resp = requests.get(
            f"{API_BASE_URL}/random",
            params={'types': types, 'count': count}
        )
        return resp.json(), resp.status_code
    except Exception as e:
        return {'success': False, 'message': '刷新服务不可用'}, 500

# 登录鉴权装饰器：未登录用户重定向到登录页
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('token'):
            # 若未登录，闪现提示并跳转登录页面
            flash("请先登录")
            return redirect(url_for('front.login'))
        return f(*args, **kwargs)
    return wrapper

@bp.route('/')
def index():
    """主页：首页面板（登录前后显示不同内容）"""
    # 如果已登录，从会话获取用户名用于个性化欢迎
    username = session.get('username')
    return render_template('index.html', username=username)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        # 获取表单字段
        username = request.form.get('username')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_pwd = request.form.get('confirm_password')
        # 简单校验：两次密码一致
        if password != confirm_pwd:
            error = "两次输入的密码不一致"
            return render_template('register.html', error=error, username=username, student_id=student_id, email=email)
        # 调用后端注册API
        payload = {
            'username': username,
            'student_id': student_id,
            'email': email,
            'password': password
        }
        try:
            resp = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        except Exception as e:
            # 后端服务不可用
            error = "后端服务无法连接，请稍后再试"
            return render_template('register.html', error=error, username=username, student_id=student_id, email=email)
        # 根据响应状态处理结果
        if resp.status_code == 201 or resp.status_code == 200:
            # 注册成功，提示并跳转到登录页
            flash("注册成功，请登录")
            return redirect(url_for('front.login'))
        else:
            # 注册失败，获取错误信息反馈
            error_msg = None
            try:
                data = resp.json()
                error_msg = data.get('message') or data.get('error')
            except Exception:
                pass
            if not error_msg:
                error_msg = f"注册失败（错误码{resp.status_code}）"
            return render_template('register.html', error=error_msg, username=username, student_id=student_id, email=email)
    # GET 请求渲染注册页面
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        payload = {
            'student_id': student_id,
            'password': password
        }
        try:
            resp = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        except Exception as e:
            error = "后端服务无法连接，请稍后再试"
            return render_template('login.html', error=error)
        if resp.status_code == 200:
            # 登录成功，获取Token和用户信息
            data = resp.json()
            token = data.get('token') or data.get('access_token')
            if not token:
                # 未返回令牌的异常情况
                error = "登录失败：认证令牌缺失"
                return render_template('login.html', error=error)
            # 将令牌和用户信息存入会话，用于后续鉴权
            session['token'] = token
            session['username'] = data.get('username') or student_id
            # 若后端返回用户ID等信息也一并保存
            session['user_id'] = data.get('user_id') or None
            user_obj = data.get('user')
            if user_obj:
                session['username'] = user_obj.get('username', session['username'])
                session['user_id'] = user_obj.get('id', session['user_id'])
            # 登录后跳转首页或下一步
            return redirect(url_for('front.index'))
        else:
            # 登录失败，解析错误信息
            error_msg = None
            try:
                error_data = resp.json()
                error_msg = error_data.get('message') or error_data.get('error')
            except Exception:
                pass
            if not error_msg:
                error_msg = "登录失败：用户名或密码错误"
            return render_template('login.html', error=error_msg)
    # GET 请求渲染登录页面
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    session.clear()  # 清除会话数据
    flash("您已退出登录")
    return redirect(url_for('front.login'))

@bp.route('/trades')
@login_required
def trades_list():
    """二手交易列表页面"""
    # 调用后端获取二手商品列表的接口
    headers = {'Authorization': f"Bearer {session['token']}"}  # 携带认证令牌
    try:
        resp = requests.get(f"{API_BASE_URL}/secondhand", headers=headers)
    except Exception as e:
        return render_template('trades_list.html', error="获取二手列表失败，服务器无法访问")
    if resp.status_code == 200:
        try:
            data = resp.json()
            # 后端返回格式: {"success": True, "items": [...], ...}
            items = data.get('items', []) if isinstance(data, dict) else []
        except Exception:
            items = []
        return render_template('trades_list.html', items=items)
    elif resp.status_code == 401:
        # Token无效或过期，要求重新登录
        session.clear()
        flash("登录已失效，请重新登录")
        return redirect(url_for('front.login'))
    else:
        error_msg = f"获取二手列表失败（错误码{resp.status_code}）"
        return render_template('trades_list.html', error=error_msg)

@bp.route('/trades/<int:item_id>')
@login_required
def trades_detail(item_id):
    """二手商品详情页面"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/secondhand/{item_id}", headers=headers)
    except Exception as e:
        return render_template('trades_detail.html', error="获取详情失败，服务器无法访问")
    if resp.status_code == 200:
        try:
            data = resp.json()
            # 后端返回格式: {"success": True, "item": {...}}
            item = data.get('item') if isinstance(data, dict) else None
        except Exception:
            item = None
        return render_template('trades_detail.html', item=item)
    elif resp.status_code == 404:
        return render_template('trades_detail.html', error="找不到该商品的信息")
    elif resp.status_code == 401:
        session.clear()
        flash("登录已失效，请重新登录")
        return redirect(url_for('front.login'))
    else:
        error_msg = f"获取商品详情失败（错误码{resp.status_code}）"
        return render_template('trades_detail.html', error=error_msg)

@bp.route('/trades/new', methods=['GET', 'POST'])
@login_required
def trades_new():
    """发布二手商品"""
    if request.method == 'POST':
        title = request.form.get('title')
        desc = request.form.get('description')
        price = request.form.get('price')
        # 基础校验：字段非空
        if not title or not desc or not price:
            error = "请填写所有必填字段"
            return render_template('trades_new.html', error=error, title=title, description=desc, price=price)
        payload = {
            'title': title,
            'description': desc,
            'price': price
        }
        headers = {'Authorization': f"Bearer {session['token']}"}
        try:
            resp = requests.post(f"{API_BASE_URL}/secondhand", json=payload, headers=headers)
        except Exception as e:
            error = "发布失败，服务器无法访问"
            return render_template('trades_new.html', error=error, title=title, description=desc, price=price)
        if resp.status_code in (200, 201):
            flash("二手商品发布成功")
            return redirect(url_for('front.trades_list'))
        else:
            error_msg = None
            try:
                data = resp.json()
                error_msg = data.get('message') or data.get('error')
            except Exception:
                pass
            if not error_msg:
                error_msg = f"发布失败（错误码{resp.status_code}）"
            return render_template('trades_new.html', error=error_msg, title=title, description=desc, price=price)
    # GET 请求渲染发布表单页面
    return render_template('trades_new.html')

@bp.route('/lostfound')
@login_required
def lostfound_list():
    """失物招领列表页面"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/lostfound", headers=headers)
    except Exception as e:
        return render_template('lostfound_list.html', error="获取失物招领列表失败，服务器无法访问")
    if resp.status_code == 200:
        try:
            data = resp.json()
            # 后端返回格式: {"success": True, "items": [...], ...}
            posts = data.get('items', []) if isinstance(data, dict) else []
        except Exception:
            posts = []
        return render_template('lostfound_list.html', posts=posts)
    elif resp.status_code == 401:
        session.clear()
        flash("登录已失效，请重新登录")
        return redirect(url_for('front.login'))
    else:
        error_msg = f"获取列表失败（错误码{resp.status_code}）"
        return render_template('lostfound_list.html', error=error_msg)

@bp.route('/lostfound/<int:post_id>')
@login_required
def lostfound_detail(post_id):
    """失物招领详情页面"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/lostfound/{post_id}", headers=headers)
    except Exception as e:
        return render_template('lostfound_detail.html', error="获取详情失败，服务器无法访问")
    if resp.status_code == 200:
        try:
            data = resp.json()
            # 后端返回格式: {"success": True, "item": {...}}
            post = data.get('item') if isinstance(data, dict) else None
        except Exception:
            post = None
        return render_template('lostfound_detail.html', post=post)
    elif resp.status_code == 404:
        return render_template('lostfound_detail.html', error="找不到该信息")
    elif resp.status_code == 401:
        session.clear()
        flash("登录已失效，请重新登录")
        return redirect(url_for('front.login'))
    else:
        error_msg = f"获取详情失败（错误码{resp.status_code}）"
        return render_template('lostfound_detail.html', error=error_msg)

@bp.route('/lostfound/<int:post_id>/status', methods=['PUT'])
@login_required
def update_lostfound_status(post_id):
    """更新失物招领状态 - 2.0版本新增"""
    headers = {
        'Authorization': f"Bearer {session['token']}",
        'Content-Type': 'application/json'
    }
    try:
        # 获取前端发送的状态
        data = request.get_json()
        resp = requests.put(
            f"{API_BASE_URL}/lostfound/{post_id}/status",
            json=data,
            headers=headers
        )
        return resp.json(), resp.status_code
    except Exception as e:
        return {'success': False, 'message': '更新服务不可用'}, 500

@bp.route('/lostfound/new', methods=['GET', 'POST'])
@login_required
def lostfound_new():
    """发布失物招领信息"""
    if request.method == 'POST':
        title = request.form.get('title')
        desc = request.form.get('description')
        location = request.form.get('location')
        contact = request.form.get('contact')
        item_type = request.form.get('item_type')  # "lost" 或 "found"
        if not title or not desc or not location or not contact or not item_type:
            error = "请填写所有必填字段"
            # 保留已填写内容，避免用户重复输入
            return render_template('lostfound_new.html', error=error, title=title, description=desc, location=location, contact=contact, item_type=item_type)
        payload = {
            'title': title,
            'description': desc,
            'location': location,
            'contact': contact,
            'type': item_type.upper()   # 后端需要大写的 LOST 或 FOUND
        }
        headers = {'Authorization': f"Bearer {session['token']}"}
        try:
            resp = requests.post(f"{API_BASE_URL}/lostfound", json=payload, headers=headers)
        except Exception as e:
            error = "发布失败，服务器无法访问"
            return render_template('lostfound_new.html', error=error, title=title, description=desc, location=location, contact=contact, item_type=item_type)
        if resp.status_code in (200, 201):
            flash("失物招领信息发布成功")
            return redirect(url_for('front.lostfound_list'))
        else:
            error_msg = None
            try:
                data = resp.json()
                error_msg = data.get('message') or data.get('error')
            except Exception:
                pass
            if not error_msg:
                error_msg = f"发布失败（错误码{resp.status_code}）"
            return render_template('lostfound_new.html', error=error_msg, title=title, description=desc, location=location, contact=contact, item_type=item_type)
    return render_template('lostfound_new.html')

@bp.route('/profile')
@login_required
def profile():
    """个人中心页面"""
    user_info = {
        'username': session.get('username'),
        'user_id': session.get('user_id')
    }
    return render_template('profile.html', user=user_info)

# 消息列表页（收件箱）
@bp.route('/messages')
@login_required
def messages_inbox():
    """查看我的消息"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        # 向后端请求我的收件箱数据
        resp = requests.get(f"{API_BASE_URL}/messages/inbox", headers=headers)
        if resp.status_code == 200:
            msgs = resp.json().get('messages', [])
        else:
            msgs = []
            flash("获取消息列表失败")
    except Exception:
        msgs = []
        flash("无法连接到消息服务")
    
    return render_template('messages.html', messages=msgs)

# 发送消息的代理接口 (供前端JS调用)
@bp.route('/api/message/send', methods=['POST'])
@login_required
def send_message_proxy():
    """代理发送消息请求到后端"""
    data = request.get_json()
    headers = {'Authorization': f"Bearer {session['token']}"}
    
    try:
        # 转发给后端
        resp = requests.post(f"{API_BASE_URL}/messages", json=data, headers=headers)
        return resp.json(), resp.status_code
    except Exception as e:
        return {'success': False, 'message': '发送服务不可用'}, 500
    
    # ... (保留上面的 send_message_proxy 等函数) ...

# 删除消息的代理接口
@bp.route('/api/message/<int:message_id>/delete', methods=['DELETE'])
@login_required
def delete_message_proxy(message_id):
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.delete(f"{API_BASE_URL}/messages/{message_id}", headers=headers)
        return resp.json(), resp.status_code
    except Exception as e:
        return {'success': False, 'message': '删除服务不可用'}, 500
    
# 删除二手商品代理
@bp.route('/api/secondhand/<int:item_id>/delete', methods=['DELETE'])
@login_required
def delete_item_proxy(item_id):
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.delete(f"{API_BASE_URL}/secondhand/{item_id}", headers=headers)
        return resp.json(), resp.status_code
    except Exception:
        return {'success': False, 'message': '服务不可用'}, 500

# 删除失物招领代理
@bp.route('/api/lostfound/<int:post_id>/delete', methods=['DELETE'])
@login_required
def delete_lostfound_proxy(post_id):
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.delete(f"{API_BASE_URL}/lostfound/{post_id}", headers=headers)
        return resp.json(), resp.status_code
    except Exception:
        return {'success': False, 'message': '服务不可用'}, 500
    
# 专门处理带文件的发布请求
@bp.route('/api/secondhand/new', methods=['POST'])
@login_required
def proxy_trade_new():
    # 1. 准备发给后端的 payload (文字部分)
    data = {
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'price': request.form.get('price')
    }
    
    # 2. 准备文件部分
    files = {}
    if 'image' in request.files:
        file = request.files['image']
        # (文件名, 文件内容, 文件类型)
        files['image'] = (file.filename, file.read(), file.content_type)

    headers = {'Authorization': f"Bearer {session['token']}"}
    
    try:
        # 注意：这里 files=files 会自动处理 multipart/form-data
        resp = requests.post(
            f"{API_BASE_URL}/secondhand", 
            data=data, 
            files=files, 
            headers=headers
        )
        return resp.json(), resp.status_code
    except Exception as e:
        return {'success': False, 'message': '发布服务不可用'}, 500
    
# 专门处理失物招领发布的代理接口 (带文件)
@bp.route('/api/lostfound/new', methods=['POST'])
@login_required
def proxy_lostfound_new():
    # 1. 准备文字数据
    data = {
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'location': request.form.get('location'),
        'contact': request.form.get('contact'),
        'type': request.form.get('type') # LOST 或 FOUND
    }

    # 2. 准备文件数据
    files = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            files = {
                'image': (file.filename, file.read(), file.content_type)
            }

    headers = {'Authorization': f"Bearer {session['token']}"}

    try:
        # 转发给后端API
        resp = requests.post(
            f"{API_BASE_URL}/lostfound",
            data=data,
            files=files,
            headers=headers
        )
        return resp.json(), resp.status_code
    except Exception as e:
        print(f"失物招领发布代理错误: {e}")
        return {'success': False, 'message': '发布服务不可用'}, 500

# 未读消息数量代理
@bp.route('/api/messages/unread-count')
@login_required
def proxy_unread_count():
    """代理获取未读消息数量"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/messages/unread-count", headers=headers)
        return resp.json(), resp.status_code
    except Exception:
        return {'success': False, 'count': 0}, 500

# 我的二手商品代理
@bp.route('/api/secondhand/my')
@login_required
def proxy_my_secondhand():
    """代理获取我发布的二手商品"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/secondhand/my", headers=headers)
        return resp.json(), resp.status_code
    except Exception:
        return {'success': False, 'message': '服务不可用'}, 500

# 我的失物招领代理
@bp.route('/api/lostfound/my')
@login_required
def proxy_my_lostfound():
    """代理获取我发布的失物招领"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{API_BASE_URL}/lostfound/my", headers=headers)
        return resp.json(), resp.status_code
    except Exception:
        return {'success': False, 'message': '服务不可用'}, 500

# 二手商品状态更新代理
@bp.route('/api/secondhand/<int:item_id>/status', methods=['PUT'])
@login_required
def proxy_update_item_status(item_id):
    """代理更新二手商品状态"""
    headers = {
        'Authorization': f"Bearer {session['token']}",
        'Content-Type': 'application/json'
    }
    try:
        data = request.get_json()
        resp = requests.put(
            f"{API_BASE_URL}/secondhand/{item_id}/status",
            json=data,
            headers=headers
        )
        return resp.json(), resp.status_code
    except Exception:
        return {'success': False, 'message': '更新服务不可用'}, 500

# 我的发布页面
@bp.route('/my-posts')
@login_required
def my_posts():
    """查看我发布的二手商品和失物招领"""
    headers = {'Authorization': f"Bearer {session['token']}"}
    items = []
    posts = []
    error = None

    # 获取二手商品
    try:
        resp_items = requests.get(f"{API_BASE_URL}/secondhand/my", headers=headers)
        if resp_items.status_code == 200:
            data = resp_items.json()
            items = data.get('items', []) if isinstance(data, dict) else []
    except Exception:
        pass

    # 获取失物招领
    try:
        resp_posts = requests.get(f"{API_BASE_URL}/lostfound/my", headers=headers)
        if resp_posts.status_code == 200:
            data = resp_posts.json()
            posts = data.get('items', []) if isinstance(data, dict) else []
    except Exception:
        pass

    if not items and not posts:
        error = None  # 暂无内容不算错误

    return render_template('my_posts.html', items=items, posts=posts, error=error)