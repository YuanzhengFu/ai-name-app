<template>
  <view class="page">
    <view class="toolbar">
      <view :class="['toolbar-item', !favoriteOnly ? 'active' : '']" @click="switchMode(false)">历史</view>
      <view :class="['toolbar-item', favoriteOnly ? 'active' : '']" @click="switchMode(true)">收藏</view>
    </view>

    <view class="filters">
      <picker mode="selector" :range="categoryOptions" @change="handleCategoryChange">
        <view class="filter-field">{{ selectedCategory || '全部分类' }}</view>
      </picker>
      <input class="search-input" v-model="keyword" placeholder="搜索名字、出处、寓意" @confirm="refresh" />
      <button class="search-btn" size="mini" @click="refresh">搜索</button>
    </view>

    <view class="compare-bar">
      <button class="compare-mode-btn" size="mini" @click="toggleCompareMode">
        {{ compareMode ? '退出对比' : '选择对比' }}
      </button>
      <text v-if="compareMode" class="compare-count">已选 {{ selectedIds.length }}/5</text>
      <button v-if="compareMode" class="compare-submit-btn" size="mini" @click="openCompare">开始对比</button>
    </view>

    <view v-if="items.length === 0 && !loading" class="empty">
      {{ favoriteOnly ? '还没有收藏的名字' : '还没有起名历史' }}
    </view>

    <view v-for="item in items" :key="item.id" class="history-card">
      <view class="card-head">
        <view class="name-head">
          <view v-if="compareMode" :class="['select-box', isSelected(item) ? 'checked' : '']" @click="toggleCompareItem(item)">
            {{ isSelected(item) ? '✓' : '' }}
          </view>
          <text class="name">{{ item.name }}</text>
          <text class="category">{{ item.category }}</text>
        </view>
        <button class="favorite-btn" size="mini" @click="toggleFavorite(item)">
          {{ item.is_favorite ? '已收藏' : '收藏' }}
        </button>
      </view>

      <view v-if="item.domain" class="domain">{{ formatDomain(item) }}</view>
      <view v-if="hasCompanyEnrichment(item)" class="company-enrichment">
        <view class="alias-row" v-if="item.pinyin || item.english_name || item.abbreviation">
          <text v-if="item.pinyin">拼音：{{ item.pinyin }}</text>
          <text v-if="item.english_name">英文：{{ item.english_name }}</text>
          <text v-if="item.abbreviation">简称：{{ item.abbreviation }}</text>
        </view>
        <view v-if="item.domain_checks && item.domain_checks.length" class="domain-checks">
          <text v-for="check in item.domain_checks" :key="check.domain" class="domain-check">{{ check.domain }} {{ check.status }}</text>
        </view>
        <view v-if="item.brand_warning" class="brand-warning">{{ item.brand_warning }}</view>
      </view>
      <view class="score-panel" v-if="item.score_total">
        <view class="score-head">
          <text class="score-total">{{ item.score_total }}</text>
          <text class="score-unit">综合评分</text>
        </view>
        <view class="score-grid">
          <view class="score-item" v-for="metric in scoreMetrics(item)" :key="metric.label">
            <text class="score-label">{{ metric.label }}</text>
            <text class="score-value">{{ metric.value }}</text>
          </view>
        </view>
        <view v-if="item.score_explanation" class="score-explain">{{ item.score_explanation }}</view>
      </view>
      <view class="detail"><text class="label">出处：</text>{{ item.reference }}</view>
      <view class="detail"><text class="label">寓意：</text>{{ item.moral }}</view>
      <view class="meta">{{ formatTime(item.created_time) }}</view>

      <view class="actions">
        <button class="continue-btn" size="mini" @click="openDetail(item)">继续基于历史修改</button>
        <button class="export-btn" size="mini" @click="exportCurrent(item)">导出</button>
        <button class="delete-btn" size="mini" @click="removeItem(item)">删除</button>
      </view>
    </view>

    <button v-if="hasMore" class="load-more" :loading="loading" @click="loadMore">加载更多</button>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import { chooseAndExportReport } from '@/utils/reportExport.js';

