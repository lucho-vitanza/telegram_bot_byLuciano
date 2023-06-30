const Telebot = require("telebot");
const { promisify } = require("util");
const exec = promisify(require("child_process").exec);
const CONSTANTS = require("./constants");

const bot = new Telebot({
  token: CONSTANTS.TELEGRAM_TOKEN,
});

const executeCommand = async (command) => {
  try {
    const { stdout, stderr } = await exec(command);
    return { stdout, stderr };
  } catch (error) {
    throw error;
  }
};

const getPresupuesto = async (numPresupuesto) => {
  const command = `python calculos.py ${numPresupuesto}`;
  const { stdout, stderr } = await executeCommand(command);
  const result = stdout.trim();
  const startIndex = result.indexOf('{');

  if (startIndex >= 0) {
    const jsonResult = result.substring(startIndex);
    try {
      const parsedResult = JSON.parse(jsonResult);
      return parsedResult;
    } catch (error) {
      console.error("Error al analizar el resultado JSON:", error);
      throw new Error("Ocurrió un error al obtener el presupuesto. Por favor, intenta de nuevo más tarde.");
    }
  } else {
    console.error("No se encontró un resultado JSON válido en la salida del script de Python.");
    throw new Error("Ocurrió un error al obtener el presupuesto. Por favor, intenta de nuevo más tarde.");
  }
};

const formatCurrency = (value) => {
  return value.toLocaleString("es-AR", { style: "currency", currency: "USD" });
};

bot.on(["/start", "/hola"], async (msg) => {
  try {
    await bot.sendMessage(msg.chat.id, `Hola ${msg.chat.username}, tenemos unos presupuestos para vos.`, {
      replyMarkup: {
        inline_keyboard: [
          [
            { text: "Presupuesto_Mejoras_PA_Prote_CCP23", callback_data: 1 },
            { text: "Presupuesto_Mnto_Planta_Prote_CCP23", callback_data: 2 },
          ],
        ],
      },
    });
  } catch (error) {
    console.error("Error al enviar el mensaje:", error);
  }
});

bot.on("callbackQuery", async (msg) => {
  const choice = msg.data;
  const chatId = msg.message.chat.id;

  if (choice === "1" || choice === "2") {
    const numPresupuesto = parseInt(choice);
    try {
      await bot.sendMessage(chatId, `Obteniendo presupuesto ${choice}...`);

      const presupuesto = await getPresupuesto(numPresupuesto);

      const {
        "Sumatoria Clasificacion": sumatoria_clasificacion,
        "Porcentaje Tipo": porcentaje_tipo,
        "Total en el proyecto": suma_total_usd,
        "Cantidad de facturas": cantidad_numero_factura,
        "Cantidad de remitos": cantidad_numero_remito,
        "Cantidad de Ordenes de compra": cantidad_oc_numero,
        "Por cuenta Contable": sumatoria_cuenta_contable
      } = presupuesto;

      await bot.sendMessage(chatId, `
        ---
        El monto ejecutado del proyecto es de 
        ${formatCurrency(suma_total_usd)}
        de los cuales hay: 
        ${cantidad_numero_factura} cantidad de facturas,
        ${cantidad_numero_remito} remitos y 
        ${cantidad_oc_numero} de Ordenes de compra
        ---
      `);

      // Tabla de porcentajes
      let tablaMd1 = "Porcentajes facturados, con remito de la OC:\n";
      tablaMd1 += "| TIPO | % |\n";

      for (const [key, value] of Object.entries(porcentaje_tipo)) {
        tablaMd1 += `| ${key} | % ${value.toFixed(2)} |\n`;
      }

      await bot.sendMessage(chatId, tablaMd1);

      // Tabla de cuentas contables
      let tablaMd2 = "Total ejecutado por Cuenta contable\n";
      tablaMd2 += "| CUENTA CONTABLE | USD |\n";

      for (const [key, value] of Object.entries(sumatoria_cuenta_contable)) {
        tablaMd2 += `| ${key} | ${formatCurrency(value)} |\n`;
      }

      await bot.sendMessage(chatId, tablaMd2);

      // Tabla por clasificación
      let tablaMd = "Presupuesto por clasificación contable:\n";
      tablaMd += "| Clasificación contable | USD |\n";

      for (const [key, value] of Object.entries(sumatoria_clasificacion)) {
        tablaMd += `| ${key} | ${formatCurrency(value)} |\n`;
      }

      await bot.sendMessage(chatId, tablaMd);
    } catch (error) {
      console.error("Error al obtener el presupuesto:", error);
      await bot.sendMessage(chatId, "Ocurrió un error al obtener el presupuesto. Por favor, intenta de nuevo más tarde.");
    }
  } else {
    await bot.sendMessage(chatId, "Opción no válida. Por favor, selecciona una opción del menú.");
  }
});

bot.start();
