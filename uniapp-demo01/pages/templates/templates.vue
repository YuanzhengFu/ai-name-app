<template>
  <view class="page">
    <view class="tabs">
      <view
        v-for="item in categories"
        :key="item"
        :class="['tab', activeCategory === item ? 'active' : '']"
        @click="switchCategory(item)"
      >
        {{ item }}
      </view>
    </view>

    <view class="toolbar">
      <button class="refresh-btn" size="mini" :loading="loading" @click="loadTemplates">刷新</button>
      <button class="new-btn" size="mini" @click="openCreate">新建模板</button>
    </view>

    <view v-if="templates.length === 0 && !loading" class="empty">当前分类还没有偏好模板</view>

    <view v-for="item in templates" :key="item.id" class="template-card">
      <view class="card-head">
        <view class="title-wrap">
          <text class="title">{{ item.title }}</text>
          <text v-if="item.is_default" class="default-badge">默认</text>
        </view>
        <text class="category">{{ item.category }}</text>
      </view>
      <view class="summary">{{ formatTemplateLabel(item) }}</view>
      <view class="meta">{{ formatTime(item.updated_time) }}</view>
      <view class="actions">
        <button size="mini" class="outline-btn" @click="openEdit(item)">编辑</button>
        <button size="mini" class="outline-btn" :disabled="item.is_default" @click="setDefault(item)">设默认</button>
        <button size="mini" class="outline-btn" @click="copyTemplate(item)">复制</button>
        <button size="mini" class="danger-btn" @click="deleteTemplate(item)">删除</button>
      </view>
    </view>

    <view v-if="editing" class="editor-mask">
      <view class="editor">
        <view class="editor-head">
          <text class="editor-title">{{ editingId ? '编辑模板' : '新建模板' }}</text>
          <text class="close" @click="closeEditor">关闭</text>
        </view>

        <input class="input" v-model="form.title" placeholder="模板名称" />

        <picker mode="selector" :range="categories" :value="categoryIndex" @change="changeFormCategory">
          <view class="input picker-line">分类：{{ form.category }}</view>
        </picker>

        <view v-if="form.category === '人名'">
          <input class="input" v-model="form.surname" placeholder="姓氏" />
          <picker mode="selector" :range="genderOptions" @change="event => form.gender = genderOptions[event.detail.value]">
            <view class="input picker-line">性别气质：{{ form.gender }}</view>
          </picker>
          <picker mode="selector" :range="lengthOptions" @change="event => form.length = lengthOptions[event.detail.value]">
            <view class="input picker-line">字数要求：{{ form.length }}</view>
          </picker>
          <input class="input" v-model="form.birth_datetime" placeholder="生辰（可选）" />
          <picker mode="selector" :range="wuxingOptions" @change="event => form.wuxing = wuxingOptions[event.detail.value]">
            <view class="input picker-line">五行偏好：{{ form.wuxing }}</view>
          </picker>
          <textarea class="textarea" v-model="form.desired_meaning" placeholder="期望寓意"></textarea>
        </view>

        <view v-if="form.category === '企业名'">
          <input class="input" v-model="form.industry" placeholder="行业" />
          <picker mode="selector" :range="styleOptions" @change="event => form.style = styleOptions[event.detail.value]">
            <view class="input picker-line">命名风格：{{ form.style }}</view>
          </picker>
          <picker mode="selector" :range="lengthOptions" @change="event => form.length = lengthOptions[event.detail.value]">
            <view class="input picker-line">字数要求：{{ form.length }}</view>
          </picker>
          <input class="input" v-model="form.region" placeholder="地域限制/目标市场" />
          <textarea class="textarea" v-model="form.target_user" placeholder="目标用户或客户"></textarea>
        </view>

        <view v-if="form.category === '宠物名'">
          <input class="input" v-model="form.pet_type" placeholder="宠物类型" />
          <picker mode="selector" :range="petStyleOptions" @change="event => form.pet_style = petStyleOptions[event.detail.value]">
            <view class="input picker-line">名字气质：{{ form.pet_style }}</view>
          </picker>
          <picker mode="selector" :range="lengthOptions" @change="event => form.length = lengthOptions[event.detail.value]">
            <view class="input picker-line">字数要求：{{ form.length }}</view>
          </picker>
        </view>

        <input class="input" v-model="excludeInput" placeholder="避开字词（逗号或空格分隔）" />
        <textarea class="textarea" v-model="form.other" placeholder="其它要求"></textarea>

        <label class="default-row">
          <switch :checked="form.is_default" @change="event => form.is_default = event.detail.value" />
          <text>保存为该分类默认模板</text>
        </label>

        <view class="editor-actions">
          <button class="cancel-btn" @click="closeEditor">取消</button>
          <button class="save-btn" :loading="saving" @click="saveTemplate">保存</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const categories = ['人名', '企业名', '宠物名'];
