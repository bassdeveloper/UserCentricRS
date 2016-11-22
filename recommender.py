"""Recommendation System"""
from configparser import ConfigParser
from math import sqrt
from operator import itemgetter
from os.path import abspath, dirname, join
from typing import Tuple, List

from haversine import haversine

from database import database


class RecommendationSystem:
    """ Movie Recommendation System """

    def __init__(self):
        config_parser = ConfigParser()
        config_parser.read('config.cfg')
        data_set = config_parser.get('system-config', 'data_set')
        data_set_abs_path = join(abspath(dirname(__file__)), data_set)
        lars_path = config_parser.get('system-config', 'lars')
        self.db = database.connect()
        from QuadTree import QuadTree
        self.quad_tree = QuadTree.import_tree(join(data_set_abs_path, abspath(lars_path)))

    def main(self):
        """
            Driver function
        """
        while True:
            try:
                choice = input('New User? Y/N\n').lower()
            except TypeError as e:
                print(e)
            else:
                if choice == 'y':
                    choice = int(input('''
                                    1. Get LARS recommendation.
                                    '''))
                    if choice == 1:

                        users = self.quad_tree.nearest_cell(
                            tuple(map(float, input("Input your location\n").split(','))),
                            input("LARS depth level"))
                        for recommended in self.lars_recommendation(users, 10):
                            print(recommended[0])

                elif choice == 'n':
                    user_id = int(input("Enter user ID\n"))
                    choice = int(input('''
                                    1. Get KFN recommendation.
                                    2. Get LARS recommendation.
                                    '''))
                    if choice == 1:
                        for recommended in self.kfn(user_id, 5, 100, 10):
                            print(recommended[0], "Predicted Score", recommended[1])
                    if choice == 2:
                        users = self.quad_tree.nearest_cell(
                            tuple(map(float, input("Input your location\n").split(','))),
                            input("LARS depth level"))
                        for recommended in self.lars_recommendation(users, 10):
                            print(recommended[0])

    def lars_recommendation(self, users: List[Tuple[int, float]], n: int):
        """
        Gets recommendation for LARS
        :param users: Neighbourhood users.
        :param n: Number of recommendations required. Does not ensure that at least n recommendations will be made.
        :returns: List of recommended movie title and predicted score tuple.
        :rtype: List[Tuple[str, float]]
        """
        catalogue = []
        for user_id, user_loc in users:
            avg_r = self.db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]
            for movie_id, rating in self.db.fetch(
                    "SELECT movie_id, rating from ratings where user_id = {0} ORDER BY rating DESC LIMIT 10".format(
                        user_id)):
                catalogue.append((movie_id, rating - avg_r))

        catalogue.sort(key=itemgetter(1), reverse=True)

        recommended_movies = []
        for movie_id, rating in catalogue:
            if movie_id not in recommended_movies:
                recommended_movies.append((movie_id, rating))
                if len(recommended_movies) == n:
                    break

        recommended = [
            (self.db.fetch("SELECT title from movies WHERE movie_id = {0}".format(movie_id))[0][0], movie_score) for
            movie_id, movie_score in recommended_movies]
        recommended.sort(key=itemgetter(1), reverse=True)
        return recommended

    def kfn(self, user_id: int, e: int, k: int, n: int):
        """
        Decides movies to be recommended. Uses a sub function to find neighbours.
        :param user_id: User id of the user requesting recommendations.
        :param e: Number of commonly rated items a user must have to qualify as a neighbour.
        :param k: Number of closest neighbour actually used to formulate the recommendations.
        :param n: Number of recommendations required. Does not ensure that at least n recommendations will be made.
        :returns: List of recommended movie title and predicted score tuple.
        :rtype: List[Tuple[str, float]]
        """
        hated_neighbours = self.__kfn__(user_id, self.db.fetch('SELECT user_id FROM users'), e, k)
        # Recommend 10 movies
        catalogue = []
        watched_movies = [movie_id[0] for movie_id in
                          self.db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user_id))]

        for neighbour, cov in hated_neighbours:
            max_r = self.db.fetch("SELECT MAX(rating) FROM ratings WHERE user_id = {0}".format(neighbour))[0][0]
            min_r = self.db.fetch("SELECT MIN(rating) FROM ratings WHERE user_id = {0}".format(neighbour))[0][0]
            avg_r = self.db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(neighbour))[0][0]

            offset = max_r + min_r - avg_r

            for movie in self.db.fetch(
                    "SELECT movie_id, rating from ratings where user_id = {0} ORDER BY rating DESC".format(
                        neighbour)):
                catalogue.append([movie[0], movie[1], cov])

                catalogue.sort(key=lambda element: (offset - element[1]) * (element[2]), reverse=True)

        recommended_movies = []
        for movie in catalogue:
            if movie[0] not in recommended_movies and movie[0] not in watched_movies:
                recommended_movies.append((movie[0], movie[1]))
                if len(recommended_movies) == n:
                    break

        recommended = [
            (self.db.fetch("SELECT title from movies WHERE movie_id = {0}".format(movie_id))[0][0], movie_score) for
            movie_id, movie_score in recommended_movies]
        recommended.sort(key=itemgetter(1), reverse=True)

        return recommended

    def __kfn__(self, user_id: int, users: List[Tuple[int]], e: int, k: int):
        """
        Chooses the neighbours for kFN recommendations.
        :param user_id: User id of the user requesting recommendations.
        :param users: Users to choose neighbour from.
        :param e: Number of commonly rated items a user must have to qualify as a neighbour.
        :param k: Number of closest neighbour actually used to formulate the recommendations.
        :returns: User id of neighbours and covariance between querying user and neighbours.
        :rtype: List[Tuple[int, float]]
        """
        hated_neighbours = []
        rated_items_user_q = self.db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user_id))

        for result in users:
            user = result[0]

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
                    sum_x_y += score_uq * (offset - score_u)
                    sum_r_x2 += pow(score_uq, 2)
                    sum_r_y2 += pow(offset - score_u, 2)
                try:
                    cov = sum_x_y / (sqrt(sum_r_x2) * sqrt(sum_r_y2))
                except ZeroDivisionError:
                    cov = 1
                hated_neighbours.append((user, cov))
                hated_neighbours.sort(key=itemgetter(1), reverse=True)
                hated_neighbours = hated_neighbours[:k]

        return hated_neighbours

    def knn(self, user_data: Tuple[int, Tuple[float, float]], e: int, k: int, n: int,
            seed_set: List[Tuple[int, float]] = None):
        """
        Decides movies to be recommended. Uses a sub function to find neighbours.
        :param user_data: User id, user location coordinates tuple of the user requesting recommendations.
        :param e: Number of commonly rated items a user must have to qualify as a neighbour.
        :param k: Number of closest neighbour actually used to formulate the recommendations.
        :param n: Number of recommendations required. Does not ensure that at least n recommendations will be made.
        :param seed_set: Set of users to use as neighbours that is force used. This is used by QuadTree. Optional param.
        :returns: List of recommended movie title and predicted score tuple.
        :rtype: List[Tuple[str, float]]
        """

        if seed_set is None:
            users = [(user_id, (lat, lon)) for user_id, lat, lon in
                     self.db.fetch('SELECT user_id, lat, lon FROM users')]
            closest_neighbours = self.__knn__(user_data, users, e, k)
        else:
            if seed_set:
                closest_neighbours = [(user_id, co_var) for user_id, co_var in seed_set]
            else:
                return []
        catalogue = []

        watched_movies = [movie_id[0] for movie_id in
                          self.db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user_data[0]))]

        for neighbour, cov in closest_neighbours:
            avg_r = self.db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(neighbour))[0][0]
            offset = avg_r

            for movie in self.db.fetch(
                    "SELECT movie_id, rating from ratings where user_id = {0} ORDER BY rating DESC".format(
                        neighbour)):
                catalogue.append([movie[0], movie[1], cov])

                # element is of form [movie_id, score, covariance_with_query_user]
                catalogue.sort(key=lambda element: (element[1] - offset) * (element[2]), reverse=True)

        recommended_movies = []
        for movie_id, movie_score in catalogue:
            if movie_id not in recommended_movies and movie_id not in watched_movies:
                recommended_movies.append((movie_id, movie_score))
                if len(recommended_movies) == n:
                    break

        recommended = [
            (self.db.fetch("SELECT title from movies WHERE movie_id = {0}".format(movie_id))[0][0], movie_score) for
            movie_id, movie_score in recommended_movies]

        recommended.sort(key=itemgetter(1), reverse=True)
        return recommended

    def __knn__(self, q_user_data: Tuple[int, Tuple[float, float]], users: List[Tuple[int, Tuple[float, float]]],
                e: int, k: int):
        """
        Chooses the neighbours for kFN recommendations.
        :param q_user_data: User id, user location coordinates tuple of the user requesting recommendations.
        :param users: Users to choose neighbour from.
        :param e: Number of commonly rated items a user must have to qualify as a neighbour.
        :param k: Number of closest neighbour actually used to formulate the recommendations.
        :returns: User id of neighbours and covariance between querying user and neighbours.
        :rtype: List[Tuple[int, float]]
        """

        if len(users) == 1:
            return []
        """ Used by Quad Tree to find closest k users """
        closest_neighbours = []  # type: List[Tuple[int, float, float]]
        q_user_id = q_user_data[0]
        q_user_loc = q_user_data[1]
        rated_items_user_q = self.db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(q_user_id))
        avg_r_q = self.db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(q_user_id))[0][0]

        max_dist = 0
        total_dist = 0
        count = 0
        for user_data in users:
            # users is of form List[Tuple[user_id, dist = Tuple[latitude, longitude]]]
            user_id = user_data[0]
            user_loc = user_data[1]
            if user_id == q_user_id:
                continue
            count += 1
            avg_r = self.db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]
            rated_items = self.db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user_id))

            overlap = [item[0] for item in filter(lambda item: item in rated_items, rated_items_user_q)]

            sum_x_y = 0
            sum_r_x2 = 0
            sum_r_y2 = 0
            if len(overlap) > e:
                for movie in overlap:
                    score_uq = self.db.fetch("SELECT rating from ratings WHERE movie_id = {0} and user_id = {1}"
                                             .format(movie, q_user_id))[0][0]
                    score_u = self.db.fetch("SELECT rating from ratings WHERE movie_id = {0} and user_id = {1}"
                                            .format(movie, user_id))[0][0]
                    sum_x_y += (score_uq - avg_r_q) * (score_u - avg_r)
                    sum_r_x2 += pow(score_uq - avg_r_q, 2)
                    sum_r_y2 += pow(score_u - avg_r, 2)
                    dist_btw_users = haversine(q_user_loc, user_loc)
                    total_dist += dist_btw_users
                    if dist_btw_users > max_dist:
                        max_dist = dist_btw_users

                    try:
                        cov = sum_x_y / (sqrt(sum_r_x2) * sqrt(sum_r_y2))
                    except ZeroDivisionError:
                        cov = 1
                    finally:
                        closest_neighbours.append((user_id, cov, dist_btw_users))
        if max_dist > 0:
            closest_neighbours = [neighbour for neighbour in map(
                lambda neighbour: (neighbour[0], neighbour[1] * (max_dist - neighbour[2]) / max_dist),
                closest_neighbours)]  # type: List[Tuple[int, float]]
        else:
            closest_neighbours = [neighbour for neighbour in map(
                lambda neighbour: (neighbour[0], neighbour[1]),
                closest_neighbours)]  # type: List[Tuple[int, float]]

        closest_neighbours.sort(key=itemgetter(1), reverse=True)
        return closest_neighbours[:k]
