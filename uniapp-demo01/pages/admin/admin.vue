<template>
  <view class="page">
    <view class="toolbar">
      <input class="search" v-model="keyword" placeholder="搜索用户、邮箱、名称" confirm-type="search" @confirm="refreshAll" />
      <button class="search-btn" size="mini" :loading="loading" @click="refreshAll">查询</button>
    </view>

    <view class="stats-grid">
      <view class="stat-item">
        <text class="stat-value">{{ generationStats.total_users }}</text>
        <text class="stat-label">总用户</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ generationStats.today_new_users }}</text>
        <text class="stat-label">今日新增</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ generationStats.today_generations }}</text>
        <text class="stat-label">今日生成</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ generationStats.today_credit_consumed }}</text>
        <text class="stat-label">今日耗额</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ generationStats.paid_conversion.conversion_rate }}%</text>
        <text class="stat-label">付费转化</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ taskStats.total }}</text>
        <text class="stat-label">知识库任务</text>
      </view>
      <view class="stat-item">
        <text class="stat-value">{{ generationStats.rag_failure_rate }}%</text>
        <text class="stat-label">RAG失败率</text>
      </view>
    </view>

    <view class="tabs">
      <view v-for="item in tabs" :key="item.key" :class="['tab', activeTab === item.key ? 'active' : '']" @click="activeTab = item.key">
        {{ item.label }}
      </view>
    </view>

    <view v-if="activeTab === 'operations'" class="section">
      <view class="section-title">运营面板</view>
      <view class="panel-grid">
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">每日起名次数</text>
            <text class="panel-value">{{ generationStats.today_generations }}</text>
          </view>
          <view v-for="item in generationStats.daily_generations" :key="'gen-' + item.date" class="bar-row">
            <text class="bar-label">{{ shortDate(item.date) }}</text>
            <view class="bar-track"><view class="bar-fill blue" :style="{ width: barWidth(item.count, generationStats.daily_generations) }"></view></view>
            <text class="bar-value">{{ item.count }}</text>
          </view>
        </view>
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">每日新增用户</text>
            <text class="panel-value">{{ generationStats.today_new_users }}</text>
          </view>
          <view v-for="item in generationStats.daily_new_users" :key="'new-' + item.date" class="bar-row">
            <text class="bar-label">{{ shortDate(item.date) }}</text>
            <view class="bar-track"><view class="bar-fill green" :style="{ width: barWidth(item.count, generationStats.daily_new_users) }"></view></view>
            <text class="bar-value">{{ item.count }}</text>
          </view>
        </view>
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">付费转化</text>
            <text class="panel-value">{{ generationStats.paid_conversion.conversion_rate }}%</text>
          </view>
          <view class="summary-line">
            <text>付费用户 {{ generationStats.paid_conversion.paid_users }}</text>
            <text>订单 {{ generationStats.paid_conversion.paid_orders }}</text>
            <text>金额 ￥{{ formatPrice(generationStats.paid_conversion.paid_amount_cents) }}</text>
          </view>
          <view v-for="item in generationStats.daily_paid_users" :key="'paid-' + item.date" class="bar-row">
            <text class="bar-label">{{ shortDate(item.date) }}</text>
            <view class="bar-track"><view class="bar-fill blue" :style="{ width: barWidth(item.count, generationStats.daily_paid_users) }"></view></view>
            <text class="bar-value">{{ item.count }}</text>
          </view>
        </view>
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">额度消耗</text>
            <text class="panel-value">{{ generationStats.today_credit_consumed }}</text>
          </view>
          <view v-for="item in generationStats.daily_credit_consumed" :key="'credit-' + item.date" class="bar-row">
            <text class="bar-label">{{ shortDate(item.date) }}</text>
            <view class="bar-track"><view class="bar-fill orange" :style="{ width: barWidth(item.credits, generationStats.daily_credit_consumed, 'credits') }"></view></view>
            <text class="bar-value">{{ item.credits }}</text>
          </view>
        </view>
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">RAG 任务失败率</text>
            <text class="panel-value">{{ generationStats.rag_failure_rate }}%</text>
          </view>
          <view v-for="item in generationStats.daily_rag_tasks" :key="'rag-' + item.date" class="bar-row">
            <text class="bar-label">{{ shortDate(item.date) }}</text>
            <view class="bar-track"><view class="bar-fill red" :style="{ width: rankWidth(item.failure_rate) }"></view></view>
            <text class="bar-value">{{ item.failed }}/{{ item.total }}</text>
          </view>
        </view>
      </view>
      <view class="panel-grid">
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">热门起名分类</text>
          </view>
          <view v-for="item in generationStats.category_stats" :key="'category-' + item.category" class="rank-row">
            <text class="rank-name">{{ item.category }}</text>
            <view class="rank-track"><view class="rank-fill blue-rank" :style="{ width: rankWidth(item.percent) }"></view></view>
            <text class="rank-value">{{ item.count }}</text>
          </view>
          <view v-if="!generationStats.category_stats.length" class="mini-empty">暂无分类数据</view>
        </view>
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">热门行业</text>
          </view>
          <view v-for="item in generationStats.hot_industries" :key="'industry-' + item.name" class="rank-row">
            <text class="rank-name">{{ item.name }}</text>
            <view class="rank-track"><view class="rank-fill" :style="{ width: rankWidth(item.percent) }"></view></view>
            <text class="rank-value">{{ item.count }}</text>
          </view>
          <view v-if="!generationStats.hot_industries.length" class="mini-empty">暂无企业名偏好数据</view>
        </view>
        <view class="metric-panel">
          <view class="panel-head">
            <text class="panel-title">热门风格</text>
          </view>
          <view v-for="item in generationStats.hot_styles" :key="'style-' + item.name" class="rank-row">
            <text class="rank-name">{{ item.name }}</text>
            <view class="rank-track"><view class="rank-fill purple" :style="{ width: rankWidth(item.percent) }"></view></view>
            <text class="rank-value">{{ item.count }}</text>
          </view>
          <view v-if="!generationStats.hot_styles.length" class="mini-empty">暂无风格偏好数据</view>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'users'" class="section">
      <view class="section-title">用户列表</view>
      <view v-for="item in users" :key="item.id" class="row-card">
        <view class="row-main">
          <text class="row-title">{{ item.username }}</text>
          <text v-if="item.is_admin" class="tag warn">管理员</text>
        </view>
        <view class="row-muted">{{ item.email }}</view>
        <view class="row-meta">生成 {{ item.history_count }} 条 · 知识库 {{ item.knowledge_task_count }} 个</view>
        <view class="credit-line">
          <text>{{ item.plan_name || '免费版' }} · 余额 {{ item.credit_balance || 0 }} · 已用 {{ item.total_consumed || 0 }}</text>
          <button class="inline-btn" size="mini" @click="adjustCredits(item)">调额</button>
        </view>
        <view class="user-actions">
          <button class="inline-btn reset-password-btn" size="mini" @click="resetUserPassword(item)">重置密码</button>
        </view>
      </view>
      <view v-if="!users.length && !loading" class="empty">暂无用户</view>
    </view>

    <view v-if="activeTab === 'histories'" class="section">
      <view class="section-title">生成记录</view>
      <view v-for="item in histories" :key="item.id" class="row-card">
        <view class="row-main">
          <text class="row-title">{{ item.name }}</text>
          <text class="tag">{{ item.category }}</text>
        </view>
        <view class="row-muted">用户ID {{ item.user_id }} · {{ formatTime(item.created_time) }}</view>
        <view v-if="item.score_total" class="row-score">
          综合 {{ item.score_total }} · 音律 {{ item.rhythm_score }} · 寓意 {{ item.meaning_score }} · 传播 {{ item.spread_score }} · 域名 {{ item.domain_score }}
        </view>
        <view class="row-detail">{{ item.moral }}</view>
        <view v-if="item.domain" class="row-meta">{{ item.domain }} · {{ item.domain_status }}</view>
      </view>
      <view v-if="!histories.length && !loading" class="empty">暂无生成记录</view>
    </view>

    <view v-if="activeTab === 'tasks'" class="section">
      <view class="section-head">
        <view class="section-title">知识库任务诊断</view>
        <button class="inline-btn" size="mini" :loading="retryingTasks" @click="retryFailedTasks">批量重跑失败任务</button>
      </view>
      <view class="status-line">
        <text>排队 {{ taskStats.queued }}</text>
        <text>处理中 {{ taskStats.processing }}</text>
        <text>完成 {{ taskStats.done }}</text>
        <text>失败 {{ taskStats.failed }}</text>
      </view>
      <view v-for="item in taskList" :key="item.id" class="row-card">
        <view class="row-main">
          <text class="row-title">{{ item.filename }}</text>
          <text :class="['tag', item.status === 'failed' ? 'danger' : '']">{{ statusText(item.status) }}</text>
        </view>
        <view class="row-muted">{{ item.username }} · {{ item.email }}</view>
        <view class="row-meta">Project {{ item.project_id || 'None' }} · Chunks {{ item.chunk_count || 0 }} · {{ item.is_active ? 'Active' : 'Inactive' }}</view>
        <view class="row-meta">创建 {{ formatTime(item.created_time) }} · 更新 {{ formatTime(item.updated_time) }}</view>
        <view v-if="item.parse_log" class="log-box">{{ item.parse_log }}</view>
        <view v-if="item.error_message" class="error-box">
          <text class="error-title">失败原因</text>
          <text class="error-text">{{ item.error_message }}</text>
        </view>
        <button
          v-if="item.status !== 'processing'"
          class="inline-btn retry-btn"
          size="mini"
          :loading="retryingTaskId === item.id"
          @click="retryTask(item)"
        >
          手动重试
        </button>
      </view>
      <view v-if="!taskList.length && !loading" class="empty">暂无知识库任务</view>
    </view>

    <view v-if="activeTab === 'data'" class="section">
      <view class="section-head">
        <view class="section-title">数据维护</view>
        <button class="inline-btn" size="mini" @click="startCreateRecord">新增记录</button>
      </view>
      <view class="data-toolbar">
        <picker mode="selector" :range="dataTableLabels" @change="handleDataTableChange">
          <view class="data-select">{{ currentDataTable?.label || '选择数据表' }}</view>
        </picker>
        <button class="inline-btn" size="mini" :loading="dataLoading" @click="loadDataRecords(false)">刷新</button>
      </view>
      <view v-if="currentDataTable" class="data-help">
        <text>可新增：{{ currentDataTable.create_columns.join(', ') || '-' }}</text>
        <text>可编辑：{{ currentDataTable.editable_columns.join(', ') || '-' }}</text>
      </view>
      <view v-for="item in dataRecords" :key="item.id" class="row-card">
        <view class="row-main">
          <text class="row-title">#{{ item.id }} {{ primaryRecordText(item) }}</text>
          <text class="tag">{{ selectedDataTable }}</text>
        </view>
        <view class="data-record">
          <text v-for="column in visiblePreviewColumns" :key="column" class="data-chip">{{ column }}={{ formatDataValue(item[column]) }}</text>
        </view>
        <view class="data-actions">
          <button class="inline-btn" size="mini" @click="startEditRecord(item)">编辑</button>
          <button class="inline-btn danger-btn-small" size="mini" @click="deleteDataRecord(item)">删除</button>
        </view>
      </view>
      <button v-if="dataHasMore" class="load-more" size="mini" :loading="dataLoading" @click="loadMoreDataRecords">加载更多</button>
      <view v-if="!dataRecords.length && !dataLoading" class="empty">暂无数据</view>

      <view v-if="dataEditorVisible" class="editor-panel">
        <view class="section-head">
          <view class="section-title">{{ dataEditorMode === 'create' ? '新增记录' : `编辑 #${dataEditorId}` }}</view>
          <button class="inline-btn muted-btn" size="mini" @click="closeDataEditor">关闭</button>
        </view>
        <textarea class="json-editor" v-model="dataEditorText" />
        <button class="save-data-btn" :loading="dataSaving" @click="saveDataRecord">保存</button>
      </view>
    </view>

    <view v-if="activeTab === 'plans'" class="section">
      <view class="section-title">套餐管理</view>
      <view v-for="item in plans" :key="item.id" class="row-card">
        <view class="row-main">
          <text class="row-title">{{ item.name }}</text>
          <text :class="['tag', item.is_active ? '' : 'danger']">{{ item.is_active ? '上架' : '下架' }}</text>
        </view>
        <view class="row-muted">{{ item.description }}</view>
        <view class="row-meta">￥{{ formatPrice(item.price_cents) }} · {{ item.credits }} 次额度 · 排序 {{ item.sort_order }}</view>
        <button class="inline-btn plan-btn" size="mini" @click="togglePlan(item)">{{ item.is_active ? '下架' : '上架' }}</button>
      </view>
      <view v-if="!plans.length && !loading" class="empty">暂无套餐</view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import http from "@/http/http.js";

