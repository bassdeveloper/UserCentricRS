import sys

import numpy

import cleaner
from QuadTree import QuadTree
from database import database
from recommender import RecommendationSystem

# TODO: Put all paths in a config.cfg for easy use.
# TODO: Replace paths with relative paths.

cleaner.main(sys.argv[1])
db = database(sys.argv[1])
db.create()
db.close()


def get_coordinates(zip_c):
    try:
        indices = numpy.where(zip_code_coord_list['zip_code'] == zip_c)
        index = indices[0][0]
    except:
        return None
    return zip_code_coord_list['lat'][index], zip_code_coord_list['lon'][index]


zip_code_data = "C:\\Users\\Jasmin2332\\Downloads\\MC\\RS\\dataset\\non_database\\zip_lat_lon.dat"
zip_code_coord_list = numpy.genfromtxt(zip_code_data, delimiter=',',
                                       dtype=([('zip_code', str, 5), ('lat', float), ('lon', float)]))

r_sys = RecommendationSystem()
user_zip_table = r_sys.db.fetch("SELECT user_id, zipcode FROM users")
qt = QuadTree(r_sys)

user_coord_table = []
for user_id, zip_code in user_zip_table:
    coord = get_coordinates(str(zip_code).rstrip("\n"))
    if coord is not None:
        user_coord_table.append([user_id, coord])
qt.to_quad_tree(user_coord_table, 4)
qt.export_tree("C:\\Users\\Jasmin2332\\Downloads\\MC\\RS\\dataset\\non_database\\lars.dat")
