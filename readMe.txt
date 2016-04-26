These are both Programs that do the essentially the same thing. I wrote it in Perl and then rewrote it in Python to practice with the language.
NOTE: These are currently meant to be run in a linux environment. There are bash commands present in the scripts.

It is meant to help those who use the GNUCash get a finer look into what their spending habits are each month per category.
There is a feature in the program but it only goes back 3 months and does not do month by month.
Prints everything to a csv file that can be read in libreoffice or Excel

Python Script:

-- use python budget.py --help to see help menu
-- by default prints out everything for the current year
-- cannot use account parameter by itself. It will not output anything to csv
-- can use account parameter with any other parameter
-- use numbers for to represent month


Perl Script

-- Unfortunately does not have help menu (TODO)
-- By default will output everything for current year back to 2015 (this is when i started budgeting)
-- Can view a list of accounts by providing account parameter by itself then you can select an account
-- use other parameters as needed