const tabs = [
  { key: "operations", label: "运营" },
  { key: "users", label: "用户" },
  { key: "histories", label: "生成记录" },
  { key: "tasks", label: "知识库" },
  { key: "data", label: "数据维护" },
  { key: "plans", label: "套餐" },
];

const activeTab = ref("operations");
const keyword = ref("");
const loading = ref(false);
const retryingTasks = ref(false);
const retryingTaskId = ref(null);
const users = ref([]);
const histories = ref([]);
const taskList = ref([]);
const plans = ref([]);
const dataTables = ref([]);
const selectedDataTable = ref("user");
const dataRecords = ref([]);
const dataTotal = ref(0);
const dataOffset = ref(0);
const dataLoading = ref(false);
const dataEditorVisible = ref(false);
const dataEditorMode = ref("create");
const dataEditorId = ref(null);
const dataEditorText = ref("{}");
const dataSaving = ref(false);
const dataLimit = 20;
const generationStats = ref({
  total_users: 0,
  total_generations: 0,
  today_generations: 0,
  today_new_users: 0,
  today_credit_consumed: 0,
  rag_failure_rate: 0,
  paid_conversion: {
    paid_users: 0,
    paid_orders: 0,
    paid_amount_cents: 0,
    conversion_rate: 0,
  },
  category_stats: [],
  daily_generations: [],
  daily_new_users: [],
  daily_paid_users: [],
  daily_credit_consumed: [],
  failed_task_trend: [],
  daily_rag_tasks: [],
  hot_industries: [],
  hot_styles: [],
});
const taskStats = ref({
  total: 0,
  today: 0,
  queued: 0,
  processing: 0,
  done: 0,
  failed: 0,
  recent_tasks: [],
});
const currentDataTable = computed(() => dataTables.value.find(item => item.name === selectedDataTable.value));
const dataTableLabels = computed(() => dataTables.value.map(item => `${item.label} (${item.name})`));
const visiblePreviewColumns = computed(() => (currentDataTable.value?.columns || []).filter(column => column !== "id").slice(0, 6));
const dataHasMore = computed(() => dataRecords.value.length < dataTotal.value);

