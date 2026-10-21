from app.catalog import list_products


def test_list_products():
    assert list_products()[0]["name"] == "Notebook"
