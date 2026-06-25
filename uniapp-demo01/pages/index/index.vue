<template>
  <view class="container">
    <view class="quick-actions">
      <button class="quick-btn membership" size="mini" @click="goMembership">会员 {{ quotaRemaining }}</button>
      <button class="quick-btn profile" size="mini" @click="goProfile">&#x6211;&#x7684;</button>
      <button v-if="isAdmin" class="quick-btn admin" size="mini" @click="goAdmin">后台</button>
      <button class="quick-btn" size="mini" @click="goProjects">项目</button>
      <button class="quick-btn" size="mini" @click="goHistory(false)">历史</button>
      <button class="quick-btn favorite" size="mini" @click="goHistory(true)">收藏</button>
    </view>

    <view class="tabs">
      <view
        v-for="item in categories"
        :key="item"
        :class="['tab', formData.category === item ? 'active' : '']"
        @click="switchCategory(item)"
      >
        {{ item }}
      </view>
    </view>

    <view class="template-section">
      <view class="template-head">
        <text class="template-title">偏好模板</text>
        <view class="template-head-actions">
          <button size="mini" class="template-manage" @click="goTemplates">管理</button>
          <button size="mini" class="template-save" :loading="templateLoading" @click="savePreferenceTemplate">保存当前偏好</button>
        </view>
      </view>
      <view class="template-actions">
        <picker mode="selector" :range="templateTitles" @change="selectPreferenceTemplate">
          <view class="template-picker">{{ selectedTemplateTitle }}</view>
        </picker>
        <button size="mini" class="template-action primary" :disabled="!selectedTemplate" @click="applySelectedTemplate">套用</button>
        <button size="mini" class="template-action danger" :disabled="!selectedTemplate" @click="deleteSelectedTemplate">删除</button>
      </view>
    </view>

    <view v-if="currentProject" class="project-strip">
      <view class="project-main">
        <text class="project-title">{{ currentProject.title }}</text>
        <text class="project-meta">结果 {{ currentProject.history_count || 0 }} · 收藏 {{ currentProject.favorite_count || 0 }}</text>
      </view>
      <button size="mini" class="project-clear" @click="clearProject">新项目</button>
    </view>

    <view class="upload-section" v-if="formData.category === '企业名'">
      <view class="upload-tip">有企业命名规范？让 AI 学习你的专属标准</view>
      <button size="mini" :disabled="uploadPolling" @click="handleUploadDocs">
        {{ uploadPolling ? '知识库处理中' : '上传专属知识库 (TXT/PDF)' }}
      </button>
      <view v-if="uploadTask" class="task-status">
        <view class="task-status-row">
          <text class="task-file">{{ uploadTask.filename }}</text>
          <text :class="['task-badge', taskStatusClass]">{{ uploadTask.status_label }}</text>
        </view>
        <view v-if="uploadTask.error_message" class="task-error">失败原因：{{ uploadTask.error_message }}</view>
      </view>
      <view class="knowledge-list">
        <view class="knowledge-list-header">
          <text class="knowledge-title">知识库文件</text>
          <button size="mini" class="knowledge-refresh" :loading="knowledgeLoading" @click="loadKnowledgeFiles">刷新</button>
        </view>
        <view v-if="knowledgeFiles.length === 0" class="knowledge-empty">暂无已上传文件</view>
        <view v-for="item in knowledgeFiles" :key="item.id" class="knowledge-item">
          <view class="knowledge-main">
            <text class="task-file">{{ item.filename }}</text>
            <view class="knowledge-meta">
              <text :class="['task-badge', getTaskStatusClass(item.status)]">{{ item.status_label || item.status }}</text>
              <text class="chunk-badge">片段 {{ item.chunk_count || 0 }}</text>
              <text v-if="item.parse_log" class="task-log">{{ item.parse_log }}</text>
              <text :class="['active-badge', item.is_active ? 'active-on' : 'active-off']">
                {{ item.is_active ? '已启用' : '已禁用' }}
              </text>
            </view>
            <view v-if="item.error_message" class="task-error">失败原因：{{ item.error_message }}</view>
          </view>
          <view class="knowledge-actions">
            <button size="mini" class="knowledge-action" @click="previewKnowledge(item)">
              预览
            </button>
            <button size="mini" class="knowledge-action" :disabled="item.status === 'processing'" @click="handleReparse(item)">
              重新解析
            </button>
            <button size="mini" class="knowledge-action danger" :disabled="item.status === 'processing'" @click="deleteKnowledge(item)">
              删除
            </button>
            <button size="mini" class="knowledge-action" @click="toggleKnowledgeActive(item)">
              {{ item.is_active ? '禁用' : '启用' }}
            </button>
          </view>
        </view>
      </view>
    </view>

    <view class="question-card">
      <view class="question-head">
        <text class="question-title">AI 先了解几个关键点</text>
        <text class="question-progress">{{ questionProgress }}</text>
      </view>
      <view class="question-text">{{ activeQuestion.label }}</view>

      <input
        v-if="activeQuestion.type === 'input'"
        class="input-box question-input"
        v-model="formData[activeQuestion.field]"
        :placeholder="activeQuestion.placeholder"
      />

      <textarea
        v-if="activeQuestion.type === 'textarea'"
        class="textarea-box question-input"
        v-model="formData[activeQuestion.field]"
        :placeholder="activeQuestion.placeholder"
      ></textarea>

      <picker
        v-if="activeQuestion.type === 'select'"
        mode="selector"
        :range="activeQuestion.options"
        @change="event => setQuestionSelect(activeQuestion.field, activeQuestion.options, event)"
      >
        <view class="input-box question-input">{{ formData[activeQuestion.field] || activeQuestion.placeholder }}</view>
      </picker>

      <view class="question-actions">
        <button class="question-btn" size="mini" :disabled="activeQuestionIndex === 0 || loading" @click="prevQuestion">上一步</button>
        <button v-if="!isLastQuestion" class="question-btn primary" size="mini" :disabled="loading" @click="nextQuestion">
          下一步
        </button>
        <button v-else class="question-btn primary" size="mini" :loading="loading" @click="handleGenerate">
          开始智能起名
        </button>
      </view>
    </view>

    <view class="advanced-toggle" @click="showAdvanced = !showAdvanced">
      {{ showAdvanced ? '收起补充信息' : '补充更多细节' }}
    </view>

    <view class="form-group" v-if="showAdvanced">
      <picker v-if="formData.category !== '人名'" mode="selector" :range="lengthOptions" @change="event => formData.length = lengthOptions[event.detail.value]">
        <view class="input-box">字数要求：{{ formData.length }}</view>
      </picker>

      <input
        v-if="formData.category === '人名'"
        class="input-box"
        v-model="formData.birth_datetime"
        placeholder="生辰（如：2024-05-20 08:30，可选）"
      />

      <picker
        v-if="formData.category === '人名'"
        mode="selector"
        :range="wuxingOptions"
        @change="event => formData.wuxing = wuxingOptions[event.detail.value]"
      >
        <view class="input-box">五行偏好：{{ formData.wuxing }}</view>
      </picker>

      <input
        v-if="formData.category === '企业名'"
        class="input-box"
        v-model="formData.region"
        placeholder="地域限制/目标市场（如：上海、华南、海外，可选）"
      />

      <input
        class="input-box"
        v-model="excludeInput"
        placeholder="避开字词（用逗号或空格分隔，如：强 刚）"
      />

      <textarea
        v-if="formData.category !== '宠物名'"
        class="textarea-box"
        v-model="formData.other"
        :placeholder="otherPlaceholder"
      ></textarea>
    </view>

    <view class="result-box" v-if="names.length > 0">
      <view class="result-title">为您生成的专属方案：</view>
      <view class="name-card" v-for="(item, index) in names" :key="item.history_id || index">
        <view class="name-header">
          <text class="name-text">{{ item.name }}</text>
          <button class="favorite-btn" size="mini" @click="toggleFavorite(item)">
            {{ item.is_favorite ? '已收藏' : '收藏' }}
          </button>
        </view>

        <text v-if="item.domain" :class="['domain-tag', isDomainAvailable(item.domain_status) ? 'domain-success' : 'domain-fail']">
          {{ item.domain }} ({{ item.domain_status }})
        </text>
        <view v-if="hasCompanyEnrichment(item)" class="company-enrichment">
          <view class="alias-row" v-if="item.pinyin || item.english_name || item.abbreviation">
            <text v-if="item.pinyin">拼音：{{ item.pinyin }}</text>
            <text v-if="item.english_name">英文：{{ item.english_name }}</text>
            <text v-if="item.abbreviation">简称：{{ item.abbreviation }}</text>
          </view>
          <view v-if="item.domain_checks && item.domain_checks.length" class="domain-checks">
            <text
              v-for="check in item.domain_checks"
              :key="check.domain"
              :class="['domain-check', isDomainAvailable(check.status) ? 'domain-success' : 'domain-fail']"
            >
              {{ check.domain }} {{ check.status }}
            </text>
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
        <view class="name-detail"><text class="label">出处：</text>{{ item.reference }}</view>
        <view class="name-detail"><text class="label">寓意：</text>{{ item.moral }}</view>
        <view class="preference-actions">
          <button class="preference-btn primary" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'direction')">保留这个方向</button>
          <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'style')">保留风格</button>
          <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'chars')">保留用字</button>
          <button class="preference-btn" size="mini" :disabled="loading" @click="regenerateWithPreference(item, 'meaning')">保留寓意</button>
        </view>
        <button class="export-btn" size="mini" @click="exportCurrent(item)">导出方案</button>
      </view>

      <view class="feedback-box">
        <textarea
          class="textarea-box"
          v-model="feedbackText"
          placeholder="对结果不满意？请输入修改意见（如：保留第二个名字，其他换成带水字旁的字）"
        ></textarea>
        <button class="btn-secondary" :loading="loading" @click="handleFeedback">基于意见重新生成</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import { chooseAndExportReport } from '@/utils/reportExport.js';