const refreshAll = async () => {
  loading.value = true;
  try {
    await http.adminMe();
    const [userRes, historyRes, generationRes, taskRes, taskListRes, planRes, dataTableRes] = await Promise.all([
      http.adminUsers({ keyword: keyword.value, limit: 50, offset: 0 }),
      http.adminNameHistories({ keyword: keyword.value, limit: 50, offset: 0 }),
      http.adminGenerationStats(),
      http.adminKnowledgeTaskStats(),
      http.adminKnowledgeTasks({ keyword: keyword.value, limit: 50, offset: 0 }),
      http.adminMembershipPlans({ include_inactive: true }),
      http.adminDataTables(),
    ]);
    users.value = userRes.items || [];
    histories.value = historyRes.items || [];
    generationStats.value = normalizeGenerationStats(generationRes);
    taskStats.value = taskRes;
    taskList.value = taskListRes.items || [];
    plans.value = planRes || [];
    dataTables.value = dataTableRes.items || [];
    if (!currentDataTable.value && dataTables.value.length) {
      selectedDataTable.value = dataTables.value[0].name;
    }
    dataOffset.value = 0;
    await loadDataRecords(false);
  } catch (error) {
    if (error && error.detail) {
      uni.showToast({ title: String(error.detail), icon: "none" });
    }
  } finally {
    loading.value = false;
  }
};

