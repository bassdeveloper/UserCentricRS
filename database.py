"""Database handler for Recommendation system"""
import sqlite3
from configparser import ConfigParser
from os import listdir
from os.path import isfile, join, abspath, dirname


class database:
    """
    Database class for storing recommendation system dataset.
    """

    def __init__(self, data_set_path=None):
        self.data_dir = data_set_path
        if data_set_path is None:
            config_parser = ConfigParser()
            config_parser.read('config.cfg')
            data_set = config_parser.get('system-config', 'data_set')
            data_set_abs_path = join(abspath(dirname(__file__)), data_set)
            self.data_dir = data_set_abs_path
        self.conn = sqlite3.connect('recommendation_system.db')
        self.c = self.conn.cursor()

    @staticmethod
    def connect():
        """
        Open database by creating instance of this class.
        :return:
        """
        return database()

    def create(self):
        """
        Create database from input files.
        """
        c = self.c
        try:
            c.execute('drop table ratings')
            c.execute('drop table movies')
            c.execute('drop table users')
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
                    lat FLOAT,
                    lon FLOAT,
                    PRIMARY KEY(user_id));''')

        files = [f for f in listdir(self.data_dir) if
                 isfile(join(self.data_dir,
                             f)) and f != "README"]

        for file in files:
            filename = file.split('.dat')[0]
            with open(join(self.data_dir, file)) as infile:
                for record in infile:
                    fields = record.split('::')
                    temp_fields = [int(field) if field.isnumeric() else field for field in fields]
                    res = ','.join(str(v) if str(v).isnumeric() else self.from_str(v) for v in temp_fields)
                    c.execute('INSERT INTO {0} VALUES ({1})'.format(filename, res))

        self.conn.commit()

    def update(self, file_name):
        """
        Update database with new/updated records in input files.
        :param file_name:
        """
        filename = file_name.split('.dat')[0]
        with open(join(self.data_dir, file_name)) as infile:
            for record in infile:
                fields = record.split('::')
                temp_fields = [int(field) if field.isnumeric() else field for field in fields]
                res = ','.join(str(v) if str(v).isnumeric() else self.from_str(v) for v in temp_fields)
                self.c.execute('INSERT OR REPLACE INTO {0} VALUES ({1})'.format(filename, res))
                infile.close()

        self.conn.commit()

    def fetch(self, query):
        """
        Execute a query on database.
        :param query: Query in string format.
        :returns: Output of query.
        :rtype: List[Tuple[Any,]]
        """
        try:
            return [[element if type(element) is not str else element.strip("\n") for element in row] for row in
                    self.c.execute(query).fetchall()]
        except sqlite3.Error:
            print(query)
            return [[]]

    def close(self):
        """
        Close database.
        """
        self.c.close()

    def export(self):
        """
        Export database to the files it was created from.
        """

        files = [f for f in listdir(self.data_dir) if
                 isfile(join(self.data_dir,
                             f)) and f != "README"]
        for file in files:
            with open(join(self.data_dir, file), "w") as outfile:
                results = self.fetch("SELECT * FROM {0}".format(file.split(".dat")[0]))
                outfile.write("\n".join(
                    ["::".join([self.to_str(element) for element in result]) for result in
                     results]))

    @staticmethod
    def to_str(element):
        """
        Convert parameter to proper type. i.e. Everything except none to its string using str().
        None is converted to "<system-reserve-None>"
        :param element: Element to be converted.
        :returns: String representation as used by the recommendation system.
        :rtype: str
        """
        if type(element) is str:
            return element
        elif element is None:
            return "<system-reserve-None>"
        else:
            return str(element)

    @staticmethod
    def from_str(element):
        """
        Convert parameter to proper representation. i.e. Everything except none to its string using str().
        None is converted to "<system-reserve-None>"
        :param element: Element to be converted.
        :returns: String representation as used by the recommendation system.
        :rtype: str
        """

        if element == "<system-reserve-None>":
            return "NULL"
        if type(element) is str:
            return "\"{0}\"".format(element)
        if type(element) is not str:
            return str(element)
