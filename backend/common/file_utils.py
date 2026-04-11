"""
校园生活圈 - 文件处理工具
处理图片上传、验证等功能
"""
import os
import uuid
import imghdr
from flask import current_app
from config import Config


def allowed_file(filename: str) -> bool:
    """
    检查文件扩展名是否合法

    Args:
        filename: 文件名

    Returns:
        bool: 是否为允许的图片格式
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def validate_image_content(file) -> bool:
    """
    验证上传文件的真实内容类型
    防止通过扩展名伪装恶意文件

    Args:
        file: FileStorage 对象

    Returns:
        bool: 文件内容是否为有效图片
    """
    try:
        # 保存当前读取位置
        file.stream.seek(0)
        header = file.stream.read(32)
        file.stream.seek(0)

        # 检查文件头识别真实类型
        image_type = imghdr.what(None, h=header)
        return image_type in {'jpeg', 'png', 'gif'}
    except Exception:
        return False


def save_uploaded_file(file) -> str | None:
    """
    保存上传文件并返回相对路径

    Args:
        file: FileStorage 对象

    Returns:
        str | None: 成功返回相对路径 (如 "static/uploads/xxx.jpg")，失败返回 None
    """
    if not file:
        return None

    # 双重验证：扩展名 + 内容类型
    if not allowed_file(file.filename):
        return None

    # 可选：启用内容验证
    # if not validate_image_content(file):
    #     return None

    # 生成随机文件名，防止中文乱码或重名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    # 确保上传目录存在
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 保存文件
    save_path = os.path.join(upload_folder, filename)
    file.save(save_path)

    # 返回相对路径（让前端能通过 URL 访问）
    return f"static/uploads/{filename}"


def delete_uploaded_file(image_path: str) -> bool:
    """
    删除上传的文件

    Args:
        image_path: 相对路径 (如 "static/uploads/xxx.jpg")

    Returns:
        bool: 是否删除成功
    """
    if not image_path:
        return False

    try:
        # 构建完整路径
        full_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            image_path
        )
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception:
        pass
    return False