# GrowTrends
> Small growtopia NLP app to keep track of item prices within the Nemo discord utilizing Discord Chat Exporter.

GrowTrends is a program that acts as a price analyzer which uses information found within
The Lost Nemo! discord server. It has over 300k members with tens of thousands of daily
posts from users. This application uses scraped messages from channels which are obtained
using DiscordChatExporter (https://github.com/Tyrrrz/DiscordChatExporter). The found prices
are then analyzed and exported to a separate CSV file.

## Installation
In order to run this program, all you need to do is install the libraries
found in `requirements.txt`.
Python and PIP are required.

Run the following command to install them:

```
pip install -r /path/to/requirements.txt
```

***It's highly recommended (but not necessary) to work inside a virtual 
environment to avoid any possible version conflicts.***

## Usage
### [formatItemName.py](/formatItemName.py)
```
usage: Format raw pet names from .txt to .json.
 [-h] --datafile DATAFILE --newfile NEWFILE [--overwriteFile]

options:
  -h, --help            show this help message and exit
  --datafile DATAFILE, -d DATAFILE
                        File name in \RawItems containing raw pet names.
  --newfile NEWFILE, -n NEWFILE
                        Name of file to put information into. Will be saved in directory \ItemNames.
  --overwriteFile, -o   Give warning about overwriting a pre-existing file.
```

### [getPrices.py](/getPrices.py)
```
usage: Get trends of Growtopia items.
 [-h] --discordfile DISCORDFILE --itemfile ITEMFILE --newfile NEWFILE
                                       [--overwritefile]

options:
  -h, --help            show this help message and exit
  --discordfile DISCORDFILE, -d DISCORDFILE
                        File name in \DiscordData containing discord chat data with 'content' column.
  --itemfile ITEMFILE, -i ITEMFILE
                        JSON file name in \ItemNames containing names of items to search for.
  --newfile NEWFILE, -n NEWFILE
                        Name of file to put information into. Will save in directory \PriceData.
  --overwritefile, -o   Give warning about overwriting a pre-existing file.
```
