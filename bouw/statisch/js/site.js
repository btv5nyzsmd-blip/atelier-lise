// Kleine extra's voor de website. De site werkt ook zonder dit bestand.

// Menu openen en sluiten op de telefoon
const menuKnop = document.querySelector(".menu-knop");
const menu = document.getElementById("menu");
menuKnop?.addEventListener("click", () => {
  const open = menuKnop.getAttribute("aria-expanded") !== "true";
  menuKnop.setAttribute("aria-expanded", open);
  menu.classList.toggle("is-open", open);
  document.body.classList.toggle("menu-open", open);
});

// Dun lijntje onder de kop zodra je scrolt, en de vaste afspraakknop
// onderin laten verschijnen als je een stukje naar beneden bent.
const kop = document.querySelector(".kop");
const plakbalk = document.querySelector(".plakbalk");
const opScroll = () => {
  kop.classList.toggle("is-gescrold", scrollY > 8);
  plakbalk?.classList.toggle("is-zichtbaar", scrollY > 420);
};
addEventListener("scroll", opScroll, { passive: true });
opScroll();

// Portfolio: foto groot bekijken
const lichtbak = document.querySelector(".lichtbak");
if (lichtbak) {
  const links = [...document.querySelectorAll(".galerij__link")];
  const img = lichtbak.querySelector("img");
  const tekst = lichtbak.querySelector("figcaption");
  let huidig = 0;

  const toon = (i) => {
    huidig = (i + links.length) % links.length;
    const link = links[huidig];
    img.src = link.href;
    img.alt = link.querySelector("img").alt;
    tekst.textContent = link.dataset.tekst || "";
  };

  links.forEach((link, i) =>
    link.addEventListener("click", (e) => {
      e.preventDefault();
      toon(i);
      lichtbak.showModal();
    })
  );
  lichtbak.querySelector(".lichtbak__sluit").addEventListener("click", () => lichtbak.close());
  lichtbak.querySelector(".lichtbak__pijl--vorige").addEventListener("click", () => toon(huidig - 1));
  lichtbak.querySelector(".lichtbak__pijl--volgende").addEventListener("click", () => toon(huidig + 1));
  lichtbak.addEventListener("click", (e) => { if (e.target === lichtbak) lichtbak.close(); });
  lichtbak.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") toon(huidig - 1);
    if (e.key === "ArrowRight") toon(huidig + 1);
  });

  // Vegen op de telefoon
  let startX = null;
  lichtbak.addEventListener("touchstart", (e) => (startX = e.touches[0].clientX), { passive: true });
  lichtbak.addEventListener("touchend", (e) => {
    if (startX === null) return;
    const verschil = e.changedTouches[0].clientX - startX;
    if (Math.abs(verschil) > 50) toon(huidig + (verschil < 0 ? 1 : -1));
    startX = null;
  });
}
