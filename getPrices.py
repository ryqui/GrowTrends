import argparse
import os
import sys
import json
import itertools
import re
import difflib
import numpy as np
import csv
import time

import UI

words_to_avoid = ['all', 'some', 'random', ] #words that we don't want in our messages
char_to_remove = [':', ' ', '*', ',', '[', ']', '|', '\\'] #characters we want to remove from our messages
logAnalysis = True


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
    """
    This funcion will scalp each message looking for an item+price combo using
    a regular expression. It will save each found item+price along with the
    type of sale, either buy or sell, in a tuple within a list. This list is
    then returned.
    """

    #holds valid messages (ones this program can use)
    validMessages = list()

    try:
        if currUI:
            counter = 0
            percentToAdd = 20
            progressAdded = 0
            try:
                lenMessagesForProgress = percentToAdd/len(messages)
            except:
                lenMessagesForProgress = 0
        
        #scalps data searching for expressions that indicate an item name + price
        for msg in messages:
            if currUI:
                counter += lenMessagesForProgress
                if counter>=1:
                    counter = 0
                    progressAdded = progressAdded + 1
                    currUI.progress = currUI.progress + 1
                    time.sleep(0.01)
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
            
            #attempt to extract all price information from message
            result = re.findall(r'(?!\r\n|\r|\n)\b(?!sell|buy|wl|at|go|each|and|[0-9]| \b)([a-z,\s,(,),\',:,.,\-]*(?<!at|go|in))\s([0-9]+[\/,-]?[0-9,-,\/]*) ?(:?[w|d|b]ls?:?)?(s)?(.*?(\r\n|\r|\n))?', msg.lower())
            
            for x,word in enumerate(result):
                for character in char_to_remove:
                    result[x] = (result[x][0], result[x][1].replace(character, ''), result[x][2].replace(character, ''))

            for word in result[:]:
                if not (word[1] or word[2]):
                    result.remove(word)

            result = [(word[0], word[1]+word[2]) for word in result]
            result = [*set(result)]

            #remove unnecessary white space
            result = [(word[0].strip(), word[1].strip().replace(' ', '')) for word in result]

            #ignore messages that didn't have any matching expressions
            if result and result[0][0] and result[0][1]:
                for x,pair in enumerate(result):
                    #add trade type into data entry in list
                    result[x] = result[x] + tradeType
                validMessages += result
        
        while progressAdded < percentToAdd and currUI.progress < 100:
            currUI.progress = currUI.progress + 1
            progressAdded = progressAdded + 1
            time.sleep(0.01)

    except Exception:
        print("There was an error extracting price information. Please make sure the " +
                "entered \"Discord File\" is in a proper JSON format. Specifically, " +
                "make sure that it is a file that was obtained by using DiscordChatExporter.")
    return validMessages


def getItemNames(itemData):
    """
    This funcion goes through the provided item name file and extracts the
    names and subnames and saves them in 3 different lists:
      allItemNames - every possible item name and subname
      subnames - every provided subname
      validItemNames - only the main item name (without subnames)
    """
    #holds all possible item names to check for
    allItemNames = []
    validItemNames = []

    #holds all the sub (alternative) names and their equivalent main name
    subNames = dict()

    try:
        if currUI:
            counter = 0
            percentToAdd = 10
            progressAdded = 0
            try:
                lenMessagesForProgress = percentToAdd/len(itemData)
            except:
                lenMessagesForProgress = 0
        
        #set up these structures based on name format
        for name in itemData.values():
            if currUI:
                counter += lenMessagesForProgress
                if counter>=1:
                    counter = 0
                    progressAdded = progressAdded + 1
                    currUI.progress = currUI.progress + 1
                    time.sleep(0.01)
            #if there is only 1 valid name
            if len(name) == 1:
                allItemNames.append(' '.join(name))
                validItemNames.append(' '.join(name))
            else:
                #if there are subnames, add them in starting with actual name
                for x,value in enumerate(name):
                    #actual item name (main name)
                    if x==0:
                        allItemNames.append(value)
                        validItemNames.append(value)

                    #this name is a subname, so add it to a dict as a value to the
                    #main item key
                    else:
                        allItemNames.append(value)
                        #if main item has already been added, append subname
                        if name[0] in subNames.keys():
                            subNames[name[x]] += name[0]

                        #if this is the first subname, add it as a key with the
                        #subname as the value
                        else:
                            subNames[name[x]] = name[0]
        
        while progressAdded < percentToAdd and currUI.progress < 100:
            currUI.progress = currUI.progress + 1
            progressAdded = progressAdded + 1
            time.sleep(0.01)

    except Exception:
        print("There was an error reading the \"Item Name File.\" Please make sure "+
                "the items are in a proper JSON format. Specifically, item names that"+
                "were formatted using the \"Format Item name\" option.")
    return allItemNames, subNames, validItemNames


