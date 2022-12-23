import argparse
import os
import sys
import pandas as pd
import json
import itertools
import re
import difflib
import numpy as np
import csv


words_to_avoid = ['all', 'some', 'random', ]

char_to_avoid = [':', ' ', '*', ',', '[', ']', '|', '\\']


def checkCLA(args):
    """
    This function checks for valid command line arguments and if the 
    new file name exists.
    """
    if not args.discordfile.endswith(".json"):
        sys.exit("Make sure the file name contains its extension '.json'.")
    
    if args.overwritefile:
        #check if file exists in directory
        if args.newfile in os.listdir(os.getcwd()):
            sys.exit("New file name must not exist to avoid overwriting data.\nDelete \""+
                        args.newfile+"\", enter a different name, " +
                        "\nor use the -o argument to ignore this check.")


def scalpMessages(messages):
    #holds valid messages (ones this program can use)
    validMessages = list()

    #scalps data searching for expressions that indicate an item name + price
    for msg in messages:
        #print("From message:", msg, "\n")
        #print(msg, flush=True)
        #input()
        #check for buying or selling (might need to optimize for location in message)
        if "sell" in msg:
            if "buy" in msg:
                sellIdx = msg.index("sell")
                buyIdx = msg.index("buy")
                tradeType = ('buy',) if buyIdx < sellIdx else ('sell',)
            else:
                tradeType = ('sell',)
        elif "buy" in msg:
            if "sell" in msg:
                sellIdx = msg.index("sell")
                buyIdx = msg.index("buy")
                tradeType = ('buy',) if buyIdx < sellIdx else ('sell',)
            else:
                tradeType = ('buy',)
        else:
            tradeType = ('sell',)
            continue
        
        result = re.findall(r'\b(?!sell|buy|wl|at|go|each|and|[0-9]\b)([a-z,\s,(,),\',:,.,\-]*(?<!at|go|in))\s([0-9]+[\/,-]?[0-9,-,\/]*)\s?(:dl:|dl|wl|:wl:|bgl|:bgl:)?(s)?', msg.lower())
        #print("Found possible items in result:", result, flush=True)
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
        #print("result before combining:", result)
        #format obtained expression and calculate price of item
        result = [(word[0], word[1]+word[2]) for word in result]
        result = [*set(result)]
        #print("result after combining:", result)
        #input()
            #print(result[x])
            #input()

        #remove unnecessary white space
        result = [(word[0].strip(), word[1].strip().replace(' ', '')) for word in result]

        #ignore messages that didn't have any matching expressions
        if result and result[0][0] and result[0][1]:
            for x,pair in enumerate(result):
                #add trade type into data entry in list
                result[x] = result[x] + tradeType
            validMessages += result
            #print("Found items in result:", result, "\n")
        #print("-----------------------------------------------------------------------")
        #if 'chameleon' in msg:
            #input()
    return validMessages


def getItemNames(itemData):
    #holds all possible item names to check for
    allItemNames = []
    validItemNames = []

    #holds all the sub (alternative) names and their equivalent main name
    subNames = dict()

    #set up these structures based on name format
    for name in itemData.values():
        #if there is only 1 valid name
        if len(name) == 1:
            allItemNames.append(' '.join(name))
            validItemNames.append(' '.join(name))
        else:
            #if there are subnames, add them in starting with actual name
            for x,value in enumerate(name):
                if x==0:
                    allItemNames.append(value)
                    validItemNames.append(value)
                else:
                    allItemNames.append(value)
                    if name[0] in subNames.keys():
                        subNames[name[x]] += name[0]
                    else:
                        subNames[name[x]] = name[0]
    return allItemNames, subNames, validItemNames


