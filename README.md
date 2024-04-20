# Octopus Energy API Discord Bot

This repository is WIP and is not yet ready for use.

## Installation

1. Clone the repository
2. Install the required packages using `pip install -r requirements.txt`
3. Create a `.env` file in the root directory of the repository and add the following:

```dotenv
OCTOPUS_EMAIL=<your email>
OCTOPUS_PASSWORD=<your password>
TOKEN=<your discord bot token>
GUILDS=<your guild id>
OWNERS=<your discord user id>
```

## Usage

Run the bot using `python main.py`
Sync commands in your discord server using following command:
```bash
!sync *
```
```bash
!sync ~
```

## Commands

- `!sync *` - Sync all commands
- `!sync ~` - Sync only owner commands
- `/ping` - Check if the bot is online
- `/usage <start_date> <end_date>` - Get the usage for the given date range
- `/compare <start_1> <end_1> <start_2> <end_2>` - Compare the usage for the given date ranges
- `/day <date>` - Get the usage for the given date. If no date is provided, it will default to today

>[!WARNING]
>Date Format should be `YYYY-MM-DD`