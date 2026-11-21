"""Minimal QR Code encoder (byte mode), following ISO/IEC 18004.
Writes an SVG in the same style as docs/poster/qr.svg in the Haris repo."""
import sys

ECC_CODEWORDS_PER_BLOCK = {  # index by version (1..40)
    'L': [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    'M': [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
    'Q': [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    'H': [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
}
NUM_BLOCKS = {
    'L': [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
    'M': [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
    'Q': [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
    'H': [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81],
}
ECL_BITS = {'L': 1, 'M': 0, 'Q': 3, 'H': 2}


def raw_modules(ver):
    r = (16 * ver + 128) * ver + 64
    if ver >= 2:
        n = ver // 7 + 2
        r -= (25 * n - 10) * n - 55
        if ver >= 7:
            r -= 36
    return r


def data_codewords(ver, ecl):
    return raw_modules(ver) // 8 - ECC_CODEWORDS_PER_BLOCK[ecl][ver] * NUM_BLOCKS[ecl][ver]


def gf_mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z & 0xFF


def rs_divisor(deg):
    res = [0] * (deg - 1) + [1]
    root = 1
    for _ in range(deg):
        for j in range(deg):
            res[j] = gf_mul(res[j], root)
            if j + 1 < deg:
                res[j] ^= res[j + 1]
        root = gf_mul(root, 2)
    return res


def rs_remainder(data, div):
    res = [0] * len(div)
    for b in data:
        f = b ^ res.pop(0)
        res.append(0)
        for i, c in enumerate(div):
            res[i] ^= gf_mul(c, f)
    return res


def alignment_positions(ver):
    if ver == 1:
        return []
    n = ver // 7 + 2
    step = (ver * 8 + n * 3 + 5) // (n * 4 - 4) * 2
    pos_list = [ver * 4 + 17 - 7 - i * step for i in range(n - 1)]
    return [6] + sorted(pos_list)


class QR:
    def __init__(self, data: bytes, ecl='M'):
        self.ecl = ecl
        for ver in range(1, 41):
            cc = 16 if ver >= 10 else 8
            needed = 4 + cc + len(data) * 8
            if needed <= data_codewords(ver, ecl) * 8:
                break
        else:
            raise ValueError('too long')
        self.ver = ver
        self.size = ver * 4 + 17
        bits = []
        def put(val, n):
            for i in range(n - 1, -1, -1):
                bits.append((val >> i) & 1)
        put(0b0100, 4)
        put(len(data), cc)
        for b in data:
            put(b, 8)
        cap = data_codewords(ver, ecl) * 8
        put(0, min(4, cap - len(bits)))
        put(0, (-len(bits)) % 8)
        pad = 0xEC
        while len(bits) < cap:
            put(pad, 8)
            pad ^= 0xEC ^ 0x11
        cw = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
        self.codewords = self._add_ecc(cw)
        self._build()

    def _add_ecc(self, data):
        ver, ecl = self.ver, self.ecl
        nb = NUM_BLOCKS[ecl][ver]
        ecc_len = ECC_CODEWORDS_PER_BLOCK[ecl][ver]
        raw = raw_modules(ver) // 8
        n_short = nb - raw % nb
        short_len = raw // nb
        div = rs_divisor(ecc_len)
        blocks = []
        k = 0
        for i in range(nb):
            dl = short_len - ecc_len + (0 if i < n_short else 1)
            dat = data[k:k + dl]
            k += dl
            ecc = rs_remainder(dat, div)
            if i < n_short:
                dat = dat + [None]
            blocks.append(dat + ecc)
        out = []
        for i in range(len(blocks[0])):
            for j, b in enumerate(blocks):
                if b[i] is not None:
                    out.append(b[i])
        assert len(out) == raw
        return out

    def _build(self):
        n = self.size
        self.m = [[False] * n for _ in range(n)]
        self.fn = [[False] * n for _ in range(n)]
        def setf(x, y, v):
            self.m[y][x] = v
            self.fn[y][x] = True
        for i in range(n):
            setf(6, i, i % 2 == 0)
            setf(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n:
                        d = max(abs(dx), abs(dy))
                        setf(x, y, d not in (2, 4))
        al = alignment_positions(self.ver)
        for i, a in enumerate(al):
            for j, b in enumerate(al):
                if (i == 0 and j == 0) or (i == 0 and j == len(al) - 1) or (i == len(al) - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        setf(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)
        self._draw_format(0, setf)
        self._draw_version(setf)
        self._draw_data()
        best, best_mask = None, 0
        for mask in range(8):
            self._apply_mask(mask)
            self._draw_format(mask, setf)
            p = self._penalty()
            if best is None or p < best:
                best, best_mask = p, mask
            self._apply_mask(mask)
        self._apply_mask(best_mask)
        self._draw_format(best_mask, setf)
        self.mask = best_mask

    def _draw_format(self, mask, setf):
        n = self.size
        data = ECL_BITS[self.ecl] << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        g = lambda i: ((bits >> i) & 1) == 1
        for i in range(6):
            setf(8, i, g(i))
        setf(8, 7, g(6)); setf(8, 8, g(7)); setf(7, 8, g(8))
        for i in range(9, 15):
            setf(14 - i, 8, g(i))
        for i in range(8):
            setf(n - 1 - i, 8, g(i))
        for i in range(8, 15):
            setf(8, n - 15 + i, g(i))
        setf(8, n - 8, True)

    def _draw_version(self, setf):
        if self.ver < 7:
            return
        rem = self.ver
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = self.ver << 12 | rem
        n = self.size
        for i in range(18):
            b = ((bits >> i) & 1) == 1
            a, c = n - 11 + i % 3, i // 3
            setf(a, c, b)
            setf(c, a, b)

    def _draw_data(self):
        n = self.size
        i = 0
        total = len(self.codewords) * 8
        right = n - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(n):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = n - 1 - vert if upward else vert
                    if not self.fn[y][x] and i < total:
                        self.m[y][x] = ((self.codewords[i >> 3] >> (7 - (i & 7))) & 1) == 1
                        i += 1
            right -= 2
        assert i == total

    def _apply_mask(self, mask):
        f = [
            lambda x, y: (x + y) % 2 == 0,
            lambda x, y: y % 2 == 0,
            lambda x, y: x % 3 == 0,
            lambda x, y: (x + y) % 3 == 0,
            lambda x, y: (x // 3 + y // 2) % 2 == 0,
            lambda x, y: x * y % 2 + x * y % 3 == 0,
            lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
            lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
        ][mask]
        n = self.size
        for y in range(n):
            for x in range(n):
                if not self.fn[y][x] and f(x, y):
                    self.m[y][x] = not self.m[y][x]

    def _penalty(self):
        n, m = self.size, self.m
        p = 0
        lines = [m[y] for y in range(n)] + [[m[y][x] for y in range(n)] for x in range(n)]
        for line in lines:
            run, prev = 0, None
            for v in line:
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        p += run - 2
                    run, prev = 1, v
            if run >= 5:
                p += run - 2
            s = ''.join('1' if v else '0' for v in line)
            for pat in ('10111010000', '00001011101'):
                p += 40 * sum(1 for k in range(len(s) - 10) if s[k:k + 11] == pat)
        for y in range(n - 1):
            for x in range(n - 1):
                c = m[y][x]
                if c == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    p += 3
        dark = sum(sum(r) for r in m)
        total = n * n
        k = (abs(dark * 20 - total * 10) + total - 1) // total - 1
        p += max(k, 0) * 10
        return p

    def svg(self, color='#0A2E2A', border=4):
        n = self.size
        parts = []
        for y in range(n):
            x = 0
            while x < n:
                if self.m[y][x]:
                    s = x
                    while x < n and self.m[y][x]:
                        x += 1
                    w = x - s
                    parts.append(f'M{s} {y}h{w}v1h-{w}z')
                else:
                    x += 1
        vb = n + 2 * border
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-{border} -{border} {vb} {vb}" shape-rendering="crispEdges">'
                f'<rect x="-{border}" y="-{border}" width="{vb}" height="{vb}" fill="#ffffff"/>'
                f'<path fill="{color}" d="{"".join(parts)}"/></svg>\n')


if __name__ == '__main__':
    text, out = sys.argv[1], sys.argv[2]
    q = QR(text.encode('utf-8'), sys.argv[3] if len(sys.argv) > 3 else 'M')
    open(out, 'w').write(q.svg())
    print(f'version {q.ver}, size {q.size}, mask {q.mask}, ecl {q.ecl}')
