// Gestión apícola · conexión con la app Mis colmenares
// Recibe lo que cargás en la app y lo escribe en esta planilla.
// También permite armar las hojas Campo y Sala. No hace falta tocar nada acá.

const CLAVE = 'PONER-LA-CLAVE';

const HOJAS = {
  visitas: 'datos · Visitas',
  tambores: 'datos · Tambores',
  campanias: 'datos · Campañas',
  movs: 'datos · Movimientos',
  precios: 'datos · Precios',
  canjes: 'datos · Canjes'
};
const NOMBRES_VIEJOS = {
  visitas: 'Visitas', tambores: 'Tambores', campanias: 'Campañas',
  movs: 'Movimientos', precios: 'Precios', canjes: 'Canjes'
};

// La app pide todos los datos
function doGet(e) {
  const p = (e && e.parameter) || {};
  if (p.clave !== CLAVE) return salida({ ok: false, error: 'clave' });
  const data = {};
  Object.keys(HOJAS).forEach(function (c) { data[c] = leer(c); });
  return salida({ ok: true, data: data });
}

// La app manda lo cargado (y desde Claude se arman las hojas)
function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return salida({ ok: false, error: 'formato' }); }
  if (body.clave !== CLAVE) return salida({ ok: false, error: 'clave' });
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const res = { ok: true };
    if (body.ops) {
      res.hechos = [];
      body.ops.forEach(function (op) {
        if (!HOJAS[op.c]) return;
        escribir(op);
        res.hechos.push(op.c + '|' + op.id + '|' + op.t);
      });
    }
    if (body.encabezados) ponerEncabezados(body.encabezados);
    if (body.armar) armar(body.armar);
    SpreadsheetApp.flush();
    if (body.mirar) res.valores = mirar(body.mirar);
    return salida(res);
  } catch (err) {
    return salida({ ok: false, error: String(err && err.message || err) });
  } finally {
    lock.releaseLock();
  }
}

function salida(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function buscarHoja(c) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(HOJAS[c]);
  if (!sh) {
    sh = ss.getSheetByName(NOMBRES_VIEJOS[c]);
    if (sh) { sh.setName(HOJAS[c]); sh.setTabColor('#9e9e9e'); }
  }
  return sh;
}

function hoja(c) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = buscarHoja(c);
  if (!sh) { sh = ss.insertSheet(HOJAS[c], ss.getNumSheets()); sh.setTabColor('#9e9e9e'); }
  return sh;
}

function encabezados(sh) {
  const n = sh.getLastColumn();
  return n ? sh.getRange(1, 1, 1, n).getValues()[0].map(String) : [];
}

function esFecha(x) { return Object.prototype.toString.call(x) === '[object Date]'; }

function aValor(v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'string') {
    if (/^\d{4}-\d{2}-\d{2}$/.test(v)) {
      const p = v.split('-').map(Number);
      return new Date(p[0], p[1] - 1, p[2]);
    }
    if (/^[=+]/.test(v)) return "'" + v;
  }
  return v;
}

function agregarColumnas(sh, H, nuevos) {
  if (!nuevos.length) return H;
  if (sh.getMaxColumns() < H.length + nuevos.length) sh.insertColumnsAfter(sh.getMaxColumns(), H.length + nuevos.length - sh.getMaxColumns());
  sh.getRange(1, H.length + 1, 1, nuevos.length).setValues([nuevos]);
  H = H.concat(nuevos);
  sh.getRange(1, 1, 1, H.length).setFontWeight('bold');
  sh.setFrozenRows(1);
  return H;
}

function escribir(op) {
  const sh = hoja(op.c);
  let H = encabezados(sh);
  if (op.op === 'set') H = agregarColumnas(sh, H, Object.keys(op.fila).filter(function (h) { return H.indexOf(h) < 0; }));
  const col = H.indexOf('ID');
  if (col < 0) return;
  const n = sh.getLastRow() - 1;
  const ids = n > 0 ? sh.getRange(2, col + 1, n, 1).getValues().map(function (r) { return String(r[0]); }) : [];
  const i = ids.indexOf(String(op.id));
  if (op.op === 'del') {
    if (i >= 0) sh.deleteRow(i + 2);
    return;
  }
  const fila = i >= 0 ? sh.getRange(i + 2, 1, 1, H.length).getValues()[0] : H.map(function () { return ''; });
  H.forEach(function (h, k) { if (h in op.fila) fila[k] = aValor(op.fila[h]); });
  const r = i >= 0 ? i + 2 : sh.getLastRow() + 1;
  sh.getRange(r, 1, 1, H.length).setValues([fila]);
}

function leer(c) {
  const sh = buscarHoja(c);
  if (!sh || sh.getLastRow() < 2) return [];
  const v = sh.getDataRange().getValues();
  const H = v[0].map(String);
  const tz = Session.getScriptTimeZone();
  const col = H.indexOf('ID');
  if (col < 0) return [];
  return v.slice(1).filter(function (r) { return r[col] !== ''; }).map(function (r) {
    const o = {};
    H.forEach(function (h, k) {
      let x = r[k];
      if (esFecha(x)) x = Utilities.formatDate(x, tz, 'yyyy-MM-dd');
      if (h && x !== '') o[h] = x;
    });
    return o;
  });
}

// ---------- armar las hojas para mirar ----------