def analyzeItems(validMessages, allItemNames, subNames, checkOnlyValid):
    itemCount = dict()
    numValidItems = 0

    validItemWords = [word for items in allItemNames for word in items.split()]
    validItemWords = [word for word in validItemWords if word not in char_to_avoid]
    #print(validItemWords)
    #print(allItemNames)
    #input()
    msgNum = 1
    #loop over every valid item and price
    for msg in validMessages:
        print("Current msg:", msgNum,"/",len(validMessages), end='\r', flush=True)
        msgNum += 1
        #print(msg)
        #if people not dumb and spelled item name right, add it as valid item
        if msg[0] in allItemNames:
            #print("Valid name: ", msg[0])
            numValidItems += 1

            if msg[0] in subNames.keys():
                currName = subNames[msg[0]]
            else:
                currName = msg[0]
            
            msg = (currName, msg[1], msg[2])

            if currName in itemCount.keys():
                itemCount[currName].append(tuple(msg))
            else:
                itemCount[currName] = [tuple(msg)]
        else:
            #if they dumb dumb and spelled it wrong, try to find the valid name in the message
            #print(msg[0])
            #print("msg not a valid name. Looking for valid word in: ", msg[0])
            msgWords = msg[0].split(' ')
            msgWords = [word for word in msgWords if word and len(word)>1]
            
            #remove any invalid words that aren't part of ANY valid name 
            #speeds up analysis time by about 400%, but is only 90% as accurate
            if checkOnlyValid:
                #attempts to find a word from all the valid words that can make up an item from the inputted item names
                msgWords = [word for word in msgWords if difflib.get_close_matches(word, validItemWords, cutoff=0.9)]
                #print("Looking for matches in name: ", msgWords)

            foundMatch = False
            i = len(msgWords)
            if i>=4:
                i=4
            #print(i)
            #if i>10:
            #print(msgWords)
            #    input()
            while i>0:
                perm = itertools.combinations(msgWords, i)
                for p in perm:
                    #print(p)
                    possName = ' '.join(p)
                    if possName in allItemNames:
                        #print("Found valid item name:", p)
                        numValidItems += 1
                        if possName in subNames.keys():
                            currName = subNames[possName]
                        else:
                            currName = possName
                        
                        msg = (currName, msg[1], msg[2])
                        
                        if currName in itemCount.keys():
                            itemCount[currName].append(tuple(msg))
                        else:
                            itemCount[currName] = [tuple(msg)]
                        foundMatch = True
                        #if 'shark' in p:
                        #    input()
                        break
                    else:
                        #match = difflib.SequenceMatcher(None, msg[0], allItemNames).find_longest_match(0,len(msg[0]), 0, len(allItemNames))
                        #print("Getting close matches for: ", possName)
                        matches = difflib.get_close_matches(possName, allItemNames, cutoff=0.95)
                        
                        #if 'shark' in p:
                        #    input()
                        if matches:
                            #print("Possible matches: ", matches)
                            #print("Found valid item name:", p)
                            #input()
                            numValidItems += 1

                            if matches[0] in subNames.keys():
                                currName = subNames[matches[0]]
                            else:
                                currName = matches[0]

                            msg = (currName, msg[1], msg[2])

                            if currName in itemCount.keys():
                                itemCount[currName].append(tuple(msg))
                                break
                            else:
                                itemCount[currName] = [tuple(msg)]
                                break
                        #print(msg[0])
                        #print("Looking for: ", msg[0])
                        #print("Found match: ", msg[0][match.a:match.a + match.size])
                        #print("Match length: ", match.size)
                        #print('\n')
                if foundMatch:
                    break
                i -= 1
            #if i == 0:
                #print("No possible item name found.")
    #print('')
    #print({name: count for name, count in sorted(itemCount.items(), key=lambda item: item[1])})
    #print("Total names found: ", numValidItems)
    return {name: count for name, count in sorted(itemCount.items(), key=lambda item: item[1], reverse=True)}, numValidItems


def extractPrices(itemCount):
    itemPrices = dict()
    for item in itemCount.keys():

        for x,price in enumerate(itemCount[item]):
            #print(price)
            
            if '-' in price[1]:
                dashIdx = price[1].index('-')

                if '/' in price[1]:
                    #print(price)
                    slashIdx = price[1].index('/')

                    if dashIdx < slashIdx:
                        if price[2] == 'buy':
                            price = (price[0], price[1][dashIdx+1:], price[2])
                        else:
                            price = (price[0], price[1][:dashIdx] + price[1][slashIdx:], price[2])
                    else:
                        if price[2] == 'buy':
                            price = (price[0], price[1][:dashIdx-1], price[2])
                        else:
                            price = (price[0], price[1][:slashIdx] + price[1][dashIdx-1:], price[2])
                else:
                    if price[2] == 'buy':
                        idx = price[1].index('-')
                        price = (price[0], price[1][idx+1:], price[2])
                    else:
                        idx = price[1].index('-')
                        price = (price[0], price[1][:idx], price[2])

            numbers = re.findall(r'\d+', price[1])
            #print("Numbers: ", numbers)

            if len(numbers) == 1:
                #print("Adding price: ", int(numbers[0]))
                if (price[0], price[2]) in itemPrices.keys():
                    itemPrices[price[0], price[2]].append(int(numbers[0]))
                else:
                    itemPrices[price[0], price[2]] = [int(numbers[0])]
            elif len(numbers) == 2:
                if '/' in price[1]:
                    idx = price[1].index('/')
                    if int(price[1][idx-1]) == 1:
                        #print("Adding price: ", int(numbers[1]))
                        if (price[0], price[2]) in itemPrices.keys():
                            itemPrices[price[0], price[2]].append(int(numbers[1]))
                        else:
                            itemPrices[price[0], price[2]] = [int(numbers[1])]
                    else:
                        #print("Adding price: ", int(numbers[1])/int(numbers[0]))
                        if (price[0], price[2]) in itemPrices.keys():
                            itemPrices[price[0], price[2]].append(int(numbers[1])/int(numbers[0]))
                        else:
                            itemPrices[price[0], price[2]] = [int(numbers[1])/int(numbers[0])]
            #print(itemPrices[price[0], price[2]])
            #input()
    return itemPrices