const genderOptions = ['不限', '男', '女'];
const lengthOptions = ['不限', '单字', '两字', '多字'];
const wuxingOptions = ['不限', '金', '木', '水', '火', '土'];
const styleOptions = ['不限', '现代', '国风', '高端', '亲和', '科技感', '国际化'];
const petStyleOptions = ['不限', '可爱', '酷一点', '国风', '洋气', '食物感', '叠字'];

const emptyForm = (category = '人名') => ({
  title: '',
  category,
  surname: '',
  gender: '不限',
  length: '不限',
  other: '',
  birth_datetime: '',
  wuxing: '不限',
  desired_meaning: '',
  industry: '',
  style: '不限',
  region: '',
  target_user: '',
  pet_type: '',
  pet_style: '不限',
  is_default: false
});

const activeCategory = ref('人名');
const templates = ref([]);
const loading = ref(false);
const saving = ref(false);
const editing = ref(false);
const editingId = ref(null);
const form = ref(emptyForm());
const excludeInput = ref('');

const categoryIndex = computed(() => Math.max(0, categories.indexOf(form.value.category)));

const addTemplatePart = (parts, value, options = {}) => {
  const text = Array.isArray(value) ? value.join('') : String(value || '').trim();
  if (!text || text === '不限') return;
  parts.push(options.prefix ? `${options.prefix}${text}` : text);
};

const formatTemplateLabel = (template) => {
  const preferences = template?.preferences || {};
  const category = template?.category || preferences.category || '常用偏好';
  const parts = [category];
  if (category === '人名') {
    addTemplatePart(parts, preferences.surname, { prefix: '姓' });
    addTemplatePart(parts, preferences.gender);
    addTemplatePart(parts, preferences.length);
    addTemplatePart(parts, preferences.wuxing);
    addTemplatePart(parts, preferences.desired_meaning);
    addTemplatePart(parts, preferences.other);
  } else if (category === '企业名') {
    addTemplatePart(parts, preferences.industry);
    addTemplatePart(parts, preferences.style);
    addTemplatePart(parts, preferences.length);
    addTemplatePart(parts, preferences.region);
    addTemplatePart(parts, preferences.target_user);
    addTemplatePart(parts, preferences.other);
  } else {
    addTemplatePart(parts, preferences.pet_type);
    addTemplatePart(parts, preferences.pet_style);
    addTemplatePart(parts, preferences.length);
    addTemplatePart(parts, preferences.other);
  }
  if (Array.isArray(preferences.exclude) && preferences.exclude.length) {
    parts.push(`避${preferences.exclude.join('')}`);
  }
  return parts.filter(Boolean).map(item => String(item).slice(0, 16)).slice(0, 7).join(' · ');
};

const loadTemplates = async () => {
  loading.value = true;
  try {
    const result = await http.getPreferenceTemplates({ category: activeCategory.value });
    templates.value = result.items || [];
  } catch (error) {
    console.error('加载偏好模板失败', error);
  } finally {
    loading.value = false;
  }
};

const switchCategory = (category) => {
  activeCategory.value = category;
  closeEditor();
  loadTemplates();
};

const cloneTemplateToForm = (template) => {
  const preferences = template.preferences || {};
  form.value = {
    ...emptyForm(template.category),
    ...preferences,
    title: template.title,
    category: template.category,
    is_default: Boolean(template.is_default)
  };
  excludeInput.value = Array.isArray(preferences.exclude) ? preferences.exclude.join(' ') : '';
};

const openCreate = () => {
  editingId.value = null;
  form.value = emptyForm(activeCategory.value);
  excludeInput.value = '';
  editing.value = true;
};

const openEdit = (template) => {
  editingId.value = template.id;
  cloneTemplateToForm(template);
  editing.value = true;
};

const closeEditor = () => {
  editing.value = false;
  editingId.value = null;
  saving.value = false;
};

const changeFormCategory = (event) => {
  const nextCategory = categories[event.detail.value];
  form.value = { ...emptyForm(nextCategory), title: form.value.title, category: nextCategory, is_default: form.value.is_default };
  excludeInput.value = '';
};

const parseExclude = () => String(excludeInput.value || '')
  .split(/[\s,，、;；]+/)
  .map(item => item.trim())
  .filter(Boolean);

const buildPreferences = () => {
  const fields = [
    'category',
    'surname',
    'gender',
    'length',
    'other',
    'birth_datetime',
    'wuxing',
    'desired_meaning',
    'industry',
    'style',
    'region',
    'target_user',
    'pet_type',
    'pet_style'
  ];
  return fields.reduce((result, field) => {
    result[field] = form.value[field] ?? '';
    return result;
  }, { exclude: parseExclude() });
};

