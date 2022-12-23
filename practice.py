import re
from getPrices import *



messages = [
    r"sell draconic wings. need urg dls. cheap 60 :dl:  at doxurg",
    r"rsell ice calf leash 3:dl: go jsvm",
    r"buy dark fairy pendant 15 dm me",
    r"sell : wolf tamer's glove 4 each red pet tyranopatos 5 wl care pear 6 wl at yecar",
    r"ethereal dragon 15 wls snakewolf 120 wls chinese dragon mask (yellow) 35wls ghost dragon charm (gdc) 480wls cloak of equilibrium 90wls at diavolostore",
    r"sell gdc 310 at butio sell gdc 310 at butio sell gdc 310 at butio",
    r"sell draconic wings. need urg dls. cheap 60 :dl:  at doxurg",
    r"sell pet leash fish :skeletalshark: 5wl  and sell riding fish :skeletalshark:  32wl   cheap!! sir or madam you buy?  go oz4b :cb_bird_wave:",
    r"SELL Pet Frog 1/wl in ICYHARBOUR",
    r"•SELLING LIST: 📷Sonar Bracelet 2📷 📷Familiar Leash 7📷 📷Electro Magnifying Glass 14📷 📷Dark Fairy Pendant 19📷 📷Star Dragon Claw 9📷AT📷📷QLEX",
    r"SELL [Robot Wants Dubstep] 3/10 SELL [Turkey Wings] 16WL SELL [Zorbnik Leash] 31WL SELL [Dragon Tail] 7/1 ===> Sell cheap at 6D03 <===",
    r":bgl: **chick leash** :bgl:  :bgl: **egg champion cape** :bgl:  :bgl: **easter creature** :bgl:  :gtcoolmoyai:  **sell at 9042** :gtcoolmoyai:"
]

validMessages = list()

#scalps data searching for expressions that indicate an item name + price
for msg in messages:
    #check for buying or selling (might need to optimize for location in message)
    if "sell" in msg:
        tradeType = ('sell',)
    elif "buy" in msg:
        tradeType = ('buy',)
    else:
        continue
    
    result = re.findall(r'\b(?!sell|buy|wl|at|go|each|and|[0-9]\b)([a-z,\s,(,),\',:,.,\-]*(?<!at))\s([0-9]+[\/,-]?[0-9,-,\/]*)\s?(:dl:|dl|wl|:wl:|bgl|:bgl:)?(s)?', msg.lower())

    #remove useless characters that might be picked up
    #result = [(word[0], word[1], word[2].replace(':', '')) for word in result]
    #result = [(word[0], word[1], word[2].replace(',', '')) for word in result]
    #result = [(word[0], word[1], word[2].replace('*', '')) for word in result]
    for x,word in enumerate(result):
        for character in char_to_avoid:
            result[x] = (result[x][0], result[x][1].replace(character, ''), result[x][2].replace(character, ''))

    for word in result[:]:
        if not (word[1] or word[2]):
            result.remove(word)

    #format obtained expression and calculate price of item
    for x,item in enumerate(result):
        print(item)
        if item[2] == 'dl':
            if not item[1]:
                result[x] = (item[0], item[1]+'100')
            else:
                result[x] = (item[0], item[1]+'00')
        elif item[2] == 'bgl':
            if not item[1]:
                result[x] = (item[0], item[1]+'10000')
            else:
                result[x] = (item[0], item[1]+'0000')

        print(result[x])
        input()

    #remove unnecessary white space
    result = [(word[0].strip(), word[1].strip().replace(' ', '')) for word in result]

    #ignore messages that didn't have any matching expressions
    if result and result[0][0] and result[0][1]:
        for x,pair in enumerate(result):
            #add trade type into data entry in list
            result[x] = result[x] + tradeType
        validMessages += result
        

for word in validMessages:
    print(word)

if not validMessages:
    print("No matches found.")