const categoryOptions = ['全部分类', '人名', '企业名', '宠物名'];
const favoriteOnly = ref(false);
const selectedCategory = ref('');
const keyword = ref('');
const items = ref([]);
const total = ref(0);
const limit = 20;
const offset = ref(0);
const loading = ref(false);
const hasMore = ref(false);
const compareMode = ref(false);
const selectedIds = ref([]);
const projectId = ref('');

onLoad((query) => {
  favoriteOnly.value = query.type === 'favorite';
  projectId.value = query.project_id || '';
  refresh();
});

onPullDownRefresh(async () => {
  await refresh();
  uni.stopPullDownRefresh();
});

const switchMode = (nextFavoriteOnly) => {
  if (favoriteOnly.value === nextFavoriteOnly) return;
  favoriteOnly.value = nextFavoriteOnly;
  refresh();
};

const handleCategoryChange = (event) => {
  const value = categoryOptions[event.detail.value];
  selectedCategory.value = value === '全部分类' ? '' : value;
  refresh();
};

const fetchList = async (append = false) => {
  if (loading.value) return;
  loading.value = true;
  try {
    const res = await http.getHistory({
      favorite_only: favoriteOnly.value,
      category: selectedCategory.value,
      keyword: keyword.value.trim(),
      project_id: projectId.value,
      limit,
      offset: offset.value
    });
    items.value = append ? items.value.concat(res.items) : res.items;
    total.value = res.total;
    hasMore.value = items.value.length < total.value;
  } finally {
    loading.value = false;
  }
};

const refresh = async () => {
  offset.value = 0;
  selectedIds.value = [];
  await fetchList(false);
};

const loadMore = async () => {
  offset.value = items.value.length;
  await fetchList(true);
};

const openDetail = (item) => {
  uni.navigateTo({ url: `/pages/history/detail?id=${item.id}` });
};

const toggleCompareMode = () => {
  compareMode.value = !compareMode.value;
  selectedIds.value = [];
};

const isSelected = (item) => selectedIds.value.includes(item.id);

const toggleCompareItem = (item) => {
  if (isSelected(item)) {
    selectedIds.value = selectedIds.value.filter((id) => id !== item.id);
    return;
  }
  if (selectedIds.value.length >= 5) {
    return uni.showToast({ title: '最多选择 5 个名字', icon: 'none' });
  }
  selectedIds.value = selectedIds.value.concat(item.id);
};

const openCompare = () => {
  if (selectedIds.value.length < 2) {
    return uni.showToast({ title: '请至少选择 2 个名字', icon: 'none' });
  }
  uni.navigateTo({ url: `/pages/history/compare?ids=${selectedIds.value.join(',')}` });
};

const toggleFavorite = async (item) => {
  const updated = await http.setHistoryFavorite(item.id, !item.is_favorite);
  item.is_favorite = updated.is_favorite;
  if (favoriteOnly.value && !updated.is_favorite) {
    items.value = items.value.filter((entry) => entry.id !== item.id);
    total.value = Math.max(0, total.value - 1);
  }
};

const exportCurrent = (item) => {
  chooseAndExportReport(item.id, item.name);
};

const removeItem = (item) => {
  uni.showModal({
    title: '删除记录',
    content: '确定删除这条起名记录吗？',
    success: async (res) => {
      if (!res.confirm) return;
      await http.deleteHistory(item.id);
      items.value = items.value.filter((entry) => entry.id !== item.id);
      total.value = Math.max(0, total.value - 1);
    }
  });
};

const formatTime = (value) => {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 19);
};

const formatDomain = (item) => {
  return item.domain_status ? `${item.domain} (${item.domain_status})` : item.domain;
};

const hasCompanyEnrichment = (item = {}) => {
  return Boolean(
    item.pinyin ||
    item.english_name ||
    item.abbreviation ||
    item.brand_warning ||
    (item.domain_checks && item.domain_checks.length)
  );
};