def analyzeItems(validMessages, allItemNames, subNames, checkOnlyValid):
    """
    For each valid message (valid price), we will try to find a valid name and
    append the corresponding price to a dict under this name. If necessary, the
    algorithm will check each permutation up to a predefined length to try and
    find the name. It will check for closely matching strings so there may be
    some uncertainty within the results (although the string must be almost a
    direct match). 
    This function returns a sorted dict (itemCount) containing the item names 
    and prices.
    """
    itemCount = dict()
    numValidItems = 0

    #split message into individual words
    validItemWords = [word for items in allItemNames for word in items.split()]
    #remove words that are character we want to avoid
    validItemWords = [word for word in validItemWords if word not in char_to_remove]

    if logAnalysis:
        #used for printing current message number
        msgNum = 1
    
    if currUI:
        counter = 0
        percentToAdd = 50
        progressAdded = 0
        try:
            lenMessagesForProgress = percentToAdd/len(validMessages)
        except:
            lenMessagesForProgress = 0

    #loop over every valid item and price
    for msg in validMessages:
        if currUI:
            counter += lenMessagesForProgress
            if counter>=1:
                counter = 0
                progressAdded = progressAdded + 1
                currUI.progress = currUI.progress + 1
                time.sleep(0.01)
        
        if logAnalysis:
            print("Current msg:", msgNum,"/",len(validMessages), end='\r', flush=True)
            msgNum += 1

        #if item name is valid, add it as valid item
        if msg[0] in allItemNames:
            #found valid item, add it to itemCount
            numValidItems += 1

            #find main name
            if msg[0] in subNames.keys():
                currName = subNames[msg[0]]
            else:
                currName = msg[0]

            msg = (currName, msg[1], msg[2])

            #add it to itemCount
            if currName in itemCount.keys():
                itemCount[currName].append(tuple(msg))
            else:
                itemCount[currName] = [tuple(msg)]
        else:
            #if name isn't valid, try to find a valid name in the message
            msgWords = msg[0].split(' ')
            #remove any blank message or messages with length of 0 or 1
            msgWords = [word for word in msgWords if word and len(word)>1]
            
            #remove any invalid words that aren't part of ANY valid name 
            #speeds up analysis time by about 400%, but only finds 90% as much
            if checkOnlyValid:
                #removes any words that aren't a valid word
                msgWords = [word for word in msgWords if difflib.get_close_matches(word, validItemWords, cutoff=0.9)]

            foundMatch = False
            i = len(msgWords)
            #limit length of possible permutations
            if i>8:
                continue
            elif i>=5:
                i=5

            while i>0:
                #get all permutations of length i
                perm = itertools.combinations(msgWords, i)
                for p in perm:
                    #check if permutation is valid name
                    possName = ' '.join(p)
                    if possName in allItemNames:
                        #found valid name
                        numValidItems += 1

                        #find main name
                        if possName in subNames.keys():
                            currName = subNames[possName]
                        else:
                            currName = possName
                        
                        msg = (currName, msg[1], msg[2])
                        
                        #add it to itemCount
                        if currName in itemCount.keys():
                            itemCount[currName].append(tuple(msg))
                        else:
                            itemCount[currName] = [tuple(msg)]
                        foundMatch = True
                        break
                    else:
                        #permutation is not a valid name, but check for close matches
                        matches = difflib.get_close_matches(possName, allItemNames, cutoff=0.95)
                        
                        if matches:
                            #found valid name
                            numValidItems += 1

                            #find main name
                            if matches[0] in subNames.keys():
                                currName = subNames[matches[0]]
                            else:
                                currName = matches[0]

                            msg = (currName, msg[1], msg[2])

                            #add it to itemCount
                            if currName in itemCount.keys():
                                itemCount[currName].append(tuple(msg))
                                break
                            else:
                                itemCount[currName] = [tuple(msg)]
                                break
                if foundMatch:
                    break
                i -= 1

    if logAnalysis:
        print('')

    while progressAdded < percentToAdd and currUI.progress < 100:
        currUI.progress = currUI.progress + 1
        progressAdded = progressAdded + 1
        time.sleep(0.01)
    
    return {name: count for name, count in sorted(itemCount.items(), key=lambda item: item[1], reverse=True)}, numValidItems


