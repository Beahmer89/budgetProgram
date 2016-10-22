#/usr/bin/python

import xml.dom.minidom
import argparse
import sys

# used to make xml readable
def make_xml_readable(file_path):
    x = xml.dom.minidom.parse(file_path)
    pretty_xml = x.toprettyxml()
    f = open('pxml.xml', 'w')
    f.write(pretty_xml)
    f.close()


def main():
    
    parser = argparse.ArgumentParser(description='The purpose of this script is'
                                     'to make xml files more readable') 
    parser.add_argument('-f','--file_name', type=str, help='(Str) Path to XML file'
                        ' Ex -i ../blah/example.gnca', required=True)
    args = parser.parse_args()

    make_xml_readable(args.file_name)

main()
