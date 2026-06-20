<script setup>
import { onLaunch } from '@dcloudio/uni-app';

onLaunch(() => {
  // 1. 应用启动时，从本地缓存中读取身份凭证 (token)
  const token = uni.getStorageSync('token');
  
  // 2. 如果不存在 token，说明未登录，强行拦截并跳转到登录页
  if (!token) {
    uni.reLaunch({
      url: '/pages/login/login'
    });
  }
});
</script>

<style>
/* 每个页面公共css，这里暂不填 */
</style>