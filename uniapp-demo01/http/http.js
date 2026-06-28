const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
const getBaseUrl = () => uni.getStorageSync("api_base_url") || DEFAULT_BASE_URL;
const setBaseUrl = (value) => uni.setStorageSync("api_base_url", String(value || "").replace(/\/+$/, ""));
const resetBaseUrl = () => uni.removeStorageSync("api_base_url");

const request = (url, options) => {
  const token = uni.getStorageSync("token");
  const baseUrl = getBaseUrl();

  return new Promise((resolve, reject) => {
    uni.request({
      url: baseUrl + url,
      header: {
        "content-type": "application/json",
        authorization: token ? "Bearer " + token : ""
      },
      ...options,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
          return;
        }

        let errorMsg = "服务器请求失败";
        if (res.data && Array.isArray(res.data.detail)) {
          errorMsg = res.data.detail[0]?.msg || "表单参数校验失败";
        } else if (res.data && typeof res.data.detail === "string") {
          errorMsg = res.data.detail;
        }

        if (res.statusCode === 401) {
          uni.removeStorageSync("token");
          uni.removeStorageSync("user");
          uni.showToast({ title: "登录已失效，请重新登录", icon: "none", duration: 3000 });
          setTimeout(() => uni.reLaunch({ url: "/pages/login/login" }), 600);
          reject(res.data);
          return;
        }

        uni.showToast({ title: String(errorMsg), icon: "none", duration: 3000 });
        reject(res.data);
      },
      fail: (err) => {
        uni.showToast({ title: `无法连接后端：${baseUrl}`, icon: "none", duration: 3500 });
        reject(err);
      }
    });
  });
};

const uploadFile = (url, filePath) => {
  const token = uni.getStorageSync("token");
  const baseUrl = getBaseUrl();

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: baseUrl + url,
      filePath,
      name: "file",
      header: {
        authorization: token ? "Bearer " + token : ""
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data));
          } catch (error) {
            uni.showToast({ title: "上传响应解析失败", icon: "none" });
            reject(error);
          }
          return;
        }
        uni.showToast({ title: "文件上传失败", icon: "none" });
        reject(res);
      },
      fail: (err) => {
        uni.showToast({ title: `上传无法连接后端：${baseUrl}`, icon: "none" });
        reject(err);
      }
    });
  });
};

const downloadFile = (url) => {
  const token = uni.getStorageSync("token");
  const baseUrl = getBaseUrl();

  return new Promise((resolve, reject) => {
    uni.downloadFile({
      url: baseUrl + url,
      header: {
        authorization: token ? "Bearer " + token : ""
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300 && res.tempFilePath) {
          resolve(res.tempFilePath);
          return;
        }
        uni.showToast({ title: "报告导出失败", icon: "none" });
        reject(res);
      },
      fail: (err) => {
        uni.showToast({ title: `导出无法连接后端：${baseUrl}`, icon: "none" });
        reject(err);
      }
    });
  });
};

const buildQuery = (params = {}) => {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
  return query ? `?${query}` : "";
};

