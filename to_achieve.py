# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 20:15:21 2016

@author: a

Simple tool to merge two spreadsheets to create an "import" roster for
Achieve 3000 folks. They use it to create their rosters with our 
existing account names and passwords.
"""

import csv
import dataset

DISTRICT = 'Hilo-Waiakea Complex Area'
SCHOOL = 'Waiakea Intermediate School'

PWFILE = 'pw-8th.csv' # saved from the reference pw spreadsheet
ROSTER = 'per6.csv' # from the PDF roster report in eSIS. Name, Student number
OUTFILE= 'period6-roster.csv' # here is what you want to send to Achieve
GRADE = '8'


db = dataset.connect('sqlite:///:memory:')

table = db['students']

with open(PWFILE) as pwfile:
    reader = csv.DictReader(pwfile)
    for row in reader:
        table.insert(row)


with open(OUTFILE, 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    # write header
    writer.writerow(['District','School','Last Name','First Name','Student ID'\
    ,'Grade','KB Login Name','KB Password','Type'])

    with open(ROSTER) as rosterfile:
        reader = csv.reader(rosterfile)
        for row in reader:
            lastname, firstname = [name.strip() for name in row[0].split(',')]
            student_id = row[1]
            print(firstname,lastname)
            res = db.query('SELECT [Email Address],[Password] FROM students \
            WHERE[First Name]="' + firstname +'" AND [Last Name]="' + lastname +'"')
            for row in res:
                writer.writerow([DISTRICT,SCHOOL, lastname, firstname, 
                                 student_id, GRADE,
                                 row['Email Address'].split('@')[0], row['Password'],'Student'])
