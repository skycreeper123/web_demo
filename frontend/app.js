const VIEW_META = {
  home: {
    title: "首页",
    subtitle: "在两个工作流之间切换：图片 I2V Prompt 和视频编辑 Prompt。",
  },
  image: {
    title: "图片 -> I2V Prompt",
    subtitle: "选择图片、编辑图片 Prompt 配置、批量生成图生视频 Prompt。",
  },
  video: {
    title: "视频 -> 视频编辑 Prompt",
    subtitle: "选择视频和参考图，先按同名规则匹配，再批量生成视频编辑 Prompt。",
  },
};

const state = {
  currentView: "home",
  defaults: null,
  browserSessionId: "",
  browserHeartbeatTimer: null,
  image: {
    files: [],
    filesExpanded: false,
    apiConfig: null,
    promptConfig: null,
    jobId: "",
    job: null,
    outputs: [],
    pollTimer: null,
  },
  video: {
    videoFiles: [],
    videoFilesExpanded: false,
    referenceFiles: [],
    referenceFilesExpanded: false,
    apiConfig: null,
    promptConfig: null,
    matchResults: [],
    matchSummary: null,
    matchResultsExpanded: false,
    jobId: "",
    job: null,
    outputs: [],
    pollTimer: null,
  },
};

const els = {
  viewTitle: document.getElementById("viewTitle"),
  viewSubtitle: document.getElementById("viewSubtitle"),
  navHomeBtn: document.getElementById("navHomeBtn"),
  navBackBtn: document.getElementById("navBackBtn"),
  shutdownAppBtn: document.getElementById("shutdownAppBtn"),
  homeView: document.getElementById("homeView"),
  imageView: document.getElementById("imageView"),
  videoView: document.getElementById("videoView"),
  goImageViewBtn: document.getElementById("goImageViewBtn"),
  goVideoViewBtn: document.getElementById("goVideoViewBtn"),

  imageInput: document.getElementById("imageInput"),
  imageDropzone: document.getElementById("imageDropzone"),
  imageFileList: document.getElementById("imageFileList"),
  imageUrlInput: document.getElementById("imageUrlInput"),
  imageSelectedCount: document.getElementById("imageSelectedCount"),
  imageStatusBadge: document.getElementById("imageStatusBadge"),
  imageJobMeta: document.getElementById("imageJobMeta"),
  imageResultCount: document.getElementById("imageResultCount"),
  imageOutputRootValue: document.getElementById("imageOutputRootValue"),
  imageApiKey: document.getElementById("imageApiKey"),
  imageBaseUrl: document.getElementById("imageBaseUrl"),
  imageModel: document.getElementById("imageModel"),
  imageOutputDir: document.getElementById("imageOutputDir"),
  imageUseMock: document.getElementById("imageUseMock"),
  imageOverwrite: document.getElementById("imageOverwrite"),
  imageModeBadge: document.getElementById("imageModeBadge"),
  imageApiConfigPath: document.getElementById("imageApiConfigPath"),
  reloadImageApiConfigBtn: document.getElementById("reloadImageApiConfigBtn"),
  saveImageApiConfigBtn: document.getElementById("saveImageApiConfigBtn"),
  imagePromptConfigPath: document.getElementById("imagePromptConfigPath"),
  imageSystemPrompt: document.getElementById("imageSystemPrompt"),
  imageUserPrompt: document.getElementById("imageUserPrompt"),
  reloadImagePromptConfigBtn: document.getElementById("reloadImagePromptConfigBtn"),
  saveImagePromptConfigBtn: document.getElementById("saveImagePromptConfigBtn"),
  imageProgressBar: document.getElementById("imageProgressBar"),
  imageProgressText: document.getElementById("imageProgressText"),
  imageProgressDetail: document.getElementById("imageProgressDetail"),
  startImageBtn: document.getElementById("startImageBtn"),
  refreshImageJobBtn: document.getElementById("refreshImageJobBtn"),
  reloadImageFilesBtn: document.getElementById("reloadImageFilesBtn"),
  openImageOutputBtn: document.getElementById("openImageOutputBtn"),
  imageLogBox: document.getElementById("imageLogBox"),
  imageOutputList: document.getElementById("imageOutputList"),

  videoInput: document.getElementById("videoInput"),
  videoDropzone: document.getElementById("videoDropzone"),
  videoFileList: document.getElementById("videoFileList"),
  videoUrlInput: document.getElementById("videoUrlInput"),
  referenceInput: document.getElementById("referenceInput"),
  referenceDropzone: document.getElementById("referenceDropzone"),
  referenceFileList: document.getElementById("referenceFileList"),
  referenceUrlInput: document.getElementById("referenceUrlInput"),
  videoSelectedCount: document.getElementById("videoSelectedCount"),
  referenceSelectedCount: document.getElementById("referenceSelectedCount"),
  videoMatchBadge: document.getElementById("videoMatchBadge"),
  videoMatchMeta: document.getElementById("videoMatchMeta"),
  videoResultCount: document.getElementById("videoResultCount"),
  scanVideoMatchBtn: document.getElementById("scanVideoMatchBtn"),
  videoApiKey: document.getElementById("videoApiKey"),
  videoBaseUrl: document.getElementById("videoBaseUrl"),
  videoModel: document.getElementById("videoModel"),
  videoOutputDir: document.getElementById("videoOutputDir"),
  videoUseMock: document.getElementById("videoUseMock"),
  videoOverwrite: document.getElementById("videoOverwrite"),
  videoModeBadge: document.getElementById("videoModeBadge"),
  videoApiConfigPath: document.getElementById("videoApiConfigPath"),
  reloadVideoApiConfigBtn: document.getElementById("reloadVideoApiConfigBtn"),
  saveVideoApiConfigBtn: document.getElementById("saveVideoApiConfigBtn"),
  videoPromptConfigPath: document.getElementById("videoPromptConfigPath"),
  videoSystemPrompt: document.getElementById("videoSystemPrompt"),
  videoUserPrompt: document.getElementById("videoUserPrompt"),
  reloadVideoPromptConfigBtn: document.getElementById("reloadVideoPromptConfigBtn"),
  saveVideoPromptConfigBtn: document.getElementById("saveVideoPromptConfigBtn"),
  videoMatchSummary: document.getElementById("videoMatchSummary"),
  videoMatchTable: document.getElementById("videoMatchTable"),
  videoProgressBar: document.getElementById("videoProgressBar"),
  videoProgressText: document.getElementById("videoProgressText"),
  videoProgressDetail: document.getElementById("videoProgressDetail"),
  startVideoBtn: document.getElementById("startVideoBtn"),
  refreshVideoJobBtn: document.getElementById("refreshVideoJobBtn"),
  reloadVideoFilesBtn: document.getElementById("reloadVideoFilesBtn"),
  openVideoOutputBtn: document.getElementById("openVideoOutputBtn"),
  videoLogBox: document.getElementById("videoLogBox"),
  videoOutputList: document.getElementById("videoOutputList"),
};

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function createBrowserSessionId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `browser-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function normalizeDisplayPath(value) {
  const text = String(value || "").trim();
  if (!text) return "";

  const normalized = text.replaceAll("\\", "/");
  const markers = [
    "backend/",
    "frontend/",
    "uploads/",
    "outputs/",
    "image_prompt_config.json",
    "video_prompt_config.json",
    "api_config.json",
  ];

  for (const marker of markers) {
    const index = normalized.toLowerCase().indexOf(marker.toLowerCase());
    if (index >= 0) {
      return normalized.slice(index);
    }
  }

  return normalized;
}

function normalizeLogLines(lines) {
  return (lines || []).map((line) => normalizeDisplayPath(line));
}

async function postBrowserSession(path, payload) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    keepalive: true,
  });
  if (!res.ok) {
    throw new Error(`Browser session request failed: ${res.status}`);
  }
  return res.json();
}

async function registerBrowserSession() {
  if (!state.browserSessionId) {
    state.browserSessionId = createBrowserSessionId();
  }
  await postBrowserSession("/api/browser-session/register", { sessionId: state.browserSessionId });
}

async function heartbeatBrowserSession() {
  if (!state.browserSessionId) return;
  try {
    await postBrowserSession("/api/browser-session/heartbeat", { sessionId: state.browserSessionId });
  } catch {
    // Ignore transient heartbeat failures; the next tick or page refresh can recover.
  }
}

function closeBrowserSession() {
  if (!state.browserSessionId) return;
  const payload = JSON.stringify({ sessionId: state.browserSessionId });
  const blob = new Blob([payload], { type: "application/json" });
  if (navigator.sendBeacon) {
    navigator.sendBeacon("/api/browser-session/close", blob);
    return;
  }
  fetch("/api/browser-session/close", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
    keepalive: true,
  }).catch(() => {});
}

function startBrowserHeartbeat() {
  if (state.browserHeartbeatTimer) {
    clearInterval(state.browserHeartbeatTimer);
  }
  state.browserHeartbeatTimer = setInterval(() => {
    heartbeatBrowserSession();
  }, 5000);
}

async function shutdownApp() {
  if (state.browserHeartbeatTimer) {
    clearInterval(state.browserHeartbeatTimer);
    state.browserHeartbeatTimer = null;
  }

  try {
    await fetch("/api/app/terminate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId: state.browserSessionId || "" }),
      keepalive: true,
    });
  } catch {
    // Ignore fetch errors here because the backend may already be shutting down.
  }

  closeBrowserSession();

  try {
    window.open("", "_self");
    window.close();
  } catch {
    // Ignore browser close restrictions and fall through to the fallback UI.
  }

  setTimeout(() => {
    document.body.innerHTML = `
      <main style="font-family: sans-serif; padding: 32px; line-height: 1.6;">
        <h1>服务已退出</h1>
        <p>后端进程已收到退出指令。这个页面现在可以手动关闭。</p>
      </main>
    `;
  }, 150);
}

function isRealApiMode(apiKeyInput, mockCheckbox) {
  return apiKeyInput.value.trim().length > 0 && !mockCheckbox.checked;
}

function isRemoteHttpUrl(value) {
  try {
    const parsed = new URL(String(value).trim());
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function inferNameFromUrl(url, fallbackPrefix, index) {
  const parsed = new URL(url);
  const rawName = decodeURIComponent(parsed.pathname.split("/").pop() || "").trim();
  return rawName || `${fallbackPrefix}-${index + 1}`;
}

function parseRemoteMediaLines(text, fallbackPrefix) {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const parts = line.includes("|") ? line.split("|") : [line];
      const url = String(parts.at(-1) || "").trim();
      if (!isRemoteHttpUrl(url)) {
        throw new Error(`发现无效媒体 URL：${url}`);
      }
      const name = String(parts.length > 1 ? parts.slice(0, -1).join("|") : "").trim() || inferNameFromUrl(url, fallbackPrefix, index);
      return { name, url };
    });
}

function getImageRemoteItems() {
  return parseRemoteMediaLines(els.imageUrlInput.value, "image");
}

function getVideoRemoteItems() {
  return parseRemoteMediaLines(els.videoUrlInput.value, "video");
}

function getReferenceRemoteItems() {
  return parseRemoteMediaLines(els.referenceUrlInput.value, "reference");
}

function getImageItemsForSubmission() {
  const remoteItems = getImageRemoteItems();
  const apiMode = isRealApiMode(els.imageApiKey, els.imageUseMock);

  if (apiMode) {
    if (!remoteItems.length) {
      throw new Error("真实 API 模式下，请提供官方可访问的图片 URL；不要直接发送本地图片文件。");
    }
    return remoteItems.map((item) => ({ name: item.name, imageUrl: item.url }));
  }

  if (remoteItems.length) {
    return remoteItems.map((item) => ({ name: item.name, imageUrl: item.url }));
  }

  return null;
}

function getVideoAndReferenceEntries() {
  const apiMode = isRealApiMode(els.videoApiKey, els.videoUseMock);
  const remoteVideos = getVideoRemoteItems();
  const remoteReferences = getReferenceRemoteItems();

  if (apiMode) {
    if (!remoteVideos.length) {
      throw new Error("真实 API 模式下，请提供官方可访问的视频 URL。");
    }
    if (!remoteReferences.length) {
      throw new Error("真实 API 模式下，请提供官方可访问的参考图 URL。");
    }
    return { apiMode, videos: remoteVideos, references: remoteReferences };
  }

  if (remoteVideos.length || remoteReferences.length) {
    return {
      apiMode,
      videos: remoteVideos.length ? remoteVideos : state.video.videoFiles.map((file) => ({ name: file.name, file })),
      references: remoteReferences.length ? remoteReferences : state.video.referenceFiles.map((file) => ({ name: file.name, file })),
    };
  }

  return {
    apiMode,
    videos: state.video.videoFiles.map((file) => ({ name: file.name, file })),
    references: state.video.referenceFiles.map((file) => ({ name: file.name, file })),
  };
}

function getFileExtension(file) {
  const match = file.name.match(/\.([^.]+)$/);
  if (match) return match[1].toUpperCase();
  if (file.type) return file.type.split("/").pop().toUpperCase();
  return "FILE";
}

function summarizeFormats(files) {
  const formats = [...new Set(files.map(getFileExtension))];
  if (!formats.length) return "FILE";
  const visible = formats.slice(0, 4);
  return formats.length > 4
    ? `${visible.join(" / ")} +${formats.length - 4}`
    : visible.join(" / ");
}

function toReadableJobStatus(status) {
  switch (status) {
    case "running":
      return "运行中";
    case "completed":
      return "已完成";
    case "failed":
      return "失败";
    case "queued":
      return "排队中";
    default:
      return "待开始";
  }
}

function toReadableMatchStatus(status) {
  switch (status) {
    case "matched":
      return "已匹配";
    case "partial_match":
      return "部分匹配";
    case "missing_reference":
      return "缺少参考图";
    case "naming_conflict":
      return "命名冲突";
    default:
      return "未扫描";
  }
}

function statusClass(status) {
  switch (status) {
    case "matched":
      return "status-matched";
    case "partial_match":
      return "status-partial";
    case "missing_reference":
      return "status-missing";
    case "naming_conflict":
      return "status-conflict";
    default:
      return "status-partial";
  }
}

function setView(view) {
  state.currentView = view;
  els.homeView.hidden = view !== "home";
  els.imageView.hidden = view !== "image";
  els.videoView.hidden = view !== "video";
  els.viewTitle.textContent = VIEW_META[view].title;
  els.viewSubtitle.textContent = VIEW_META[view].subtitle;
  els.navBackBtn.disabled = view === "home";
}

function setModuleModeBadge(apiInput, mockCheckbox, badgeEl) {
  const hasKey = apiInput.value.trim().length > 0;
  const useMock = mockCheckbox.checked;
  if (useMock && hasKey) {
    badgeEl.textContent = "Hybrid";
  } else if (useMock) {
    badgeEl.textContent = "Mock";
  } else {
    badgeEl.textContent = "API";
  }
}

function renderFileRows(files) {
  return files.map((file) => `
    <div class="file-row">
      <div>
        <strong>${escapeHtml(file.name)}</strong>
        <small>${formatBytes(file.size)}</small>
      </div>
      <small>${escapeHtml(file.type || getFileExtension(file))}</small>
    </div>
  `).join("");
}

function renderStackList(files, target, emptyText, options = {}) {
  if (!files.length) {
    target.classList.add("empty");
    target.textContent = emptyText;
    return;
  }

  const {
    label = "文件",
    previewCount = 4,
    expanded = false,
    toggleKey = "",
  } = options;

  const previewFiles = files.slice(0, previewCount);
  const remainingFiles = files.slice(previewCount);
  const totalBytes = files.reduce((sum, file) => sum + (file.size || 0), 0);

  target.classList.remove("empty");
  target.innerHTML = `
    <div class="file-summary-card">
      <div class="file-summary-copy">
        <strong>已加载 ${files.length} 个${escapeHtml(label)}</strong>
        <small>总大小 ${formatBytes(totalBytes)} · 格式 ${escapeHtml(summarizeFormats(files))}</small>
      </div>
      ${remainingFiles.length ? `
        <button
          type="button"
          class="btn btn-ghost file-toggle"
          data-list-toggle="${escapeHtml(toggleKey)}"
          aria-expanded="${expanded ? "true" : "false"}"
        >
          ${expanded ? "收起列表" : `展开全部 (${files.length})`}
        </button>
      ` : `
        <span class="chip chip-soft">已全部显示</span>
      `}
    </div>
    <div class="file-preview-note">
      默认展示前 ${Math.min(files.length, previewCount)} 项，避免目录过长影响主流程。
    </div>
    <div class="file-preview-list">
      ${renderFileRows(previewFiles)}
    </div>
    ${remainingFiles.length ? `
      <div class="file-expand-shell ${expanded ? "is-open" : ""}">
        <div class="file-expand-note">其余 ${remainingFiles.length} 个${escapeHtml(label)}</div>
        ${expanded ? `<div class="file-list-scroll">${renderFileRows(remainingFiles)}</div>` : ""}
      </div>
    ` : ""}
  `;
}

function listViewConfig(toggleKey) {
  switch (toggleKey) {
    case "image":
      return {
        files: state.image.files,
        expanded: state.image.filesExpanded,
        target: els.imageFileList,
        emptyText: "还没有选择图片",
        label: "图片",
      };
    case "video":
      return {
        files: state.video.videoFiles,
        expanded: state.video.videoFilesExpanded,
        target: els.videoFileList,
        emptyText: "还没有选择视频",
        label: "视频",
      };
    case "reference":
      return {
        files: state.video.referenceFiles,
        expanded: state.video.referenceFilesExpanded,
        target: els.referenceFileList,
        emptyText: "还没有选择参考图",
        label: "参考图",
      };
    default:
      return null;
  }
}

function renderNamedStackList(toggleKey) {
  const config = listViewConfig(toggleKey);
  if (!config) return;
  renderStackList(config.files, config.target, config.emptyText, {
    label: config.label,
    previewCount: 4,
    expanded: config.expanded,
    toggleKey,
  });
}

function setListExpanded(toggleKey, expanded) {
  switch (toggleKey) {
    case "image":
      state.image.filesExpanded = expanded;
      break;
    case "video":
      state.video.videoFilesExpanded = expanded;
      break;
    case "reference":
      state.video.referenceFilesExpanded = expanded;
      break;
    default:
      return;
  }
  renderNamedStackList(toggleKey);
}

function renderMatchRows(items) {
  return items.map((item) => `
    <div class="match-row">
      <div>
        <strong>${escapeHtml(item.video)}</strong>
        <small>${item.canGenerate ? "可生成" : "需修正后再生成"}</small>
      </div>
      <div>${escapeHtml(item.matchKey)}</div>
      <div>${escapeHtml(item.referenceMain || "-")}</div>
      <div>${escapeHtml(item.referenceAlt1 || "-")}</div>
      <div>${escapeHtml(item.referenceAlt2 || "-")}</div>
      <div><span class="status-pill ${statusClass(item.status)}">${toReadableMatchStatus(item.status)}</span></div>
    </div>
  `).join("");
}

function renderOutputList(files, target, counter, emptyText) {
  counter.textContent = String(files.length);
  if (!files.length) {
    target.classList.add("empty");
    target.textContent = emptyText;
    return;
  }
  target.classList.remove("empty");
  target.innerHTML = files.map((file) => `
    <div class="output-row">
      <div>
        <strong>${escapeHtml(file.name)}</strong>
        <small>已生成</small>
      </div>
      <a href="${file.url}" target="_blank" rel="noreferrer">打开</a>
    </div>
  `).join("");
}

function renderImageJob(job) {
  state.image.job = job;
  const percent = job.total ? Math.round((job.progress / job.total) * 100) : 0;
  els.imageProgressBar.style.width = `${percent}%`;
  els.imageStatusBadge.textContent = toReadableJobStatus(job.status);
  els.imageJobMeta.textContent = job.id ? `Job ${job.id} · ${job.progress}/${job.total}` : "未启动任务";
  els.imageProgressText.textContent = toReadableJobStatus(job.status);
  els.imageProgressDetail.textContent = job.status === "completed"
    ? "图片 Prompt 已生成完成。"
    : job.status === "failed"
      ? `任务失败：${job.error || "unknown"}`
      : job.status === "running"
        ? "正在处理图片并保存结果。"
        : "等待开始。";
  els.imageOutputRootValue.textContent = normalizeDisplayPath(job.output_dir) || normalizeDisplayPath(els.imageOutputDir.value.trim()) || "未设置";
}

function renderVideoJob(job) {
  state.video.job = job;
  const percent = job.total ? Math.round((job.progress / job.total) * 100) : 0;
  els.videoProgressBar.style.width = `${percent}%`;
  els.videoProgressText.textContent = toReadableJobStatus(job.status);
  els.videoProgressDetail.textContent = job.status === "completed"
    ? "视频编辑 Prompt 已生成完成。"
    : job.status === "failed"
      ? `任务失败：${job.error || "unknown"}`
      : job.status === "running"
        ? "正在打包视频并提交生成任务。"
        : "等待开始。";
}

function setImageLog(lines) {
  const normalizedLines = normalizeLogLines(lines);
  els.imageLogBox.textContent = normalizedLines.length ? normalizedLines.join("\n") : "暂无日志";
}

function setVideoLog(lines) {
  const normalizedLines = normalizeLogLines(lines);
  els.videoLogBox.textContent = normalizedLines.length ? normalizedLines.join("\n") : "暂无日志";
}

function getImagePromptPayload() {
  return {
    system_prompt: els.imageSystemPrompt.value,
    user_text: els.imageUserPrompt.value,
  };
}

function getVideoPromptPayload() {
  return {
    system_prompt: els.videoSystemPrompt.value,
    user_text: els.videoUserPrompt.value,
  };
}

function renderImagePromptConfig(data) {
  state.image.promptConfig = data.config || null;
  els.imagePromptConfigPath.textContent = normalizeDisplayPath(data.path) || "未找到配置文件";
  els.imageSystemPrompt.value = data.config?.system_prompt || "";
  els.imageUserPrompt.value = data.config?.user_text || "";
}

function renderVideoPromptConfig(data) {
  state.video.promptConfig = data.config || null;
  els.videoPromptConfigPath.textContent = normalizeDisplayPath(data.path) || "未找到配置文件";
  els.videoSystemPrompt.value = data.config?.system_prompt || "";
  els.videoUserPrompt.value = data.config?.user_text || "";
}

async function loadDefaults() {
  const res = await fetch("/api/config");
  const data = await res.json();
  state.defaults = data;

  els.imageBaseUrl.value = data.baseUrl || "";
  els.imageModel.value = data.model || "";
  els.imageOutputDir.value = data.imageOutputRoot || data.outputRoot || "";
  els.imageUseMock.checked = data.useMock ?? true;
  els.imageApiKey.placeholder = "直接粘贴 API Key";
  els.imageOutputRootValue.textContent = data.imageOutputRoot || data.outputRoot || "未设置";

  els.videoBaseUrl.value = data.baseUrl || "";
  els.videoModel.value = data.model || "";
  els.videoOutputDir.value = data.videoOutputRoot || data.outputRoot || "";
  els.videoUseMock.checked = data.useMock ?? true;
  els.videoApiKey.placeholder = "直接粘贴 API Key";

  setModuleModeBadge(els.imageApiKey, els.imageUseMock, els.imageModeBadge);
  setModuleModeBadge(els.videoApiKey, els.videoUseMock, els.videoModeBadge);
}

async function loadImagePromptConfig() {
  const res = await fetch("/api/prompt-config/image");
  const data = await res.json();
  renderImagePromptConfig(data);
}

async function loadVideoPromptConfig() {
  const res = await fetch("/api/prompt-config/video");
  const data = await res.json();
  renderVideoPromptConfig(data);
}

async function savePromptConfig(kind, config) {
  const res = await fetch(`/api/prompt-config/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "保存配置失败");
  }
  return data;
}

