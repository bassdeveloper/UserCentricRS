from os.path import join


def main(data_set_path):
    with open(join(data_set_path, "movies.dat"), 'w') as outfile:
        with open(join(data_set_path, "movies_original.dat"), "r") as infile:
            cleaned_field_length = len(infile.readline().split("::")) - 1
            infile.seek(0)
            for record in infile:
                fields = record.split('::')
                outfile.write("::".join(fields[:cleaned_field_length]) + "\n")
