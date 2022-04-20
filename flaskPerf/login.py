import csv

filePath = './config/users.csv'

def checkAccess(login):
    accessible = False 
    with open(filePath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["header"] == login:
                accessible = True
    return accessible