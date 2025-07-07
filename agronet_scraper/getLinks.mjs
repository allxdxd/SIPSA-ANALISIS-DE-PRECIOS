import { chromium } from "playwright";
import pc from "picocolors";
import { writeFile, readFile } from "fs/promises";

console.log(pc.green("Iniciando el script..."));
console.log(pc.yellow("Cargando el navegador..."));

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
});

console.log(pc.yellow("Creando una nueva página..."));
const page = await context.newPage();

let dataLinks = [];
let flag = 0;

page.on("console", async (msg) => {
  // Solo interesan los mensajes que tienen al menos un argumento
  if (msg.args().length > 0) {
    const firstArg = msg.args()[0];
    try {
      const value = await firstArg.jsonValue();
      // Verificamos si el valor es un string Y si termina con '.xlsx'
      if (typeof value === "string" && value.endsWith(".xlsx")) {
        // console.log("Archivo capturado:", value);
        // Guardamos el enlace en el array
        process.stdout.write(`\r${pc.cyan("Capturando enlaces...")} ${dataLinks.length + 1}/51`);
        dataLinks.push(`https://www.agronet.gov.co${value}`);
        flag = dataLinks.length;
      }
    } catch (e) {
      console.log("Error al obtener el valor:", e);
    }
  }
});

console.log(pc.yellow("Abriendo la página de Agronet..."));

await page.goto(
  "https://www.agronet.gov.co/estadistica/Paginas/home.aspx?cod=67",
  {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  }
);

while (flag !== 51) {
  await page.waitForTimeout(1000);
}

console.log(pc.green("Cerrando el navegador..."));
await page.close();
await browser.close();
console.log(pc.green("Navegador cerrado."));
console.log(pc.green("Archivo(s) capturado(s):"));
dataLinks.forEach((link) => {
  console.log(pc.blue(link));
});

try {
  // Leer enlaces existentes si el archivo existe
  let existingLinks = [];
  try {
    const fileContent = await readFile("dataLinks.json", "utf-8");
    existingLinks = JSON.parse(fileContent);
  } catch (err) {
    // Si el archivo no existe, continuar con array vacío
    if (err.code !== "ENOENT") throw err;
  }

  // Juntar y eliminar duplicados usando el tipo de datos set
  const allLinks = Array.from(new Set([...existingLinks, ...dataLinks]));

  await writeFile("dataLinks.json", JSON.stringify(allLinks, null, 2), "utf-8");
  console.log(pc.green("Enlaces añadidos a dataLinks.json"));
} catch (err) {
  console.log(pc.red("Error al guardar el archivo JSON:"), err);
}

