# AQW Utility Thing
Utility application to run alongside AQW that tracks character stats, drop rates, gold/exp rates, and more. Will incorporate this repo [aqw-calc](https://github.com/Shell1010/aqw-calc) into this eventually. WIP so really buggy. NOT A BOT.

## Disclaimer :warning:
[AQW's ToS](https://www.aq.com/lore/guides/AQWRules) states no 3rd party programs (seems intentionally vague), while this is not a cheating tool, it is technically regarded to be a 3rd party program. It does not connect to the servers nor does it automate sending data on behalf of you, so it's not a bot. This cannot be detected through normal means as it's the equivalent of running wireshark on your PC, it's not necessarily something AE will crack down on.

## Feature Roadmap
- [x] Gathering skills/passives data
- [ ] Using above data for aqw damage calculator, be able to pass values into raw damage calculator
- [ ] Raw damage calculator, basically inputted values from scratch
- [x] Gold/Exp/Rep gain rate as you farm
- [x] Estimated Drop rates when farming drops, and estimate when your next drop will be

## Installation & Setup
Install python3.11 or later. On windows it's possible to install via Microsoft Store.

Download as zip or run this
```sh
git clone https://github.com/Shell1010/aqw-utils.git
```

Install dependencies by running this in your cli
```sh
pip install -r requirements.txt
```

On Windows, due to the fact it does packet sniffing, you'll have to install [Npcap](https://npcap.com/#download). 

Additionally you can edit the config.toml to dictate how long drop cache should last before clearing it. It's in seconds. Cache for the specific resource is only reset if no activity occurs in the period.


Run script
```sh
python main.py
```

### Usage
Use arrow keys to navigate server list, enter to select.
It utilises packet sniffing, so only gets data AFTER an event happens, get class data by changing classes, changing pots.