const categories = ['人名', '企业名', '宠物名'];
const genderOptions = ['不限', '男', '女'];
const lengthOptions = ['不限', '单字', '两字', '多字'];
const wuxingOptions = ['不限', '金', '木', '水', '火', '土'];
const styleOptions = ['不限', '现代', '国风', '高端', '亲和', '科技感', '国际化'];
const petStyleOptions = ['不限', '可爱', '酷一点', '国风', '洋气', '食物感', '叠字'];

const formData = ref({
  category: '人名',
  surname: '',
  gender: '不限',
  length: '不限',
  other: '',
  exclude: [],
  birth_datetime: '',
  wuxing: '不限',
  desired_meaning: '',
  industry: '',
  style: '不限',
  region: '',
  target_user: '',
  pet_type: '',
  pet_style: '不限'
});

const loading = ref(false);
const names = ref([]);
const threadId = ref('');
const feedbackText = ref('');
const uploadTask = ref(null);
const uploadPolling = ref(false);
const knowledgeFiles = ref([]);
const knowledgeLoading = ref(false);
const quotaRemaining = ref('-');
const currentProject = ref(null);
const currentProjectId = ref(null);
const activeQuestionIndex = ref(0);
const showAdvanced = ref(false);
const excludeInput = ref('');
const preferenceTemplates = ref([]);
const selectedTemplateIndex = ref(-1);
const templateLoading = ref(false);
let uploadPollTimer = null;
let uploadPollCount = 0;
const currentUser = uni.getStorageSync('user');
const isAdmin = ref(Boolean(currentUser && currentUser.is_admin));

