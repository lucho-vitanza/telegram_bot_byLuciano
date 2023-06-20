const Telebot = require("telebot");
const { exec } = require("child_process");
const CONSTANTS = require("./CONSTANTS");

const bot = new Telebot({
  token: CONSTANTS.TELEGRAM_TOKEN,
});

bot.on(["/start", "/hola"], (msg) => {
  bot.sendMessage(msg.chat.id, `Hola ${msg.chat.username}, tenemos unos presupuestos para vos.`, {
    replyMarkup: {
      inline_keyboard: [
        [
          { text: "Presupuesto Consumo Masivo", callback_data: "consumoMasivo" },
          { text: "Presupuesto Producción CaCO3", callback_data: "produccionCaCO3" },
        ],
      ],
    },
  });
});

let isWaitingForArticleNumber = false; // Variable para controlar si se está esperando el número de artículo

bot.on("text", (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (isWaitingForArticleNumber) {
    const numArticulo = text;

    exec(`python main.py ${numArticulo}`, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error al ejecutar el archivo Python: ${error}`);
        bot.sendMessage(chatId, "Ocurrió un error al obtener el presupuesto. Por favor, intenta de nuevo más tarde.");
        return;
      }

      // stdout contendrá los resultados del archivo Python
      const result = stdout.trim();
      console.log(result); // Imprimir el resultado en la consola
      const parsedResult = JSON.parse(result.trim()); // Analizar el resultado como JSON
      console.log(parsedResult);
      
      
      // Procesar los resultados y enviar la respuesta al usuario
      const {
        cantidad_solicitada,
        cantidad_recibida,
        cantidad_pendiente,
        fecha_compromiso_entrega
      } = JSON.parse(result);

      bot.sendMessage(chatId, `Este es el código de artículo que pediste: ${numArticulo}`);
      bot.sendMessage(chatId, `Esta es la cantidad recibida hasta la fecha actual: ${cantidad_solicitada}`);
      bot.sendMessage(chatId, `Esta es la cantidad recibida hasta la fecha actual: ${cantidad_recibida}`);
      bot.sendMessage(chatId, `Esta es la cantidad pendiente: ${cantidad_pendiente}`);
      bot.sendMessage(chatId, `Esta es la fecha pactada para la próxima entrega de la OC: ${fecha_compromiso_entrega}`);  


      
      isWaitingForArticleNumber = false; // Reiniciar el estado de espera
    });
  }
});

bot.on("callbackQuery", (msg) => {
  const choice = msg.data;
  const chatId = msg.message.chat.id;

  if (choice === "consumoMasivo" || choice === "produccionCaCO3") {
    //bot.sendMessage(chatId, `Obteniendo presupuesto ${choice}...`);

    // Esperar la respuesta del usuario con el número de artículo
    bot.sendMessage(chatId, "Por favor, ingresa el número de artículo:");
    isWaitingForArticleNumber = true;
  } else {
    bot.sendMessage(chatId, "Opción no válida. Por favor, selecciona una opción del menú.");
  }
});

bot.start();