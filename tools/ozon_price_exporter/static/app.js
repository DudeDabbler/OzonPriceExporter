(() => {
  let token = "";
  let lastLogSignature = "";
  let toastTimer = null;

  const byId = (id) => document.getElementById(id);
  const els = {
    profileName: byId("profileName"),
    profileList: byId("profileList"),
    openBrowser: byId("openBrowser"),
    closeBrowser: byId("closeBrowser"),
    checkLogin: byId("checkLogin"),
    startCollection: byId("startCollection"),
    stopCollection: byId("stopCollection"),
    downloadExcel: byId("downloadExcel"),
    shutdownApp: byId("shutdownApp"),
    loginDot: byId("loginDot"),
    loginText: byId("loginText"),
    statusBadge: byId("statusBadge"),
    statusMessage: byId("statusMessage"),
    discovered: byId("discovered"),
    processed: byId("processed"),
    okCount: byId("okCount"),
    failedCount: byId("failedCount"),
    progressBar: byId("progressBar"),
    exportName: byId("exportName"),
    log: byId("log"),
    toast: byId("toast"),
  };

  const phaseNames = {
    idle: "Готово",
    opening_browser: "Открываю браузер",
    waiting_login: "Ожидается вход",
    checking_login: "Проверка входа",
    ready: "Можно собирать",
    discovering: "Поиск товаров",
    collecting: "Сбор цен",
    complete: "Готово",
    stopped: "Остановлено",
    error: "Ошибка",
  };

  function toast(message) {
    els.toast.textContent = message;
    els.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove("show"), 3500);
  }

  async function jsonFetch(url, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (token) headers["X-App-Token"] = token;
    if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
    const response = await fetch(url, { ...options, headers, cache: "no-store" });
    const data = await response.json().catch(() => ({ ok: false, error: `HTTP ${response.status}` }));
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  async function post(url, payload = {}) {
    return jsonFetch(url, { method: "POST", body: JSON.stringify(payload) });
  }

  function renderLogs(logs) {
    const signature = JSON.stringify(logs);
    if (signature === lastLogSignature) return;
    lastLogSignature = signature;
    els.log.replaceChildren();
    if (!logs || logs.length === 0) {
      const empty = document.createElement("div");
      empty.className = "log-empty";
      empty.textContent = "Событий пока нет.";
      els.log.appendChild(empty);
      return;
    }
    logs.slice(-120).forEach((entry) => {
      const line = document.createElement("div");
      line.className = `log-line ${entry.level || "info"}`;
      const ts = document.createElement("span");
      ts.textContent = entry.ts || "";
      const message = document.createElement("span");
      message.textContent = entry.message || "";
      line.append(ts, message);
      els.log.appendChild(line);
    });
    els.log.scrollTop = els.log.scrollHeight;
  }

  function render(status) {
    const phase = status.phase || "idle";
    els.statusBadge.dataset.phase = phase;
    els.statusBadge.textContent = phaseNames[phase] || phase;
    els.statusMessage.textContent = status.message || "";
    els.discovered.textContent = status.discovered || 0;
    els.processed.textContent = status.processed || 0;
    els.okCount.textContent = status.ok || 0;
    els.failedCount.textContent = status.failed || 0;

    const total = Math.max(Number(status.discovered || 0), Number(status.total_hint || 0));
    const processed = Number(status.processed || 0);
    const progress = total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : 0;
    els.progressBar.style.width = `${progress}%`;
    els.exportName.textContent = status.export_filename ? `Файл: ${status.export_filename}` : "";

    els.loginDot.classList.toggle("ok", Boolean(status.logged_in));
    els.loginDot.classList.toggle("warn", Boolean(status.browser_open && !status.logged_in));
    els.loginText.textContent = status.logged_in
      ? `Вход подтверждён${status.profile_name ? ` · ${status.profile_name}` : ""}`
      : status.browser_open
        ? "Браузер открыт, завершите вход в Ozon"
        : "Браузер ещё не открыт";

    const busy = ["opening_browser", "checking_login", "discovering", "collecting"].includes(phase);
    els.profileName.disabled = busy || status.browser_open;
    els.openBrowser.disabled = busy || status.browser_open;
    els.closeBrowser.disabled = !status.browser_open || status.running;
    els.checkLogin.disabled = !status.browser_open || status.running || phase === "checking_login";
    els.startCollection.disabled = !status.logged_in || status.running;
    els.stopCollection.disabled = !status.running;
    els.downloadExcel.disabled = !status.export_ready;
    renderLogs(status.logs || []);
  }

  async function pollStatus() {
    try {
      const data = await jsonFetch("/api/status");
      render(data.status);
    } catch (error) {
      els.statusMessage.textContent = error.message;
    }
  }

  async function loadProfiles() {
    try {
      const data = await jsonFetch("/api/profiles");
      els.profileList.replaceChildren();
      (data.profiles || []).forEach((profile) => {
        const option = document.createElement("option");
        option.value = profile.name;
        els.profileList.appendChild(option);
      });
      if (!els.profileName.value && data.profiles && data.profiles.length) {
        els.profileName.value = data.profiles[0].name;
      }
    } catch (error) {
      toast(error.message);
    }
  }

  els.openBrowser.addEventListener("click", async () => {
    const profileName = els.profileName.value.trim();
    if (!profileName) {
      toast("Укажите название профиля магазина.");
      els.profileName.focus();
      return;
    }
    try {
      await post("/api/browser/open", { profile_name: profileName });
      toast("Команда на открытие браузера принята.");
    } catch (error) { toast(error.message); }
  });

  els.closeBrowser.addEventListener("click", async () => {
    try { await post("/api/browser/close"); } catch (error) { toast(error.message); }
  });

  els.checkLogin.addEventListener("click", async () => {
    try { await post("/api/session/check"); } catch (error) { toast(error.message); }
  });

  els.startCollection.addEventListener("click", async () => {
    try {
      await post("/api/collect/start");
      toast("Сбор запущен.");
    } catch (error) { toast(error.message); }
  });

  els.stopCollection.addEventListener("click", async () => {
    try { await post("/api/collect/stop"); } catch (error) { toast(error.message); }
  });

  els.downloadExcel.addEventListener("click", async () => {
    try {
      const response = await fetch("/api/export", { headers: { "X-App-Token": token }, cache: "no-store" });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match ? match[1] : "ozon_customer_prices.xlsx";
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) { toast(error.message); }
  });

  els.shutdownApp.addEventListener("click", async () => {
    try {
      await post("/api/app/shutdown");
      document.body.innerHTML = '<main class="shell"><section class="progress-card"><h1>Приложение закрыто</h1><p>Эту вкладку можно закрыть.</p></section></main>';
    } catch (error) { toast(error.message); }
  });

  async function init() {
    try {
      const bootstrap = await jsonFetch("/api/bootstrap");
      token = bootstrap.token;
      await loadProfiles();
      await pollStatus();
      setInterval(pollStatus, 1000);
    } catch (error) {
      els.statusMessage.textContent = error.message;
    }
  }

  init();
})();
