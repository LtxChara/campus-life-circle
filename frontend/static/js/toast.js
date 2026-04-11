/**
 * 校园生活圈 - Toast提示组件
 * 替代原生alert()，提供更友好的用户提示
 */

const Toast = {
  container: null,

  /**
   * 初始化Toast容器
   */
  init() {
    if (this.container) return;

    this.container = document.createElement('div');
    this.container.id = 'toastContainer';
    this.container.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-width: 320px;
    `;
    document.body.appendChild(this.container);
  },

  /**
   * 显示Toast消息
   * @param {string} message - 提示内容
   * @param {string} type - 类型: 'success' | 'error' | 'warning' | 'info'
   * @param {number} duration - 显示时长(ms)，默认3000
   */
  show(message, type = 'info', duration = 3000) {
    this.init();

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;

    // 样式配置
    const styles = {
      success: { bg: '#e6f9f0', border: '#22c55e', color: '#0f766e', icon: '✓' },
      error: { bg: '#fef2f2', border: '#ef4444', color: '#b91c1c', icon: '✗' },
      warning: { bg: '#fff4e6', border: '#f97316', color: '#c2410c', icon: '⚠' },
      info: { bg: '#eef2ff', border: '#3b82f6', color: '#1d4ed8', icon: 'ℹ' }
    };

    const s = styles[type] || styles.info;

    toast.style.cssText = `
      padding: 12px 16px;
      background: ${s.bg};
      border: 1px solid ${s.border};
      border-radius: 12px;
      color: ${s.color};
      font-weight: 500;
      font-size: 0.95rem;
      box-shadow: 0 8px 24px rgba(0,0,0,0.12);
      display: flex;
      align-items: center;
      gap: 8px;
      animation: toastSlideIn 0.3s ease;
      cursor: pointer;
    `;

    toast.innerHTML = `<span style="font-size:1.1rem">${s.icon}</span><span>${message}</span>`;

    // 点击关闭
    toast.addEventListener('click', () => this.remove(toast));

    this.container.appendChild(toast);

    // 自动消失
    setTimeout(() => this.remove(toast), duration);

    return toast;
  },

  /**
   * 移除Toast
   * @param {HTMLElement} toast - Toast元素
   */
  remove(toast) {
    if (!toast || !toast.parentNode) return;
    toast.style.animation = 'toastSlideOut 0.3s ease';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  },

  // 快捷方法
  success(message, duration) { return this.show(message, 'success', duration); },
  error(message, duration) { return this.show(message, 'error', duration); },
  warning(message, duration) { return this.show(message, 'warning', duration); },
  info(message, duration) { return this.show(message, 'info', duration); }
};

// 添加动画样式
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes toastSlideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes toastSlideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
`;
document.head.appendChild(styleSheet);

// 导出到全局
window.Toast = Toast;
window.toast = Toast; // 简短别名