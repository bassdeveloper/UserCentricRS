import math
from operator import itemgetter
from database import database
import loader

loader.main()
db = database.connect()


def main():
    try:
        choice = input('New User? Y/N\n').lower()
    except TypeError as e:
        print(e)
    else:
        user_id = None
        if choice == 'y':
            user_id = 0
            '''get cold start recommendation'''
        elif choice == 'n':
            '''not cold start'''
            user_id = int(input("Enter user ID\n"))

        choice = int(input('''
                        1. Rating a movie by ID.
                        2. Get recommendation.
                        '''))
        if choice == 1:
            '''rate function here'''
        elif choice == 2:
            '''get recommendation'''
            kfn(user_id, 8, 15)


def kfn(user_id, e, k):
    hated_neighbours = []
    var = open('C:\\Users\\Jasmin2332\\Downloads\\MC\\RS\\cov.txt', "w")

    max_r_userq = db.fetch("SELECT MAX(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]
    min_r_userq = db.fetch("SELECT MIN(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]
    avg_r_userq = db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(user_id))[0][0]

    offsetq = max_r_userq + min_r_userq - avg_r_userq
    rated_items_user_q = db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user_id))

    for result in db.fetch('SELECT user_id FROM users'):
        user = result[0]
        print(user)
        if user == user_id:
            continue
        max_r = db.fetch("SELECT MAX(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
        min_r = db.fetch("SELECT MIN(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]
        avg_r = db.fetch("SELECT AVG(rating) FROM ratings WHERE user_id = {0}".format(user))[0][0]

        offset = max_r + min_r - avg_r
        rated_items = db.fetch("SELECT movie_id FROM ratings WHERE user_id = {0}".format(user))

        overlap = [item[0] for item in filter(lambda item: item in rated_items, rated_items_user_q)]

        sum_x_y = 0
        sum_r_x2 = 0
        sum_r_y2 = 0
        if len(overlap) > e:
            for movie in overlap:
                score_uq = db.fetch("SELECT rating from ratings WHERE movie_id = {0} and user_id = {1}"
                                    .format(movie, user_id))[0][0]
                score_u = db.fetch("SELECT rating from ratings WHERE movie_id = {0} and user_id = {1}"
                                   .format(movie, user))[0][0]
                sum_x_y += (offsetq - score_uq) * (offset - score_u)
                sum_r_x2 += math.pow(offsetq - score_uq, 2)
                sum_r_y2 += math.pow(offset - score_u, 2)
            try:
                cov = sum_x_y / (math.sqrt(sum_r_x2) * math.sqrt(sum_r_y2))
            except ZeroDivisionError:
                cov = 0
            var.write(str(cov) + "\n")
            hated_neighbours.append((user, cov))
            hated_neighbours = sorted(hated_neighbours, key=itemgetter(1))
            hated_neighbours = hated_neighbours[:k]
    print(hated_neighbours)
    var.close()


if __name__ == '__main__':
    main()
