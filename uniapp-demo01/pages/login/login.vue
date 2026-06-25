<template>
  <view class="container">
    <view class="title">AI &#x667A;&#x80FD;&#x8D77;&#x540D;</view>

    <view class="api-card">
      <view class="api-head">
        <text class="api-title">后端地址</text>
        <button class="api-small" size="mini" @click="resetApiUrl">默认</button>
      </view>
      <input class="api-input" v-model="apiBaseUrl" placeholder="例如 http://192.168.1.10:8000" />
      <button class="api-test" size="mini" :loading="testingApi" @click="testApiUrl">测试连接</button>
    </view>

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
    <view class="link secondary" @click="showReset = !showReset">忘记密码</view>

    <view v-if="showReset" class="reset-card">
      <input class="input-box" v-model="resetForm.email" placeholder="邮箱" />
      <view class="code-row">
        <input class="code-input" v-model="resetForm.code" placeholder="验证码" />
        <button class="code-btn" size="mini" :loading="sendingCode" @click="sendResetCode">获取验证码</button>
      </view>
      <input class="input-box" v-model="resetForm.new_password" type="password" placeholder="新密码" />
      <input class="input-box" v-model="resetForm.confirm_password" type="password" placeholder="确认新密码" />
      <button class="btn reset-btn" :loading="resettingPassword" @click="resetPassword">重置密码</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import http from '@/http/http.js';

const form = ref({ email: '', password: '' });
const loading = ref(false);
const adminMode = ref(false);
const apiBaseUrl = ref(http.getBaseUrl());
const testingApi = ref(false);
const showReset = ref(false);
const sendingCode = ref(false);
const resettingPassword = ref(false);
const resetForm = ref({
  email: '',
  code: '',
  new_password: '',
  confirm_password: ''
});

const emailPlaceholder = '\u8bf7\u8f93\u5165\u90ae\u7bb1';
const passwordPlaceholder = '\u8bf7\u8f93\u5165\u5bc6\u7801';
const userLoginText = '\u767b\u5f55';
const adminLoginText = '\u7ba1\u7406\u5458\u767b\u5f55';
const adminRequiredText = '\u8be5\u8d26\u53f7\u4e0d\u662f\u7ba1\u7406\u5458';
const incompleteText = '\u8bf7\u586b\u5199\u5b8c\u6574';
const successText = '\u767b\u5f55\u6210\u529f';

const targetUrl = computed(() => (adminMode.value ? '/pages/admin/admin' : '/pages/index/index'));

const saveApiUrl = () => {
  const value = apiBaseUrl.value.trim();
  if (!value) {
    http.resetBaseUrl();
    apiBaseUrl.value = http.getBaseUrl();
    return;
  }
  http.setBaseUrl(value);
  apiBaseUrl.value = http.getBaseUrl();
};

const resetApiUrl = () => {
  http.resetBaseUrl();
  apiBaseUrl.value = http.getBaseUrl();
  uni.showToast({ title: '已恢复默认地址', icon: 'none' });
};

const testApiUrl = async () => {
  saveApiUrl();
  testingApi.value = true;
  try {
    await http.testConnection();
    uni.showToast({ title: '后端连接正常', icon: 'success' });
  } catch (error) {
    console.error('后端连接失败', error);
  } finally {
    testingApi.value = false;
  }
};

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) {
    return uni.showToast({ title: incompleteText, icon: 'none' });
  }

  loading.value = true;
  try {
    saveApiUrl();
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

const sendResetCode = async () => {
  const email = resetForm.value.email.trim();
  if (!email) return uni.showToast({ title: '请输入邮箱', icon: 'none' });
  sendingCode.value = true;
  try {
    await http.getEmailCode(email);
    uni.showToast({ title: '验证码已发送', icon: 'none' });
  } catch (error) {
    console.error(error);
  } finally {
    sendingCode.value = false;
  }
};

const resetPassword = async () => {
  const data = { ...resetForm.value, email: resetForm.value.email.trim() };
  if (!data.email || !data.code || !data.new_password || !data.confirm_password) {
    return uni.showToast({ title: '请填写完整', icon: 'none' });
  }
  if (data.new_password !== data.confirm_password) {
    return uni.showToast({ title: '两次密码不一致', icon: 'none' });
  }
  resettingPassword.value = true;
  try {
    await http.resetPassword(data);
    resetForm.value = { email: data.email, code: '', new_password: '', confirm_password: '' };
    showReset.value = false;
    uni.showToast({ title: '密码已重置', icon: 'success' });
  } catch (error) {
    console.error(error);
  } finally {
    resettingPassword.value = false;
  }
};
</script>

<style scoped>
.container { padding: 40rpx; min-height: 100vh; background: #f5f7fa; box-sizing: border-box; }
.title { font-size: 48rpx; font-weight: bold; margin-bottom: 48rpx; text-align: center; color: #202124; }
.api-card { padding: 22rpx; margin-bottom: 26rpx; background: #fff; border-radius: 8rpx; }
.api-head { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; margin-bottom: 14rpx; }
.api-title { color: #202124; font-size: 28rpx; font-weight: 700; }
.api-small { margin: 0; color: #1677ff; background: #eef6ff; }
.api-input { height: 72rpx; padding: 0 18rpx; background: #f7f8fa; border-radius: 8rpx; font-size: 26rpx; box-sizing: border-box; }
.api-test { margin: 16rpx 0 0; color: #fff; background: #16213e; border-radius: 8rpx; }
.login-mode { display: flex; padding: 8rpx; margin-bottom: 36rpx; background: #fff; border-radius: 12rpx; }
.mode-item { flex: 1; height: 72rpx; line-height: 72rpx; text-align: center; border-radius: 8rpx; font-size: 28rpx; color: #606266; }
.mode-item.active { background: #1677ff; color: #fff; font-weight: 600; }
.input-box { height: 88rpx; padding: 0 24rpx; margin-bottom: 24rpx; background: #fff; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.btn { background-color: #007aff; color: white; border-radius: 8rpx; margin-top: 36rpx; }
.btn.admin { background-color: #1677ff; }
.tip { margin-top: 20rpx; text-align: center; color: #6b7280; font-size: 24rpx; }
.link { text-align: center; color: #007aff; margin-top: 28rpx; font-size: 28rpx; }
.link.secondary { color: #606266; margin-top: 18rpx; }
.reset-card { padding: 22rpx; margin-top: 24rpx; background: #fff; border-radius: 8rpx; }
.code-row { display: flex; gap: 14rpx; align-items: center; margin-bottom: 24rpx; }
.code-input { flex: 1; height: 88rpx; padding: 0 24rpx; background: #f7f8fa; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.code-btn { width: 180rpx; height: 72rpx; line-height: 72rpx; padding: 0; color: #fff; background: #16213e; border-radius: 8rpx; font-size: 24rpx; }
.reset-btn { margin-top: 10rpx; background: #2e7d32; }
</style>
