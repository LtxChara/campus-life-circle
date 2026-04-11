"""
校园生活圈 - 查询工具
数据库查询相关的辅助函数
"""


def escape_like_pattern(keyword: str) -> str:
    """
    转义 SQL LIKE 查询中的特殊字符
    防止通配符注入

    在 SQL LIKE 语句中，% 和 _ 是通配符：
    - % 匹配任意多个字符
    - _ 匹配单个字符

    如果用户输入这些字符，可能导致意外的匹配结果。
    此函数将这些字符转义，使其被当作普通字符处理。

    Args:
        keyword: 用户输入的搜索关键字

    Returns:
        str: 转义后的关键字

    Examples:
        >>> escape_like_pattern("test%name")
        'test\\\\%name'
        >>> escape_like_pattern("user_id")
        'user\\\\_id'
    """
    if not keyword:
        return ""

    # 按顺序转义：先转义反斜杠本身，再转义 % 和 _
    escaped = keyword.replace('\\', '\\\\') \
                     .replace('%', '\\%') \
                     .replace('_', '\\_')
    return escaped


def build_like_condition(keyword: str, escape_char: str = '\\') -> str:
    """
    构建 LIKE 查询条件
    自动添加前后通配符并进行转义

    Args:
        keyword: 用户输入的搜索关键字
        escape_char: 转义字符，默认为 '\\'

    Returns:
        str: 格式化的 LIKE 条件字符串

    Examples:
        >>> build_like_condition("test")
        '%test%'
    """
    escaped = escape_like_pattern(keyword)
    return f"%{escaped}%"