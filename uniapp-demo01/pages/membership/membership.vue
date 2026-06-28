<template>
  <view class="page">
    <view class="account">
      <view>
        <view class="account-title">{{ account.plan_name || '免费版' }}</view>
        <view class="account-sub">当前可用额度</view>
      </view>
      <view class="balance">{{ account.credit_balance || 0 }}</view>
    </view>

    <view class="summary">
      <view class="summary-item">
        <text class="summary-value">{{ account.total_recharged || 0 }}</text>
        <text class="summary-label">累计获得</text>
      </view>
      <view class="summary-item">
        <text class="summary-value">{{ account.total_consumed || 0 }}</text>
        <text class="summary-label">累计消耗</text>
      </view>
      <view class="summary-item">
        <text class="summary-value">{{ expiresText }}</text>
        <text class="summary-label">有效期</text>
      </view>
    </view>

    <view class="section">
      <view class="section-title">套餐充值</view>
      <view v-for="plan in plans" :key="plan.id" class="plan">
        <view class="plan-main">
          <view class="plan-name">{{ plan.name }}</view>
          <view class="plan-desc">{{ plan.description }}</view>
          <view class="plan-meta">{{ plan.credits }} 次额度</view>
        </view>
        <view class="plan-side">
          <view class="price">¥{{ formatPrice(plan.price_cents) }}</view>
          <button class="buy-btn" size="mini" :loading="rechargingId === plan.id" @click="recharge(plan)">充值</button>
        </view>
      </view>
      <view v-if="!plans.length && !loading" class="empty">暂无可用套餐</view>
    </view>

    <view class="section">
      <view class="section-head">
        <view class="section-title">额度流水</view>
        <button class="refresh-btn" size="mini" :loading="loading" @click="refreshAll">刷新</button>
      </view>
      <view v-for="item in transactions" :key="item.id" class="tx">
        <view>
          <view class="tx-title">{{ transactionText(item) }}</view>
          <view class="tx-time">{{ formatTime(item.created_time) }}</view>
        </view>
        <view :class="['tx-amount', item.change_amount > 0 ? 'plus' : 'minus']">
          {{ item.change_amount > 0 ? '+' : '' }}{{ item.change_amount }}
        </view>
      </view>
      <view v-if="!transactions.length && !loading" class="empty">暂无额度流水</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const account = ref({});
const plans = ref([]);
const transactions = ref([]);
const loading = ref(false);
const rechargingId = ref(0);
const pendingOrderId = ref(uni.getStorageSync('pending_alipay_order_id') || 0);

const expiresText = computed(() => {
  if (!account.value.expires_at) return '长期';
  return formatTime(account.value.expires_at).slice(0, 10);
});

const requireLogin = () => {
  const token = uni.getStorageSync('token');
  if (token) return true;
  uni.showToast({ title: '请先登录', icon: 'none' });
  setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 500);
  return false;
};

const refreshAll = async () => {
  if (!requireLogin()) return;
  loading.value = true;
  try {
    const [accountRes, planRes, txRes] = await Promise.all([
      http.getMembership(),
      http.getMembershipPlans(),
      http.getCreditTransactions({ limit: 30, offset: 0 })
    ]);
    account.value = accountRes;
    plans.value = planRes || [];
    transactions.value = txRes.items || [];
    await syncPendingAlipayOrder();
  } catch (error) {
    console.error('加载会员信息失败', error);
  } finally {
    loading.value = false;
  }
};

const recharge = async (plan) => {
  rechargingId.value = plan.id;
  try {
    const order = await http.rechargeMembership(plan.id, getPayScene());
    const payload = parsePaymentPayload(order.payment_payload);
    if (!payload.checkout_url) {
      uni.showToast({ title: 'Payment link failed', icon: 'none' });
      return;
    }
    pendingOrderId.value = order.id;
    uni.setStorageSync('pending_alipay_order_id', order.id);
    openAlipayCheckout(payload.checkout_url);
  } catch (error) {
    console.error('充值失败', error);
  } finally {
    rechargingId.value = 0;
  }
};

