import sys
import cleaner
from database import database

cleaner.main(sys.argv[1])
db = database(sys.argv[1])
db.create()
db.close()
