# AQW Utility Thing
TUI application to run alongside AQW that tracks character stats, drop rates, gold/exp rates, and more. Will incorporate this repo [aqw-calc](https://github.com/Shell1010/aqw-calc) into this eventually. WIP so really buggy. NOT A BOT.

This is probably not going to be used by the casual AQW player. If you're interested in technical stuff regarding AQW, whether you want to optimise your resource farms (drops, gold, rep, etc), or you want to document class data, this is *probably* going to be somewhat useful for you.

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

## Usage
First select a server to sniff from. Use the arrow keys to navigate the serverlist, and Enter to select. Servers are grouped together because multiple servers share a single IP address. Here's a list below.

**Servers grouped by IP**
- socket6.aq.com (172.65.249.3)
  - Safiria
  - Galanoth
- socket5.aq.com (172.65.210.123)
  - Twilly
- socket4.aq.com (172.65.235.85)
  - Twig
  - Gravelyn
  - Alteon
- socket3.aq.com (172.65.249.41)
  - Yorumi
- socket2.aq.com (172.65.220.106)
  - Sepulchure
  - Sir Ver
  - Espada
- socket.aq.com (172.65.160.131)
  - Artix
- euro.aqw.artix.com (172.65.207.70)
  - Swordhaven (EU)
- asia.game.artix.com (172.65.236.72)
  - Yokai (SEA)

Once you've selected a server, you can alternate between pages with the Enter key, use the arrow keys to alternate between boxes on the Class Data page.

Class Data holds the raw skill/passive data, I don't have any actual documentation written out yet for all the different keys regarding this data, but currently what is most documented are the functions and coefficients associated.

You can view them [here](https://docs.google.com/spreadsheets/d/1wU6JlyrK_jYn5mVAzrLI4pRA4UM8LgY715kKU2U1vbQ/edit?gid=101348511#gid=101348511).

There is also [this sheet](https://docs.google.com/spreadsheets/d/1aiw1TneA6ITVfpsn_lNJ-9q4h7kwWN4lNo9jvxwR7gw/edit?gid=0#gid=0) for reading stat data that may not be obvious.

The resource monitor page has stats for your Gold, Exp, Rep, Kills and even your Drops. You can use this page to monitor the rates at which you farm, you can even use this to estimate drop rates and see when you'll most likely get your next drop.

Drop rates in the Resource Monitor page aren't the actual drop rates and can only be assumed from farms themselves. However, over periods of time they can be an accurate depiction of the drop rates for said item.

Drop rates are calculated as `drop_count/kills` where drop_count is the amount of times it's dropped from a kill.

The assumed next drop attempts to calculate the number of kills needed to reach a 90% CDF or above over a geometric distribution. The equation is `n=log(1-0.9)/log(1-p)` where p is the previous assumed drop rate from before. It is then rounded up.