const saveTemplate = async () => {
  const title = form.value.title.trim();
  if (!title) {
    return uni.showToast({ title: '请输入模板名称', icon: 'none' });
  }

  saving.value = true;
  try {
    const payload = {
      title,
      category: form.value.category,
      preferences: buildPreferences(),
      is_default: form.value.is_default
    };
    if (editingId.value) {
      await http.updatePreferenceTemplate(editingId.value, payload);
    } else {
      await http.createPreferenceTemplate(payload);
    }
    activeCategory.value = form.value.category;
    await loadTemplates();
    closeEditor();
    uni.showToast({ title: '模板已保存', icon: 'success' });
  } catch (error) {
    console.error('保存偏好模板失败', error);
  } finally {
    saving.value = false;
  }
};

const setDefault = async (template) => {
  await http.updatePreferenceTemplate(template.id, { is_default: true });
  await loadTemplates();
  uni.showToast({ title: '已设为默认', icon: 'success' });
};

const copyTemplate = async (template) => {
  await http.createPreferenceTemplate({
    title: `${template.title} 副本`,
    category: template.category,
    preferences: { ...(template.preferences || {}), category: template.category },
    is_default: false
  });
  await loadTemplates();
  uni.showToast({ title: '模板已复制', icon: 'success' });
};

const deleteTemplate = (template) => {
  uni.showModal({
    title: '删除模板',
    content: `确认删除“${template.title}”？`,
    success: async (res) => {
      if (!res.confirm) return;
      await http.deletePreferenceTemplate(template.id);
      templates.value = templates.value.filter(item => item.id !== template.id);
      uni.showToast({ title: '模板已删除', icon: 'none' });
    }
  });
};

const formatTime = (value) => {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 19);
};

onLoad((query) => {
  if (query.category && categories.includes(query.category)) {
    activeCategory.value = query.category;
  }
  loadTemplates();
});

onPullDownRefresh(async () => {
  await loadTemplates();
  uni.stopPullDownRefresh();
});
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; background: #f5f7fa; box-sizing: border-box; }
.tabs { display: flex; justify-content: space-around; background: #fff; padding: 18rpx; border-radius: 14rpx; margin-bottom: 20rpx; }
.tab { font-size: 28rpx; color: #666; padding: 10rpx 24rpx; }
.tab.active { color: #007aff; font-weight: 700; border-bottom: 4rpx solid #007aff; }
.toolbar { display: flex; justify-content: flex-end; gap: 14rpx; margin-bottom: 20rpx; }
.refresh-btn { margin: 0; color: #1677ff; background: #fff; }
.new-btn { margin: 0; color: #fff; background: #1677ff; }
.empty { text-align: center; color: #888; font-size: 28rpx; padding: 120rpx 0; }
.template-card { background: #fff; border-radius: 14rpx; padding: 24rpx; margin-bottom: 20rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.card-head { display: flex; justify-content: space-between; gap: 16rpx; align-items: center; margin-bottom: 12rpx; }
.title-wrap { display: flex; align-items: center; gap: 12rpx; min-width: 0; }
.title { color: #202124; font-size: 32rpx; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.default-badge { flex-shrink: 0; color: #8a5a00; background: #fff4d6; border-radius: 8rpx; padding: 4rpx 12rpx; font-size: 22rpx; }
.category { flex-shrink: 0; color: #1677ff; background: #eaf4ff; border-radius: 20rpx; padding: 4rpx 14rpx; font-size: 22rpx; }
.summary { color: #52677a; font-size: 26rpx; line-height: 1.6; }
.meta { color: #999; font-size: 22rpx; margin-top: 10rpx; }
.actions { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12rpx; margin-top: 18rpx; }
.outline-btn, .danger-btn { margin: 0; font-size: 24rpx; }
.outline-btn { color: #1677ff; background: #f7fbff; }
.danger-btn { color: #c62828; background: #fff5f5; }
.editor-mask { position: fixed; inset: 0; z-index: 20; background: rgba(0,0,0,0.35); display: flex; align-items: flex-end; }
.editor { width: 100%; max-height: 88vh; overflow-y: auto; background: #fff; border-radius: 18rpx 18rpx 0 0; padding: 28rpx; box-sizing: border-box; }
.editor-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18rpx; }
.editor-title { color: #202124; font-size: 32rpx; font-weight: 700; }
.close { color: #1677ff; font-size: 26rpx; }
.input { height: 78rpx; line-height: 78rpx; padding: 0 18rpx; margin-bottom: 14rpx; background: #f7f8fa; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.picker-line { color: #202124; }
.textarea { width: 100%; height: 150rpx; padding: 18rpx; margin-bottom: 14rpx; background: #f7f8fa; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.default-row { display: flex; align-items: center; gap: 12rpx; color: #334155; font-size: 26rpx; padding: 8rpx 0 18rpx; }
.editor-actions { display: flex; gap: 16rpx; }
.cancel-btn, .save-btn { flex: 1; margin: 0; border-radius: 8rpx; }
.cancel-btn { color: #1677ff; background: #f7fbff; }
.save-btn { color: #fff; background: #1677ff; }
</style>
