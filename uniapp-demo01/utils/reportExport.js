import http from '@/http/http.js';

const FORMAT_LABELS = {
  pdf: 'PDF',
  image: '图片',
  txt: '文本'
};

const FORMAT_TYPES = {
  pdf: 'pdf',
  txt: 'txt'
};

const FORMAT_ACTIONS = ['导出 PDF', '导出图片', '导出文本'];
const FORMAT_VALUES = ['pdf', 'image', 'txt'];

const openExportedFile = (filePath, format, name) => {
  if (format === 'image') {
    uni.previewImage({ urls: [filePath], current: filePath });
    return;
  }

  uni.openDocument({
    filePath,
    fileType: FORMAT_TYPES[format],
    showMenu: true,
    fail: () => {
      uni.showToast({ title: `${name}已导出`, icon: 'none' });
    }
  });
};

const exportDownloadedReport = async (downloadFn, format, name) => {
  uni.showLoading({ title: `导出${FORMAT_LABELS[format]}中...` });
  try {
    const filePath = await downloadFn(format);
    uni.hideLoading();
    openExportedFile(filePath, format, name);
  } catch (error) {
    uni.hideLoading();
    console.error('导出报告失败:', error);
  }
};

export const chooseAndExportReport = (historyId, name = '起名方案') => {
  if (!historyId) {
    uni.showToast({ title: '当前方案暂不可导出', icon: 'none' });
    return;
  }

  uni.showActionSheet({
    itemList: FORMAT_ACTIONS,
    success: ({ tapIndex }) => {
      exportReport(historyId, FORMAT_VALUES[tapIndex], name);
    }
  });
};

export const exportReport = async (historyId, format, name = '起名方案') => {
  await exportDownloadedReport(
    (selectedFormat) => http.downloadHistoryReport(historyId, selectedFormat),
    format,
    name
  );
};

export const chooseAndExportProjectReport = (projectId, name = '项目命名方案') => {
  if (!projectId) {
    uni.showToast({ title: '当前项目暂不可导出', icon: 'none' });
    return;
  }

  uni.showActionSheet({
    itemList: FORMAT_ACTIONS,
    success: ({ tapIndex }) => {
      exportProjectReport(projectId, FORMAT_VALUES[tapIndex], name);
    }
  });
};

export const exportProjectReport = async (projectId, format, name = '项目命名方案') => {
  await exportDownloadedReport(
    (selectedFormat) => http.downloadProjectReport(projectId, selectedFormat),
    format,
    name
  );
};