const addTemplatePart = (parts, value, options = {}) => {
  const text = Array.isArray(value) ? value.join('') : String(value || '').trim();
  if (!text || text === '不限') {
    return;
  }
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
  } else if (category === '宠物名') {
    addTemplatePart(parts, preferences.pet_type);
    addTemplatePart(parts, preferences.pet_style);
    addTemplatePart(parts, preferences.length);
    addTemplatePart(parts, preferences.other);
  }

  if (Array.isArray(preferences.exclude) && preferences.exclude.length) {
    parts.push(`避${preferences.exclude.join('')}`);
  }

  const summary = parts
    .filter(Boolean)
    .map(item => String(item).slice(0, 12))
    .slice(0, 6)
    .join(' · ');
  return summary || template?.title || '常用偏好';
};

const questionSets = {
  人名: [
    { field: 'surname', type: 'input', required: true, label: '宝宝姓什么？', placeholder: '请输入姓氏（如：张）' },
    { field: 'gender', type: 'select', required: true, label: '希望名字偏向哪种性别气质？', placeholder: '请选择性别倾向', options: genderOptions },
    { field: 'length', type: 'select', required: true, label: '名字希望是单字还是多字？', placeholder: '请选择字数要求', options: lengthOptions },
    { field: 'desired_meaning', type: 'textarea', required: false, label: '最希望名字传达什么寓意？', placeholder: '如：沉稳、聪慧、开朗；不确定也可以跳过' }
  ],
  企业名: [
    { field: 'industry', type: 'input', required: true, label: '公司或品牌属于哪个行业？', placeholder: '如：科技、餐饮、教育、服装' },
    { field: 'style', type: 'select', required: true, label: '你希望名字是什么风格？', placeholder: '请选择命名风格', options: styleOptions },
    { field: 'target_user', type: 'textarea', required: false, label: '主要面向哪些用户或客户？', placeholder: '如：一线城市年轻女性、中小企业老板、海外消费者' }
  ],
  宠物名: [
    { field: 'pet_type', type: 'input', required: false, label: '它是什么宠物？', placeholder: '如：猫、狗、兔子；不填也可以' },
    { field: 'other', type: 'textarea', required: true, label: '它有什么特征或性格？', placeholder: '如：白色、活泼、粘人、胆小' },
    { field: 'pet_style', type: 'select', required: false, label: '名字想要什么感觉？', placeholder: '请选择名字气质', options: petStyleOptions }
  ]
};

const goAdmin = () => {
  uni.navigateTo({ url: '/pages/admin/admin' });
};

const goProfile = () => {
  uni.navigateTo({ url: '/pages/profile/profile' });
};

const goMembership = () => {
  uni.navigateTo({ url: '/pages/membership/membership' });
};

const goProjects = () => {
  uni.navigateTo({ url: '/pages/projects/projects' });
};

const goTemplates = () => {
  uni.navigateTo({ url: `/pages/templates/templates?category=${encodeURIComponent(formData.value.category)}` });
};

const taskStatusClass = computed(() => {
  const status = uploadTask.value?.status || '';
  return getTaskStatusClass(status);
});

const activeQuestions = computed(() => questionSets[formData.value.category] || questionSets['人名']);
const activeQuestion = computed(() => activeQuestions.value[activeQuestionIndex.value] || activeQuestions.value[0]);
const isLastQuestion = computed(() => activeQuestionIndex.value >= activeQuestions.value.length - 1);
const questionProgress = computed(() => `${activeQuestionIndex.value + 1}/${activeQuestions.value.length}`);
const selectedTemplate = computed(() => preferenceTemplates.value[selectedTemplateIndex.value] || null);
const templateTitles = computed(() => {
  if (preferenceTemplates.value.length === 0) {
    return ['暂无模板'];
  }
  return preferenceTemplates.value.map(item => formatTemplateLabel(item));
});
const selectedTemplateTitle = computed(() => selectedTemplate.value ? formatTemplateLabel(selectedTemplate.value) : '选择常用偏好模板');