const syncPendingAlipayOrder = async () => {
  const orderId = pendingOrderId.value || uni.getStorageSync('pending_alipay_order_id');
  if (!orderId) return;

  let order = await http.getRechargeOrder(orderId);
  if (order.status === 'pending' || order.status === 'processing') {
    order = await http.alipayQueryRechargeOrder(orderId);
  }

  if (order.status === 'paid' || order.status === 'failed' || order.status === 'refunded') {
    pendingOrderId.value = 0;
    uni.removeStorageSync('pending_alipay_order_id');
    if (order.status === 'paid') {
      const [accountRes, txRes] = await Promise.all([
        http.getMembership(),
        http.getCreditTransactions({ limit: 30, offset: 0 })
      ]);
      account.value = accountRes;
      transactions.value = txRes.items || [];
      uni.showToast({ title: 'Paid', icon: 'success' });
    }
  }
};

const parsePaymentPayload = (value) => {
  if (!value) return {};
  if (typeof value === 'object') return value;
  try {
    return JSON.parse(value);
  } catch (error) {
    return {};
  }
};

const getPayScene = () => {
  const platform = String(uni.getSystemInfoSync().platform || '').toLowerCase();
  return platform === 'ios' || platform === 'android' ? 'wap' : 'page';
};

const openAlipayCheckout = (url) => {
  // #ifdef H5
  window.location.href = url;
  // #endif
  // #ifndef H5
  if (typeof plus !== 'undefined' && plus.runtime) {
    plus.runtime.openURL(url);
  } else {
    uni.showModal({ title: 'Alipay link', content: url, showCancel: false });
  }
  // #endif
};

const formatPrice = (cents = 0) => (Number(cents || 0) / 100).toFixed(2);
const formatTime = (value) => (value ? String(value).replace('T', ' ').slice(0, 19) : '');
const transactionText = (item) => item.remark || item.transaction_type || '额度变动';

onShow(refreshAll);
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.account { display: flex; align-items: center; justify-content: space-between; padding: 34rpx; margin-bottom: 18rpx; background: #16213e; border-radius: 8rpx; color: #fff; }
.account-title { font-size: 34rpx; font-weight: 700; line-height: 44rpx; }
.account-sub { margin-top: 8rpx; font-size: 24rpx; color: rgba(255,255,255,0.72); }
.balance { font-size: 56rpx; line-height: 64rpx; font-weight: 800; }
.summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-bottom: 22rpx; }
.summary-item { min-width: 0; padding: 20rpx 10rpx; background: #fff; border-radius: 8rpx; text-align: center; }
.summary-value { display: block; font-size: 30rpx; line-height: 38rpx; font-weight: 700; color: #202124; }
.summary-label { display: block; margin-top: 6rpx; font-size: 22rpx; color: #6b7280; }
.section { padding: 24rpx; margin-bottom: 22rpx; background: #fff; border-radius: 8rpx; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }
.section-title { margin-bottom: 18rpx; font-size: 30rpx; line-height: 38rpx; font-weight: 700; color: #202124; }
.refresh-btn { margin: 0 0 18rpx; color: #1677ff; background: #eef6ff; }
.plan { display: flex; gap: 18rpx; padding: 22rpx 0; border-top: 1px solid #eef0f3; }
.plan:first-of-type { border-top: none; }
.plan-main { flex: 1; min-width: 0; }
.plan-name { font-size: 30rpx; line-height: 40rpx; font-weight: 700; color: #202124; }
.plan-desc { margin-top: 8rpx; font-size: 24rpx; line-height: 34rpx; color: #667085; }
.plan-meta { margin-top: 10rpx; font-size: 24rpx; line-height: 32rpx; color: #1677ff; }
.plan-side { width: 150rpx; text-align: right; }
.price { margin-bottom: 12rpx; font-size: 30rpx; line-height: 38rpx; font-weight: 800; color: #f04438; }
.buy-btn { margin: 0; width: 140rpx; color: #fff; background: #1677ff; border-radius: 8rpx; }
.tx { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; padding: 18rpx 0; border-top: 1px solid #eef0f3; }
.tx:first-of-type { border-top: none; }
.tx-title { font-size: 26rpx; line-height: 36rpx; color: #202124; }
.tx-time { margin-top: 6rpx; font-size: 22rpx; line-height: 30rpx; color: #8a94a6; }
.tx-amount { flex: none; font-size: 30rpx; line-height: 38rpx; font-weight: 800; }
.tx-amount.plus { color: #2e7d32; }
.tx-amount.minus { color: #d93026; }
.empty { padding: 50rpx 0; text-align: center; color: #9ca3af; font-size: 26rpx; }
</style>