// Crea los títulos de columna de las hojas de datos que todavía están vacías
function ponerEncabezados(enc) {
  Object.keys(enc).forEach(function (c) {
    if (!HOJAS[c]) return;
    const sh = hoja(c);
    const H = encabezados(sh);
    agregarColumnas(sh, H, enc[c].filter(function (h) { return H.indexOf(h) < 0; }));
  });
}

// «Visitas|Colmenar» se convierte en la columna Colmenar de la hoja de datos de visitas
function resolver(x) {
  if (typeof x !== 'string' || x.indexOf('«') < 0) return x;
  return x.replace(/«([^|»]+)\|([^»]+)»/g, function (_, h, campo) {
    const c = Object.keys(NOMBRES_VIEJOS).filter(function (k) { return NOMBRES_VIEJOS[k] === h; })[0];
    const sh = c && hoja(c);
    const H = sh ? encabezados(sh) : [];
    const i = H.indexOf(campo);
    if (i < 0) throw new Error('No encuentro la columna ' + campo + ' en ' + h);
    const L = letra(i + 1);
    return "'" + HOJAS[c] + "'!$" + L + '$2:$' + L;
  });
}

function letra(n) { let s = ''; while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); } return s; }

function armar(specs) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  specs.forEach(function (s) {
    let sh = ss.getSheetByName(s.hoja);
    if (!sh) sh = ss.insertSheet(s.hoja);
    if (s.limpiar) {
      sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).breakApart();
      sh.clear();
      sh.clearConditionalFormatRules();
      sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).clearDataValidations();
      if (sh.getFilter()) sh.getFilter().remove();
      sh.setFrozenRows(0); sh.setFrozenColumns(0);
    }
    if (s.filas && sh.getMaxRows() < s.filas) sh.insertRowsAfter(sh.getMaxRows(), s.filas - sh.getMaxRows());
    if (s.columnas && sh.getMaxColumns() < s.columnas) sh.insertColumnsAfter(sh.getMaxColumns(), s.columnas - sh.getMaxColumns());
    if (s.color) sh.setTabColor(s.color);
    if ('sinCuadricula' in s) sh.setHiddenGridlines(!!s.sinCuadricula);
    if (s.posicion) { ss.setActiveSheet(sh); ss.moveActiveSheet(s.posicion); }
    if (s.fuente) sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).setFontFamily(s.fuente);
    Object.keys(s.anchos || {}).forEach(function (L) { sh.setColumnWidth(sh.getRange(L + '1').getColumn(), s.anchos[L]); });
    Object.keys(s.altos || {}).forEach(function (r) { sh.setRowHeight(+r, s.altos[r]); });
    (s.celdas || []).forEach(function (c) {
      if (c.v !== undefined) {
        const v = Array.isArray(c.v) ? c.v : [[c.v]];
        const r0 = sh.getRange(c.en || c.a1);
        sh.getRange(r0.getRow(), r0.getColumn(), v.length, v[0].length).setValues(v.map(function (fila) { return fila.map(resolver); }));
      }
      if (!c.a1) return;
      const r = sh.getRange(c.a1);
      if (c.combinar) r.merge();
      if (c.negrita !== undefined) r.setFontWeight(c.negrita ? 'bold' : 'normal');
      if (c.tam) r.setFontSize(c.tam);
      if (c.letra) r.setFontFamily(c.letra);
      if (c.colorTexto) r.setFontColor(c.colorTexto);
      if (c.fondo) r.setBackground(c.fondo);
      if (c.formato) r.setNumberFormat(c.formato);
      if (c.alinear) r.setHorizontalAlignment(c.alinear);
      if (c.valinear) r.setVerticalAlignment(c.valinear);
      if (c.ajustar !== undefined) r.setWrap(!!c.ajustar);
      if (c.italica) r.setFontStyle('italic');
      if (c.borde) r.setBorder(c.borde.arriba || null, c.borde.izq || null, c.borde.abajo || null, c.borde.der || null, null, c.borde.medio || null, c.borde.color || '#cccccc', SpreadsheetApp.BorderStyle[c.borde.estilo || 'SOLID']);
      if (c.lista) r.setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(c.lista, true).build());
    });
    if (s.congelarFilas !== undefined) sh.setFrozenRows(s.congelarFilas);
    if (s.congelarColumnas !== undefined) sh.setFrozenColumns(s.congelarColumnas);
    if (s.condicionales) {
      const reglas = s.condicionales.map(function (k) {
        let b = SpreadsheetApp.newConditionalFormatRule().whenFormulaSatisfied(resolver(k.formula)).setRanges([sh.getRange(k.a1)]);
        if (k.fondo) b = b.setBackground(k.fondo);
        if (k.colorTexto) b = b.setFontColor(k.colorTexto);
        if (k.negrita) b = b.setBold(true);
        return b.build();
      });
      sh.setConditionalFormatRules(reglas);
    }
    if (s.filtro) sh.getRange(s.filtro).createFilter();
    (s.ocultarColumnas || []).forEach(function (L) { sh.hideColumns(sh.getRange(L + '1').getColumn()); });
  });
}

// Devuelve lo que se ve en un rango, para revisar que las fórmulas den bien
function mirar(lista) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  return lista.map(function (m) {
    const sh = ss.getSheetByName(m.hoja);
    if (!sh) return null;
    const r = sh.getRange(m.a1);
    return { valores: r.getDisplayValues(), formulas: m.formulas ? r.getFormulas() : undefined };
  });
}
