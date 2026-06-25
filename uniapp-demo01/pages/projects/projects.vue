<template>
  <view class="page">
    <view class="filters">
      <input class="search-input" v-model="keyword" placeholder="搜索项目名称或说明" @confirm="refresh" />
      <button class="search-btn" size="mini" @click="refresh">搜索</button>
    </view>

    <view v-if="items.length === 0 && !loading" class="empty">还没有命名项目</view>

    <view v-for="item in items" :key="item.id" class="project-card">
      <view class="card-head">
        <view class="title-wrap">
          <text class="title">{{ item.title }}</text>
          <text class="category">{{ item.category }}</text>
        </view>
        <button class="continue-btn" size="mini" @click="continueProject(item)">继续</button>
      </view>

      <view v-if="item.description" class="description">{{ item.description }}</view>
      <view class="stats">
        <text>结果 {{ item.history_count || 0 }}</text>
        <text>收藏 {{ item.favorite_count || 0 }}</text>
        <text>知识库 {{ item.knowledge_file_count || 0 }}</text>
      </view>
      <view class="meta">{{ formatTime(item.updated_time) }}</view>

      <view class="actions">
        <button size="mini" class="outline-btn" @click="openHistory(item)">查看结果</button>
        <button size="mini" class="export-btn" @click="exportProject(item)">导出项目</button>
        <button size="mini" class="archive-btn" @click="archiveProject(item)">归档</button>
      </view>
    </view>

    <button v-if="hasMore" class="load-more" :loading="loading" @click="loadMore">加载更多</button>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import { chooseAndExportProjectReport } from '@/utils/reportExport.js';

const items = ref([]);
const total = ref(0);
const offset = ref(0);
const limit = 20;
const hasMore = ref(false);
const loading = ref(false);
const keyword = ref('');

onLoad(() => {
  refresh();
});

onPullDownRefresh(async () => {
  await refresh();
  uni.stopPullDownRefresh();
});

const fetchList = async (append = false) => {
  if (loading.value) return;
  loading.value = true;
  try {
    const res = await http.getProjects({
      keyword: keyword.value.trim(),
      limit,
      offset: offset.value
    });
    items.value = append ? items.value.concat(res.items || []) : (res.items || []);
    total.value = res.total || 0;
    hasMore.value = items.value.length < total.value;
  } finally {
    loading.value = false;
  }
};

const refresh = async () => {
  offset.value = 0;
  await fetchList(false);
};

const loadMore = async () => {
  offset.value = items.value.length;
  await fetchList(true);
};

const continueProject = (item) => {
  uni.navigateTo({ url: `/pages/index/index?project_id=${item.id}` });
};

const openHistory = (item) => {
  uni.navigateTo({ url: `/pages/history/history?project_id=${item.id}` });
};

const exportProject = (item) => {
  chooseAndExportProjectReport(item.id, item.title || '项目命名方案');
};

const archiveProject = (item) => {
  uni.showModal({
    title: '归档项目',
    content: '归档后默认列表不再显示，历史和收藏不会删除。',
    success: async (res) => {
      if (!res.confirm) return;
      await http.archiveProject(item.id);
      items.value = items.value.filter((entry) => entry.id !== item.id);
      total.value = Math.max(0, total.value - 1);
    }
  });
};

const formatTime = (value) => {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 19);
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.filters { display: flex; gap: 12rpx; align-items: center; margin-bottom: 22rpx; }
.search-input { flex: 1; height: 68rpx; line-height: 68rpx; background: #fff; border-radius: 10rpx; padding: 0 18rpx; font-size: 26rpx; box-sizing: border-box; }
.search-btn { margin: 0; background: #007aff; color: #fff; }
.empty { text-align: center; color: #888; font-size: 28rpx; padding: 120rpx 0; }
.project-card { background: #fff; border-radius: 14rpx; padding: 26rpx; margin-bottom: 20rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.card-head { display: flex; justify-content: space-between; gap: 20rpx; align-items: center; margin-bottom: 12rpx; }
.title-wrap { display: flex; align-items: center; min-width: 0; }
.title { font-size: 34rpx; font-weight: 700; color: #222; margin-right: 14rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.category { flex-shrink: 0; font-size: 22rpx; color: #007aff; background: #e8f2ff; border-radius: 20rpx; padding: 4rpx 14rpx; }
.continue-btn { margin: 0; color: #fff; background: #007aff; }
.description { color: #555; font-size: 26rpx; line-height: 1.6; margin-bottom: 14rpx; }
.stats { display: flex; gap: 18rpx; color: #52677a; font-size: 24rpx; margin-top: 10rpx; }
.meta { color: #999; font-size: 22rpx; margin-top: 14rpx; }
.actions { display: flex; gap: 16rpx; margin-top: 18rpx; }
.outline-btn { flex: 1; margin: 0; color: #1677ff; background: #f7fbff; border: 1px solid #cfe3ff; }
.export-btn { flex: 1; margin: 0; color: #fff; background: #2e7d32; }
.archive-btn { width: 140rpx; margin: 0; color: #fff; background: #8a8f98; }
.load-more { margin-top: 24rpx; background: #fff; color: #007aff; }
</style>
