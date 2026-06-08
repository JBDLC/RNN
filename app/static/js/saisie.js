(function () {
  const checkbox = document.getElementById("douteux_manuel");
  const motifGroup = document.getElementById("motif-doute-group");

  if (!checkbox || !motifGroup) return;

  function toggleMotif() {
    motifGroup.style.display = checkbox.checked ? "block" : "none";
  }

  checkbox.addEventListener("change", toggleMotif);
  toggleMotif();
})();
