<template>
  <view class="page">
    <view class="header">
      <view class="avatar">{{ avatarText }}</view>
      <view class="identity">
        <view class="username">{{ profile.username || '未登录用户' }}</view>
        <view class="email">{{ profile.email || '请先登录' }}</view>
      </view>
      <text v-if="profile.is_admin" class="role">管理员</text>
    </view>

    <view class="section">
      <view class="section-title">账号信息</view>
      <view class="field readonly">
        <text class="label">邮箱</text>
        <text class="value">{{ profile.email || '-' }}</text>
      </view>
      <view class="field readonly">
        <text class="label">用户 ID</text>
        <text class="value">{{ profile.id || '-' }}</text>
      </view>
      <view class="field">
        <text class="label">用户名</text>
        <input class="input" v-model="profileForm.username" placeholder="请输入用户名" />
      </view>
      <button class="primary-btn" :loading="savingProfile" @click="saveProfile">保存资料</button>
    </view>

    <view class="section">
      <view class="section-title">修改密码</view>
      <input class="password-input" v-model="passwordForm.old_password" type="password" placeholder="当前密码" />
      <input class="password-input" v-model="passwordForm.new_password" type="password" placeholder="新密码" />
      <input class="password-input" v-model="passwordForm.confirm_password" type="password" placeholder="确认新密码" />
      <button class="primary-btn password-btn" :loading="savingPassword" @click="changePassword">更新密码</button>
    </view>

    <view class="section">
      <view class="section-title">邮箱换绑</view>
      <input class="password-input" v-model="emailForm.new_email" placeholder="新邮箱" />
      <view class="code-row">
        <input class="code-input" v-model="emailForm.code" placeholder="验证码" />
        <button class="code-btn" size="mini" :loading="sendingEmailCode" @click="sendEmailCode">获取验证码</button>
      </view>
      <input class="password-input" v-model="emailForm.password" type="password" placeholder="当前密码" />
      <button class="primary-btn" :loading="savingEmail" @click="changeEmail">确认换绑</button>
    </view>

    <view class="section">
      <view class="section-title">最近登录</view>
      <view v-for="item in loginRecords" :key="item.id" class="login-record">
        <view class="record-main">
          <text>{{ item.success ? '登录成功' : '登录失败' }}</text>
          <text>{{ formatTime(item.created_time) }}</text>
        </view>
        <view class="record-meta">{{ item.ip_address || '-' }} · {{ item.user_agent || '-' }}</view>
        <view v-if="item.failure_reason" class="record-error">{{ item.failure_reason }}</view>
      </view>
      <view v-if="!loginRecords.length" class="empty-record">暂无登录记录</view>
    </view>

    <view class="section actions">
      <button class="ghost-btn" @click="refreshProfile">刷新资料</button>
      <button class="danger-btn" @click="logout">退出登录</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const profile = ref({});
const profileForm = ref({ username: '' });
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
});
const savingProfile = ref(false);
const savingPassword = ref(false);
const savingEmail = ref(false);
const sendingEmailCode = ref(false);
const emailForm = ref({
  new_email: '',
  code: '',
  password: ''
});
const loginRecords = ref([]);

const avatarText = computed(() => {
  const name = profile.value.username || profile.value.email || '我';
  return String(name).slice(0, 1).toUpperCase();
});

onShow(() => {
  loadCachedUser();
  refreshProfile();
  refreshLoginRecords();
});

const loadCachedUser = () => {
  const cachedUser = uni.getStorageSync('user');
  if (cachedUser) {
    profile.value = cachedUser;
    profileForm.value.username = cachedUser.username || '';
  }
};

const requireLogin = () => {
  const token = uni.getStorageSync('token');
  if (token) return true;
  uni.showToast({ title: '请先登录', icon: 'none' });
  setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 500);
  return false;
};

const refreshProfile = async () => {
  if (!requireLogin()) return;
  try {
    const user = await http.getProfile();
    profile.value = user;
    profileForm.value.username = user.username || '';
    uni.setStorageSync('user', user);
  } catch (error) {
    console.error('刷新个人资料失败', error);
  }
};

const refreshLoginRecords = async () => {
  if (!uni.getStorageSync('token')) return;
  try {
    loginRecords.value = await http.getLoginRecords({ limit: 10 });
  } catch (error) {
    console.error('鍔犺浇鐧诲綍璁板綍澶辫触', error);
  }
};

const saveProfile = async () => {
  if (!requireLogin()) return;
  const username = profileForm.value.username.trim();
  if (!username) {
    return uni.showToast({ title: '请输入用户名', icon: 'none' });
  }

  savingProfile.value = true;
  try {
    const user = await http.updateProfile({ username });
    profile.value = user;
    profileForm.value.username = user.username || '';
    uni.setStorageSync('user', user);
    uni.showToast({ title: '资料已保存', icon: 'success' });
  } catch (error) {
    console.error('保存个人资料失败', error);
  } finally {
    savingProfile.value = false;
  }
};

