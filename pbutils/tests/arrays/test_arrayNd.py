from pbutils.arrays import arrayNd


def test_array3():
    X, Y, Z = 2, 2, 2
    d3 = arrayNd(X, Y, Z)
    for x in range(X):
        for y in range(Y):
            for z in range(Z):
                assert d3[x][y][z] is None


def test_array4():
    W, X, Y, Z = 1, 2, 3, 4
    d3 = arrayNd(W, X, Y, Z)
    for w in range(W):
        for x in range(X):
            for y in range(Y):
                for z in range(Z):
                    assert d3[w][x][y][z] is None
