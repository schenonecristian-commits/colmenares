/* Cómo se guarda cada dato de la app en la planilla "Gestión apícola".
   Cada fila: [campo en la app, título de la columna, tipo]
   Tipos: s texto · n número (vacío = 0) · nn número (vacío = sin dato) · d fecha · b sí/no · l lista · vr muestras de varroa */
(function (root) {
  var ESQUEMA = {
    visitas: [
      ["fecha", "Fecha", "d"], ["colmenar", "Colmenar", "s"], ["estacion", "Estación", "s"], ["tareas", "Tareas", "l"],
      ["colmenas", "Colmenas", "n"],
      ["bajas.muertas", "Bajas: muertas", "n"], ["bajas.zanganeras", "Bajas: zanganeras", "n"], ["bajas.huerfanas", "Bajas: huérfanas", "n"],
      ["bajas.loque", "Bajas: loque", "n"], ["bajas.yeso", "Bajas: cría yesificada", "n"], ["bajas.otra", "Bajas: otra causa", "n"],
      ["altas_nuc", "Altas: núcleos a cámara", "n"], ["altas_enj", "Altas: enjambres a cámara", "n"], ["altas_ing", "Altas: compradas", "n"],
      ["cat1", "Categoría I", "n"], ["cat2", "Categoría II", "n"], ["cat3", "Categoría III", "n"],
      ["quedan_m", "Alzas melarias: 1/2", "nn"], ["quedan_s", "Alzas melarias: alzas", "nn"],
      ["puse_m", "Puse: ½ alzas", "nn"], ["puse_s", "Puse: alzas", "nn"], ["puse_origen", "Puse: desde", "s"],
      ["apilado_n", "Material: nucleros", "nn"], ["apilado_c", "Material: cámaras", "nn"], ["apilado_m", "Material: 1/2 alzas", "nn"], ["apilado_s", "Material: alzas", "nn"],
      ["cosecha_m", "Cosecha: 1/2 alzas", "n"], ["cosecha_s", "Cosecha: alzas", "n"], ["cosecha_p", "Cosecha: llenado %", "n"], ["lote", "Lote de extracción", "s"],
      ["jarabe", "Jarabe (L)", "n"], ["promotor", "Promotor", "b"], ["promotor_ml", "Promotor (ml/L)", "n"], ["torta", "Torta (kg)", "n"],
      ["nectar", "Néctar", "s"], ["polen", "Polen", "s"],
      ["cura", "Cura: productos", "l"], ["cura_det", "Cura: dosis / método", "s"], ["cura_lote", "Cura: lote o proveedor", "s"],
      ["varroa", "Varroa: muestras (abejas/varroas)", "vr"], ["varroa_pct", "Varroa %", "nn"],
      ["destino", "Traslado: destino", "s"], ["tras_col", "Traslado: colmenas", "n"], ["tras_nuc", "Traslado: núcleos", "n"], ["tras_enj", "Traslado: enjambres", "n"],
      ["mult_nuc", "Multiplicación: núcleos", "n"], ["mult_can", "Multiplicación: canasto técnico", "n"], ["mult_cel", "Multiplicación: celdas reales", "n"],
      ["mult_rf", "Multiplicación: reinas fecundadas", "n"], ["mult_rv", "Multiplicación: reinas vírgenes", "n"],
      ["obs", "Observaciones", "s"], ["id", "ID", "s"], ["creado", "Creado", "nn"]
    ],
    tambores: [
      ["campana", "Campaña (año de inicio)", "n"], ["numero", "N° de llenado", "n"], ["etiqueta", "Etiqueta", "s"], ["tipo", "Tipo", "s"],
      ["tara", "Tara (kg)", "nn"], ["colmenar", "Colmenar", "s"], ["lote", "Lote de extracción", "s"], ["productor", "Productor", "s"],
      ["destino", "Destino / estado", "s"], ["bruto", "Bruto (kg)", "nn"], ["neto", "Neto (kg)", "nn"], ["color", "Color", "s"],
      ["obs", "Observaciones", "s"], ["canje", "Canje (ID)", "s"], ["id", "ID", "s"], ["creado", "Creado", "nn"]
    ],
    campanias: [
      ["campana", "Campaña", "s"], ["orden", "Año de inicio", "n"], ["colmenas", "Colmenas", "nn"], ["kg", "Miel (kg)", "nn"],
      ["tambores", "Tambores", "nn"], ["id", "ID", "s"]
    ],
    movs: [
      ["fecha", "Fecha", "d"], ["ambito", "Ámbito", "s"], ["tipo", "Tipo", "s"], ["categoria", "Categoría", "s"], ["detalle", "Detalle", "s"],
      ["unidad", "Se paga en", "s"], ["monto", "Monto ($)", "n"], ["cant", "Cantidad de miel", "n"], ["color", "Miel", "s"],
      ["colmenar", "Colmenar", "s"], ["kg", "Kg vendidos", "n"], ["kgcolor", "Miel vendida", "s"], ["id", "ID", "s"], ["creado", "Creado", "nn"]
    ],
    precios: [
      ["fecha", "Fecha", "d"], ["comprador", "Comprador", "s"], ["clara", "Clara ($/kg)", "n"], ["oscura", "Oscura ($/kg)", "n"], ["id", "ID", "s"]
    ],
    canjes: [
      ["fecha", "Fecha", "d"], ["proveedor", "Proveedor", "s"], ["tipo", "Tipo", "s"], ["vacios", "Vacíos recibidos", "n"],
      ["relacion", "Relación (vacíos por 1 lleno)", "n"], ["id", "ID", "s"]
    ]
  };

  function leerRuta(o, r) { var p = r.split("."), x = o; for (var i = 0; i < p.length; i++) { if (x == null) return undefined; x = x[p[i]]; } return x; }
  function ponerRuta(o, r, v) { var p = r.split("."), x = o; for (var i = 0; i < p.length - 1; i++) { if (x[p[i]] == null || typeof x[p[i]] != "object") x[p[i]] = {}; x = x[p[i]]; } x[p[p.length - 1]] = v; }
  function rutas(o, pre, out) { Object.keys(o).forEach(function (k) { var v = o[k], r = pre ? pre + "." + k : k; if (v && typeof v == "object" && !Array.isArray(v)) rutas(v, r, out); else out.push(r); }); return out; }

  // De la app a una fila de la planilla
  function aFila(c, obj) {
    var E = ESQUEMA[c] || [], f = {}, usadas = {};
    E.forEach(function (e) {
      var v = leerRuta(obj, e[0]), t = e[2]; usadas[e[0]] = 1;
      if (t == "l") v = Array.isArray(v) ? v.join(", ") : (v || "");
      else if (t == "vr") v = Array.isArray(v) ? v.map(function (m) { return (m.a || 0) + "/" + (m.v || 0); }).join("; ") : "";
      else if (t == "b") v = !!v;
      else if (v == null) v = "";
      f[e[1]] = v;
    });
    rutas(obj, "", []).forEach(function (r) { if (!usadas[r]) { var v = leerRuta(obj, r); f[r] = v == null ? "" : (typeof v == "object" ? JSON.stringify(v) : v); } });
    return f;
  }

  // De una fila de la planilla a la app
  function deFila(c, fila) {
    var E = ESQUEMA[c] || [], o = {}, usados = {};
    E.forEach(function (e) {
      var v = fila[e[1]], t = e[2]; usados[e[1]] = 1;
      if (t == "n") { v = parseFloat(String(v == null ? "" : v).replace(",", ".")); if (isNaN(v)) v = 0; }
      else if (t == "nn") { v = (v === "" || v == null) ? null : parseFloat(String(v).replace(",", ".")); if (v !== null && isNaN(v)) v = null; }
      else if (t == "b") v = v === true || /^(true|verdadero|sí|si|1)$/i.test(String(v == null ? "" : v));
      else if (t == "l") v = String(v == null ? "" : v).split(",").map(function (x) { return x.trim(); }).filter(Boolean);
      else if (t == "d") { v = v == null ? "" : String(v).trim(); if (/^\d{4}-\d{2}-\d{2}T/.test(v)) { var dt = new Date(v); if (!isNaN(dt)) v = dt.getFullYear() + "-" + String(dt.getMonth() + 1).padStart(2, "0") + "-" + String(dt.getDate()).padStart(2, "0"); } }
      else if (t == "vr") v = String(v == null ? "" : v).split(";").map(function (x) { var p = x.trim().split("/"); return { a: parseInt(p[0], 10) || 0, v: parseInt(p[1], 10) || 0 }; }).filter(function (m) { return m.a > 0; });
      else v = v == null ? "" : String(v).trim();
      ponerRuta(o, e[0], v);
    });
    Object.keys(fila).forEach(function (h) { if (!usados[h]) { var v = fila[h]; if (typeof v == "string" && /^[\[{]/.test(v)) { try { v = JSON.parse(v); } catch (e) { } } ponerRuta(o, h, v); } });
    return o;
  }

  var api = { ESQUEMA: ESQUEMA, aFila: aFila, deFila: deFila };
  if (typeof module != "undefined" && module.exports) module.exports = api; else root.Esquema = api;
})(this);
