from datasets import load_dataset
import os

#ds = load_dataset("koutch/staqc", "man_python")
# load ds from parquet file
ds = load_dataset("parquet", data_files={"train": "../test_parquet/0000.parquet"})

lower = 101
upper = 201

for x in range(lower, upper):
    # print(ds['train'][x]['question'])
    # writing questions to file
    with open("../questions/standard/{}.txt".format(x), "x") as file:
        file.write(ds['train'][x]['question'] + "\n")
    # print(ds['train'][x]['snippet']['text'][0].encode('utf-8').decode('unicode_escape'))  # decode unicode characters
    # writing code snippets to file
    with open("../test_files/{}.py".format(x), "x") as file:
        file.write(ds['train'][x]['snippet']['text'][0].encode('utf-8').decode('unicode_escape') + "\n")