def calculateAverages(itemPrices, validItemNames):
    for item in itemPrices:
        if len(itemPrices[item])<3:
            continue
        #Calculate the mean and standard deviation
        mean = np.mean(itemPrices[item])
        std = np.std(itemPrices[item])

        if std==0:
            continue

        #Normalize the data
        normalizedData = [(price-mean)/std for price in itemPrices[item]]
        
        #print("Starting price list: \t", itemPrices[item])
        #print("Length: ", len(itemPrices[item]))
        
        #Get boundaries
        q1, q3 = np.percentile(normalizedData, [20, 90])

        # Calculate the IQR
        iqr = q3-q1

        # Calculate the lower and upper bounds
        lowerBound = q1-(1.5*iqr)
        upperBound = q3+(1.5*iqr)

        # Remove outliers from the original data
        itemPrices[item] = [x for x, y in zip(itemPrices[item], normalizedData) if y >= lowerBound and y <= upperBound]
        #print("Length: ", len(itemPrices[item]))
        #print("After removing outliers:", itemPrices[item], "\n\n")
        #input()
    
    averagePrices = {name: round(np.mean(prices), 2) for name,prices in itemPrices.items()}
    #for item in itemPrices:
    #    print(item, '\t', round(np.mean(itemPrices[item]), 2))
    #print(numItems)

    #combining item's buy and sell elements into a single one (I should've done this originally, but now it's too much work)
    combinedItemNames = {}
    for name in averagePrices:
        if name[0] not in combinedItemNames.keys():
            combinedItemNames[name[0]] = {}
            combinedItemNames[name[0]]['sell'] = 'N/A'
            combinedItemNames[name[0]]['buy'] = 'N/A'
        if name[1] == 'buy':
            combinedItemNames[name[0]]['buy'] = averagePrices[name]
        else:
            combinedItemNames[name[0]]['sell'] = averagePrices[name]

    #fill in empty information for items with no prices
    for name in validItemNames:
        if name not in combinedItemNames.keys():
            combinedItemNames[name] = {}
            combinedItemNames[name]['buy'] = 'N/A'
            combinedItemNames[name]['sell'] = 'N/A'
    
    return combinedItemNames


def processData(discordfile, itemData):
    print("Attempting to find discord file.")

    #load in discord message data
    try:
        rawData = json.load(open(discordfile, encoding="utf8"))
    except Exception as e:
        print(e)
        exit("Failure to load in data file. Make sure file exists and is in same repository as this program.")

    print("Found file.")

    #format json for content only and all to be lowercase
    messages = [(rawData['messages'][i]['content']).lower() for i in range(len(rawData['messages']))]

    print("Total messages (unsorted):", len(messages))

    #remove duplicates (people have a habit of copy pasting a lot)
    messages = [*set(messages)]

    print("Removing useless messages.")
    #general message cleanup to remove blatently useless ones
    for msg in messages[:]:
        if msg.count('\n') > 8 or len(msg) > 300:
            messages.remove(msg)
            continue
        
        for word in msg.split(' '):
            if word in words_to_avoid:
                messages.remove(msg)
                break
    
    print("Done.")

    #remove newline characters
    for x,msg in enumerate(messages):
        messages[x] = msg.replace('\n', ' ')
    
    #count up instances of words (most common words)
    #wordData = dict()
    #for msg in messages:
    #    for word in msg.split(' '):
    #        if word in wordData.keys():
    #            wordData[word] += 1
    #        else:
    #            wordData[word] = 0
        #print(msg)
        #print("-----------------------------------------------")
    
    #wordData = dict(reversed(sorted(wordData.items(), key=lambda x:x[1])))
    #wordData = {word:count for word,count in wordData.items() if count>3}
    
    #print(wordData)
    #print("Results:")

    print("Total messages:", len(messages))

    print("Searching for valid messages...")
    validMessages = scalpMessages(messages)
    print("Done.")

    print("Total valid price messages:", len(validMessages))

    print("Getting valid items...")
    allItemNames, subNames, validItemNames = getItemNames(itemData)
    print("Done.")

    print("Scraping found items...")
    itemCount, numItems = analyzeItems(validMessages, allItemNames, subNames, False)
    print("Done.")

    print("Number of found pets:", numItems)

    itemPrices = extractPrices(itemCount)

    #print("Selling slime prices: ", itemPrices['pet slime', 'sell'])
    #print("Buying slime prices: ", itemPrices['pet slime', 'buy'])
    #print(itemPrices)

    averagePrices = calculateAverages(itemPrices, validItemNames)

    return averagePrices, itemPrices, numItems


