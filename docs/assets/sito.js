// Indice laterale, pagina attiva e pulsanti "Copia" sui blocchi di comandi.
(function () {
  var PAGINE = [
    { gruppo: "Inizio" },
    { file: "index.html", titolo: "Benvenuto", durata: "" },
    { file: "lab0.html", titolo: "Lab 0 · Ripartenza", durata: "10'" },
    { gruppo: "In aula" },
    { file: "lab1.html", titolo: "Lab 1 · Prove prima del rilascio", durata: "30'" },
    { file: "lab2.html", titolo: "Lab 2 · Rilascio reversibile", durata: "25'" },
    { file: "lab3.html", titolo: "Lab 3 · Il controllo sta fuori dal modello", durata: "25'" },
    { file: "lab4.html", titolo: "Lab 4 · Più agenti solo se serve", durata: "25'" },
    { gruppo: "Da fare da soli" },
    { file: "lab5.html", titolo: "Lab 5 · Guasti e retry", durata: "25'" },
    { file: "lab6.html", titolo: "Lab 6 · Grafo e controllore", durata: "25'" },
    { file: "lab7.html", titolo: "Lab 7 · L'identità dell'utente", durata: "30'" },
    { file: "lab8.html", titolo: "Lab 8 · Dati personali", durata: "25'" },
    { file: "lab9.html", titolo: "Lab 9 · Agenti di team diversi", durata: "25'" },
    { file: "lab10.html", titolo: "Lab 10 · Allarmi e monitoraggio", durata: "20'" },
    { file: "lab11.html", titolo: "Lab 11 · Swarm e limiti", durata: "20'" },
    { gruppo: "Fine" },
    { file: "regole.html", titolo: "Le regole in una pagina", durata: "" },
    { file: "pulizia.html", titolo: "Pulizia", durata: "10'" },
  ];

  var corrente = location.pathname.split("/").pop() || "index.html";

  var nav = document.querySelector("nav.indice");
  if (nav) {
    PAGINE.forEach(function (p) {
      if (p.gruppo) {
        var g = document.createElement("div");
        g.className = "gruppo";
        g.textContent = p.gruppo;
        nav.appendChild(g);
        return;
      }
      var a = document.createElement("a");
      a.href = p.file;
      a.textContent = p.titolo;
      if (p.durata) {
        var d = document.createElement("span");
        d.className = "durata";
        d.textContent = p.durata;
        a.appendChild(d);
      }
      if (p.file === corrente) a.className = "attivo";
      nav.appendChild(a);
    });
  }

  var bottone = document.querySelector(".menu-bottone");
  if (bottone && nav) {
    bottone.addEventListener("click", function () { nav.classList.toggle("aperto"); });
  }

  var solo = PAGINE.filter(function (p) { return p.file; });
  var i = solo.findIndex(function (p) { return p.file === corrente; });
  var main = document.querySelector("main");
  if (main && i >= 0) {
    var barra = document.createElement("div");
    barra.className = "navigazione";
    var sx = document.createElement("span");
    var dx = document.createElement("span");
    if (i > 0) { sx.innerHTML = '<a href="' + solo[i - 1].file + '">&larr; ' + solo[i - 1].titolo + "</a>"; }
    if (i < solo.length - 1) { dx.innerHTML = '<a href="' + solo[i + 1].file + '">' + solo[i + 1].titolo + " &rarr;</a>"; }
    barra.appendChild(sx);
    barra.appendChild(dx);
    main.appendChild(barra);
  }

  document.querySelectorAll(".blocco").forEach(function (blocco) {
    var pre = blocco.querySelector("pre");
    if (!pre) return;
    var b = document.createElement("button");
    b.className = "copia";
    b.type = "button";
    b.textContent = "Copia";
    b.addEventListener("click", function () {
      var testo = pre.innerText.replace(/\n$/, "");
      var fatto = function () {
        b.textContent = "Copiato";
        setTimeout(function () { b.textContent = "Copia"; }, 1500);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(testo).then(fatto);
      } else {
        var t = document.createElement("textarea");
        t.value = testo;
        document.body.appendChild(t);
        t.select();
        document.execCommand("copy");
        document.body.removeChild(t);
        fatto();
      }
    });
    blocco.appendChild(b);
  });
})();