const getTaskStatusClass = (status = '') => {
  return {
    queued: 'task-queued',
    processing: 'task-processing',
    done: 'task-done',
    failed: 'task-failed'
  }[status] || 'task-queued';
};

const otherPlaceholder = computed(() => {
  if (formData.value.category === '人名') {
    return '其它要求（如：不想太常见、偏古典）';
  }
  if (formData.value.category === '企业名') {
    return '核心诉求（如：突出可信赖、适合做品牌）';
  }
  return '宠物特征/性格（如：白色、活泼、粘人）';
});

const goHistory = (favoriteOnly) => {
  const projectQuery = currentProjectId.value ? `&project_id=${currentProjectId.value}` : '';
  uni.navigateTo({
    url: `/pages/history/history?type=${favoriteOnly ? 'favorite' : 'history'}${projectQuery}`
  });
};

const loadProject = async (projectId) => {
  if (!projectId) return;
  try {
    const project = await http.getProjectDetail(projectId);
    currentProject.value = project;
    currentProjectId.value = project.id;
    formData.value.category = project.category;
    if (project.category === '企业名') {
      loadKnowledgeFiles();
    }
  } catch (error) {
    currentProject.value = null;
    currentProjectId.value = null;
    console.error('加载项目失败', error);
  }
};

const clearProject = () => {
  currentProject.value = null;
  currentProjectId.value = null;
  names.value = [];
  threadId.value = '';
  feedbackText.value = '';
  loadKnowledgeFiles();
};

const setQuestionSelect = (field, options, event) => {
  formData.value[field] = options[event.detail.value];
};

const parseExcludeInput = () => {
  return String(excludeInput.value || '')
    .split(/[\s,，、;；]+/)
    .map(item => item.trim())
    .filter(Boolean);
};

const syncExcludeFromInput = () => {
  formData.value.exclude = parseExcludeInput();
};

const buildTemplatePreferences = () => {
  syncExcludeFromInput();
  const fields = [
    'category',
    'surname',
    'gender',
    'length',
    'other',
    'exclude',
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
    const value = formData.value[field];
    if (Array.isArray(value)) {
      result[field] = [...value];
    } else {
      result[field] = value ?? '';
    }
    return result;
  }, {});
};

const buildTemplateTitle = () => {
  return formatTemplateLabel({
    category: formData.value.category,
    preferences: buildTemplatePreferences()
  });
};

const loadPreferenceTemplates = async () => {
  templateLoading.value = true;
  try {
    const result = await http.getPreferenceTemplates({ category: formData.value.category });
    preferenceTemplates.value = result.items || [];
    selectedTemplateIndex.value = preferenceTemplates.value.length ? 0 : -1;
  } catch (error) {
    console.error('加载偏好模板失败', error);
  } finally {
    templateLoading.value = false;
  }
};

const selectPreferenceTemplate = (event) => {
  if (preferenceTemplates.value.length === 0) {
    selectedTemplateIndex.value = -1;
    return;
  }
  selectedTemplateIndex.value = Number(event.detail.value);
};

const applySelectedTemplate = () => {
  const template = selectedTemplate.value;
  if (!template) {
    return uni.showToast({ title: '请先选择模板', icon: 'none' });
  }

  formData.value = {
    ...formData.value,
    ...template.preferences,
    category: template.category
  };
  excludeInput.value = Array.isArray(formData.value.exclude) ? formData.value.exclude.join(' ') : '';
  activeQuestionIndex.value = 0;
  showAdvanced.value = true;
  names.value = [];
  threadId.value = '';
  feedbackText.value = '';
  if (template.category === '企业名') {
    loadKnowledgeFiles();
  }
  uni.showToast({ title: '已套用模板', icon: 'success' });
};

const savePreferenceTemplate = async () => {
  templateLoading.value = true;
  try {
    const template = await http.createPreferenceTemplate({
      title: buildTemplateTitle(),
      category: formData.value.category,
      preferences: buildTemplatePreferences()
    });
    preferenceTemplates.value = [template, ...preferenceTemplates.value];
    selectedTemplateIndex.value = 0;
    uni.showToast({ title: '模板已保存', icon: 'success' });
  } catch (error) {
    console.error('保存偏好模板失败', error);
  } finally {
    templateLoading.value = false;
  }
};

const deleteSelectedTemplate = async () => {
  const template = selectedTemplate.value;
  if (!template) {
    return;
  }
  const result = await new Promise(resolve => {
    uni.showModal({
      title: '删除模板',
      content: `确认删除“${template.title}”？`,
      success: resolve,
      fail: () => resolve({ confirm: false })
    });
  });
  if (!result.confirm) {
    return;
  }
  await http.deletePreferenceTemplate(template.id);
  preferenceTemplates.value.splice(selectedTemplateIndex.value, 1);
  selectedTemplateIndex.value = preferenceTemplates.value.length ? 0 : -1;
  uni.showToast({ title: '模板已删除', icon: 'none' });
};

