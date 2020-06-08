from code.helpers import *
def test_order_vertices():
    try:
        from vertex import Vertex
    except (SystemError, ImportError):
        from code.vertex import Vertex

    p = [-100, 0, 100, 0]  # power vector
    c = [0.4, 0.3, 0.3, 0.2]  # marginal price vector
    uv = []
    for i in range(len(p)):
        uv.append(Vertex(c[i], 0, p[i]))

    ov = order_vertices(uv)
    print (uv)
    print (ov)




if __name__ == "__main__":
    # test_is_hlh()  # Relies on date parser this is not available.
    test_order_vertices()