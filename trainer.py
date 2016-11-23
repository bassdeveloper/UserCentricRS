"""Trains the recommendation system"""
from configparser import ConfigParser
from os.path import abspath, join, dirname

import numpy

from QuadTree import QuadTree
from database import database
from recommender import RecommendationSystem

configParser = ConfigParser()
configParser.read('config.cfg')
data_set = configParser.get('system-config', 'data_set')

movies_original_data_set = configParser.get('system-config', 'movies_original_data_set')
zip_to_coord_data_set = configParser.get('system-config', 'zip_lat_lon_data_set')
data_set_abs_path = join(abspath(dirname(__file__)), data_set)


with open(join(data_set_abs_path, "movies.dat"), 'w') as outfile:
    with open(join(data_set_abs_path, abspath(movies_original_data_set)), "r") as infile:
        cleaned_field_length = len(infile.readline().split("::")) - 1
        infile.seek(0)
        for record in infile:
            fields = record.split('::')
            outfile.write("::".join(fields[:cleaned_field_length]) + "\n")

zip_to_coord = numpy.genfromtxt(join(abspath(dirname(__file__)), zip_to_coord_data_set),
                                delimiter=',', dtype=([('zipcode', int), ('lat', float), ('lon', float)]))


def coordinates(index):
    """
    Returns lat, lon for a zipcode.
    :param index: Where is the record for the zipcode located.
    :returns: Latitude and longitude at the zipcode's index.
    :rtype Tuple[float, float]
    """
    try:
        index = index[0][0]
        index = int(index)
        return zip_to_coord[index][1], zip_to_coord[index][2]
    except IndexError:
        return None, None


original_r = []

with open(join(data_set_abs_path, "users.dat"), "r") as user_file:
    for line in user_file:
        ele = line.split("::")
        cleaned_record = ele[:4]
        try:
            c = coordinates(numpy.where(zip_to_coord['zipcode'] == int(ele[4])))
        except ValueError as e:
            try:
                c = coordinates(numpy.where(zip_to_coord['zipcode'] == int(ele[4].split("-")[0])))
            except ValueError as e:
                c = None, None
        lat, lon = c
        if lat is None or lon is None:
            cleaned_record.extend(["<system-reserve-None>", "<system-reserve-None>"])
        else:
            cleaned_record.extend([str(lat), str(lon)])
        original_r.append(cleaned_record)

with open(join(data_set_abs_path, "users.dat"), "w") as user_file:
    for ele in original_r:
        user_file.write("::".join(ele) + "\n")

db = database(data_set_abs_path)
db.create()
db.close()
db = database.connect()
r_sys = RecommendationSystem()

user_zip_list = [(user_id, (lat, lon)) for user_id, lat, lon in
                 r_sys.db.fetch("SELECT user_id, lat, lon FROM users WHERE lat IS NOT NULL AND lon IS NOT NULL")]

tree = QuadTree(r_sys)
tree.to_quad_tree(user_zip_list)
lars_path = configParser.get('system-config', 'lars')
tree.export_tree(join(data_set_abs_path, abspath(lars_path)))
