import os


def main():
    dir = os.path.dirname(__file__)
    config_file = os.path.join(dir, 'config.cfg')
    return {k: v for k, v in map(lambda x: x.split(" = "), open(config_file))}


if __name__ == '__main__':
    main()
