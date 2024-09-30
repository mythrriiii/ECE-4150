"""
use this line in Hadoop to run wordcount mapreduce program:

python challenge1.py -r hadoop hdfs:///user/mmuralikannan3/googlebooks-eng-us-all-2gram-20090715-50-subset.csv --output-dir=hdfs:///user/mmuralikannan3/challenge1output --conf-path=mrjob.conf

"""

from mrjob.job import MRJob
import re

class MRmyjob(MRJob):
  def mapper(self, _, line):

    # Read each line and only get the first 2 things
    parts = line.strip().split('\t')
    if len(parts) == 5:
      bigram = parts[0]
      year = int(parts[1])
      yield bigram, year

  
  def reducer(self, key, list_of_values):
    
    sorted_val = sorted(list_of_values)
    if (int(sorted_val[0] >= 1992)):
      yield key, sorted_val[0]

if __name__ == '__main__':
    MRmyjob.run()