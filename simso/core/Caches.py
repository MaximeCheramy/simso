class Cache(object):
    def __init__(self, name, identifier, size, associativity, access_time):
        self.name = name
        self.identifier = identifier
        self.size = size
        self.access_time = access_time
        self.associativity = associativity
        self.penalty = 0

        self.shared_with = None

    def init(self):
        self.shared_with = []


class Cache_LRU(Cache):
    def __init__(self, name, identifier, size, associativity, penalty):
        Cache.__init__(self, name, identifier, size, associativity, penalty)
        self._groups = None

    def init(self):
        Cache.init(self)
        self._groups = []

    def update(self, task, lines):
        self._groups = [x for x in self._groups if x[0] != task]
        self._groups.append([task, lines])

        usedlines = sum([x[1] for x in self._groups])

        while usedlines > self.size:
            if self._groups[0][1] <= usedlines - self.size:
                usedlines -= self._groups.pop(0)[1]
            else:
                self._groups[0][1] -= usedlines - self.size
                usedlines = self.size

    def get_lines(self, task):
        groups = [x for x in self._groups if x[0] == task]
        return groups and groups[0][1] or 0
