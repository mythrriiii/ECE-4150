from mrjob.job import MRJob
import re

class MRmyjob(MRJob):
  def mapper(self, _, line):

    # Read each line and only get the first 2 things
    parts = line.strip().split('\t')
    if len(parts) == 5:
      bigram = parts[0]
      times = int(parts[2])
      books = int(parts[4])
      yield bigram, (times, books)

  
  def reducer(self, key, list_of_values):

    total_times = 0
    total_books = 0

    for i in list_of_values:
      total_times += i[0]
      total_books += i[1]

    yield key, total_times/total_books  


if __name__ == '__main__':
    MRmyjob.run()
