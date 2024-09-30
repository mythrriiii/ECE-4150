import sys, os
import pymysql.cursors

print("Connecting to Databse instance")

DB_HOSTNAME = "" # <--- ADD HOSTNAME
DB_PORT = 30038
DB_USERNAME = "root"
DB_PASSWORD = "photo123"
DB_NAME = "photodbs"
DB_TABLE = "photos"

conn = pymysql.connect(
    host=DB_HOSTNAME,
    user=DB_USERNAME,
    password=DB_PASSWORD,
    db=DB_NAME,
    port=DB_PORT,
    cursorclass=pymysql.cursors.DictCursor,
)

print("Connected to Databse instance")

cursor = conn.cursor()
cursor.execute("SELECT VERSION()")
row = cursor.fetchone()
print("\nServer version:", row["VERSION()"])

print("\nCreating table for photos.")
cursor.execute(
    f"""CREATE TABLE `{DB_TABLE}` ( \
        `PhotoID` int NOT NULL AUTO_INCREMENT, \
        `Title` TEXT NOT NULL, \
        `Description` TEXT NOT NULL, \
        `Tags` TEXT NOT NULL, \
        `URL` TEXT NOT NULL, \
        `EXIF` TEXT NOT NULL, \
        `CreationTime` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, \
        PRIMARY KEY (`PhotoID`));"""
)
print("\nTable for photos created.")

cursor.close()
conn.close()
