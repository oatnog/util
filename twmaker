import csv

def main():
    print("Hi guys")
    outfile = open('per8tw.csv', 'w', newline='')
    studentwriter = csv.writer(outfile, delimiter=' ',quotechar='"', quoting=csv.QUOTE_MINIMAL)

    studentwriter.writerow(["Username,","Password,","Firstname,","Lastname,","Email"])
    with open('per8.csv', newline='') as csvfile:
        studentreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in studentreader:
            username = "joebob"
            password = row[1]
            # later, fix quotes for spaces in first and last names.
            firstname = row[0].split(',')[1].replace(' ','')
            lastname = row[0].split(',')[0].replace(' ','')
            # create the real username
            username = firstname.lower().rstrip()[:4] + lastname.lower().rstrip()[:4]
            print(','.join([username, password, firstname, lastname]))
            studentwriter.writerow([','.join([username, password, firstname, lastname])])

    outfile.close()


if __name__ == '__main__':
    main()