const scoreMetrics = (item) => [
  { label: '音律', value: item.rhythm_score || 0 },
  { label: '寓意', value: item.meaning_score || 0 },
  { label: '传播性', value: item.spread_score || 0 },
  { label: '域名', value: item.domain_score || 0 }
];
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.toolbar { display: flex; background: #fff; border-radius: 14rpx; padding: 8rpx; margin-bottom: 20rpx; }
.toolbar-item { flex: 1; text-align: center; padding: 18rpx 0; font-size: 28rpx; color: #666; border-radius: 10rpx; }
.toolbar-item.active { background: #007aff; color: #fff; font-weight: 600; }
.filters { display: flex; gap: 12rpx; align-items: center; margin-bottom: 22rpx; }
.filter-field, .search-input { height: 68rpx; line-height: 68rpx; background: #fff; border-radius: 10rpx; padding: 0 18rpx; font-size: 26rpx; box-sizing: border-box; }
.filter-field { width: 180rpx; color: #333; }
.search-input { flex: 1; }
.search-btn { margin: 0; background: #007aff; color: #fff; }
.compare-bar { display: flex; align-items: center; gap: 14rpx; margin-bottom: 22rpx; }
.compare-mode-btn { margin: 0; background: #ffffff; color: #1677ff; border: 1px solid #cfe3ff; }
.compare-count { flex: 1; color: #52677a; font-size: 24rpx; }
.compare-submit-btn { margin: 0; color: #fff; background: #1677ff; }
.empty { text-align: center; color: #888; font-size: 28rpx; padding: 120rpx 0; }
.history-card { background: #fff; border-radius: 14rpx; padding: 26rpx; margin-bottom: 20rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.card-head { display: flex; justify-content: space-between; gap: 20rpx; align-items: center; margin-bottom: 12rpx; }
.name-head { display: flex; align-items: center; min-width: 0; }
.select-box { width: 40rpx; height: 40rpx; margin-right: 14rpx; border: 2rpx solid #b8c4d6; border-radius: 8rpx; color: #fff; background: #fff; text-align: center; line-height: 40rpx; font-size: 26rpx; font-weight: 700; }
.select-box.checked { background: #1677ff; border-color: #1677ff; }
.name { font-size: 40rpx; font-weight: 700; color: #222; margin-right: 16rpx; }
.category { font-size: 22rpx; color: #007aff; background: #e8f2ff; border-radius: 20rpx; padding: 4rpx 14rpx; }
.favorite-btn { margin: 0; font-size: 24rpx; color: #fff; background: #ff9800; }
.domain { font-size: 24rpx; color: #4caf50; margin-bottom: 10rpx; }
.company-enrichment { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 12rpx; margin: 10rpx 0 14rpx; }
.alias-row { display: flex; flex-wrap: wrap; gap: 12rpx; color: #334155; font-size: 23rpx; line-height: 1.6; }
.domain-checks { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 8rpx; }
.domain-check { color: #475569; background: #eef2f7; font-size: 21rpx; padding: 5rpx 10rpx; border-radius: 8rpx; }
.brand-warning { margin-top: 8rpx; color: #8a5a00; background: #fff8e1; border-radius: 8rpx; padding: 8rpx; font-size: 22rpx; line-height: 1.5; }
.score-panel { background: #f7fbff; border: 1px solid #e0efff; border-radius: 12rpx; padding: 18rpx; margin: 14rpx 0; }
.score-head { display: flex; align-items: baseline; gap: 10rpx; margin-bottom: 14rpx; }
.score-total { font-size: 40rpx; font-weight: 800; color: #1677ff; }
.score-unit { font-size: 24rpx; color: #4b6b8a; }
.score-grid { display: flex; gap: 10rpx; }
.score-item { flex: 1; min-width: 0; background: #fff; border-radius: 8rpx; padding: 10rpx 6rpx; text-align: center; }
.score-label { display: block; font-size: 22rpx; color: #667085; }
.score-value { display: block; font-size: 28rpx; font-weight: 700; color: #222; margin-top: 4rpx; }
.score-explain { color: #52677a; font-size: 24rpx; line-height: 1.6; margin-top: 14rpx; }
.detail { font-size: 26rpx; color: #555; line-height: 1.7; margin-top: 6rpx; }
.label { color: #222; font-weight: 600; }
.meta { color: #999; font-size: 22rpx; margin-top: 14rpx; }
.actions { display: flex; gap: 16rpx; margin-top: 18rpx; }
.continue-btn { flex: 1; margin: 0; color: #fff; background: #007aff; }
.export-btn { width: 130rpx; margin: 0; color: #fff; background: #2e7d32; }
.delete-btn { width: 150rpx; margin: 0; color: #fff; background: #f44336; }
.load-more { margin-top: 24rpx; background: #fff; color: #007aff; }
</style>
