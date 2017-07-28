#!/bin/env/python

from itertools import count, izip

def find_windows(inlist) :

    out = []

    last_check = 0
    for iielem, ielem in enumerate(inlist) :
        if not iielem >= last_check : continue
        continuous_group = [ielem]
        i_check = 1
        for jjelem, jelem in enumerate(inlist) :
            if not jjelem > iielem : continue
            cont = ielem + i_check
            if jelem == cont :
                continuous_group.append(jelem)
                i_check += 1
            else :
                out.append(continuous_group)
                last_check = jjelem + 1
                break
    return out

def ranges(seq):

    start, end = seq[0], seq[0]
    count = start
    for item in seq:
        if not count == item:
            yield start, end
            start, end = item, item
            count = item
        end = item
        count += 1
    yield start, end

class EmptyWindow :
    def __init__(self, start, stop, length) :
        self.start = start
        self.stop = stop
        self.length = length

    def Print(self) :
        print "EW start: %d  stop: %d  len: %d"%(self.start, self.stop, self.length)


def main() :
    l = [1,2,3,8,9,10,11,18,19,20,30]

    missing = set(range(l[len(l)-1])[1:]) - set(l)

    #print list(missing)

    grouped_missing = list(ranges(list(missing)))
   # print grouped_missing

    windows = [#]
    for gm in grouped_missing :
        f = gm[0]
        l = gm[1]
        s = int(l - f)
        ew = EmptyWindow(f, l, s)
        windows.append(ew)
    for ew in windows :
        ew.Print()

#_
if __name__ == "__main__" :
    main()