const changePassword = async () => {
  if (!requireLogin()) return;
  const data = {
    old_password: passwordForm.value.old_password,
    new_password: passwordForm.value.new_password,
    confirm_password: passwordForm.value.confirm_password
  };

  if (!data.old_password || !data.new_password || !data.confirm_password) {
    return uni.showToast({ title: '请填写完整密码信息', icon: 'none' });
  }
  if (data.new_password !== data.confirm_password) {
    return uni.showToast({ title: '两次新密码不一致', icon: 'none' });
  }

  savingPassword.value = true;
  try {
    await http.changePassword(data);
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' };
    uni.showToast({ title: '密码已更新', icon: 'success' });
  } catch (error) {
    console.error('修改密码失败', error);
  } finally {
    savingPassword.value = false;
  }
};

const sendEmailCode = async () => {
  if (!requireLogin()) return;
  const email = emailForm.value.new_email.trim();
  if (!email) return uni.showToast({ title: '请输入新邮箱', icon: 'none' });
  sendingEmailCode.value = true;
  try {
    await http.getEmailCode(email);
    uni.showToast({ title: '验证码已发送', icon: 'none' });
  } catch (error) {
    console.error(error);
  } finally {
    sendingEmailCode.value = false;
  }
};

const changeEmail = async () => {
  if (!requireLogin()) return;
  const data = {
    new_email: emailForm.value.new_email.trim(),
    code: emailForm.value.code,
    password: emailForm.value.password
  };
  if (!data.new_email || !data.code || !data.password) {
    return uni.showToast({ title: '请填写完整', icon: 'none' });
  }
  savingEmail.value = true;
  try {
    const user = await http.changeEmail(data);
    profile.value = user;
    uni.setStorageSync('user', user);
    emailForm.value = { new_email: '', code: '', password: '' };
    uni.showToast({ title: '邮箱已换绑', icon: 'success' });
  } catch (error) {
    console.error(error);
  } finally {
    savingEmail.value = false;
  }
};

const logout = () => {
  uni.showModal({
    title: '退出登录',
    content: '确定退出当前账号吗？',
    success: (res) => {
      if (!res.confirm) return;
      uni.removeStorageSync('token');
      uni.removeStorageSync('user');
      uni.reLaunch({ url: '/pages/login/login' });
    }
  });
};

const formatTime = (value) => (value ? String(value).replace('T', ' ').slice(0, 19) : '');
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.header { display: flex; align-items: center; gap: 22rpx; padding: 28rpx; margin-bottom: 24rpx; background: #fff; border-radius: 14rpx; }
.avatar { width: 92rpx; height: 92rpx; line-height: 92rpx; text-align: center; border-radius: 50%; color: #fff; background: #1677ff; font-size: 40rpx; font-weight: 700; }
.identity { flex: 1; min-width: 0; }
.username { color: #202124; font-size: 34rpx; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.email { margin-top: 8rpx; color: #667085; font-size: 24rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.role { flex-shrink: 0; padding: 6rpx 14rpx; border-radius: 8rpx; color: #8a5a00; background: #fff4d6; font-size: 22rpx; }
.section { padding: 26rpx; margin-bottom: 24rpx; background: #fff; border-radius: 14rpx; }
.section-title { margin-bottom: 18rpx; color: #202124; font-size: 30rpx; font-weight: 700; }
.field { display: flex; align-items: center; min-height: 86rpx; border-bottom: 1px solid #eef0f3; }
.field:last-of-type { border-bottom: none; }
.label { width: 150rpx; color: #667085; font-size: 26rpx; }
.value { flex: 1; color: #202124; font-size: 26rpx; text-align: right; word-break: break-all; }
.input { flex: 1; height: 72rpx; text-align: right; color: #202124; font-size: 28rpx; }
.password-input { height: 82rpx; padding: 0 20rpx; margin-bottom: 18rpx; background: #f7f8fa; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.code-row { display: flex; gap: 14rpx; align-items: center; margin-bottom: 18rpx; }
.code-input { flex: 1; height: 82rpx; padding: 0 20rpx; background: #f7f8fa; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.code-btn { width: 180rpx; height: 72rpx; line-height: 72rpx; padding: 0; color: #fff; background: #16213e; border-radius: 8rpx; font-size: 24rpx; }
.login-record { padding: 16rpx 0; border-bottom: 1px solid #eef0f3; }
.login-record:last-child { border-bottom: none; }
.record-main { display: flex; justify-content: space-between; gap: 16rpx; color: #202124; font-size: 26rpx; line-height: 36rpx; }
.record-meta { margin-top: 6rpx; color: #667085; font-size: 22rpx; line-height: 32rpx; word-break: break-all; }
.record-error { margin-top: 6rpx; color: #d93026; font-size: 22rpx; line-height: 32rpx; }
.empty-record { padding: 28rpx 0; color: #9ca3af; text-align: center; font-size: 24rpx; }
.primary-btn { margin-top: 24rpx; color: #fff; background: #1677ff; border-radius: 8rpx; }
.password-btn { background: #2e7d32; }
.actions { display: flex; gap: 18rpx; background: transparent; padding: 0; }
.ghost-btn, .danger-btn { flex: 1; margin: 0; border-radius: 8rpx; font-size: 28rpx; }
.ghost-btn { color: #1677ff; background: #fff; }
.danger-btn { color: #fff; background: #f04438; }
</style>
