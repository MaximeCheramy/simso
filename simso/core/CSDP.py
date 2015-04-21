# coding=utf-8


class CSDP(object):
    def __init__(self, stack):
        self._csdp = [0]
        c = 0
        s = 0.0
        for dist, value in stack.items():
            while c < dist:
                self._csdp.append(s)
                c += 1
            s += value
        self._csdp.append(s)

    def get(self, dist):
        if dist < len(self._csdp):
            return self._csdp[dist]
        else:
            return self._csdp[-1]