const validateQuestion = (question = activeQuestion.value) => {
  const value = formData.value[question.field];
  if (question.required && !String(value || '').trim()) {
    uni.showToast({ title: '请先回答当前问题', icon: 'none' });
    return false;
  }
  return true;
};

const nextQuestion = () => {
  if (!validateQuestion()) {
    return;
  }
  activeQuestionIndex.value = Math.min(activeQuestionIndex.value + 1, activeQuestions.value.length - 1);
};

const prevQuestion = () => {
  activeQuestionIndex.value = Math.max(activeQuestionIndex.value - 1, 0);
};

const validateQuestionFlow = () => {
  for (const question of activeQuestions.value) {
    if (!validateQuestion(question)) {
      activeQuestionIndex.value = activeQuestions.value.findIndex(item => item.field === question.field);
      return false;
    }
  }
  return true;
};

const buildGeneratePayload = () => {
  syncExcludeFromInput();
  const payload = { ...formData.value };
  const extraParts = [];

  if (payload.category === '企业名') {
    if (payload.target_user && payload.target_user.trim()) {
      extraParts.push(`目标用户：${payload.target_user.trim()}`);
    }
    if (payload.other && payload.other.trim()) {
      extraParts.push(payload.other.trim());
    }
    payload.other = extraParts.join('；');
  }

  if (payload.category === '宠物名') {
    if (payload.pet_type && payload.pet_type.trim()) {
      extraParts.push(`宠物类型：${payload.pet_type.trim()}`);
    }
    if (payload.other && payload.other.trim()) {
      extraParts.push(`特征性格：${payload.other.trim()}`);
    }
    if (payload.pet_style && payload.pet_style !== '不限') {
      extraParts.push(`名字气质：${payload.pet_style}`);
    }
    payload.other = extraParts.join('；');
  }

  delete payload.target_user;
  delete payload.pet_type;
  delete payload.pet_style;
  return payload;
};

const switchCategory = (cat) => {
  formData.value.category = cat;
  names.value = [];
  threadId.value = '';
  feedbackText.value = '';
  activeQuestionIndex.value = 0;
  showAdvanced.value = false;
  selectedTemplateIndex.value = -1;
  loadPreferenceTemplates();
  if (cat === '企业名') {
    loadKnowledgeFiles();
  }
};

const loadKnowledgeFiles = async () => {
  knowledgeLoading.value = true;
  try {
    const result = await http.getKnowledgeFiles({ limit: 50, project_id: currentProjectId.value });
    knowledgeFiles.value = result.items || [];
  } catch (error) {
    console.error('查询知识库文件失败', error);
  } finally {
    knowledgeLoading.value = false;
  }
};

const clearUploadPolling = () => {
  if (uploadPollTimer) {
    clearTimeout(uploadPollTimer);
    uploadPollTimer = null;
  }
  uploadPolling.value = false;
};

const startUploadPolling = (taskId) => {
  clearUploadPolling();
  uploadPolling.value = true;
  uploadPollCount = 0;

  const poll = async () => {
    try {
      const task = await http.getKnowledgeTask(taskId);
      uploadTask.value = task;
      const index = knowledgeFiles.value.findIndex(item => item.id === task.id);
      if (index >= 0) {
        knowledgeFiles.value[index] = task;
      }

      if (task.status === 'done') {
        clearUploadPolling();
        loadKnowledgeFiles();
        uni.showToast({ title: '知识库学习完成', icon: 'success' });
        return;
      }

      if (task.status === 'failed') {
        clearUploadPolling();
        loadKnowledgeFiles();
        uni.showToast({ title: '知识库处理失败', icon: 'none' });
        return;
      }

      uploadPollCount += 1;
      if (uploadPollCount >= 60) {
        clearUploadPolling();
        uni.showToast({ title: '任务仍在处理中，请稍后查看', icon: 'none' });
        return;
      }

      uploadPollTimer = setTimeout(poll, 2000);
    } catch (error) {
      clearUploadPolling();
      console.error('查询知识库任务状态失败:', error);
    }
  };

  poll();
};

const handleUploadDocs = () => {
  uni.chooseFile({
    count: 1,
    type: 'all',
    extension: ['.txt', '.pdf'],
    success: async (res) => {
      const tempFilePath = res.tempFiles?.[0]?.path || res.tempFilePaths?.[0];
      if (!tempFilePath) {
        return uni.showToast({ title: '未获取到文件路径', icon: 'none' });
      }

      uni.showLoading({ title: '文件上传中...' });

      try {
        const result = await http.uploadKnowledge(tempFilePath, currentProjectId.value);
        uploadTask.value = result.task || {
          id: result.task_id,
          filename: res.tempFiles?.[0]?.name || '知识库文件',
          status: result.status,
          status_label: result.status_label
        };

        uni.hideLoading();

        if (uploadTask.value.status === 'failed') {
          return uni.showToast({ title: '后台任务创建失败', icon: 'none' });
        }

        uni.showToast({ title: '已加入处理队列', icon: 'none' });
        loadKnowledgeFiles();
        startUploadPolling(uploadTask.value.id);
      } catch (error) {
        uni.hideLoading();
        console.error('上传失败:', error);
      }
    },
    fail: (err) => {
      console.log('用户取消选择文件或选择失败', err);
    }
  });
};

