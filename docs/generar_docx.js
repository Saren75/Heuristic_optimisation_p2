// Convierte MEMORIA.md en el Word de la memoria con el formato de la plantilla
// de la practica 1 (Calibri, titulos de seccion centrados, pie con numero de pagina).
// Uso: node generar_docx.js   (desde la carpeta docs)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType, Footer,
  PageNumber, PageBreak, LevelFormat,
} = require("docx");

const FUENTE = "Calibri";
const ANCHO_UTIL = 9026;   // A4 con margenes de 2,54 cm, en DXA
const SALIDA = path.join(__dirname, "..", "550260-522170.docx");

const SUBINDICES = { "₀": "0", "₁": "1", "₂": "2", "₋": "−", "₌": "=", "₍": "(", "₎": ")", "ₐ": "a", "ₖ": "k", "ᵢ": "i" };
const SUPERINDICES = { "²": "2", "ᵏ": "k", "⁵": "5", "⁻": "−" };

// ---------------------------------------------------------------- texto en linea
function runs(texto, base = {}) {
  const salida = [];
  let negrita = false, cursiva = false, buffer = "";
  const volcar = (extra = {}) => {
    if (buffer) salida.push(new TextRun({ text: buffer, font: FUENTE, bold: negrita || base.bold, italics: cursiva, size: base.size, ...extra }));
    buffer = "";
  };
  for (let i = 0; i < texto.length; ) {
    const c = texto[i];
    if (c === "\\" && i + 1 < texto.length) { buffer += texto[i + 1]; i += 2; continue; }
    if (c === "`") {
      const fin = texto.indexOf("`", i + 1);
      volcar();
      salida.push(new TextRun({ text: texto.slice(i + 1, fin), font: "Consolas", size: (base.size || 22) - 2, bold: base.bold }));
      i = fin + 1; continue;
    }
    if (texto.startsWith("***", i)) { volcar(); negrita = !negrita; cursiva = !cursiva; i += 3; continue; }
    if (texto.startsWith("**", i)) { volcar(); negrita = !negrita; i += 2; continue; }
    if (c === "*") { volcar(); cursiva = !cursiva; i += 1; continue; }
    if (c === "_" && /[a-z]/.test(texto[i + 1] || "") && !/[a-z]/i.test(texto[i + 2] || "")) {
      volcar(); buffer = texto[i + 1]; volcar({ subScript: true, italics: true }); i += 2; continue;
    }
    if (SUBINDICES[c] !== undefined) {
      volcar(); buffer = SUBINDICES[c];
      volcar({ subScript: true, italics: /[a-z]/.test(SUBINDICES[c]) }); i += 1; continue;
    }
    if (SUPERINDICES[c] !== undefined) {
      volcar(); buffer = SUPERINDICES[c];
      volcar({ superScript: true, italics: /[a-z]/.test(SUPERINDICES[c]) }); i += 1; continue;
    }
    buffer += c; i += 1;
  }
  volcar();
  return salida;
}

// ---------------------------------------------------------------- tablas
function celdas(linea) {
  return linea.trim().replace(/^\|/, "").replace(/\|$/, "").split(/(?<!\\)\|/).map((c) => c.trim());
}

