import sys

inputfile = open(sys.argv[1], 'r')

for line in inputfile:
	cells = line.split()
	#print cells[int(sys.argv[2])]
	i = len(cells)
	print i

inputfile.close()
