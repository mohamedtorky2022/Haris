// Install Haris on the phone's home screen, without WhatsApp or an app store.
(() => {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
  }

  const standalone = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  if (standalone) return;

  const TEXT = {
    ar: { title: "ثبّت «حارس» على هاتفك", install: "تثبيت", ios: "اضغط زر المشاركة ثم «إضافة إلى الشاشة الرئيسية».", close: "إغلاق" },
    en: { title: "Install Haris on your phone", install: "Install", ios: "Tap Share, then “Add to Home Screen”.", close: "Close" },
    ur: { title: "«حارس» کو اپنے فون پر انسٹال کریں", install: "انسٹال", ios: "شیئر کا بٹن دبائیں، پھر “Add to Home Screen”۔", close: "بند کریں" },
    hi: { title: "Haris को अपने फ़ोन पर इंस्टॉल करें", install: "इंस्टॉल", ios: "शेयर बटन दबाएँ, फिर “Add to Home Screen”।", close: "बंद करें" },
    ru: { title: "Установите Haris на телефон", install: "Установить", ios: "Нажмите «Поделиться», затем «На экран „Домой“».", close: "Закрыть" },
  };
  const KEY = "haris-install-dismissed";
  const dismissed = () => { try { return localStorage.getItem(KEY) === "1"; } catch { return false; } };
  const remember = () => { try { localStorage.setItem(KEY, "1"); } catch { /* private mode */ } };

  const ua = navigator.userAgent;
  const isIOS = /iPhone|iPad|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  let deferred = null;
  let bar = null;

  function render() {
    if (!bar) return;
    const t = TEXT[document.documentElement.lang] || TEXT.ar;
    bar.querySelector(".install-title").textContent = t.title;
    bar.querySelector(".install-hint").textContent = deferred ? "" : t.ios;
    bar.querySelector(".install-hint").hidden = !!deferred;
    bar.querySelector(".install-go").textContent = t.install;
    bar.querySelector(".install-go").hidden = !deferred;
    bar.querySelector(".install-close").setAttribute("aria-label", t.close);
  }

  function show() {
    if (bar || dismissed()) return;
    const top = document.querySelector(".topbar");
    if (!top) return;
    bar = document.createElement("div");
    bar.className = "install-bar";
    bar.setAttribute("role", "region");
    bar.innerHTML =
      '<img src="icons/icon-192.png" alt="" width="36" height="36">' +
      '<div class="install-text"><strong class="install-title"></strong><span class="install-hint"></span></div>' +
      '<button type="button" class="install-go"></button>' +
      '<button type="button" class="install-close">×</button>';
    top.insertAdjacentElement("afterend", bar);
    bar.querySelector(".install-go").addEventListener("click", async () => {
      if (!deferred) return;
      deferred.prompt();
      const choice = await deferred.userChoice.catch(() => null);
      deferred = null;
      if (choice && choice.outcome === "accepted") hide();
      else render();
    });
    bar.querySelector(".install-close").addEventListener("click", () => { remember(); hide(); });
    new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    render();
  }

  function hide() { if (bar) { bar.remove(); bar = null; } }

  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); deferred = e; show(); render(); });
  window.addEventListener("appinstalled", () => { remember(); hide(); });
  if (isIOS && /Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS/.test(ua)) window.addEventListener("load", show);
})();
