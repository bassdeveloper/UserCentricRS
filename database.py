import sqlite3
from os import listdir
from os.path import isfile, join


class database:
    def __init__(self, data_set_path=None):
        self.data_dir = data_set_path
        self.conn = sqlite3.connect('recommendation_system.db')
        self.c = self.conn.cursor()

    @staticmethod
    def connect():
        return database()

    def create(self):
        c = self.c
        try:
            c.execute('drop table ratings')
            c.execute('drop table movies')
            c.execute('drop table users')
            c.execute('drop table user_min_max_ratings')
        except Exception as e:
            print(e)

        c.execute('''CREATE TABLE ratings
                    (user_id INT NOT NULL,
                    movie_id INT NOT NULL,
                    rating INT NOT NULL,
                    timestamp INT NOT NULL,
                    PRIMARY KEY(user_id, movie_id));''')

        c.execute('''CREATE TABLE movies
                    (movie_id INT NOT NULL,
                    title TEXT NOT NULL,
                    PRIMARY KEY(movie_id));''')

        c.execute('''CREATE TABLE users
                    (user_id INT NOT NULL,
                    gender CHAR(1) NOT NULL,
                    age INT NOT NULL,
                    occupation INT NOT NULL,
                    zipcode INT NOT NULL,
                    PRIMARY KEY(user_id));''')

        c.execute('''CREATE TABLE user_min_max_ratings
                    (user_id INT NOT NULL,
                    min_r INT NOT NULL,
                    max_r INT NOT NULL,
                    PRIMARY KEY (user_id));''')

        files = [f for f in listdir(self.data_dir) if
                 isfile(join(self.data_dir, f)) and f != "README" and f != "movies_original.dat"]

        for file in files:
            filename = file.split('.dat')[0]
            with open(join(self.data_dir, file)) as infile:
                for record in infile:
                    fields = record.split('::')
                    temp_fields = [int(field) if field.isnumeric() else field for field in fields]
                    res = ','.join(str(v) if str(v).isnumeric() else "\"{0}\"".format(v) for v in temp_fields)
                    c.execute('INSERT INTO {0} VALUES ({1})'.format(filename, res))

        for result in self.fetch('SELECT user_id FROM users'):
            user = result[0]
            max_r = self.fetch("SELECT MAX(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
            min_r = self.fetch("SELECT MIN(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
            c.execute('INSERT INTO user_min_max_ratings VALUES ({0})'.format(
                ','.join(str(v) if str(v).isnumeric() else "\"{0}\"".format(v) for v in [user, min_r, max_r])))

        self.conn.commit()

    def update(self, file_name):
        filename = file_name.split('.dat')[0]
        with open(join(self.data_dir, file_name)) as infile:
            for record in infile:
                fields = record.split('::')
                temp_fields = [int(field) if field.isnumeric() else field for field in fields]
                res = ','.join(str(v) if str(v).isnumeric() else "\"{0}\"".format(v) for v in temp_fields)
                self.c.execute('INSERT OR REPLACE INTO {0} VALUES ({1})'.format(filename, res))
                infile.close()
        for result in self.fetch('SELECT user_id FROM users'):
            user = result[0]
            max_r = self.fetch("SELECT MAX(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
            min_r = self.fetch("SELECT MIN(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
            self.c.execute('INSERT INTO user_min_max_ratings VALUES ({0})'.format(
                ','.join(str(v) if str(v).isnumeric() else "\"{0}\"".format(v) for v in [user, min_r, max_r])))

        self.conn.commit()

    def fetch(self, query):
        return [[element for element in row] for row in self.c.execute(query).fetchall()]

    def close(self):
        self.c.close()
