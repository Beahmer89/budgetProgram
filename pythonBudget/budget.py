#/usr/bin/python

import pprint
import xml.etree.ElementTree as ET
import xml.dom.minidom
import argparse
import sys
import subprocess 
import os.path 
import glob

"""
GLOBAL VARIABLES:
---------------------------------------------------
build namespace dictionary with custom prefixes as keys
values would be the appropriate uri
"""

ns = {
        'trn':'http://www.gnucash.org/XML/trn',
        'split':'http://www.gnucash.org/XML/split',
        'ts':'http://www.gnucash.org/XML/ts',
        'act':'http://www.gnucash.org/XML/act'
    }

accounts = {}

"""
Summary: finds nested values 

Objective: Uses recursion to find the nested values of amount, date, and account. 

Accepts following parameters:
    trans: a transaction element
    key: str key to the namespace dictionary to find infor about transaction 
    info: value of key from info dictionary. Used to get multiple values in transaction	
    found: list of data that is found.
    accounts: dictionary of accounts 
Returns:
    found: list of data that is found through recursion 
"""
def find_nested_values(trans, key, info, found, accounts):

    for el in trans.findall('trn:'+ key, ns):
        #if the value of info is a dictionary, we know it is nested deeper
        if type(info[0]) is dict:
            for key,value in info[0].items():
                found = find_nested_values(el, key, value, found, accounts)
        else:
            #else go through the list and find all the values that are needed
            for item in info:
                val = el.find(item,ns)
                name = val.text

                if name in accounts or 'date' in item:
                    found.append(name)

                #there are 2 splits, one where the value is negative and one that is positive
                # the negative takes the money out of a particular category in savings 
                # the positive marks how much was spent in particular category 
                if '/' in name and name[0] != '-':
                    name = '=' + name
                    found.append(name)

    return found


"""
Summary: Main logic for getting info 

Objective: Loop through each transaction and get info specified in info dict. 
If all information is found, then it is added to the list of transactions.

Accepts following parameters:
    root: root of xml file 
    accounts: dictionary of accounts 
Returns:
    trans_list: list of transactions
"""

def get_info(root, accounts):
    trans_list = [] 

    #build dictionary of what is needed for output
    #keys are the info thats needed and values are custom prefix with specific tag where info is stored
    info = {
        'description':['trn:description'],
        'date-posted':['ts:date'],
        'splits':[{'split':['split:value', 'split:account']}]
    }

    #loop through each transaction
    for trans in root.iter('{http://www.gnucash.org/XML/gnc}transaction'):

        found = []
        #dont need to include paycheck so make sure that is not one of the descriptions
        val = trans.find(info['description'][0], ns)

        if 'Paycheck' not in val.text:
            #loop through each key in info dictionary
            for key in info.keys():
                if key != 'description':
                    found = find_nested_values(trans, key, info[key], found, accounts)
                else:		
                    found.insert(0,val.text)
            #only add trans that have desc, total, accnt, and date
            if len(found) == 4:
                lst = ",".join(found)
                trans_list.append(lst)
            # if len(found) < 4:
            #     print(val.text)
            #     pprint.pprint(found)

    return trans_list;

"""
Summary: Gets accounts from gnu cash xml

Objective: Get Expense accounts in xml file and create dictionary 
Dictionary has id as key and str(name) as value

Accepts following parameters:
    root: root of xml file 
Returns:
    accounts: dict 
"""

def get_accounts(root):

    accounts = {}
    count = 0
    for accnt in root.iter('{http://www.gnucash.org/XML/gnc}account'):
        accnt_id = accnt.find('act:id',ns)
        if accnt.find('act:type', ns).text == 'EXPENSE': #or \
           #accnt.find('act:type', ns).text == 'CREDIT': 
            name = accnt.find('act:name',ns)
            accounts[accnt_id.text] = name.text
    return accounts