const handleDataTableChange = (event) => {
  const table = dataTables.value[event.detail.value];
  if (!table) return;
  selectedDataTable.value = table.name;
  dataOffset.value = 0;
  dataEditorVisible.value = false;
  loadDataRecords(false);
};

const loadDataRecords = async (append = false) => {
  if (!selectedDataTable.value || dataLoading.value) return;
  dataLoading.value = true;
  try {
    const res = await http.adminDataList(selectedDataTable.value, {
      keyword: keyword.value,
      limit: dataLimit,
      offset: dataOffset.value,
    });
    dataRecords.value = append ? dataRecords.value.concat(res.items || []) : (res.items || []);
    dataTotal.value = res.total || 0;
  } catch (error) {
    console.error("加载数据维护记录失败", error);
  } finally {
    dataLoading.value = false;
  }
};

const loadMoreDataRecords = async () => {
  dataOffset.value = dataRecords.value.length;
  await loadDataRecords(true);
};

const pickFields = (item, columns) => {
  const data = {};
  for (const column of columns) {
    if (Object.prototype.hasOwnProperty.call(item, column)) {
      data[column] = item[column];
    }
  }
  return data;
};

const startCreateRecord = () => {
  if (!currentDataTable.value) return;
  dataEditorMode.value = "create";
  dataEditorId.value = null;
  const template = {};
  for (const column of currentDataTable.value.create_columns) {
    template[column] = column === "password" ? "" : null;
  }
  dataEditorText.value = JSON.stringify(template, null, 2);
  dataEditorVisible.value = true;
};

