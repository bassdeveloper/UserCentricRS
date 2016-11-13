import math
from operator import itemgetter

from haversine import haversine

import loader
from database import database


class RecommendationSystem:
    """ Movie Recommendation System """
    def __init__(self):
        loader.main()
        self.db = database.connect()

    def main(self):
        try:
            choice = input('New User? Y/N\n').lower()
        except TypeError as e:
            print(e)
        else:
            user_id = None
            if choice == 'y':
                user_id = 0
                ''' TODO :: Get cold start recommendation '''
            elif choice == 'n':
                user_id = int(input("Enter user ID\n"))

            choice = int(input('''
                            1. Get KFN recommendation.
                            2. Get LARS recommendation.
                            '''))
            if choice == 1:
                # TODO: Fetch appropriate movies rated of opposite neighbours and recommend.
                self.kfn(user_id, 8, 15)
            if choice == 2:
                ''' TODO :: Get LARS recommendation '''

    def kfn(self, user_id, e, k):
        """ Run a kFN on users with atleast e commonly rated items """
        return self.__kfn__(user_id, self.db.fetch('SELECT user_id FROM users'), e, k)

    def __kfn__(self, user_id, users, e, k):
        hated_neighbours = []
        max_r_userq = self.db.fetch("SELECT MAX(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]
        min_r_userq = self.db.fetch("SELECT MIN(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]
        avg_r_userq = self.db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]

        offsetq = max_r_userq + min_r_userq - avg_r_userq
        rated_items_user_q = self.db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user_id))

        for result in users:
            user = result[0]
            if user == user_id:
                continue
            max_r = self.db.fetch("SELECT MAX(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
            min_r = self.db.fetch("SELECT MIN(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
            avg_r = self.db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]

            offset = max_r + min_r - avg_r
            rated_items = self.db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user))

            overlap = [item[0] for item in filter(lambda item: item in rated_items, rated_items_user_q)]

            sum_x_y = 0
            sum_r_x2 = 0
            sum_r_y2 = 0
            if len(overlap) > e:
                for movie in overlap:
                    score_uq = self.db.fetch("SELECT rating from ratings WHERE movie_id = {0} and user_id = {1}"
                                             .format(movie, user_id))[0][0]
                    score_u = self.db.fetch("SELECT rating from ratings WHERE movie_id = {0} and user_id = {1}"
                                            .format(movie, user))[0][0]
                    sum_x_y += (offsetq - score_uq) * (offset - score_u)
                    sum_r_x2 += math.pow(offsetq - score_uq, 2)
                    sum_r_y2 += math.pow(offset - score_u, 2)
                try:
                    cov = sum_x_y / (math.sqrt(sum_r_x2) * math.sqrt(sum_r_y2))
                except ZeroDivisionError:
                    cov = 0
                hated_neighbours.append((user, cov))
                hated_neighbours.sort(key=itemgetter(1))
                hated_neighbours = hated_neighbours[:k]
        return hated_neighbours

    @staticmethod
    def __knn__(user_data, data_points, k):
        """ Used by Quad Tree to find closest k users """
        # TODO: Add weights according to user occupation
        user_coord = user_data[1]
        user_distances = []
        for user, coord in data_points:
            user_distances.append((user, haversine(user_coord, coord)))
        user_distances.sort(key=itemgetter(1))
        return user_distances[:k]
