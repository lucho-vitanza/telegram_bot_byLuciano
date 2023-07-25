Project state: telegram_bot_byLuciano.V01

INFORMATION ABOUT THE PROJECT

## Prerequisites
Before running the bot, please make sure you have NVM (Node Version Manager) installed on your system. If you don't have it installed, you can follow the instructions to install it [here](https://github.com/nvm-sh/nvm#installation).

## Configuration bot
Before running the bot, you need to set up your Telegram Bot token. Follow these steps:

1. Go to the [BotFather](https://t.me/botfather) on Telegram and create a new bot.
2. Copy the generated API token.
3. Create a `.env` file in the root directory of the project.
4. Add the following line to the `.env` file and replace `<YOUR_BOT_TOKEN>` with the API token you obtained from the BotFather
5. Write token in constants.js

## Project description
The project consists of two main parts:

    Processing Account Data:
        -"calculos.py" and "df_totales.py" are the core components responsible for processing the data.
        -"df_totales.py" takes a file.xlsx from the "src" folder and saves "df_totales_${num}.xlsx" in the same folder.
        -Each budget is identified by a unique number (keyID) that is used by "calculos.py" on demand for processing.

    Showing Information in Telegram Bot:
        -On demand, when "index.js" is called from Node.js and the client selects a budget to analyze from the menu, "index.js" calls                      "calculos.py" with the corresponding keyID as a parameter.
        -The function "estadisticas" in "calculos.py" returns a JSON response via stdout, which is then caught and sent to the Telegram Bot to             display the information.

Python:
      ```linux console
    pip install -r requirements.txt
      ```
  I use: 
    ```pyenv==2.3.20```
  
  ```requirements:
    python==3.11.4
    pandas==1.3.0
    numpy==1.19.5
    textblob==0.15.3
    python-Levenshtein==0.12.2
    datefinder==0.7.1
  ```
```Node.js:
  nvm use 18.16.0
```
run bot:
  console linux in index.js directory: npm start


Enjoy your budget analizator :)


  
  