const startEditRecord = (item) => {
  if (!currentDataTable.value) return;
  dataEditorMode.value = "edit";
  dataEditorId.value = item.id;
  dataEditorText.value = JSON.stringify(pickFields(item, currentDataTable.value.editable_columns), null, 2);
  dataEditorVisible.value = true;
};

const closeDataEditor = () => {
  dataEditorVisible.value = false;
  dataEditorId.value = null;
  dataEditorText.value = "{}";
};

const parseDataEditor = () => {
  try {
    const value = JSON.parse(dataEditorText.value || "{}");
    if (!value || Array.isArray(value) || typeof value !== "object") {
      throw new Error("JSON must be an object");
    }
    return value;
  } catch (error) {
    uni.showToast({ title: "请输入合法 JSON 对象", icon: "none" });
    throw error;
  }
};

const saveDataRecord = async () => {
  const data = parseDataEditor();
  dataSaving.value = true;
  try {
    if (dataEditorMode.value === "create") {
      await http.adminDataCreate(selectedDataTable.value, data);
      uni.showToast({ title: "记录已新增", icon: "success" });
    } else {
      await http.adminDataUpdate(selectedDataTable.value, dataEditorId.value, data);
      uni.showToast({ title: "记录已更新", icon: "success" });
    }
    closeDataEditor();
    dataOffset.value = 0;
    await loadDataRecords(false);
  } catch (error) {
    console.error("保存数据维护记录失败", error);
  } finally {
    dataSaving.value = false;
  }
};

const deleteDataRecord = (item) => {
  uni.showModal({
    title: "删除记录",
    content: `确定删除 ${selectedDataTable.value} #${item.id} 吗？`,
    success: async (res) => {
      if (!res.confirm) return;
      try {
        await http.adminDataDelete(selectedDataTable.value, item.id);
        uni.showToast({ title: "记录已删除", icon: "none" });
        dataRecords.value = dataRecords.value.filter(record => record.id !== item.id);
        dataTotal.value = Math.max(0, dataTotal.value - 1);
      } catch (error) {
        console.error("删除数据维护记录失败", error);
      }
    }
  });
};