const handleReparse = async (item) => {
  try {
    const task = await http.reparseKnowledgeTask(item.id);
    uploadTask.value = task;
    const index = knowledgeFiles.value.findIndex(file => file.id === task.id);
    if (index >= 0) {
      knowledgeFiles.value[index] = task;
    }
    uni.showToast({ title: '已加入处理队列', icon: 'none' });
    startUploadPolling(task.id);
  } catch (error) {
    console.error('重新解析知识库文件失败', error);
  }
};

const toggleKnowledgeActive = async (item) => {
  try {
    const task = await http.setKnowledgeTaskActive(item.id, !item.is_active);
    const index = knowledgeFiles.value.findIndex(file => file.id === task.id);
    if (index >= 0) {
      knowledgeFiles.value[index] = task;
    }
    uni.showToast({ title: task.is_active ? '已启用' : '已禁用', icon: 'none' });
  } catch (error) {
    console.error('切换知识库文件状态失败', error);
  }
};

const previewKnowledge = async (item) => {
  try {
    const result = await http.previewKnowledgeTask(item.id, { max_chars: 3000 });
    uni.showModal({
      title: result.filename || 'Preview',
      content: result.content || 'No preview content',
      showCancel: false,
      confirmText: 'OK'
    });
  } catch (error) {
    console.error('preview knowledge file failed', error);
  }
};

const deleteKnowledge = async (item) => {
  uni.showModal({
    title: 'Delete knowledge file',
    content: 'This will clean related vectors and remove the file from RAG retrieval.',
    confirmText: 'Delete',
    confirmColor: '#d93025',
    success: async (res) => {
      if (!res.confirm) {
        return;
      }
      try {
        await http.deleteKnowledgeTask(item.id);
        knowledgeFiles.value = knowledgeFiles.value.filter(file => file.id !== item.id);
        if (uploadTask.value?.id === item.id) {
          uploadTask.value = null;
        }
        uni.showToast({ title: 'Deleted', icon: 'none' });
      } catch (error) {
        console.error('delete knowledge file failed', error);
      }
    }
  });
};

