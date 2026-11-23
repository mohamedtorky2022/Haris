// The opening: the UAE map draws itself, the seven emirates light up and link, a shield closes
// around them and the threats break on it. Once per visit; a tap or Escape skips it.
(() => {
  const splash = document.getElementById("splash");
  if (!splash) return;
  let seen = false;
  try { seen = sessionStorage.getItem("haris-splash") === "1"; } catch { /* storage blocked */ }
  if (seen) { splash.remove(); return; }
  try { sessionStorage.setItem("haris-splash", "1"); } catch { /* storage blocked */ }

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
})();