def startAnalysis(itemFile, discordFile):
    with open(itemFile, 'r') as fp:
        itemData = json.load(fp)

    print("Beginning analysis on items in file:", itemFile)
    itemInformation, itemPrices, numItems = processData(discordFile, itemData)
    print("Analysis complete.")

    #print("Found average prices: ")
    #for name,price in averagePrices.items():
    #    if price != 'N/A':
    #        print("It looks like people are  " + name[1] + "ing\t" + name[0] + " for", price, "wls on average (based on the provided data).")
    
    #combined information into one dictionary
    for item in itemInformation.keys():
        if itemInformation[item]['buy'] != 'N/A':
            itemInformation[item]['buyPrices'] = itemPrices[(item, 'buy')]
            
            if itemInformation[item]['sell'] != 'N/A':
                itemInformation[item]['sellPrices'] = itemPrices[(item, 'sell')]
            else:
                itemInformation[item]['sellPrices'] = 'N/A'
        elif itemInformation[item]['sell'] != 'N/A':
            itemInformation[item]['sellPrices'] = itemPrices[(item, 'sell')]
            
            if itemInformation[item]['buy'] != 'N/A':
                itemInformation[item]['buyPrices'] = itemPrices[(item, 'buy')]
            else:
                itemInformation[item]['buyPrices'] = 'N/A'
        else:
            itemInformation[item]['sellPrices'] = 'N/A'
            itemInformation[item]['buyPrices'] = 'N/A'

    sortedItemKeys = sorted(itemInformation, key=lambda x: x)
    itemInformation = {key: itemInformation[key] for key in sortedItemKeys}

    return itemInformation


def writeToFile(itemInformation, fileName, overwrite):
    if not overwrite:
        #print("Attempting to remove:", fileName)
        if os.path.isfile(fileName):
            os.remove(fileName)

    columns = ['Name', 'Buy', 'Sell', 'Found Buy Prices', 'Found Sell Prices']

    with open(fileName, 'w', newline='') as csvfile:
        #create writer
        writer = csv.writer(csvfile)

        #create titles
        writer.writerow(columns)
        #writer.writerow(['Name', 'Buy', 'Sell'])

        #populate CSV file
        for name, values in itemInformation.items():
            #print("trying to write: ", name, values)
            #write key and values
            writer.writerow([name, values['buy'], values['sell'], values['buyPrices'], values['sellPrices']])
            #writer.writerow([name, values['buy'], values['sell']])


def main():
    #CLA argument definitions
    parser = argparse.ArgumentParser("Get trends of Growtopia items.\n")
    parser.add_argument('--discordfile', '-d', type=str, required=True, help="File name in \DiscordData containing discord chat data with 'content' column.")
    parser.add_argument('--itemfile', '-i', type=str, required=True, help="JSON file name in \ItemNames containing names of items to search for.")
    parser.add_argument('--newfile', '-n', type=str, required=True, help="Name of file to put information into. Will save in directory \PriceData.")
    parser.add_argument('--overwritefile', '-o', action='store_false', help="Give warning about overwriting a pre-existing file.")
    args = parser.parse_args()

    checkCLA(args)

    #read CLA for uncleaned data file and new data file name
    itemFile = os.getcwd() + '\\ItemNames\\' + args.itemfile
    discordFile = os.getcwd() + '\\DiscordData\\' + args.discordfile
    newFile = os.getcwd() + '\\PriceData\\' + args.newfile

    itemInformation = startAnalysis(itemFile, discordFile)

    print("Writing results to", args.newfile)
    writeToFile(itemInformation, newFile, args.overwritefile)
    print("Finished.")


if __name__ == "__main__":
    main()