export default {
  DEFAULT_BASE_URL,
  getBaseUrl,
  setBaseUrl,
  resetBaseUrl,
  testConnection: () => request("/", { method: "GET", timeout: 3000 }),

  getEmailCode: (email) => request("/auth/code?email=" + encodeURIComponent(email), { method: "GET" }),
  register: (data) => request("/auth/register", { method: "POST", data }),
  login: (data) => request("/auth/login", { method: "POST", data }),
  resetPassword: (data) => request("/auth/password/reset", { method: "POST", data }),

  getProfile: () => request("/users/me", { method: "GET" }),
  updateProfile: (data) => request("/users/me", { method: "PATCH", data }),
  changePassword: (data) => request("/users/me/password", { method: "POST", data }),
  changeEmail: (data) => request("/users/me/email", { method: "POST", data }),
  getLoginRecords: (params) => request("/users/me/login-records" + buildQuery(params), { method: "GET" }),

  generateName: (data) => request("/names/generate", { method: "POST", data }),
  feedbackName: (data) => request("/names/feedback", { method: "POST", data }),
  getQuota: () => request("/names/quota", { method: "GET" }),

  getPreferenceTemplates: (params) => request("/preference-templates" + buildQuery(params), { method: "GET" }),
  createPreferenceTemplate: (data) => request("/preference-templates", { method: "POST", data }),
  updatePreferenceTemplate: (id, data) => request(`/preference-templates/${id}`, { method: "PATCH", data }),
  deletePreferenceTemplate: (id) => request(`/preference-templates/${id}`, { method: "DELETE" }),

  createProject: (data) => request("/projects", { method: "POST", data }),
  getProjects: (params) => request("/projects" + buildQuery(params), { method: "GET" }),
  getProjectDetail: (id) => request(`/projects/${id}`, { method: "GET" }),
  updateProject: (id, data) => request(`/projects/${id}`, { method: "PATCH", data }),
  archiveProject: (id) => request(`/projects/${id}`, { method: "DELETE" }),

  getMembership: () => request("/membership/me", { method: "GET" }),
  getMembershipPlans: () => request("/membership/plans", { method: "GET" }),
  rechargeMembership: (planId, payScene = "page") => request("/membership/recharge", { method: "POST", data: { plan_id: planId, pay_scene: payScene } }),
  getRechargeOrder: (orderId) => request(`/membership/orders/${orderId}`, { method: "GET" }),
  alipayQueryRechargeOrder: (orderId) => request(`/membership/orders/${orderId}/alipay-query`, { method: "POST" }),
  getCreditTransactions: (params) => request("/membership/transactions" + buildQuery(params), { method: "GET" }),

  uploadKnowledge: (filePath, projectId) => uploadFile("/knowledge/upload" + buildQuery({ project_id: projectId }), filePath),
  getKnowledgeFiles: (params) => request("/knowledge/files" + buildQuery(params), { method: "GET" }),
  getKnowledgeTask: (taskId) => request(`/knowledge/tasks/${taskId}`, { method: "GET" }),
  previewKnowledgeTask: (taskId, params) => request(`/knowledge/tasks/${taskId}/preview` + buildQuery(params), { method: "GET" }),
  reparseKnowledgeTask: (taskId) => request(`/knowledge/tasks/${taskId}/reparse`, { method: "POST" }),
  deleteKnowledgeTask: (taskId) => request(`/knowledge/tasks/${taskId}`, { method: "DELETE" }),
  setKnowledgeTaskActive: (taskId, isActive) =>
    request(`/knowledge/tasks/${taskId}/active`, { method: "PATCH", data: { is_active: isActive } }),

  getHistory: (params) => request("/history" + buildQuery(params), { method: "GET" }),
  getHistoryDetail: (id) => request(`/history/${id}`, { method: "GET" }),
  compareHistory: (historyIds) => request("/history/compare", { method: "POST", data: { history_ids: historyIds } }),
  downloadHistoryReport: (id, format) => downloadFile(`/history/${id}/export?format=${encodeURIComponent(format)}`),
  downloadProjectReport: (id, format) => downloadFile(`/projects/${id}/export?format=${encodeURIComponent(format)}`),
  setHistoryFavorite: (id, isFavorite) =>
    request(`/history/${id}/favorite`, { method: "PATCH", data: { is_favorite: isFavorite } }),
  deleteHistory: (id) => request(`/history/${id}`, { method: "DELETE" }),

  adminMe: () => request("/admin/me", { method: "GET" }),
  adminUsers: (params) => request("/admin/users" + buildQuery(params), { method: "GET" }),
  adminNameHistories: (params) => request("/admin/name-histories" + buildQuery(params), { method: "GET" }),
  adminGenerationStats: () => request("/admin/generation-stats", { method: "GET" }),
  adminKnowledgeTaskStats: () => request("/admin/knowledge-tasks/stats", { method: "GET" }),
  adminKnowledgeTasks: (params) => request("/admin/knowledge-tasks" + buildQuery(params), { method: "GET" }),
  adminReparseKnowledgeTask: (taskId) => request(`/admin/knowledge-tasks/${taskId}/reparse`, { method: "POST" }),
  adminReparseKnowledgeTasks: (data) => request("/admin/knowledge-tasks/reparse", { method: "POST", data }),
  adminMembershipPlans: (params) => request("/admin/membership/plans" + buildQuery(params), { method: "GET" }),
  adminCreateMembershipPlan: (data) => request("/admin/membership/plans", { method: "POST", data }),
  adminUpdateMembershipPlan: (id, data) => request(`/admin/membership/plans/${id}`, { method: "PATCH", data }),
  adminAdjustUserCredits: (userId, data) => request(`/admin/users/${userId}/credits`, { method: "POST", data }),
  adminResetUserPassword: (userId, data) => request(`/admin/users/${userId}/password`, { method: "POST", data }),
  adminDataTables: () => request("/admin/data/tables", { method: "GET" }),
  adminDataList: (table, params) => request(`/admin/data/${table}` + buildQuery(params), { method: "GET" }),
  adminDataGet: (table, id) => request(`/admin/data/${table}/${id}`, { method: "GET" }),
  adminDataCreate: (table, data) => request(`/admin/data/${table}`, { method: "POST", data: { data } }),
  adminDataUpdate: (table, id, data) => request(`/admin/data/${table}/${id}`, { method: "PATCH", data: { data } }),
  adminDataDelete: (table, id) => request(`/admin/data/${table}/${id}`, { method: "DELETE" })
};