function tabla(lineas) {
  const cabecera = celdas(lineas[0]);
  const alineacion = celdas(lineas[1]).map((c) => (c.endsWith(":") ? AlignmentType.RIGHT : AlignmentType.LEFT));
  const filas = lineas.slice(2).map(celdas);
  const conCabecera = cabecera.some((c) => c !== "");
  const n = cabecera.length;
  const numerica = alineacion.filter((a) => a === AlignmentType.RIGHT).length >= n - 1;
  const tamano = n >= 9 ? 16 : n >= 5 ? 18 : 20;

  // Anchos: proporcionales a la longitud maxima del contenido de cada columna.
  const largos = cabecera.map((_, j) => Math.max(4, ...[cabecera, ...filas].map((f) => (f[j] || "").replace(/[*`\\]/g, "").length)));
  const tope = numerica ? 30 : 60;
  const pesos = largos.map((l) => Math.min(l, tope));
  const total = pesos.reduce((a, b) => a + b, 0);
  const anchos = pesos.map((p) => Math.floor((ANCHO_UTIL * p) / total));
  anchos[n - 1] += ANCHO_UTIL - anchos.reduce((a, b) => a + b, 0);

  const borde = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
  const bordes = { top: borde, bottom: borde, left: borde, right: borde };
  const fila = (valores, esCabecera) => new TableRow({
    tableHeader: esCabecera,
    cantSplit: true,
    children: valores.map((valor, j) => new TableCell({
      width: { size: anchos[j], type: WidthType.DXA },
      borders: bordes,
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      shading: esCabecera ? { type: ShadingType.CLEAR, fill: "D9E2F3" } : undefined,
      children: [new Paragraph({
        alignment: esCabecera && numerica ? AlignmentType.CENTER : alineacion[j],
        children: runs(valor, { size: tamano, bold: esCabecera }),
      })],
    })),
  });
  const filasDocx = [];
  if (conCabecera) filasDocx.push(fila(cabecera, true));
  filas.forEach((f) => filasDocx.push(fila(f, false)));
  return new Table({ width: { size: ANCHO_UTIL, type: WidthType.DXA }, columnWidths: anchos, rows: filasDocx });
}

// ---------------------------------------------------------------- portada
function portada() {
  const centrado = (texto, opciones = {}, antes = 0, despues = 160) => new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: antes, after: despues },
    children: [new TextRun({ text: texto, font: FUENTE, ...opciones })],
  });
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 600, after: 700 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(__dirname, "logo-uc3m.png")),
        transformation: { width: 330, height: 106 },
        altText: { title: "uc3m", description: "Logotipo de la Universidad Carlos III de Madrid", name: "logo" } })],
    }),
    centrado("Universidad Carlos III", { size: 30 }),
    centrado("Heurística y Optimización", { size: 40, bold: true }, 80, 240),
    centrado("Práctica 2: Búsqueda", { size: 26 }),
    centrado("Curso 2026-27", { size: 26 }),
    centrado("Grupo: 01", { size: 26, bold: true }, 0, 480),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [
      new TextRun({ text: "Julio César Ruiz Sánchez", font: FUENTE, size: 26, bold: true }),
      new TextRun({ text: " (NIA: 100522170)", font: FUENTE, size: 26 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "Denis Ángel Sánchez Rybianska", font: FUENTE, size: 26, bold: true }),
      new TextRun({ text: " (NIA: 100550260)", font: FUENTE, size: 26 }),
      new PageBreak()] }),
  ];
}

// ---------------------------------------------------------------- cuerpo
function cuerpo(markdown) {
  const lineas = markdown.replace(/<!--[\s\S]*?-->/g, "").split("\n");
  const inicio = lineas.findIndex((l) => l.startsWith("# 1."));   // se salta la portada
  const bloques = [];
  let parrafo = [];
  const cerrarParrafo = () => {
    if (!parrafo.length) return;
    const texto = parrafo.join(" ");
    const esPie = /^\*\*Tabla \d+\.\*\*/.test(texto);
    bloques.push(new Paragraph({
      alignment: AlignmentType.JUSTIFIED,
      keepNext: esPie,
      spacing: { before: esPie ? 160 : 0, after: esPie ? 80 : 140 },
      children: runs(texto, esPie ? { size: 20 } : {}),
    }));
    parrafo = [];
  };
  for (let i = inicio; i < lineas.length; i++) {
    const linea = lineas[i];
    if (linea.trim() === "" || linea.trim() === "---") { cerrarParrafo(); continue; }
    const titulo = /^(#{1,3}) (.*)$/.exec(linea);
    if (titulo) {
      cerrarParrafo();
      const nivel = titulo[1].length;
      bloques.push(new Paragraph({
        heading: [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3][nivel - 1],
        alignment: nivel === 1 ? AlignmentType.CENTER : AlignmentType.LEFT,
        children: [new TextRun({ text: titulo[2].replace(/\\/g, "") })],
      }));
      continue;
    }
    if (linea.startsWith("|")) {
      cerrarParrafo();
      const filas = [];
      while (i < lineas.length && lineas[i].startsWith("|")) filas.push(lineas[i++]);
      i--;
      bloques.push(tabla(filas));
      bloques.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
      continue;
    }
    const vineta = /^(- |\d+\. )(.*)$/.exec(linea);
    if (vineta) {
      cerrarParrafo();
      bloques.push(new Paragraph({
        numbering: { reference: /^\d/.test(vineta[1]) ? "numeros" : "vinetas", level: 0 },
        alignment: AlignmentType.JUSTIFIED, spacing: { after: 60 },
        children: runs(vineta[2]),
      }));
      continue;
    }
    if (linea.startsWith("  ")) {   // formula centrada
      cerrarParrafo();
      bloques.push(new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 60, after: 160 },
        children: runs(linea.trim()),
      }));
      continue;
    }
    parrafo.push(linea.trim());
  }
  cerrarParrafo();
  return bloques;
}

const estiloTitulo = (size, antes, despues) => ({
  run: { font: FUENTE, size, bold: true, color: "000000" },
  paragraph: { spacing: { before: antes, after: despues }, keepNext: true },
});

const documento = new Document({
  creator: "Julio César Ruiz Sánchez; Denis Ángel Sánchez Rybianska",
  title: "Práctica 2: Búsqueda",
  styles: {
    default: {
      document: { run: { font: FUENTE, size: 22 }, paragraph: { spacing: { line: 259 } } },
      heading1: estiloTitulo(32, 320, 160),
      heading2: estiloTitulo(26, 240, 120),
      heading3: estiloTitulo(23, 180, 100),
    },
  },
  numbering: { config: [
    { reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "numeros", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FUENTE, size: 20 })] })] }) },
    children: [...portada(), ...cuerpo(fs.readFileSync(path.join(__dirname, "MEMORIA.md"), "utf8"))],
  }],
});

Packer.toBuffer(documento).then((buffer) => {
  fs.writeFileSync(SALIDA, buffer);
  console.log("Escrito", SALIDA);
});
