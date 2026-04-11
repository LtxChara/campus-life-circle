/**
 * 校园生活圈 - 全局配置模块
 * 用于统一管理API地址、图片URL等配置
 */

const AppConfig = {
  // 后端API基础URL (前端在5001端口，后端在5000端口)
  API_BASE_URL: window.location.port === '5001'
    ? 'http://127.0.0.1:5000'
    : window.location.origin,

  // 图片基础URL
  IMAGE_BASE_URL: window.location.port === '5001'
    ? 'http://127.0.0.1:5000'
    : window.location.origin,

  // 默认占位图片
  DEFAULT_IMAGE: 'https://via.placeholder.com/600x400?text=Campus+Life',

  // 默认商品图片
  DEFAULT_GOODS_IMAGE: 'https://via.placeholder.com/600x400?text=二手商品',

  // 默认失物招领图片
  DEFAULT_LOST_IMAGE: 'https://via.placeholder.com/600x400?text=失物招领'
};

/**
 * 获取完整图片URL
 * @param {string} path - 图片路径（相对路径或完整URL）
 * @param {string} type - 图片类型: 'goods' | 'lost' | 'default'
 * @returns {string} 完整的图片URL
 */
function getImageUrl(path, type = 'default') {
  if (!path) {
    switch (type) {
      case 'goods': return AppConfig.DEFAULT_GOODS_IMAGE;
      case 'lost': return AppConfig.DEFAULT_LOST_IMAGE;
      default: return AppConfig.DEFAULT_IMAGE;
    }
  }
  // 如果已经是完整URL，直接返回
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  // 拼接基础URL
  return `${AppConfig.IMAGE_BASE_URL}/${path}`;
}

/**
 * 处理图片加载错误，显示占位图
 * @param {HTMLImageElement} img - 图片元素
 * @param {string} type - 图片类型
 */
function handleImageError(img, type = 'default') {
  img.onerror = null; // 防止无限循环
  img.src = getImageUrl(null, type);
}

/**
 * 获取API完整URL
 * @param {string} endpoint - API端点路径
 * @returns {string} 完整的API URL
 */
function getApiUrl(endpoint) {
  return `${AppConfig.API_BASE_URL}/api${endpoint}`;
}

// 导出到全局
window.AppConfig = AppConfig;
window.getImageUrl = getImageUrl;
window.handleImageError = handleImageError;
window.getApiUrl = getApiUrl;