"""
Summary: function narrows down results by month if provided 

Objective: Check if month passed in is valid number. 
Only returns transactions dealing with month user specified 

Accepts following parameters:
    month: month user specified 
    transactions: list of comma sperated vales found from data structure 
Returns:
    trans_list: list of comma sperated vales 
"""

def get_trans_for_month(transactions, month):
    trans_list = []
    for trans in transactions:
        if month <= 12 and month > 0:
            tmp = trans.split(",") 
            t = tmp[3].split("-") 

            if int(t[1]) == month:
                #print(trans)
                trans_list.append(trans)
        else:
            sys.exit("Invalid Month Provided")

    #print(trans_list)
    return trans_list

"""
Summary: function narrows down results by year if provided 

Objective: Check if year passed in is valid number. 
Only returns transactions dealing with year user specified 

Accepts following parameters:
    year: year user specified 
    transactions: list of comma sperated vales found from data structure 
Returns:
    trans_list: list of comma sperated vales 
"""

def get_trans_for_year(transactions, year):
    trans_list = []
    for trans in transactions:
        if year > 0:
            tmp = trans.split(",") 
            t = tmp[3].split("-") 

            if int(t[0]) == year:
                trans_list.append(trans)
        else:
            sys.exit("Invalid Year Provided")

    return trans_list

"""
Summary: function narrows down results by accounts if provided 

Objective: Check if name passed in is an actual account.
Only returns transactions dealing with account user specified 

Accepts following parameters:
    accnt: account user specified 
    transactions: list of comma sperated vales found from data structure 
Returns:
    trans_list: list of comma sperated vales 
"""

def get_trans_for_account(transactions, accnt):
    trans_list = []
    accnt_id = '' 

    for account, name in accounts.items():
        if name == accnt:
            accnt_id = account
            
    if accnt_id:
        for trans in transactions:
            tmp = trans.split(",") 
            if accnt_id == tmp[2]:
                trans_list.append(trans)
    else:
        sys.exit("Invalid Account Provided")

    return trans_list

# function print_trans 
# Objective: print values out to .csv file to be read by excel/libreoffice calc
# Accepts following parameters:
    #	args: args user passed in 
    #	transactions: list of comma sperated vales found from data structure 

"""
Summary: prints transactions 

Objective: Based on input from user to script, it will return a list 
of data that narrowed down by any variation of month, year, or account.

If nothing is supplied, all transactions are written to file.

Accepts following parameters:
    args: arguments passed in by user 
    transactions: list of comma sperated vales found from data structure 
Returns:
   Nothing 
"""
def print_trans(args, transactions):

    output = 'output.csv'

    #only works if in Unix environment
    if os.path.exists('./' + output):
        subprocess.call("rm " + output, shell=True)

    file_name = open(output, 'a')

    #TODO insert Month Headers and spacing in csv file
    #possible rework logic
    if args.month:
        transactions = get_trans_for_month(transactions, args.month)
    if args.year:
        transactions = get_trans_for_year(transactions, args.year)
    if args.account:
        transactions = get_trans_for_account(transactions, args.account)

    for trans in transactions:
        file_name.write(trans)	
        file_name.write("\n")

    file_name.close();

def main():
    parser = argparse.ArgumentParser(description='The purpose of this script is to print transactions to a csv file that can be run in OpenLibre office and Excel.' +
                                     'This script will print all transactions for each year by default')
    parser.add_argument('-y','--year', type=int, help='(Num) Limit transactions for particular year. Ex -y 2016', required=False)
    parser.add_argument('-m','--month', type=int, help='(Num) Limit transactions per month. By default will show month for each year. Add year to limit further. Ex. -m 01', required=False)
    parser.add_argument('-a','--account', type=str, help='(String) Limit transactions for particular account. Use Quotes for words with spaces', required=False)
    args = parser.parse_args()

    #gets latest xml file
    new_file = max(glob.iglob('../xml/*.gnca')) 
    tree = ET.parse(new_file)
    root = tree.getroot()

    global accounts
    accounts = get_accounts(root)
    transactions = get_info(root, accounts)
    print_trans(args, transactions)



main()
