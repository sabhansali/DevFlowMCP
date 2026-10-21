from app.orders import total


def test_total():
    assert total([1.5, 2.5]) == 4
