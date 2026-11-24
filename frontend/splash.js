// The opening: the UAE map draws itself, the seven emirates light up and link, a shield closes
// around them and the threats break on it. Once per visit; a tap or Escape skips it.
// The chat writes the opening into its page; the dashboards leave #splash empty and give its
// words in data-title, data-line and data-small, and the drawing is built here.
(() => {
  const DEFS = "<defs><linearGradient id=\"g-shield\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop offset=\"0\" stop-color=\"#14b8a6\"/><stop offset=\".55\" stop-color=\"#0f766e\"/><stop offset=\"1\" stop-color=\"#c8942f\"/></linearGradient><linearGradient id=\"g-land\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\"><stop offset=\"0\" stop-color=\"#ccfbf1\"/><stop offset=\"1\" stop-color=\"#99f6e4\"/></linearGradient></defs>";
  const SYMBOL = "<symbol id=\"uae\" viewBox=\"-8 -8 1016 805\"><path pathLength=\"1\" d=\"M976.7 102.5 L988.9 108.8 L992.8 112.0 L997.3 129.1 L996.6 141.4 L995.5 151.6 L996.6 160.5 L998.8 169.7 L1000.0 174.6 L998.1 188.1 L995.0 224.7 L994.7 229.3 L994.8 232.1 L998.3 252.7 L993.8 253.3 L991.1 254.9 L990.2 256.7 L991.1 264.8 L991.3 267.6 L989.7 271.9 L983.7 274.8 L980.3 277.7 L978.9 280.6 L976.6 282.4 L967.6 286.0 L959.8 288.0 L957.9 297.9 L950.4 307.2 L942.2 308.6 L936.5 307.9 L933.9 306.5 L916.5 277.3 L920.2 273.0 L926.4 275.1 L931.1 278.6 L927.7 260.2 L925.2 255.8 L920.5 253.2 L915.6 252.1 L909.1 251.9 L904.3 253.3 L897.3 257.2 L892.6 261.2 L888.3 266.2 L881.7 274.1 L879.6 280.0 L881.7 309.8 L882.9 316.2 L887.9 328.1 L881.4 340.3 L874.9 347.4 L878.3 367.6 L882.9 381.4 L885.7 404.3 L868.4 424.3 L885.7 431.6 L899.6 427.1 L889.2 472.9 L830.7 476.7 L816.3 582.8 L755.5 772.0 L741.6 789.3 L208.4 719.4 L0.0 450.0 L0.2 417.1 L8.3 416.2 L29.7 417.0 L39.7 435.9 L38.9 441.8 L39.5 447.2 L42.7 466.5 L45.2 473.7 L48.5 477.2 L56.4 479.4 L73.1 479.6 L104.8 486.8 L130.1 483.6 L135.1 482.7 L139.9 481.3 L155.8 476.2 L177.3 464.7 L195.8 448.9 L208.0 432.9 L217.4 431.7 L223.1 438.6 L228.0 444.7 L247.8 445.5 L283.5 445.2 L306.8 448.9 L312.0 448.3 L325.6 445.6 L342.0 445.6 L363.1 453.2 L381.7 452.1 L391.1 452.4 L405.6 456.6 L411.3 460.6 L413.5 464.6 L417.7 466.6 L477.4 463.0 L529.4 444.3 L542.5 434.8 L554.9 426.9 L583.2 419.0 L592.7 411.3 L598.8 400.0 L601.5 392.8 L603.2 382.8 L608.4 376.6 L617.6 377.6 L623.6 375.8 L643.1 325.0 L639.7 312.1 L639.2 305.8 L651.2 293.4 L700.9 258.6 L713.4 253.4 L715.6 251.8 L722.5 246.6 L725.9 243.8 L739.1 228.4 L749.2 216.2 L752.0 212.7 L754.9 209.0 L757.3 204.9 L759.8 201.1 L767.0 192.2 L775.0 183.5 L780.1 178.0 L781.0 176.6 L789.1 165.3 L800.6 157.8 L803.6 154.8 L809.3 153.2 L814.8 142.8 L817.1 139.6 L820.0 130.9 L822.0 124.4 L825.2 118.6 L829.5 114.9 L829.7 116.6 L825.8 122.6 L826.5 127.7 L834.0 127.5 L843.8 125.2 L845.0 120.8 L847.0 114.8 L856.1 105.4 L867.8 96.7 L891.2 83.1 L925.6 46.1 L929.5 35.5 L935.8 13.2 L937.1 4.2 L952.4 0.0 L959.1 15.8 L955.0 40.2 L949.5 57.5 L949.8 79.8 L951.1 95.6 L953.6 96.4 L958.7 98.1 L970.1 104.7 L976.7 102.5 Z\"/></symbol>";
  const ART = "<svg class=\"splash-art\" viewBox=\"-300 -330 1600 1520\">\n      <path class=\"sh-glow\" d=\"M500 -210 C690 -130 900 -110 1110 -95 L1110 400 C1110 750 830 960 500 1060 C170 960 -110 750 -110 400 L-110 -95 C100 -110 310 -130 500 -210 Z\"/>\n      <path class=\"sh-line\" pathLength=\"1\" d=\"M500 -210 C690 -130 900 -110 1110 -95 L1110 400 C1110 750 830 960 500 1060 C170 960 -110 750 -110 400 L-110 -95 C100 -110 310 -130 500 -210 Z\"/>\n      <use class=\"land\" href=\"#uae\" x=\"-8\" y=\"-8\" width=\"1016\" height=\"805\"/>\n      <use class=\"coast\" href=\"#uae\" x=\"-8\" y=\"-8\" width=\"1016\" height=\"805\"/>\n      <line class=\"link l1\" pathLength=\"1\" x1=\"650\" y1=\"372\" x2=\"785\" y2=\"222\"/><line class=\"link l2\" pathLength=\"1\" x1=\"785\" y1=\"222\" x2=\"808\" y2=\"186\"/><line class=\"link l3\" pathLength=\"1\" x1=\"808\" y1=\"186\" x2=\"822\" y2=\"168\"/><line class=\"link l4\" pathLength=\"1\" x1=\"822\" y1=\"168\" x2=\"838\" y2=\"140\"/><line class=\"link l5\" pathLength=\"1\" x1=\"838\" y1=\"140\" x2=\"918\" y2=\"88\"/><line class=\"link l6\" pathLength=\"1\" x1=\"918\" y1=\"88\" x2=\"978\" y2=\"232\"/><line class=\"link l7\" pathLength=\"1\" x1=\"978\" y1=\"232\" x2=\"785\" y2=\"222\"/><line class=\"link l8\" pathLength=\"1\" x1=\"650\" y1=\"372\" x2=\"978\" y2=\"232\"/>\n      <g class=\"node n1\"><circle class=\"ripple\" cx=\"650\" cy=\"372\" r=\"14\"/><circle class=\"core\" cx=\"650\" cy=\"372\" r=\"11\"/></g><g class=\"node n2\"><circle class=\"ripple\" cx=\"785\" cy=\"222\" r=\"14\"/><circle class=\"core\" cx=\"785\" cy=\"222\" r=\"11\"/></g><g class=\"node n3\"><circle class=\"ripple\" cx=\"808\" cy=\"186\" r=\"14\"/><circle class=\"core\" cx=\"808\" cy=\"186\" r=\"11\"/></g><g class=\"node n4\"><circle class=\"ripple\" cx=\"822\" cy=\"168\" r=\"14\"/><circle class=\"core\" cx=\"822\" cy=\"168\" r=\"11\"/></g><g class=\"node n5\"><circle class=\"ripple\" cx=\"838\" cy=\"140\" r=\"14\"/><circle class=\"core\" cx=\"838\" cy=\"140\" r=\"11\"/></g><g class=\"node n6\"><circle class=\"ripple\" cx=\"918\" cy=\"88\" r=\"14\"/><circle class=\"core\" cx=\"918\" cy=\"88\" r=\"11\"/></g><g class=\"node n7\"><circle class=\"ripple\" cx=\"978\" cy=\"232\" r=\"14\"/><circle class=\"core\" cx=\"978\" cy=\"232\" r=\"11\"/></g>\n      <g class=\"threat t1\"><circle class=\"bug\" cx=\"-110\" cy=\"150\" r=\"40\"/><circle class=\"burst\" cx=\"-110\" cy=\"150\" r=\"40\"/></g><g class=\"threat t2\"><circle class=\"bug\" cx=\"1110\" cy=\"60\" r=\"40\"/><circle class=\"burst\" cx=\"1110\" cy=\"60\" r=\"40\"/></g><g class=\"threat t3\"><circle class=\"bug\" cx=\"-60\" cy=\"700\" r=\"40\"/><circle class=\"burst\" cx=\"-60\" cy=\"700\" r=\"40\"/></g><g class=\"threat t4\"><circle class=\"bug\" cx=\"1050\" cy=\"690\" r=\"40\"/><circle class=\"burst\" cx=\"1050\" cy=\"690\" r=\"40\"/></g><g class=\"threat t5\"><circle class=\"bug\" cx=\"500\" cy=\"-205\" r=\"40\"/><circle class=\"burst\" cx=\"500\" cy=\"-205\" r=\"40\"/></g><g class=\"threat t6\"><circle class=\"bug\" cx=\"260\" cy=\"1000\" r=\"40\"/><circle class=\"burst\" cx=\"260\" cy=\"1000\" r=\"40\"/></g>\n    </svg>";
  const splash = document.getElementById("splash");
  if (!splash) return;
  const key = splash.dataset.key || "haris-splash";
  let seen = false;
  try { seen = sessionStorage.getItem(key) === "1"; } catch { /* storage blocked */ }
  if (seen) { splash.remove(); return; }
  try { sessionStorage.setItem(key, "1"); } catch { /* storage blocked */ }
  if (!splash.firstElementChild) build(splash);

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  splash.classList.add("play");
  let gone = false;
  const done = () => {
    if (gone) return;
    gone = true;
    splash.classList.add("leave");
    setTimeout(() => splash.remove(), 450);
  };
  setTimeout(done, reduce ? 1200 : 3900);
  splash.addEventListener("click", done);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") done(); });

  function build(el) {
    if (!document.getElementById("uae")) {
      const holder = document.createElement("div");
      holder.innerHTML = '<svg class="splash-sprite" width="0" height="0" aria-hidden="true" focusable="false">' + DEFS + SYMBOL + "</svg>";
      document.body.prepend(holder.firstChild);
    }
    el.innerHTML = ART + '<div class="splash-text"><strong></strong><span></span><small></small></div>';
    const [title, line, small] = el.querySelectorAll(".splash-text > *");
    title.textContent = el.dataset.title || "حارس";
    line.textContent = el.dataset.line || "";
    small.textContent = el.dataset.small || "";
  }
})();