async function saveImagePromptConfig() {
  try {
    const data = await savePromptConfig("image", {
      ...(state.image.promptConfig || {}),
      ...getImagePromptPayload(),
    });
    renderImagePromptConfig(data);
    alert("图片 Prompt 配置已保存");
  } catch (error) {
    alert(error.message);
  }
}

async function saveVideoPromptConfig() {
  try {
    const data = await savePromptConfig("video", {
      ...(state.video.promptConfig || {}),
      ...getVideoPromptPayload(),
    });
    renderVideoPromptConfig(data);
    alert("视频 Prompt 配置已保存");
  } catch (error) {
    alert(error.message);
  }
}

function getImageApiConfigPayload() {
  return {
    api_key: els.imageApiKey.value.trim(),
    base_url: els.imageBaseUrl.value.trim(),
    model: els.imageModel.value.trim(),
    output_dir: els.imageOutputDir.value.trim(),
    use_mock: els.imageUseMock.checked,
    overwrite: els.imageOverwrite.checked,
  };
}

function getVideoApiConfigPayload() {
  return {
    api_key: els.videoApiKey.value.trim(),
    base_url: els.videoBaseUrl.value.trim(),
    model: els.videoModel.value.trim(),
    output_dir: els.videoOutputDir.value.trim(),
    use_mock: els.videoUseMock.checked,
    overwrite: els.videoOverwrite.checked,
  };
}