const adjustCredits = (user) => {
  uni.showModal({
    title: `调整 ${user.username} 的额度`,
    editable: true,
    placeholderText: "输入整数，正数增加，负数扣减",
    success: async (res) => {
      if (!res.confirm) return;
      const amount = Number(res.content);
      if (!Number.isInteger(amount) || amount === 0) {
        return uni.showToast({ title: "请输入非 0 整数", icon: "none" });
      }
      try {
        await http.adminAdjustUserCredits(user.id, { amount, reason: "管理员手动调整" });
        uni.showToast({ title: "额度已调整", icon: "success" });
        refreshAll();
      } catch (error) {
        console.error("调整额度失败", error);
      }
    }
  });
};

const resetUserPassword = (user) => {
  uni.showModal({
    title: `重置 ${user.username} 的密码`,
    editable: true,
    placeholderText: "输入新密码，至少 4 位",
    success: async (res) => {
      if (!res.confirm) return;
      const password = String(res.content || "");
      if (password.length < 4) {
        return uni.showToast({ title: "密码至少 4 位", icon: "none" });
      }
      try {
        await http.adminResetUserPassword(user.id, {
          new_password: password,
          confirm_password: password,
        });
        uni.showToast({ title: "密码已重置", icon: "success" });
      } catch (error) {
        console.error("重置用户密码失败", error);
      }
    }
  });
};

const retryTask = async (task) => {
  retryingTaskId.value = task.id;
  try {
    const updated = await http.adminReparseKnowledgeTask(task.id);
    const index = taskList.value.findIndex(item => item.id === updated.id);
    if (index >= 0) {
      taskList.value[index] = updated;
    }
    uni.showToast({ title: "已重新入队", icon: "none" });
    refreshAll();
  } catch (error) {
    console.error("重试知识库任务失败", error);
  } finally {
    retryingTaskId.value = null;
  }
};

const retryFailedTasks = async () => {
  retryingTasks.value = true;
  try {
    const result = await http.adminReparseKnowledgeTasks({ status: "failed", limit: 100 });
    uni.showToast({ title: `已重跑 ${result.retried || 0} 个`, icon: "none" });
    refreshAll();
  } catch (error) {
    console.error("批量重跑知识库任务失败", error);
  } finally {
    retryingTasks.value = false;
  }
};

const togglePlan = async (plan) => {
  try {
    await http.adminUpdateMembershipPlan(plan.id, { is_active: !plan.is_active });
    uni.showToast({ title: plan.is_active ? "套餐已下架" : "套餐已上架", icon: "none" });
    refreshAll();
  } catch (error) {
    console.error("更新套餐失败", error);
  }
};

const formatPrice = (cents = 0) => (Number(cents || 0) / 100).toFixed(2);
const formatTime = (value) => (value ? String(value).replace("T", " ").slice(0, 19) : "");
const shortDate = (value) => (value ? String(value).slice(5, 10) : "");
const barWidth = (value, items, key = "count") => {
  const max = Math.max(1, ...items.map(item => Number(item[key] || 0)));
  const percent = Math.round(Number(value || 0) * 100 / max);
  return `${Math.max(percent, value > 0 ? 8 : 0)}%`;
};
const rankWidth = (percent = 0) => `${Math.max(Number(percent || 0), 6)}%`;
const normalizeGenerationStats = (data = {}) => ({
  total_users: data.total_users || 0,
  total_generations: data.total_generations || 0,
  today_generations: data.today_generations || 0,
  today_new_users: data.today_new_users || 0,
  today_credit_consumed: data.today_credit_consumed || 0,
  rag_failure_rate: data.rag_failure_rate || 0,
  paid_conversion: {
    paid_users: data.paid_conversion?.paid_users || 0,
    paid_orders: data.paid_conversion?.paid_orders || 0,
    paid_amount_cents: data.paid_conversion?.paid_amount_cents || 0,
    conversion_rate: data.paid_conversion?.conversion_rate || 0,
  },
  category_stats: data.category_stats || [],
  daily_generations: data.daily_generations || [],
  daily_new_users: data.daily_new_users || [],
  daily_paid_users: data.daily_paid_users || [],
  daily_credit_consumed: data.daily_credit_consumed || [],
  failed_task_trend: data.failed_task_trend || [],
  daily_rag_tasks: data.daily_rag_tasks || [],
  hot_industries: data.hot_industries || [],
  hot_styles: data.hot_styles || [],
});
const statusText = (status) => {
  const map = { queued: "排队", processing: "处理中", done: "完成", failed: "失败" };
  return map[status] || status;
};
const primaryRecordText = (item) => item.name || item.title || item.username || item.email || item.filename || item.plan_name || "";
const formatDataValue = (value) => {
  if (value === null || value === undefined || value === "") return "-";
  const text = String(value);
  return text.length > 32 ? `${text.slice(0, 32)}...` : text;
};

