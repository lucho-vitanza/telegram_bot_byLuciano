const Telebot = require("telebot");
const { promisify } = require("util");
const exec = promisify(require("child_process").exec);
const CONSTANTS = require("./constants");
const nodemailer = require("nodemailer");

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
  const filePath = `/mnt/b/Documentos/9_PORTAhnos/chatBot_telegram/src/df_clasificada_${numPresupuesto}.xlsx`;
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

const enviarCorreo = async (destinatario, asunto, contenido, archivoAdjunto, nombre, numPresupuesto) => {
  try {
    const transporter = nodemailer.createTransport({
      service: "Outlook",
      auth: {
        user: "lvitanza@porta.com.ar",
        pass: "Porta2791",
      },
    });

    const mensaje = {
      from: "lvitanza@porta.com.ar",
      to: destinatario,
      subject: asunto,
      html: contenido,
      attachments: [
        {
          filename: `df_clasificada_${numPresupuesto}.xlsx`,
          path: archivoAdjunto,
        },
      ],
    };

    const info = await transporter.sendMail(mensaje);
    console.log("Correo electrónico enviado:", info.messageId);
  } catch (error) {
    console.error("Error al enviar el correo electrónico:", error);
    throw error;
  }
};

// PRES MEJORAS PA - PROTE - CCP 23 =  1
// PRES MANTENIMIENTO PA - PROTE - CCP 23 = 2
// 

const proyectos = [
  { numPresupuesto: 1, nombre: "PRESUPUESTO MEJ. PA- PROTE- CCP23" },
  { numPresupuesto: 2, nombre: "PRESUPUESTO MNTO. PA- PROTE- CCP23" },
  { numPresupuesto: 3, nombre: "PRESUPUESTO PROD. CONS MASIV 23" },
  { numPresupuesto: 4, nombre: "PROYECTO PRENSADO DE SOJA" },
  { numPresupuesto: 5, nombre: "PRESUPUESTO PROD. PA MIN CACO 23" },
  { numPresupuesto: 6, nombre: "PROYECTO PLANTA SPC FOOD 1000 TN" },
  { numPresupuesto: 7, nombre: "PRES MANTO CONS MASIVO 23" },
  { numPresupuesto: 8, nombre: "PRES MEJORAS CONS MASIVO 23" },
];

const getNombreProyecto = (numPresupuesto) => {
  const proyecto = proyectos.find((p) => p.numPresupuesto === numPresupuesto);
  return proyecto ? proyecto.nombre : "";
};

bot.on(["/start", "/hola"], async (msg) => {
  try {
    await bot.sendMessage(msg.chat.id, `Hola ${msg.chat.username}, tenemos unos presupuestos para vos.`, {
      replyMarkup: {
        inline_keyboard: [
          [
            { text: "PRESUPUESTO MEJ. PA- PROTE- CCP23", callback_data: "1" },
          ],
          [
            { text: "PRESUPUESTO MNTO. PA- PROTE- CCP23", callback_data: "2" },
          ],
          [
            { text: "PRESUPUESTO PROD. CONS MASIV 23", callback_data: "3" },
          ],
          [
            { text: "PRESUPUESTO PROD. PA MIN CACO 23", callback_data: "5" },
          ],
          [
            { text: "PROYECTO PRENSADO DE SOJA", callback_data: "4" },
          ],
          [
            { text: "PROYECTO PLANTA SPC FOOD 1000 TN", callback_data: "6" },
          ],
          [
            { text: "PRES MNTO CONS MASIVO 23", callback_data: "7" },
          ],
          [
            { text: "PRES MEJORAS CONS MASIVO 23", callback_data: "8" },
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

  if (choice === "1" || choice === "2" || choice === "3" || choice === "4" || choice === "5" || choice === "6" || choice === "7" || choice === "8") {
    const numPresupuesto = parseInt(choice);
    try {
      const nombreProyecto = getNombreProyecto(numPresupuesto);
      await bot.sendMessage(chatId, `Obteniendo presupuesto ${nombreProyecto}...`);

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
        ${cantidad_numero_factura} facturas,
        ${cantidad_numero_remito} remitos y 
        ${cantidad_oc_numero} Ordenes de compras
        ---
      `);

      // Tabla de porcentajes
      let tablaMd1 = "Porcentajes facturados, con remito, en OC de lo ejecutado:\n";
     
      tablaMd1 += "| TIPO | % |\n";

      for (const [key, value] of Object.entries(porcentaje_tipo)) {
        tablaMd1 += `| ${key} | % ${value.toFixed(1)} |\n`;
      }

      await bot.sendMessage(chatId, tablaMd1);

      // Tabla por clasificación
      let tablaMd = "Presupuesto por Clasificación contable:\n";
      tablaMd += "| Clasificación contable | USD |\n";

      for (const [key, value] of Object.entries(sumatoria_clasificacion)) {
        tablaMd += `| ${key} | ${formatCurrency(value)} |\n`;
      }

      await bot.sendMessage(chatId, tablaMd);

      // Tabla de cuentas contables
      let tablaMd2 = "Total ejecutado por Cuenta contable:\n";
      tablaMd2 += "| CUENTA CONTABLE | USD |\n";

      for (const [key, value] of Object.entries(sumatoria_cuenta_contable)) {
        tablaMd2 += `| ${key} | ${formatCurrency(value)} |\n`;
      }
      await bot.sendMessage(chatId, tablaMd2);
//---------------------------------------------------------ENVIAR POR MAIL----------------------------------

      await bot.sendMessage(chatId, "Presiona el botón 'Enviar por correo' para enviar el presupuesto por correo.", {
        replyMarkup: {
          inline_keyboard: [
            [
              { text: "Enviar por correo", callback_data: `enviar_correo_${numPresupuesto}` },
            ],
          ],
        },
      });
    } catch (error) {
      console.error("Error al obtener el presupuesto:", error);
      await bot.sendMessage(chatId, "Ocurrió un error al obtener el presupuesto. Por favor, intenta de nuevo más tarde.");
    }
    
  } else if (choice.startsWith("enviar_correo_")) {
      const numPresupuesto = choice.split("_")[2];
      const nombreProyecto = getNombreProyecto(parseInt(numPresupuesto));
  
      await bot.sendMessage(chatId, "Por favor, ingresa tu correo electrónico:");
  
      bot.on("text", async (msg) => {
        const correoElectronico = msg.text;
  
        try {
          await bot.sendMessage(chatId, "Enviando correo electrónico...");
  
          const archivoAdjunto = `./src/df_clasificada_${numPresupuesto}.xlsx`;

          const contenido = "Adjunto el presupuesto solicitado.";
  
          await enviarCorreo(correoElectronico, `Presupuesto neteado de ${nombreProyecto}`, contenido, archivoAdjunto, nombreProyecto, numPresupuesto);
  
          await bot.sendMessage(chatId, "El correo electrónico ha sido enviado exitosamente.");
        } catch (error) {
          console.error("Error al enviar el correo electrónico:", error);
          await bot.sendMessage(chatId, "Ocurrió un error al enviar el correo electrónico. Por favor, intenta de nuevo más tarde.");
        }
  
      });
  }
  
  });

bot.start();