function renderImageApiConfig(data) {
  state.image.apiConfig = data.config || null;
  els.imageApiConfigPath.textContent = normalizeDisplayPath(data.path) || "未找到配置文件";
  els.imageApiKey.value = data.config?.api_key || "";
  els.imageBaseUrl.value = data.config?.base_url || "";
  els.imageModel.value = data.config?.model || "";
  els.imageOutputDir.value = normalizeDisplayPath(data.config?.output_dir || "");
  els.imageUseMock.checked = data.config?.use_mock ?? true;
  els.imageOverwrite.checked = data.config?.overwrite ?? false;
  els.imageApiKey.placeholder = "直接粘贴 API Key";
  els.imageOutputRootValue.textContent = normalizeDisplayPath(els.imageOutputDir.value.trim()) || "未设置";
  setModuleModeBadge(els.imageApiKey, els.imageUseMock, els.imageModeBadge);
}

function renderVideoApiConfig(data) {
  state.video.apiConfig = data.config || null;
  els.videoApiConfigPath.textContent = normalizeDisplayPath(data.path) || "未找到配置文件";
  els.videoApiKey.value = data.config?.api_key || "";
  els.videoBaseUrl.value = data.config?.base_url || "";
  els.videoModel.value = data.config?.model || "";
  els.videoOutputDir.value = normalizeDisplayPath(data.config?.output_dir || "");
  els.videoUseMock.checked = data.config?.use_mock ?? true;
  els.videoOverwrite.checked = data.config?.overwrite ?? false;
  els.videoApiKey.placeholder = "直接粘贴 API Key";
  setModuleModeBadge(els.videoApiKey, els.videoUseMock, els.videoModeBadge);
}

