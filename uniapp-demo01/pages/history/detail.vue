<template>
  <view class="page">
    <view v-if="detail" class="history-card">
      <view class="card-head">
        <view>
          <text class="name">{{ detail.name }}</text>
          <text class="category">{{ detail.category }}</text>
        </view>
        <button class="favorite-btn" size="mini" @click="toggleFavorite(detail)">
          {{ detail.is_favorite ? '已收藏' : '收藏' }}
        </button>
      </view>

      <view v-if="detail.domain" class="domain">{{ formatDomain(detail) }}</view>
      <view v-if="hasCompanyEnrichment(detail)" class="company-enrichment">
        <view class="alias-row" v-if="detail.pinyin || detail.english_name || detail.abbreviation">
          <text v-if="detail.pinyin">拼音：{{ detail.pinyin }}</text>
          <text v-if="detail.english_name">英文：{{ detail.english_name }}</text>
          <text v-if="detail.abbreviation">简称：{{ detail.abbreviation }}</text>
        </view>
        <view v-if="detail.domain_checks && detail.domain_checks.length" class="domain-checks">
          <text v-for="check in detail.domain_checks" :key="check.domain" class="domain-check">{{ check.domain }} {{ check.status }}</text>
        </view>
        <view v-if="detail.brand_warning" class="brand-warning">{{ detail.brand_warning }}</view>
      </view>
      <view class="score-panel" v-if="detail.score_total">
        <view class="score-head">
          <text class="score-total">{{ detail.score_total }}</text>
          <text class="score-unit">综合评分</text>
        </view>
        <view class="score-grid">
          <view class="score-item" v-for="metric in scoreMetrics(detail)" :key="metric.label">
            <text class="score-label">{{ metric.label }}</text>
            <text class="score-value">{{ metric.value }}</text>
          </view>
        </view>
        <view v-if="detail.score_explanation" class="score-explain">{{ detail.score_explanation }}</view>
      </view>
      <view class="detail"><text class="label">出处：</text>{{ detail.reference }}</view>
      <view class="detail"><text class="label">寓意：</text>{{ detail.moral }}</view>
      <view class="preference-actions">
        <button class="preference-btn primary" size="mini" :disabled="loading" @click="regenerateWithPreference(detail, 'direction')">保留这个方向</button>
        <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(detail, 'style')">保留风格</button>
        <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(detail, 'chars')">保留用字</button>
        <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(detail, 'meaning')">保留寓意</button>
      </view>
      <button class="export-btn" size="mini" @click="exportCurrent(detail)">导出方案</button>
      <view class="memory-tip">将沿用这条记录所属会话的 LangGraph thread_id 继续修改。</view>
    </view>

    <view class="feedback-box">
      <view class="section-title">继续基于历史修改</view>
      <textarea
        class="textarea-box"
        v-model="feedbackText"
        placeholder="输入新的修改意见，例如：保留这个名字的风格，换成更适合科技公司的方案"
      ></textarea>
      <button class="btn-primary" :loading="loading" @click="continueFeedback">继续生成</button>
    </view>

    <view v-if="names.length > 0" class="result-box">
      <view class="section-title">新的修改结果</view>
      <view class="name-card" v-for="(item, index) in names" :key="item.history_id || index">
        <view class="card-head">
          <text class="name">{{ item.name }}</text>
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
        <view class="preference-actions">
          <button class="preference-btn primary" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'direction')">保留这个方向</button>
          <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'style')">保留风格</button>
          <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'chars')">保留用字</button>
          <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'meaning')">保留寓意</button>
        </view>
        <button class="export-btn" size="mini" @click="exportCurrent(item)">导出方案</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import { chooseAndExportReport } from '@/utils/reportExport.js';

const historyId = ref('');
const detail = ref(null);
const feedbackText = ref('');
const names = ref([]);
const loading = ref(false);

onLoad(async (query) => {
  historyId.value = query.id || '';
  if (!historyId.value) {
    uni.showToast({ title: '缺少历史记录ID', icon: 'none' });
    return;
  }
  await loadDetail();
});