const handleGenerate = async () => {
  if (!validateQuestionFlow()) {
    return;
  }

  const payload = buildGeneratePayload();
  if (currentProjectId.value) {
    payload.project_id = currentProjectId.value;
  }

  if (payload.category === '人名' && !payload.surname.trim()) {
    return uni.showToast({ title: '人名必须填写姓氏', icon: 'none' });
  }

  if (payload.category === '企业名' && !payload.industry.trim() && !payload.other.trim()) {
    return uni.showToast({ title: '请填写行业或核心诉求', icon: 'none' });
  }

  loading.value = true;
  uni.showLoading({ title: 'AI思考中...' });

  try {
    const res = await http.generateName(payload);
    names.value = res.names;
    threadId.value = res.thread_id;
    if (res.project_id) {
      currentProjectId.value = res.project_id;
      loadProject(res.project_id);
    }
    syncQuota(res);
    feedbackText.value = '';
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};

const buildPreferenceFeedback = (item, type = 'direction') => {
  const name = item?.name || '这个名字';
  const moral = String(item?.moral || '').trim();
  const reference = String(item?.reference || '').trim();
  const category = formData.value.category;
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

const submitFeedback = async (feedback, successTitle = '已重新生成') => {
  if (!threadId.value) {
    return uni.showToast({ title: '请先生成名字', icon: 'none' });
  }
  const text = String(feedback || '').trim();
  if (!text) {
    return uni.showToast({ title: '请输入修改意见', icon: 'none' });
  }

  loading.value = true;
  uni.showLoading({ title: '微调修改中...' });

  try {
    const res = await http.feedbackName({
      thread_id: threadId.value,
      project_id: currentProjectId.value,
      category: formData.value.category,
      feedback: text
    });
    names.value = res.names;
    syncQuota(res);
    feedbackText.value = '';
    uni.showToast({ title: successTitle, icon: 'success' });
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
    uni.hideLoading();
  }
};

const handleFeedback = async () => {
  await submitFeedback(feedbackText.value);
};

const regenerateWithPreference = async (item, type) => {
  await submitFeedback(buildPreferenceFeedback(item, type), '已按偏好生成');
};

const toggleFavorite = async (item) => {
  if (!item.history_id) {
    return uni.showToast({ title: '当前记录暂不可收藏', icon: 'none' });
  }

  const updated = await http.setHistoryFavorite(item.history_id, !item.is_favorite);
  item.is_favorite = updated.is_favorite;
  uni.showToast({ title: item.is_favorite ? '已加入收藏' : '已取消收藏', icon: 'none' });
};

const exportCurrent = (item) => {
  chooseAndExportReport(item.history_id, item.name);
};

const isDomainAvailable = (status = '') => {
  return status.includes('可') || status.toLowerCase().includes('available');
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

const syncQuota = (res = {}) => {
  if (res.quota_remaining !== undefined && res.quota_remaining !== null) {
    quotaRemaining.value = res.quota_remaining;
  }
};

const loadQuota = async () => {
  try {
    const quota = await http.getQuota();
    quotaRemaining.value = quota.remaining_quota ?? '-';
  } catch (error) {
    console.error('加载额度失败', error);
  }
};

onMounted(() => {
  loadQuota();
  loadPreferenceTemplates();
  if (formData.value.category === '企业名') {
    loadKnowledgeFiles();
  }
});

onShow(() => {
  loadPreferenceTemplates();
});

onLoad((query) => {
  if (query.project_id) {
    loadProject(query.project_id);
  }
});

onUnmounted(() => {
  clearUploadPolling();
});
</script>

<style scoped>
.container { padding: 30rpx; background-color: #f5f7fa; min-height: 100vh; box-sizing: border-box; }
.quick-actions { display: flex; justify-content: flex-end; gap: 16rpx; margin-bottom: 20rpx; }
.quick-btn { margin: 0; color: #007aff; background: #fff; }
.quick-btn.membership { color: #fff; background: #16213e; }
.quick-btn.profile { color: #2e7d32; background: #fff; }
.quick-btn.admin { color: #fff; background: #1677ff; }
.quick-btn.favorite { color: #fff; background: #ff9800; }
.project-strip { display: flex; align-items: center; gap: 16rpx; background: #fff; border-radius: 14rpx; padding: 18rpx; margin-bottom: 24rpx; }
.project-main { flex: 1; min-width: 0; }
.project-title { display: block; font-size: 30rpx; font-weight: 700; color: #222; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.project-meta { display: block; margin-top: 6rpx; font-size: 22rpx; color: #667085; }
.project-clear { margin: 0; color: #1677ff; background: #f7fbff; }
.tabs { display: flex; justify-content: space-around; background: #fff; padding: 20rpx; border-radius: 16rpx; margin-bottom: 30rpx; }
.tab { font-size: 30rpx; color: #666; padding: 10rpx 30rpx; }
.tab.active { color: #007aff; font-weight: bold; border-bottom: 4rpx solid #007aff; }
.template-section { background: #fff; border-radius: 16rpx; padding: 20rpx; margin-bottom: 24rpx; }
.template-head { display: flex; justify-content: space-between; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.template-title { font-size: 28rpx; color: #222; font-weight: 700; }
.template-head-actions { display: flex; gap: 12rpx; align-items: center; }
.template-manage { margin: 0; color: #1677ff; background: #f7fbff; font-size: 24rpx; }
.template-save { margin: 0; color: #fff; background: #1677ff; font-size: 24rpx; }
.template-actions { display: grid; grid-template-columns: 1fr 120rpx 120rpx; gap: 12rpx; align-items: center; }
.template-picker { background: #f7fbff; border: 1px solid #d9ecff; border-radius: 8rpx; padding: 16rpx; color: #334155; font-size: 26rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.template-action { margin: 0; font-size: 24rpx; }
.template-action.primary { color: #fff; background: #2e7d32; }
.template-action.danger { color: #c62828; background: #fff5f5; }
.upload-section { background: #e6f7ff; padding: 20rpx; border-radius: 12rpx; margin-bottom: 30rpx; text-align: center; }
.upload-tip { font-size: 24rpx; color: #007aff; margin-bottom: 10rpx; }
.task-status { margin-top: 18rpx; padding: 18rpx; background: #fff; border-radius: 8rpx; text-align: left; }
.task-status-row { display: flex; justify-content: space-between; align-items: center; gap: 16rpx; }
.task-file { flex: 1; min-width: 0; color: #333; font-size: 24rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-badge { flex-shrink: 0; padding: 6rpx 14rpx; border-radius: 8rpx; font-size: 22rpx; }
.task-queued { background: #fff8e1; color: #8a5a00; }
.task-processing { background: #e3f2fd; color: #1565c0; }
.task-done { background: #e8f5e9; color: #2e7d32; }
.task-failed { background: #ffebee; color: #c62828; }
.task-error { margin-top: 10rpx; color: #c62828; font-size: 22rpx; line-height: 1.5; }
.knowledge-list { margin-top: 18rpx; padding-top: 18rpx; border-top: 1px solid #d2ecff; text-align: left; }
.knowledge-list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.knowledge-title { color: #333; font-size: 26rpx; font-weight: bold; }
.knowledge-refresh { margin: 0; color: #007aff; background: #fff; font-size: 22rpx; }
.knowledge-empty { color: #777; font-size: 24rpx; padding: 16rpx 0; }
.knowledge-item { background: #fff; border-radius: 8rpx; padding: 16rpx; margin-top: 12rpx; }
.knowledge-main { min-width: 0; }
.knowledge-meta { display: flex; gap: 10rpx; flex-wrap: wrap; margin-top: 10rpx; }
.active-badge { padding: 6rpx 14rpx; border-radius: 8rpx; font-size: 22rpx; }
.active-on { background: #e8f5e9; color: #2e7d32; }
.active-off { background: #f3f4f6; color: #666; }
.chunk-badge { padding: 6rpx 14rpx; border-radius: 8rpx; font-size: 22rpx; background: #fff7e6; color: #ad6800; }
.task-log { flex-basis: 100%; min-width: 0; color: #586069; font-size: 22rpx; line-height: 1.5; word-break: break-all; }
.knowledge-actions { display: flex; gap: 12rpx; margin-top: 12rpx; }
.knowledge-action { margin: 0; flex: 1; color: #007aff; background: #f7fbff; font-size: 22rpx; }
.knowledge-action.danger { color: #c62828; background: #fff5f5; }
.question-card { background: #fff; padding: 28rpx; border-radius: 16rpx; margin-bottom: 20rpx; }
.question-head { display: flex; justify-content: space-between; align-items: center; gap: 16rpx; margin-bottom: 18rpx; }
.question-title { font-size: 28rpx; color: #333; font-weight: 700; }
.question-progress { flex-shrink: 0; color: #1677ff; background: #eaf4ff; border-radius: 8rpx; padding: 6rpx 14rpx; font-size: 22rpx; }
.question-text { color: #222; font-size: 34rpx; font-weight: 700; line-height: 1.45; margin-bottom: 10rpx; }
.question-input { margin-top: 10rpx; }
.question-actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.question-btn { margin: 0; flex: 1; color: #1677ff; background: #f7fbff; }
.question-btn.primary { color: #fff; background: #007aff; }
.advanced-toggle { color: #1677ff; text-align: center; font-size: 26rpx; padding: 10rpx 0 24rpx; }
.form-group { background: #fff; padding: 20rpx; border-radius: 16rpx; margin-bottom: 30rpx; }
.input-box { border-bottom: 1px solid #eee; padding: 24rpx 10rpx; font-size: 28rpx; }
.textarea-box { width: 100%; height: 160rpx; background: #f9f9f9; padding: 20rpx; box-sizing: border-box; border-radius: 8rpx; font-size: 28rpx; margin-top: 20rpx; }
.btn-primary { background: #007aff; color: #fff; border-radius: 50rpx; margin-bottom: 40rpx; }
.btn-secondary { background: #ff9800; color: #fff; border-radius: 50rpx; margin-top: 20rpx; }
.result-box { margin-top: 40rpx; }
.result-title { font-size: 32rpx; font-weight: bold; margin-bottom: 20rpx; }
.name-card { background: #fff; padding: 30rpx; border-radius: 16rpx; margin-bottom: 24rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); }
.name-header { display: flex; justify-content: space-between; gap: 16rpx; align-items: center; margin-bottom: 16rpx; }
.name-text { font-size: 40rpx; font-weight: bold; color: #333; }
.favorite-btn { margin: 0; color: #fff; background: #ff9800; font-size: 24rpx; }
.export-btn { margin: 18rpx 0 0; color: #fff; background: #2e7d32; font-size: 24rpx; }
.domain-tag { display: inline-block; font-size: 22rpx; padding: 6rpx 16rpx; border-radius: 30rpx; margin-bottom: 12rpx; }
.domain-success { background: #e8f5e9; color: #4caf50; }
.domain-fail { background: #ffebee; color: #f44336; }
.company-enrichment { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 14rpx; margin: 10rpx 0 14rpx; }
.alias-row { display: flex; flex-wrap: wrap; gap: 12rpx; color: #334155; font-size: 23rpx; line-height: 1.6; }
.domain-checks { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 10rpx; }
.domain-check { font-size: 21rpx; padding: 5rpx 12rpx; border-radius: 8rpx; }
.brand-warning { margin-top: 10rpx; color: #8a5a00; background: #fff8e1; border-radius: 8rpx; padding: 10rpx; font-size: 22rpx; line-height: 1.5; }
.score-panel { background: #f7fbff; border: 1px solid #e0efff; border-radius: 12rpx; padding: 18rpx; margin: 14rpx 0; }
.score-head { display: flex; align-items: baseline; gap: 10rpx; margin-bottom: 14rpx; }
.score-total { font-size: 42rpx; font-weight: 800; color: #1677ff; }
.score-unit { font-size: 24rpx; color: #4b6b8a; }
.score-grid { display: flex; gap: 10rpx; }
.score-item { flex: 1; min-width: 0; background: #fff; border-radius: 8rpx; padding: 10rpx 6rpx; text-align: center; }
.score-label { display: block; font-size: 22rpx; color: #667085; }
.score-value { display: block; font-size: 28rpx; font-weight: 700; color: #222; margin-top: 4rpx; }
.score-explain { color: #52677a; font-size: 24rpx; line-height: 1.6; margin-top: 14rpx; }
.name-detail { font-size: 26rpx; color: #666; line-height: 1.6; margin-bottom: 8rpx; }
.label { font-weight: bold; color: #333; }
.preference-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12rpx; margin-top: 18rpx; }
.preference-btn { margin: 0; color: #1677ff; background: #f7fbff; font-size: 24rpx; border-radius: 8rpx; }
.preference-btn.primary { color: #fff; background: #1677ff; }
.feedback-box { margin-top: 40rpx; background: #fff; padding: 30rpx; border-radius: 16rpx; }
</style>
