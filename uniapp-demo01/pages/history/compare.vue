<template>
  <view class="page">
    <view v-if="loading" class="loading">正在生成对比...</view>

    <view v-else-if="result" class="content">
      <view class="recommend-box">
        <view class="section-title">推荐结论</view>
        <view class="recommend-text">{{ result.recommendation }}</view>
      </view>

      <view class="section">
        <view class="section-title">推荐排序</view>
        <view v-for="item in result.ranking" :key="item.history_id" class="rank-card">
          <view class="rank-main">
            <text class="rank-no">No.{{ item.rank }}</text>
            <text class="rank-name">{{ item.name }}</text>
            <text class="rank-score">{{ item.compare_score }}分</text>
          </view>
          <view class="rank-reason">{{ item.reason }}</view>
        </view>
      </view>

      <view class="section">
        <view class="section-title">分项对比</view>
        <scroll-view scroll-x class="table-scroll">
          <view class="compare-table">
            <view class="table-row header">
              <view class="table-cell first">项目</view>
              <view v-for="item in result.items" :key="item.history_id" class="table-cell name-cell">
                {{ item.name }}
              </view>
            </view>
            <view class="table-row" v-for="row in compareRows" :key="row.key">
              <view class="table-cell first">{{ row.label }}</view>
              <view v-for="item in result.items" :key="item.history_id" class="table-cell">
                {{ row.value(item) }}
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="section">
        <view class="section-title">适用场景</view>
        <view v-for="item in result.items" :key="item.history_id" class="scene-card">
          <view class="scene-name">{{ item.name }}</view>
          <view v-for="scene in item.suitable_scenes" :key="scene" class="scene-line">{{ scene }}</view>
          <view class="tag-row">
            <text v-for="tag in item.strengths" :key="tag" class="tag strength">{{ tag }}</text>
            <text v-for="tag in item.tradeoffs" :key="tag" class="tag tradeoff">{{ tag }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const loading = ref(false);
const result = ref(null);

const compareRows = computed(() => [
  { key: 'moral', label: '寓意', value: (item) => item.moral || '-' },
  { key: 'rhythm', label: '音律', value: (item) => `${item.rhythm_score || 0}分` },
  { key: 'meaning', label: '寓意评分', value: (item) => `${item.meaning_score || 0}分` },
  { key: 'spread', label: '传播性', value: (item) => `${item.spread_score || 0}分` },
  { key: 'domain', label: '域名状态', value: (item) => formatDomain(item) },
  { key: 'score', label: '对比得分', value: (item) => `${item.compare_score || 0}分` }
]);

onLoad(async (query) => {
  const ids = String(query.ids || '')
    .split(',')
    .map((id) => Number(id))
    .filter((id) => Number.isInteger(id) && id > 0);

  if (ids.length < 2) {
    uni.showToast({ title: '请至少选择 2 个名字', icon: 'none' });
    return;
  }

  loading.value = true;
  try {
    result.value = await http.compareHistory(ids);
  } finally {
    loading.value = false;
  }
});

const formatDomain = (item) => {
  if (!item.domain) return item.domain_status || '-';
  return item.domain_status ? `${item.domain}（${item.domain_status}）` : item.domain;
};
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.loading { padding: 120rpx 0; text-align: center; color: #667085; font-size: 28rpx; }
.recommend-box, .section { background: #fff; border-radius: 14rpx; padding: 26rpx; margin-bottom: 22rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.section-title { font-size: 30rpx; font-weight: 700; color: #222; margin-bottom: 18rpx; }
.recommend-text { color: #1d4f91; background: #eef6ff; border-radius: 10rpx; padding: 18rpx; font-size: 28rpx; line-height: 1.7; }
.rank-card { padding: 18rpx 0; border-bottom: 1px solid #edf0f5; }
.rank-card:last-child { border-bottom: 0; }
.rank-main { display: flex; align-items: center; gap: 16rpx; }
.rank-no { color: #1677ff; font-size: 24rpx; font-weight: 700; }
.rank-name { flex: 1; min-width: 0; color: #222; font-size: 34rpx; font-weight: 700; }
.rank-score { color: #ff8a00; font-size: 26rpx; font-weight: 700; }
.rank-reason { margin-top: 10rpx; color: #52677a; font-size: 25rpx; line-height: 1.6; }
.table-scroll { width: 100%; }
.compare-table { min-width: 980rpx; border: 1px solid #e6ebf2; border-radius: 10rpx; overflow: hidden; }
.table-row { display: flex; border-bottom: 1px solid #e6ebf2; }
.table-row:last-child { border-bottom: 0; }
.table-row.header { background: #f7fbff; font-weight: 700; color: #22354a; }
.table-cell { flex: 0 0 260rpx; width: 260rpx; padding: 16rpx; box-sizing: border-box; color: #44576d; font-size: 24rpx; line-height: 1.55; border-right: 1px solid #e6ebf2; word-break: break-all; }
.table-cell:last-child { border-right: 0; }
.table-cell.first { flex-basis: 160rpx; width: 160rpx; color: #222; font-weight: 700; background: #fbfcfe; }
.name-cell { color: #1677ff; font-size: 26rpx; }
.scene-card { padding: 18rpx 0; border-bottom: 1px solid #edf0f5; }
.scene-card:last-child { border-bottom: 0; }
.scene-name { color: #222; font-size: 32rpx; font-weight: 700; margin-bottom: 10rpx; }
.scene-line { color: #52677a; font-size: 25rpx; line-height: 1.7; }
.tag-row { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 14rpx; }
.tag { padding: 6rpx 12rpx; border-radius: 8rpx; font-size: 22rpx; }
.tag.strength { color: #1677ff; background: #eaf4ff; }
.tag.tradeoff { color: #9a5a00; background: #fff4df; }
</style>
