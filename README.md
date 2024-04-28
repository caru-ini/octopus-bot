>[!WARNING] :construction: WIP 
>This repository is Work In Progress and it may contain bugs or incomplete features.
# Octopus Energy API Discord Bot

オクトパスエナジーのAPIを使用したDiscordボット。
日本のAPI(api.oejp-kraken.energy)を想定して作成されていますので、UKなどの他のAPIとは互換性がありません。

Discord bot using the Octopus Energy API.
It is designed to work with the Japanese API (api.oejp-kraken.energy) and is not compatible with other APIs such as the UK one.

## Disclaimer

このBotの使用によって生じたいかなる損害についても、制作者は一切の責任を負いません。利用者の責任においてご利用ください。

The creator is not responsible for any damage caused by the use of this bot. Please use it at your own risk.

## Installation

1. Clone the repository `git clone https://github.com/caru-ini/octopus-bot.git`
2. (Optional) Create a virtual environment using `python -m venv venv` 
3. (Optional) Activate it using `source venv/bin/activate` on Linux or `venv\Scripts\activate` on Windows
4. Install the required packages using `pip install -r requirements.txt`
5. Create a `.env` file in the root directory of the repository and add the following:

```dotenv
OCTOPUS_EMAIL=<your email>
OCTOPUS_PASSWORD=<your password>
TOKEN=<your discord bot token>
GUILDS=<your guild id>
OWNERS=<your discord user id> # Optional, comma separated
```

## Usage

Run the bot using `python main.py`
Sync commands in your discord server using following command:
```bash
!sync *
```
This required every time you change the commands.\
In most cases, you will only need to run this command once.

## Commands

- `!sync *` - Sync all commands
- `/ping` - Check if the bot is online
- `/usage <start_date> <end_date>` - Get the usage for the given date range
- `/compare <start_1> <end_1> <start_2> <end_2>` - Compare the usage for the given date ranges
- `/day <date>` - Get the usage for the given date. If no date is provided, it will default to today

>[!WARNING] Caution
>Date Format should be `YYYY-MM-DD`

## To Do

- [ ] Add notifications for when the usage is above a certain threshold
- [ ] Show the usage in a graph
- [ ] Make easier to select the date range

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