def extractPrices(itemCount):
    """
    Go through each price entry and extract the actual price, accommodating the
    variance in possible price formats. It is hard to account for some higher
    priced items, as instead of referring to them in the base amount, they make
    the assumtion that it is known that the higher value is being referred to
    (i.e. they may say '3' but actually mean '3,000,000' because it could easily
    be inferred that they were talking about the higher amount with context).
    Overall, it is more accurate with lower priced items.
    
    This function returns a dict with each item as the key, and the values as
    a list of that items found prices. 
    """
    itemPrices = dict()

    if currUI:
        counter = 0
        percentToAdd = 5
        progressAdded = 0
        try:
            lenMessagesForProgress = percentToAdd/len(itemCount)
        except:
            lenMessagesForProgress = 0

    #loop over each item
    for item in itemCount.keys():
        if currUI:
            counter += lenMessagesForProgress
            if counter>=1:
                counter = 0
                progressAdded = progressAdded + 1
                currUI.progress = currUI.progress + 1
                time.sleep(0.01)
        
        #loop over all the prices found for that item and attempt to extract the price
        for x,price in enumerate(itemCount[item]):
            #if price is a range
            if '-' in price[1]:
                dashIdx = price[1].index('-')

                #represents the price per item amount
                if '/' in price[1]:
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

            if len(numbers) == 1:
                if int(numbers[0]) == 0:
                    continue
                if (price[0], price[2]) in itemPrices.keys():
                    itemPrices[price[0], price[2]].append(int(numbers[0]))
                else:
                    itemPrices[price[0], price[2]] = [int(numbers[0])]
            elif len(numbers) == 2:
                if '/' in price[1]:
                    if numbers[1] == 0:
                        continue
                    idx = price[1].index('/')
                    if int(price[1][idx-1]) == 1:
                        if (price[0], price[2]) in itemPrices.keys():
                            itemPrices[price[0], price[2]].append(int(numbers[1]))
                        else:
                            itemPrices[price[0], price[2]] = [int(numbers[1])]
                    else:
                        if (price[0], price[2]) in itemPrices.keys():
                            itemPrices[price[0], price[2]].append(int(numbers[1])/int(numbers[0]))
                        else:
                            itemPrices[price[0], price[2]] = [int(numbers[1])/int(numbers[0])]
    
    while progressAdded < percentToAdd and currUI.progress < 100:
        currUI.progress = currUI.progress + 1
        progressAdded = progressAdded + 1
        time.sleep(0.01)
    
    return itemPrices