const loadDetail = async () => {
  detail.value = await http.getHistoryDetail(historyId.value);
};

const buildPreferenceFeedback = (item, type = 'direction') => {
  const name = item?.name || '这个名字';
  const moral = String(item?.moral || '').trim();
  const reference = String(item?.reference || '').trim();
  const category = item?.category || detail.value?.category || '名字';
  const base = `我喜欢“${name}”`;

  const prompts = {
    direction: `${base}这个方向。请保留它的整体风格、核心用字感觉和寓意气质，重新生成一组同类候选，不要简单重复原名。`,
    style: `${base}的风格。请延续这种${category}命名风格和气质，重新生成一组同类候选，不要简单重复原名。`,
    chars: `${base}的用字感觉。请优先保留相近的字形、字音、关键字或意象，重新生成一组同类候选，不要简单重复原名。`,
    meaning: `${base}的寓意${moral ? `：“${moral}”` : ''}。请围绕相近寓意重新生成一组同类候选，不要简单重复原名。`
  };

  return reference
    ? `${prompts[type] || prompts.direction} 可参考原出处/说明：“${reference}”。`
    : (prompts[type] || prompts.direction);
};

const submitFeedback = async (feedback, successTitle = '已基于历史生成') => {
  if (!detail.value) return;
  const text = String(feedback || '').trim();
  if (!text) {
    return uni.showToast({ title: '请输入修改意见', icon: 'none' });
  }

  loading.value = true;
  uni.showLoading({ title: '基于历史生成中...' });
  try {
    const res = await http.feedbackName({
      thread_id: detail.value.thread_id,
      project_id: detail.value.project_id,
      category: detail.value.category,
      feedback: text
    });
    names.value = res.names;
    feedbackText.value = '';
    uni.showToast({ title: successTitle, icon: 'success' });
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};

const continueFeedback = async () => {
  await submitFeedback(feedbackText.value);
};

const regenerateWithPreference = async (item, type) => {
  await submitFeedback(buildPreferenceFeedback(item, type), '已按偏好生成');
};

const toggleFavorite = async (item) => {
  const id = item.history_id || item.id;
  if (!id) return;
  const updated = await http.setHistoryFavorite(id, !item.is_favorite);
  item.is_favorite = updated.is_favorite;
  if (detail.value && detail.value.id === updated.id) {
    detail.value.is_favorite = updated.is_favorite;
  }
};

const exportCurrent = (item) => {
  chooseAndExportReport(item.history_id || item.id, item.name);
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
.history-card, .feedback-box, .name-card { background: #fff; border-radius: 14rpx; padding: 26rpx; margin-bottom: 22rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.card-head { display: flex; justify-content: space-between; gap: 20rpx; align-items: center; margin-bottom: 12rpx; }
.name { font-size: 40rpx; font-weight: 700; color: #222; margin-right: 16rpx; }
.category { font-size: 22rpx; color: #007aff; background: #e8f2ff; border-radius: 20rpx; padding: 4rpx 14rpx; }
.favorite-btn { margin: 0; font-size: 24rpx; color: #fff; background: #ff9800; }
.export-btn { margin: 18rpx 0 0; font-size: 24rpx; color: #fff; background: #2e7d32; }
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
.preference-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12rpx; margin-top: 18rpx; }
.preference-btn { margin: 0; color: #1677ff; background: #f7fbff; font-size: 24rpx; border-radius: 8rpx; }
.preference-btn.primary { color: #fff; background: #1677ff; }
.memory-tip { margin-top: 18rpx; padding: 16rpx; background: #e8f2ff; color: #1b64b0; border-radius: 10rpx; font-size: 24rpx; }
.section-title { font-size: 30rpx; font-weight: 700; color: #222; margin-bottom: 16rpx; }
.textarea-box { width: 100%; height: 180rpx; background: #f9f9f9; padding: 20rpx; box-sizing: border-box; border-radius: 8rpx; font-size: 28rpx; }
.btn-primary { background: #007aff; color: #fff; border-radius: 50rpx; margin-top: 22rpx; }
.result-box { margin-top: 28rpx; }
</style>
