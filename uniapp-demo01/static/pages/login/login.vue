<template>
  <view class="container">
    <view class="title">AI &#x667A;&#x80FD;&#x8D77;&#x540D;</view>

    <view class="login-mode">
      <view :class="['mode-item', !adminMode ? 'active' : '']" @click="adminMode = false">
        &#x7528;&#x6237;&#x767B;&#x5F55;
      </view>
      <view :class="['mode-item', adminMode ? 'active' : '']" @click="adminMode = true">
        &#x7BA1;&#x7406;&#x5458;&#x767B;&#x5F55;
      </view>
    </view>

    <input class="input-box" v-model="form.email" :placeholder="emailPlaceholder" />
    <input class="input-box" v-model="form.password" type="password" :placeholder="passwordPlaceholder" />

    <button class="btn" :class="{ admin: adminMode }" :loading="loading" @click="handleLogin">
      {{ adminMode ? adminLoginText : userLoginText }}
    </button>

    <view v-if="adminMode" class="tip">
      &#x4EC5; is_admin=true &#x7684;&#x8D26;&#x53F7;&#x53EF;&#x8FDB;&#x5165;&#x540E;&#x53F0;
    </view>
    <view class="link" @click="goRegister">&#x6CA1;&#x6709;&#x8D26;&#x53F7;&#xFF1F;&#x53BB;&#x6CE8;&#x518C;</view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import http from '@/http/http.js';

const form = ref({ email: '', password: '' });
const loading = ref(false);
const adminMode = ref(false);

const emailPlaceholder = '\u8bf7\u8f93\u5165\u90ae\u7bb1';
const passwordPlaceholder = '\u8bf7\u8f93\u5165\u5bc6\u7801';
const userLoginText = '\u767b\u5f55';
const adminLoginText = '\u7ba1\u7406\u5458\u767b\u5f55';
const adminRequiredText = '\u8be5\u8d26\u53f7\u4e0d\u662f\u7ba1\u7406\u5458';
const incompleteText = '\u8bf7\u586b\u5199\u5b8c\u6574';
const successText = '\u767b\u5f55\u6210\u529f';

const targetUrl = computed(() => (adminMode.value ? '/pages/admin/admin' : '/pages/index/index'));

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) {
    return uni.showToast({ title: incompleteText, icon: 'none' });
  }

  loading.value = true;
  try {
    const res = await http.login(form.value);
    if (adminMode.value && !res.user?.is_admin) {
      uni.removeStorageSync('token');
      uni.removeStorageSync('user');
      return uni.showToast({ title: adminRequiredText, icon: 'none' });
    }

    uni.setStorageSync('token', res.token);
    uni.setStorageSync('user', res.user);
    uni.showToast({ title: successText });
    setTimeout(() => uni.reLaunch({ url: targetUrl.value }), 500);
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const goRegister = () => uni.navigateTo({ url: '/pages/register/register' });
</script>

<style scoped>
.container { padding: 40rpx; min-height: 100vh; background: #f5f7fa; box-sizing: border-box; }
.title { font-size: 48rpx; font-weight: bold; margin-bottom: 48rpx; text-align: center; color: #202124; }
.login-mode { display: flex; padding: 8rpx; margin-bottom: 36rpx; background: #fff; border-radius: 12rpx; }
.mode-item { flex: 1; height: 72rpx; line-height: 72rpx; text-align: center; border-radius: 8rpx; font-size: 28rpx; color: #606266; }
.mode-item.active { background: #1677ff; color: #fff; font-weight: 600; }
.input-box { height: 88rpx; padding: 0 24rpx; margin-bottom: 24rpx; background: #fff; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.btn { background-color: #007aff; color: white; border-radius: 8rpx; margin-top: 36rpx; }
.btn.admin { background-color: #1677ff; }
.tip { margin-top: 20rpx; text-align: center; color: #6b7280; font-size: 24rpx; }
.link { text-align: center; color: #007aff; margin-top: 28rpx; font-size: 28rpx; }
</style>
