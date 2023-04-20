import json
import argparse
import os
import sys


def checkCLA(args):
    """
    This function checks for valid command line arguments and if the 
    new file name exists.
    """
    if not args.datafile.endswith(".txt"):
        sys.exit("Make sure the file name contains its extension '.txt'.")
    
    if args.overwriteFile:
        #check if file exists in directory
        if args.newfile in os.listdir(os.getcwd()):
            sys.exit("New file name must not exist to avoid overwriting data.\nDelete \""+
                        fileName+"\", enter a different name, " +
                        "\nor use the -o argument to ignore this check.")

def appendItemNames(mainItemFile, rawItemDataFile, appUI=None):
    data = getItemNames(rawItemDataFile)
    
    try:
        with open(mainItemFile, "r") as f:
            oldNames = json.load(f)
    except Exception():
        if appUI:
            appUI.outputMessage("Error reading in raw item names.")
        else:
            exit("Error reading in raw item names.")
    
    data.update(oldNames)
    print(data)


def getItemNames(dataFile):
    """
    Read in txt file and format information into a dict.
    """
    try:
        itemDataFile = open(dataFile, "r", encoding="utf8")
    except FileNotFoundError:
        exit("Error opening raw data file. Please check that it exists within the \RawItems directory.")
    
    rawItemData = itemDataFile.read()
    rawItemData = rawItemData.split('\n')
    
    #remove any whitespace, tabs, and newlines
    for x,word in enumerate(rawItemData):
        rawItemData[x] = rawItemData[x].lower()
        rawItemData[x] = rawItemData[x].lstrip(' ')
        rawItemData[x] = rawItemData[x].rstrip(' ')
        if '\t' in word:
            rawItemData[x] = rawItemData[x].replace('\t', '')
        if '\n' in word:
            rawItemData[x] = rawItemData[x].replace('\n', '')

    #remove any short item less than 2 characters long
    for word in rawItemData[:]:
        if len(word) < 2:
            rawItemData.remove(word)
            continue

    itemData = {}
    prevVName = ""
    for x,word in enumerate(rawItemData):
        #add in item name if it's not subname
        if rawItemData[x][0] != '|':
            itemData[rawItemData[x]] = [rawItemData[x]]
            prevVName = rawItemData[x]
        else:
            #if it is subname, append it to previous valid name list
            rawItemData[x] = rawItemData[x][1:]
            itemData[prevVName].append(rawItemData[x])
    return itemData


def main():
    #CLA argument definitions
    parser = argparse.ArgumentParser("Format raw pet names from .txt to .json.\n")
    parser.add_argument('--datafile', '-d', type=str, required=True, help="File name in \RawItems containing raw pet names.")
    parser.add_argument('--newfile', '-n', type=str, required=True, help="Name of file to put information into. Will be saved in directory \ItemNames.")
    parser.add_argument('--overwriteFile', '-o', action='store_false', help="Give warning about overwriting a pre-existing file.")
    args = parser.parse_args()

    args.newfile = os.getcwd() + '\ItemNames\\' + args.newfile

    checkCLA(args)

    #get dict of item main names and their subnames
    itemData = getItemNames(args.datafile)

    #write dict to json file
    with open(args.newfile, 'w') as fp:
        json.dump(itemData, fp, indent='\t', sort_keys=True, separators=(',', ': '))


if __name__ == "__main__":
    main()