async function loadDefaults() {
  const res = await fetch("/api/config");
  const data = await res.json();
  state.defaults = data;
  renderImageApiConfig({ path: data.imageApiConfigPath, config: data.imageApiConfig });
  renderVideoApiConfig({ path: data.videoApiConfigPath, config: data.videoApiConfig });
}

async function loadImageApiConfig() {
  const res = await fetch("/api/runtime-config/image");
  const data = await res.json();
  renderImageApiConfig(data);
}

async function loadVideoApiConfig() {
  const res = await fetch("/api/runtime-config/video");
  const data = await res.json();
  renderVideoApiConfig(data);
}

async function saveApiConfig(kind, config) {
  const res = await fetch(`/api/runtime-config/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "保存配置失败");
  }
  return data;
}

async function saveImageApiConfig() {
  try {
    const data = await saveApiConfig("image", {
      ...(state.image.apiConfig || {}),
      ...getImageApiConfigPayload(),
    });
    renderImageApiConfig(data);
    alert("图片 API 配置已保存");
  } catch (error) {
    alert(error.message);
  }
}

async function saveVideoApiConfig() {
  try {
    const data = await saveApiConfig("video", {
      ...(state.video.apiConfig || {}),
      ...getVideoApiConfigPayload(),
    });
    renderVideoApiConfig(data);
    alert("视频 API 配置已保存");
  } catch (error) {
    alert(error.message);
  }
}

function toDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function bindDropzone(dropzone, input, onFiles) {
  const prevent = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };

  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, prevent, false);
  });
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => dropzone.classList.add("dragover"));
  });
  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => dropzone.classList.remove("dragover"));
  });
  dropzone.addEventListener("drop", (event) => {
    const dt = new DataTransfer();
    Array.from(event.dataTransfer.files || []).forEach((file) => dt.items.add(file));
    input.files = dt.files;
    onFiles(Array.from(dt.files));
  });
}

async function startImageGeneration() {
  try {
    els.startImageBtn.disabled = true;
    els.imageProgressText.textContent = "准备中";
    els.imageProgressDetail.textContent = "正在整理图片输入并提交任务。";

    let images = getImageItemsForSubmission();
    if (!images) {
      if (!state.image.files.length) {
        throw new Error("请先选择图片，或填写官方可访问的图片 URL。");
      }
      images = [];
      for (const file of state.image.files) {
        const dataUrl = await toDataUrl(file);
        images.push({ name: file.name, dataUrl });
      }
    }

    const res = await fetch("/api/generate/image-prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        apiKey: els.imageApiKey.value.trim(),
        baseUrl: els.imageBaseUrl.value.trim(),
        model: els.imageModel.value.trim(),
        outputDir: els.imageOutputDir.value.trim(),
        overwrite: els.imageOverwrite.checked,
        useMock: els.imageUseMock.checked,
        promptConfig: {
          ...(state.image.promptConfig || {}),
          ...getImagePromptPayload(),
        },
        images,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "启动失败");
    }

    state.image.jobId = data.jobId;
    setImageLog(data.job?.logs || []);
    renderImageJob(data.job);
    pollImageJob();
  } catch (error) {
    els.startImageBtn.disabled = false;
    alert(error.message);
  }
}

async function pollImageJob() {
  if (state.image.pollTimer) clearInterval(state.image.pollTimer);
  const tick = async () => {
    if (!state.image.jobId) return;
    const res = await fetch(`/api/jobs/${state.image.jobId}`);
    const job = await res.json();
    renderImageJob(job);
    setImageLog(job.logs || []);

    if (job.output_dir) {
      const filesRes = await fetch(`/api/jobs/${state.image.jobId}/files`);
      const filesData = await filesRes.json();
      state.image.outputs = filesData.files || [];
      renderOutputList(state.image.outputs, els.imageOutputList, els.imageResultCount, "运行后会显示生成的文件");
    }

    if (job.status === "completed" || job.status === "failed") {
      els.startImageBtn.disabled = false;
      clearInterval(state.image.pollTimer);
      state.image.pollTimer = null;
    }
  };
  await tick();
  state.image.pollTimer = setInterval(tick, 1000);
}

async function openImageOutput() {
  if (!state.image.jobId) {
    alert("请先运行一次图片生成任务");
    return;
  }
  const res = await fetch(`/api/jobs/${state.image.jobId}/open-output`, { method: "POST" });
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "无法打开输出目录");
  }
}

async function scanVideoMatches() {
  try {
    const { videos, references } = getVideoAndReferenceEntries();
    if (!videos.length) {
      throw new Error("请先选择视频目录，或填写官方可访问的视频 URL。");
    }
    if (!references.length) {
      throw new Error("请先选择参考图目录，或填写官方可访问的参考图 URL。");
    }

    const res = await fetch("/api/video/scan-match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        videos: videos.map((item) => ({ name: item.name })),
        references: references.map((item) => ({ name: item.name })),
      }),
    });
    const data = await res.json();
    state.video.matchResults = data.matches || [];
    state.video.matchSummary = data.summary || null;
    state.video.matchResultsExpanded = false;
    renderVideoMatches();
  } catch (error) {
    alert(error.message);
  }
}

function renderVideoMatches() {
  const summary = state.video.matchSummary || {
    total: 0,
    matched: 0,
    partial_match: 0,
    missing_reference: 0,
    naming_conflict: 0,
  };
  els.videoMatchSummary.innerHTML = `
    <span class="chip">总数 ${summary.total}</span>
    <span class="chip">成功 ${summary.matched}</span>
    <span class="chip">部分匹配 ${summary.partial_match}</span>
    <span class="chip">缺失 ${summary.missing_reference}</span>
    <span class="chip">冲突 ${summary.naming_conflict}</span>
  `;

  const validCount = state.video.matchResults.filter((item) => item.canGenerate).length;
  els.videoMatchBadge.textContent = summary.total ? `${validCount}/${summary.total}` : "未扫描";
  els.videoMatchMeta.textContent = summary.total
    ? `可生成 ${validCount} 条，阻塞 ${summary.missing_reference + summary.naming_conflict} 条`
    : "等待扫描";

  if (!state.video.matchResults.length) {
    els.videoMatchTable.classList.add("empty");
    els.videoMatchTable.textContent = "完成扫描后，这里会展示每个视频的匹配结果。";
    return;
  }

  els.videoMatchTable.classList.remove("empty");
  els.videoMatchTable.innerHTML = `
    <div class="table-head">
      <div>视频</div>
      <div>匹配键</div>
      <div>主参考图</div>
      <div>参考图 1</div>
      <div>参考图 2</div>
      <div>状态</div>
    </div>
    ${state.video.matchResults.map((item) => `
      <div class="match-row">
        <div>
          <strong>${escapeHtml(item.video)}</strong>
          <small>${item.canGenerate ? "可生成" : "需修正后再生成"}</small>
        </div>
        <div>${escapeHtml(item.matchKey)}</div>
        <div>${escapeHtml(item.referenceMain || "-")}</div>
        <div>${escapeHtml(item.referenceAlt1 || "-")}</div>
        <div>${escapeHtml(item.referenceAlt2 || "-")}</div>
        <div><span class="status-pill ${statusClass(item.status)}">${toReadableMatchStatus(item.status)}</span></div>
      </div>
    `).join("")}
  `;
}

function renderVideoMatches() {
  const summary = state.video.matchSummary || {
    total: 0,
    matched: 0,
    partial_match: 0,
    missing_reference: 0,
    naming_conflict: 0,
  };
  els.videoMatchSummary.innerHTML = `
    <span class="chip">总数 ${summary.total}</span>
    <span class="chip">成功 ${summary.matched}</span>
    <span class="chip">部分匹配 ${summary.partial_match}</span>
    <span class="chip">缺失 ${summary.missing_reference}</span>
    <span class="chip">冲突 ${summary.naming_conflict}</span>
  `;

  const validCount = state.video.matchResults.filter((item) => item.canGenerate).length;
  els.videoMatchBadge.textContent = summary.total ? `${validCount}/${summary.total}` : "未扫描";
  els.videoMatchMeta.textContent = summary.total
    ? `可生成 ${validCount} 条，阻塞 ${summary.missing_reference + summary.naming_conflict} 条`
    : "等待扫描";

  if (!state.video.matchResults.length) {
    els.videoMatchTable.classList.add("empty");
    els.videoMatchTable.textContent = "完成扫描后，这里会展示每个视频的匹配结果。";
    return;
  }

  const previewCount = 5;
  const previewMatches = state.video.matchResults.slice(0, previewCount);
  const remainingMatches = state.video.matchResults.slice(previewCount);

  els.videoMatchTable.classList.remove("empty");
  els.videoMatchTable.innerHTML = `
    <div class="match-preview-shell">
      <div class="file-summary-card">
        <div class="file-summary-copy">
          <strong>已生成 ${state.video.matchResults.length} 条匹配结果</strong>
          <small>默认展示前 ${Math.min(state.video.matchResults.length, previewCount)} 条，详细结果可按需展开。</small>
        </div>
        ${remainingMatches.length ? `
          <button
            type="button"
            class="btn btn-ghost file-toggle"
            data-match-toggle="video"
            aria-expanded="${state.video.matchResultsExpanded ? "true" : "false"}"
          >
            ${state.video.matchResultsExpanded ? "收起匹配表" : `展开全部 (${state.video.matchResults.length})`}
          </button>
        ` : `
          <span class="chip chip-soft">已全部显示</span>
        `}
      </div>

      <div class="match-table-preview">
        <div class="table-head">
          <div>视频</div>
          <div>匹配键</div>
          <div>主参考图</div>
          <div>参考图 1</div>
          <div>参考图 2</div>
          <div>状态</div>
        </div>
        ${renderMatchRows(previewMatches)}
      </div>

      ${remainingMatches.length ? `
        <div class="match-expand-shell ${state.video.matchResultsExpanded ? "is-open" : ""}">
          <div class="file-expand-note">其余 ${remainingMatches.length} 条匹配结果</div>
          ${state.video.matchResultsExpanded ? `
            <div class="match-table-scroll">
              ${renderMatchRows(remainingMatches)}
            </div>
          ` : ""}
        </div>
      ` : ""}
    </div>
  `;
}

async function prepareVideoGenerationItems() {
  const candidates = state.video.matchResults.filter((item) => item.canGenerate);
  if (!candidates.length) {
    throw new Error("当前没有可生成的视频条目，请先扫描并修正匹配结果。");
  }

  const { apiMode, videos, references } = getVideoAndReferenceEntries();
  const videoEntryMap = new Map(videos.map((item) => [item.name, item]));
  const referenceEntryMap = new Map(references.map((item) => [item.name, item]));
  const items = [];

  for (const match of candidates) {
    const videoEntry = videoEntryMap.get(match.video);
    if (!videoEntry) {
      throw new Error(`未找到视频文件：${match.video}`);
    }

    let videoPayload = {};
    if (videoEntry.url) {
      els.videoProgressDetail.textContent = `正在使用视频 URL：${match.video}`;
      videoPayload = { videoUrl: videoEntry.url };
    } else {
      if (apiMode) {
        throw new Error(`真实 API 模式下缺少视频 URL：${match.video}`);
      }
      els.videoProgressDetail.textContent = `正在读取视频文件：${match.video}`;
      videoPayload = { videoDataUrl: await toDataUrl(videoEntry.file) };
    }

    const references = [];
    for (const referenceName of [match.referenceMain, match.referenceAlt1, match.referenceAlt2]) {
      if (!referenceName) continue;
      const referenceEntry = referenceEntryMap.get(referenceName);
      if (!referenceEntry) continue;
      if (referenceEntry.url) {
        references.push({
          name: referenceName,
          url: referenceEntry.url,
        });
      } else {
        if (apiMode) {
          throw new Error(`真实 API 模式下缺少参考图 URL：${referenceName}`);
        }
        references.push({
          name: referenceName,
          dataUrl: await toDataUrl(referenceEntry.file),
        });
      }
    }

    items.push({
      name: match.video,
      matchKey: match.matchKey,
      referenceMain: match.referenceMain,
      referenceAlt1: match.referenceAlt1,
      referenceAlt2: match.referenceAlt2,
      ...videoPayload,
      references,
    });
  }

  return items;
}

async function startVideoGeneration() {
  try {
    els.startVideoBtn.disabled = true;
    els.videoProgressText.textContent = "准备中";
    els.videoProgressDetail.textContent = "正在检查匹配结果并读取视频文件。";

    const videos = await prepareVideoGenerationItems();
    const res = await fetch("/api/generate/video-prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        apiKey: els.videoApiKey.value.trim(),
        baseUrl: els.videoBaseUrl.value.trim(),
        model: els.videoModel.value.trim(),
        outputDir: els.videoOutputDir.value.trim(),
        overwrite: els.videoOverwrite.checked,
        useMock: els.videoUseMock.checked,
        promptConfig: {
          ...(state.video.promptConfig || {}),
          ...getVideoPromptPayload(),
        },
        videos,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "启动失败");
    }

    state.video.jobId = data.jobId;
    setVideoLog(data.job?.logs || []);
    renderVideoJob(data.job);
    pollVideoJob();
  } catch (error) {
    els.startVideoBtn.disabled = false;
    alert(error.message);
  }
}

async function pollVideoJob() {
  if (state.video.pollTimer) clearInterval(state.video.pollTimer);
  const tick = async () => {
    if (!state.video.jobId) return;
    const res = await fetch(`/api/jobs/${state.video.jobId}`);
    const job = await res.json();
    renderVideoJob(job);
    setVideoLog(job.logs || []);

    if (job.output_dir) {
      const filesRes = await fetch(`/api/jobs/${state.video.jobId}/files`);
      const filesData = await filesRes.json();
      state.video.outputs = filesData.files || [];
      renderOutputList(state.video.outputs, els.videoOutputList, els.videoResultCount, "运行后会显示生成的文件");
    }

    if (job.status === "completed" || job.status === "failed") {
      els.startVideoBtn.disabled = false;
      clearInterval(state.video.pollTimer);
      state.video.pollTimer = null;
    }
  };
  await tick();
  state.video.pollTimer = setInterval(tick, 1000);
}

async function openVideoOutput() {
  if (!state.video.jobId) {
    alert("请先运行一次视频生成任务");
    return;
  }
  const res = await fetch(`/api/jobs/${state.video.jobId}/open-output`, { method: "POST" });
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "无法打开输出目录");
  }
}

function bindEvents() {
  els.navHomeBtn.addEventListener("click", () => setView("home"));
  els.navBackBtn.addEventListener("click", () => setView("home"));
  els.shutdownAppBtn.addEventListener("click", shutdownApp);
  els.goImageViewBtn.addEventListener("click", () => setView("image"));
  els.goVideoViewBtn.addEventListener("click", () => setView("video"));

  document.addEventListener("click", (event) => {
    const matchToggleButton = event.target.closest("[data-match-toggle]");
    if (matchToggleButton) {
      state.video.matchResultsExpanded = !state.video.matchResultsExpanded;
      renderVideoMatches();
      return;
    }

    const toggleButton = event.target.closest("[data-list-toggle]");
    if (!toggleButton) return;
    const toggleKey = toggleButton.dataset.listToggle;
    const config = listViewConfig(toggleKey);
    if (!config) return;
    setListExpanded(toggleKey, !config.expanded);
  });

  els.imageInput.addEventListener("change", () => {
    state.image.files = Array.from(els.imageInput.files || []);
    state.image.filesExpanded = false;
    renderNamedStackList("image");
    els.imageSelectedCount.textContent = String(state.image.files.length);
  });
  els.videoInput.addEventListener("change", () => {
    state.video.videoFiles = Array.from(els.videoInput.files || []);
    state.video.videoFilesExpanded = false;
    renderNamedStackList("video");
    els.videoSelectedCount.textContent = String(state.video.videoFiles.length);
  });
  els.referenceInput.addEventListener("change", () => {
    state.video.referenceFiles = Array.from(els.referenceInput.files || []);
    state.video.referenceFilesExpanded = false;
    renderNamedStackList("reference");
    els.referenceSelectedCount.textContent = String(state.video.referenceFiles.length);
  });

  bindDropzone(els.imageDropzone, els.imageInput, (files) => {
    state.image.files = files.filter((file) => file.type.startsWith("image/"));
    state.image.filesExpanded = false;
    renderNamedStackList("image");
    els.imageSelectedCount.textContent = String(state.image.files.length);
  });
  bindDropzone(els.videoDropzone, els.videoInput, (files) => {
    state.video.videoFiles = files.filter((file) => file.type.startsWith("video/") || /\.(mp4|mov|avi|mkv|webm)$/i.test(file.name));
    state.video.videoFilesExpanded = false;
    renderNamedStackList("video");
    els.videoSelectedCount.textContent = String(state.video.videoFiles.length);
  });
  bindDropzone(els.referenceDropzone, els.referenceInput, (files) => {
    state.video.referenceFiles = files.filter((file) => file.type.startsWith("image/"));
    state.video.referenceFilesExpanded = false;
    renderNamedStackList("reference");
    els.referenceSelectedCount.textContent = String(state.video.referenceFiles.length);
  });

  els.imageApiKey.addEventListener("input", () => setModuleModeBadge(els.imageApiKey, els.imageUseMock, els.imageModeBadge));
  els.imageUseMock.addEventListener("change", () => setModuleModeBadge(els.imageApiKey, els.imageUseMock, els.imageModeBadge));
  els.imageOutputDir.addEventListener("input", () => {
    els.imageOutputRootValue.textContent = els.imageOutputDir.value.trim() || "未设置";
  });

  els.videoApiKey.addEventListener("input", () => setModuleModeBadge(els.videoApiKey, els.videoUseMock, els.videoModeBadge));
  els.videoUseMock.addEventListener("change", () => setModuleModeBadge(els.videoApiKey, els.videoUseMock, els.videoModeBadge));

  els.reloadImageApiConfigBtn.addEventListener("click", loadImageApiConfig);
  els.saveImageApiConfigBtn.addEventListener("click", saveImageApiConfig);
  els.reloadImagePromptConfigBtn.addEventListener("click", loadImagePromptConfig);
  els.saveImagePromptConfigBtn.addEventListener("click", saveImagePromptConfig);
  els.startImageBtn.addEventListener("click", startImageGeneration);
  els.refreshImageJobBtn.addEventListener("click", () => state.image.jobId && pollImageJob());
  els.reloadImageFilesBtn.addEventListener("click", async () => {
    if (!state.image.jobId) return;
    const res = await fetch(`/api/jobs/${state.image.jobId}/files`);
    const data = await res.json();
    state.image.outputs = data.files || [];
    renderOutputList(state.image.outputs, els.imageOutputList, els.imageResultCount, "运行后会显示生成的文件");
  });
  els.openImageOutputBtn.addEventListener("click", openImageOutput);

  els.reloadVideoApiConfigBtn.addEventListener("click", loadVideoApiConfig);
  els.saveVideoApiConfigBtn.addEventListener("click", saveVideoApiConfig);
  els.scanVideoMatchBtn.addEventListener("click", scanVideoMatches);
  els.reloadVideoPromptConfigBtn.addEventListener("click", loadVideoPromptConfig);
  els.saveVideoPromptConfigBtn.addEventListener("click", saveVideoPromptConfig);
  els.startVideoBtn.addEventListener("click", startVideoGeneration);
  els.refreshVideoJobBtn.addEventListener("click", () => state.video.jobId && pollVideoJob());
  els.reloadVideoFilesBtn.addEventListener("click", async () => {
    if (!state.video.jobId) return;
    const res = await fetch(`/api/jobs/${state.video.jobId}/files`);
    const data = await res.json();
    state.video.outputs = data.files || [];
    renderOutputList(state.video.outputs, els.videoOutputList, els.videoResultCount, "运行后会显示生成的文件");
  });
  els.openVideoOutputBtn.addEventListener("click", openVideoOutput);

  window.addEventListener("pagehide", closeBrowserSession);
  window.addEventListener("beforeunload", closeBrowserSession);
}

async function init() {
  bindEvents();
  await registerBrowserSession();
  startBrowserHeartbeat();
  setView("home");
  renderNamedStackList("image");
  renderNamedStackList("video");
  renderNamedStackList("reference");
  renderOutputList([], els.imageOutputList, els.imageResultCount, "运行后会显示生成的文件");
  renderOutputList([], els.videoOutputList, els.videoResultCount, "运行后会显示生成的文件");
  renderImageJob({ id: "", status: "idle", progress: 0, total: 0, error: "", output_dir: "" });
  renderVideoJob({ id: "", status: "idle", progress: 0, total: 0, error: "", output_dir: "" });
  renderVideoMatches();
  setImageLog([]);
  setVideoLog([]);
  await loadDefaults();
  await loadImagePromptConfig();
  await loadVideoPromptConfig();
}

init();