def calculateAverages(itemPrices, validItemNames):
    """
    Remove outliers and calculate the average price for each item.
    """
    if currUI:
        counter = 0
        percentToAdd = 5
        progressAdded = 0
        try:
            lenMessagesForProgress = percentToAdd/len(itemPrices)
        except:
            lenMessagesForProgress = 0

    for item in itemPrices:
        if currUI:
            counter += lenMessagesForProgress
            if counter>=1:
                counter = 0
                progressAdded = progressAdded + 1
                currUI.progress = currUI.progress + 1
                time.sleep(0.01)

        if len(itemPrices[item])<3:
            continue
        
        #calculate the mean and standard deviation
        mean = np.mean(itemPrices[item])
        std = np.std(itemPrices[item])

        if std==0:
            continue
        
        #normalize the data
        normalizedData = [(price-mean)/std for price in itemPrices[item]]

        # calculate the median and median absolute deviation of the data
        median = np.median(normalizedData)
        mad = np.median(np.abs(normalizedData - median))

        #log messages
        if logAnalysis:
            print('\n',normalizedData,'\n')
            print("mean:", np.mean(itemPrices[item]))
            print("median: ", median)
            print("mad =", mad)

        # define the threshold as 3 times the median absolute deviation
        threshold = 8

        # calculate the modified z-scores for each data point
        modified_z_scores = 0.8 * (normalizedData - median) / (mad + 0.00001)

        if logAnalysis:
            print("modified_z_scores: ", modified_z_scores)

        # remove any data points that have a modified z-score greater than the threshold
        itemPrices[item] = [x for x, score in zip(itemPrices[item], modified_z_scores) if np.abs(score) <= threshold]

        #calculate new mean
        mean = np.mean(itemPrices[item])

        #define a valid range of data (to help remove outliers + keep prices consistent)
        priceRange = 0.85 * mean

        lowerBound = mean - priceRange
        upperBound = mean + priceRange

        if logAnalysis:
            print("Uncleaned List:\n",sorted(itemPrices[item]), sep='')

        itemPrices[item] = [x for x in itemPrices[item] if lowerBound < x < upperBound]

        if logAnalysis:
            # print the outlier removed list
            print("Cleaned List:\n",sorted(itemPrices[item]), sep='')

        #input()

        #remove outliers from the original data
        #itemPrices[item] = [x for x, y in zip(itemPrices[item], normalizedData) if y >= lowerBound and y <= upperBound]

    while progressAdded < percentToAdd and currUI.progress < 100:
        currUI.progress = currUI.progress + 1
        progressAdded = progressAdded + 1
        time.sleep(0.01)
    
    averagePrices = {name: round(np.mean(prices), 2) for name,prices in itemPrices.items() if prices}

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
    """
    Function to process the given data using a provided discord message log file.
    """

    if logAnalysis:
        print("Attempting to find discord file.")

    #load in discord message data
    try:
        rawData = json.load(open(discordfile, encoding="utf8"))
    except Exception as e:
        if logAnalysis:
            print(e)
            exit("Failure to load in data file. Make sure file exists and is in same repository as this program.")

    if logAnalysis:
        print("Found file.")

    try:
        #format json for content only and all to be lowercase
        messages = [(rawData['messages'][i]['content']).lower() for i in range(len(rawData['messages']))]
    except:
        currUI.outputMessage("Error: Discord file is not formatted properly.", -1)
        return None, None, None

    if logAnalysis:
        print("Total messages (unsorted):", len(messages))

    #remove duplicates (people have a habit of copy-pasting a lot)
    messages = [*set(messages)]

    if logAnalysis:
        print("Removing useless messages.")

    if currUI:
        counter = 0
        percentToAdd = 5
        progressAdded = 0
        try:
            lenMessagesForProgress = percentToAdd/len(messages)
        except:
            lenMessagesForProgress = 0

    #general message cleanup to remove blatently useless ones
    for msg in messages[:]:
        if currUI:
            counter += lenMessagesForProgress
            if counter>=1:
                counter = 0
                progressAdded = progressAdded + 1
                currUI.progress = currUI.progress + 1
                time.sleep(0.01)

        if len(msg) > 850:
            messages.remove(msg)
            continue
        
        for word in msg.split(' '):
            if word in words_to_avoid:
                messages.remove(msg)
                break
        

    while progressAdded < percentToAdd and currUI.progress < 100:
        currUI.progress = currUI.progress + 1
        progressAdded = progressAdded + 1
        time.sleep(0.01)
    
    if logAnalysis:
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
    
    #wordData = dict(reversed(sorted(wordData.items(), key=lambda x:x[1])))
    #wordData = {word:count for word,count in wordData.items() if count>3}

    if logAnalysis:
        print("Total messages:", len(messages))
        print("Searching for valid messages...")

    #get the valid messages
    validMessages = scalpMessages(messages)
    
    if logAnalysis:
        print("Done.")
        print("Total valid price messages:", len(validMessages))
        print("Getting valid items...")
    
    #get the item names
    allItemNames, subNames, validItemNames = getItemNames(itemData)
    
    if logAnalysis:
        print("Done.")
        print("Scraping found items...")

    #get item data from the valid messages
    itemCount, numItems = analyzeItems(validMessages, allItemNames, subNames, False)
    
    if logAnalysis:
        print("Done.")
        print("Number of found pets:", numItems)

    #get the item prices
    itemPrices = extractPrices(itemCount)

    #remove outliers and get data averages
    averagePrices = calculateAverages(itemPrices, validItemNames)

    for item in averagePrices:
        if averagePrices[item]['buy'] is np.nan:
            averagePrices[item]['buy'] = "N/A"
        if averagePrices[item]['sell'] is np.nan:
            averagePrices[item]['sell'] = "N/A"

    return averagePrices, itemPrices, numItems