onMounted(refreshAll);
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.toolbar { display: flex; gap: 16rpx; align-items: center; margin-bottom: 24rpx; }
.search { flex: 1; height: 72rpx; padding: 0 24rpx; border-radius: 8rpx; background: #fff; font-size: 26rpx; box-sizing: border-box; }
.search-btn { width: 132rpx; height: 72rpx; line-height: 72rpx; padding: 0; background: #1677ff; color: #fff; border-radius: 8rpx; font-size: 26rpx; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12rpx; margin-bottom: 24rpx; }
.stat-item { min-width: 0; padding: 20rpx 8rpx; background: #fff; border-radius: 8rpx; text-align: center; }
.stat-value { display: block; font-size: 34rpx; line-height: 42rpx; font-weight: 700; color: #202124; }
.stat-label { display: block; margin-top: 6rpx; font-size: 22rpx; line-height: 28rpx; color: #6b7280; }
.tabs { display: flex; background: #fff; border-radius: 8rpx; margin-bottom: 24rpx; overflow: hidden; }
.tab { flex: 1; height: 76rpx; line-height: 76rpx; text-align: center; font-size: 26rpx; color: #606266; }
.tab.active { color: #1677ff; font-weight: 700; background: #edf5ff; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; margin: 8rpx 0 16rpx; }
.section-title { font-size: 30rpx; font-weight: 700; color: #202124; }
.panel-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16rpx; margin-top: 16rpx; }
.metric-panel { min-width: 0; padding: 20rpx; background: #fff; border-radius: 8rpx; box-sizing: border-box; }
.panel-head { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; margin-bottom: 14rpx; }
.panel-title { font-size: 26rpx; line-height: 34rpx; font-weight: 700; color: #202124; }
.panel-value { font-size: 30rpx; line-height: 38rpx; font-weight: 700; color: #1677ff; }
.summary-line { display: flex; flex-wrap: wrap; gap: 12rpx; margin-bottom: 12rpx; font-size: 22rpx; line-height: 30rpx; color: #4b5563; }
.bar-row { display: grid; grid-template-columns: 72rpx minmax(0, 1fr) 56rpx; align-items: center; gap: 10rpx; min-height: 36rpx; }
.bar-label, .bar-value { font-size: 22rpx; line-height: 30rpx; color: #6b7280; }
.bar-value { text-align: right; }
.bar-track { height: 14rpx; overflow: hidden; background: #edf1f5; border-radius: 8rpx; }
.bar-fill { height: 100%; border-radius: 8rpx; background: #1677ff; }
.bar-fill.green { background: #12a150; }
.bar-fill.blue { background: #1677ff; }
.bar-fill.orange { background: #d97706; }
.bar-fill.red { background: #d93026; }
.rank-row { display: grid; grid-template-columns: 140rpx minmax(0, 1fr) 50rpx; align-items: center; gap: 10rpx; min-height: 42rpx; }
.rank-name, .rank-value { font-size: 24rpx; line-height: 34rpx; color: #374151; }
.rank-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-value { text-align: right; color: #6b7280; }
.rank-track { height: 18rpx; overflow: hidden; background: #edf1f5; border-radius: 8rpx; }
.rank-fill { height: 100%; border-radius: 8rpx; background: #12a150; }
.rank-fill.purple { background: #7c3aed; }
.rank-fill.blue-rank { background: #1677ff; }
.mini-empty { padding: 24rpx 0; text-align: center; font-size: 24rpx; color: #9ca3af; }
.row-card { padding: 22rpx; margin-bottom: 16rpx; background: #fff; border-radius: 8rpx; }
.row-main { display: flex; gap: 12rpx; align-items: center; justify-content: space-between; }
.row-title { flex: 1; min-width: 0; font-size: 30rpx; line-height: 40rpx; font-weight: 700; color: #202124; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-muted { margin-top: 8rpx; font-size: 24rpx; line-height: 34rpx; color: #6b7280; word-break: break-all; }
.row-meta { margin-top: 8rpx; font-size: 24rpx; line-height: 34rpx; color: #4b5563; }
.row-score { margin-top: 8rpx; font-size: 24rpx; line-height: 34rpx; color: #1677ff; background: #eef6ff; border-radius: 8rpx; padding: 8rpx 12rpx; }
.row-detail { margin-top: 10rpx; font-size: 26rpx; line-height: 38rpx; color: #374151; }
.credit-line { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; margin-top: 12rpx; color: #16213e; font-size: 24rpx; line-height: 34rpx; background: #f4f7fb; border-radius: 8rpx; padding: 12rpx; }
.user-actions { display: flex; justify-content: flex-end; margin-top: 12rpx; }
.inline-btn { flex: none; margin: 0; color: #fff; background: #16213e; border-radius: 8rpx; font-size: 22rpx; }
.reset-password-btn { background: #d97706; }
.retry-btn { margin-top: 14rpx; background: #1677ff; }
.plan-btn { margin-top: 14rpx; background: #1677ff; }
.tag { flex: none; padding: 4rpx 12rpx; border-radius: 6rpx; background: #e8f3ff; color: #1677ff; font-size: 22rpx; line-height: 30rpx; }
.tag.warn { background: #fff4d6; color: #8a5a00; }
.tag.danger { background: #fff1f0; color: #d93026; }
.status-line { display: flex; flex-wrap: wrap; gap: 12rpx; margin-bottom: 16rpx; font-size: 24rpx; color: #4b5563; }
.error-box { margin-top: 12rpx; padding: 12rpx; border-radius: 8rpx; background: #fff1f0; }
.error-title { display: block; margin-bottom: 4rpx; font-size: 22rpx; line-height: 30rpx; color: #a8071a; font-weight: 700; }
.error-text { display: block; font-size: 24rpx; line-height: 34rpx; color: #d93026; word-break: break-all; }
.log-box { margin-top: 12rpx; padding: 12rpx; border-radius: 8rpx; background: #f6f8fa; color: #586069; font-size: 22rpx; line-height: 32rpx; word-break: break-all; }
.empty { padding: 80rpx 0; text-align: center; font-size: 26rpx; color: #9ca3af; }
.data-toolbar { display: flex; gap: 14rpx; align-items: center; margin-bottom: 14rpx; }
.data-select { min-width: 280rpx; height: 68rpx; line-height: 68rpx; padding: 0 18rpx; background: #fff; border-radius: 8rpx; font-size: 26rpx; color: #202124; box-sizing: border-box; }
.data-help { display: flex; flex-direction: column; gap: 8rpx; padding: 14rpx; margin-bottom: 16rpx; background: #eef6ff; border-radius: 8rpx; color: #4b5563; font-size: 22rpx; line-height: 32rpx; word-break: break-all; }
.data-record { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 12rpx; }
.data-chip { max-width: 100%; padding: 6rpx 10rpx; background: #f4f7fb; border-radius: 6rpx; color: #4b5563; font-size: 22rpx; line-height: 30rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.data-actions { display: flex; gap: 12rpx; margin-top: 14rpx; }
.danger-btn-small { background: #d93026; }
.muted-btn { background: #6b7280; }
.editor-panel { padding: 20rpx; margin-top: 18rpx; background: #fff; border-radius: 8rpx; }
.json-editor { width: 100%; height: 360rpx; padding: 18rpx; background: #111827; color: #e5e7eb; border-radius: 8rpx; font-size: 24rpx; line-height: 34rpx; box-sizing: border-box; }
.save-data-btn { margin-top: 16rpx; color: #fff; background: #1677ff; border-radius: 8rpx; }
.load-more { margin-top: 16rpx; color: #1677ff; background: #fff; border-radius: 8rpx; }
</style>
