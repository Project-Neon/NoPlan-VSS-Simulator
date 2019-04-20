import sys
from src.kernel import Kernel

def main():

	if len(sys.argv) > 1:
		two_teams = int(sys.argv[1])
	else:
		two_teams = 0

	kernel = Kernel(two_teams)
	kernel.loop()

if __name__ == "__main__":
    # execute only if run as a script
    main()	