def startAnalysis(itemFile, discordFile, appUI=None):
    """
    Loads and runs an analysis on the items in the provided item file.
    """
    if appUI:
        global currUI
        currUI = appUI
    
    try:
        with open(itemFile, 'r') as fp:
            itemData = json.load(fp)
    except:
        currUI.outputMessage("Error: Item Name file is not formatted properly.", -1)
        return

    if logAnalysis:
        print("Beginning analysis on items in file:", itemFile)
    
    #processes the discord file and item data
    itemInformation, itemPrices, numItems = processData(discordFile, itemData)

    if not itemInformation:
        return
    
    if logAnalysis:
        print("Analysis complete.")

    if currUI:
        counter = 0
        percentToAdd = 5
        progressAdded = 0
        try:
            lenMessagesForProgress = percentToAdd/len(itemInformation.keys())
        except:
            lenMessagesForProgress = 0

    #combine information into one dictionary
    for item in itemInformation.keys():
        if currUI:
            counter += lenMessagesForProgress
            if counter>=1:
                counter = 0
                progressAdded = progressAdded + 1
                currUI.progress = currUI.progress + 1
                time.sleep(0.01)
        
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

    while progressAdded < percentToAdd and currUI.progress < 100:
        currUI.progress = currUI.progress + 1
        progressAdded = progressAdded + 1
        time.sleep(0.01)

    #sort items
    sortedItemKeys = sorted(itemInformation, key=lambda x: x)
    itemInformation = {key: itemInformation[key] for key in sortedItemKeys}

    return itemInformation


def writeToFile(itemInformation, fileName, overwrite=0):
    """
    Outputs information into a CSV file
    """
    if not overwrite:
        if os.path.isfile(fileName):
            os.remove(fileName)

    columns = ['Name', 'Average Buy', 'Average Sell', 'Found Buy Prices', 'Found Sell Prices']

    with open(fileName, 'w', newline='') as csvfile:
        #create writer
        writer = csv.writer(csvfile)

        #create titles
        writer.writerow(columns)
        #writer.writerow(['Name', 'Buy', 'Sell'])

        #populate CSV file
        for name, values in itemInformation.items():
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

    #performs analysis and recieves a dict of found information
    itemInformation = startAnalysis(itemFile, discordFile)

    print("Writing results to", args.newfile)
    #writes results to a CSV file
    writeToFile(itemInformation, newFile, args.overwritefile)
    print("Finished.")


if __name__ == "__main__":
    main()