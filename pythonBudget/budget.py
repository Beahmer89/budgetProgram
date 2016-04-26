#/usr/bin/python

import pprint
import xml.etree.ElementTree as ET
import xml.dom.minidom
import argparse
import sys
import subprocess 
import os.path 

#GLOBAL VARIABLES:
#---------------------------------------------------
#build namespace dictionary with custom prefixes as keys
#values would be the appropriate uri
ns = {
	'trn':'http://www.gnucash.org/XML/trn',
	'split':'http://www.gnucash.org/XML/split',
	'ts':'http://www.gnucash.org/XML/ts',
	'act':'http://www.gnucash.org/XML/act'
     }


#---------------------------------------------------

# function find_nested_values
# Objective: Dives further into each individual transaction element using recursion to get needed info 
# Accepts following parameters:
#	trans: a transaction element
#	key: a key to the namespace dictionary to be used to find information about transaction 
#	info: value of key from info dictionary. Used to get multiple values in transaction	
#	found: list of values that recursion has found 
#	accounts: dict of accounts with id as key and name of account is value 

def find_nested_values(trans, key, info, found, accounts):
	for el in trans.findall('trn:'+ key, ns):
		#if the value of info is a dictionary, we know it is nested deeper
		if type(info[0]) is dict:
			for key,value in info[0].items():
				found = find_nested_values(el, key, value, found, accounts)
				#pprint.pprint(found)
		else:
			#else go through the list and find all the values that are needed
			for item in info:
				val = el.find(item,ns)
				test = val.text

				if test[0] != '-':
					#there are 2 splits, one where the value is negative and one that is positive
					# the negative takes the money out of a particular category in savings 
					# the positive marks how much was spent in particular category 
					var = val.text.split()
					if 'account' in item:
						var[0] = accounts[var[0]]
					elif '/' in var[0]:
						var[0] = '=' + var[0]
					found.append(var[0])
				else:
					break
	return found
			
# function get_info 
# Objective: Dives into each individual transaction element to get needed info 
# Accepts following parameters:
#	root: root of the xml file
#	file_name: file in which to right to 

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
					#print "CALLING NESTED FN"
					found = find_nested_values(trans, key, info[key], found, accounts)
					#print "OUT OF FN"
					#pprint.pprint(found)
				else:		
					#trans_list[trans_id.text].append(val.text)
					#file_name.write(val.text)
					found.insert(0,val.text)
			if len(found) > 0:
				lst = ",".join(found)
				trans_list.append(lst)
				#file_name.write(lst)	
				#file_name.write("\n")
			#print "_____________________________________"
			#sys.exit()
	#pprint.pprint(trans_list)
	return trans_list;

# function get_accounts
# Objective: Creates list of accounts 
# Accepts following parameters:
#	root: root of the xml file

def get_accounts(root):

	accounts = {}
	for accnt in root.iter('{http://www.gnucash.org/XML/gnc}account'):
		accnt_id = accnt.find('act:id',ns)
		name = accnt.find('act:name',ns)
		accounts[accnt_id.text] = name.text
	return accounts

# function print_trans 
# Objective: print values out to .csv file to be read by excel/libreoffice calc
# Accepts following parameters:
#	args: args user passed in 
#	transactions: list of comma sperated vales found from data structure 

def print_trans(args, transactions):
	
	output = 'output.csv'

	#TODO need to check if it works in Windows
	if os.path.exists('./' + output):
		subprocess.call("rm " + output, shell=True)

	file_name = open(output, 'a')
	
	#TODO insert Month Headers and spacing in csv file
    #possible rework logic

	for trans in transactions:
		pvar = 0
		if args.month and args.year:
			tmp = trans.split(",") 
			t = tmp[3].split("-") 

			if str(args.month) in t[1] and str(args.year) in t[0]:
				pvar = 1
		elif args.year:
			tmp = trans.split(",") 
			if str(args.year) in tmp[3]:
				pvar = 1
		elif args.month:
			tmp = trans.split(",") 
			t = tmp[3].split("-") 
			if str(args.month) in t[1]:
				pvar = 1

		if args.account:
			if args.account in trans and pvar:
				print trans
				file_name.write(trans)	
				file_name.write("\n")
		else:
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
	
	
	#TODO: Need to get latest file so its not hardcoded 
	tree = ET.parse('../xml/20160425_193934_gnucash_export.gnca')
	root = tree.getroot()
	
	accounts = get_accounts(root)
	transactions = get_info(root, accounts)
	print_trans(args, transactions)



main()
