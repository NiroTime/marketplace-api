import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASEURL = "http://127.0.0.1:8000/"

ROOT_ID = "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"

FIRST_DATE_IN_IMPORT_BATCHES = "2022-02-01T12:00:00.000Z"

LAST_DATE_IN_IMPORT_BATCHES = "2022-02-03T16:00:00Z"

IMPORT_BATCHES = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ],
        "updateDate": FIRST_DATE_IN_IMPORT_BATCHES
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Смартфоны",
                "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "jPhone 13",
                "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 79999
            },
            {
                "type": "OFFER",
                "name": "Xomiа Readme 10",
                "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 59999
            }
        ],
        "updateDate": "2022-02-02T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Samson 70\" LED UHD Smart",
                "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 32999
            },
            {
                "type": "OFFER",
                "name": "Phyllis 50\" LED UHD Smarter",
                "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 49999
            },
            {
                "type": "CATEGORY",
                "name": "Телевизоры",
                "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            }
        ],
        "updateDate": "2022-02-03T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar 65\" LED UHD LOL Very Smart",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 69999
            }
        ],
        "updateDate": "2022-02-03T15:00:00.000Z"
    }
]

EXPECTED_TREE = {
    "name": "Товары",
    "type": "CATEGORY",
    "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
    "parentId": None,
    "date": "2022-02-03T16:00:00.000Z",
    "price": 55999,
    "children": [
        {
            "name": "Смартфоны",
            "type": "CATEGORY",
            "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "date": "2022-02-03T16:00:00.000Z",
            "price": 59999,
            "children": [
                {
                    "name": "jPhone 13",
                    "type": "OFFER",
                    "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "date": "2022-02-02T12:00:00.000Z",
                    "price": 79999,
                    "children": None
                },
                {
                    "name": "Xomiа Readme 10",
                    "type": "OFFER",
                    "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "date": "2022-02-02T12:00:00.000Z",
                    "price": 59999,
                    "children": None
                },
                {
                    "name": "jPhone 10",
                    "type": "OFFER",
                    "id": "73bc3b36-02d1-4245-ab35-3996c9ee1c65",
                    "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                    "date": "2022-02-03T16:00:00.000Z",
                    "price": 39999,
                    "children": None
                }
            ]
        },
        {
            "name": "Телевизоры",
            "type": "CATEGORY",
            "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "date": "2022-02-03T16:00:00.000Z",
            "price": 50999,
            "children": [
                {
                    "name": "Samson 70\" LED UHD Smart",
                    "type": "OFFER",
                    "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "date": "2022-02-03T12:00:00.000Z",
                    "price": 32999,
                    "children": None
                },
                {
                    "name": "Phyllis 50\" LED UHD Smarter",
                    "type": "OFFER",
                    "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "date": "2022-02-03T12:00:00.000Z",
                    "price": 49999,
                    "children": None
                },
                {
                    "name": "Goldstar 65\" LED UHD LOL Very Smart",
                    "type": "OFFER",
                    "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                    "date": "2022-02-03T16:00:00.000Z",
                    "price": 69999,
                    "children": None
                }
            ]
        },
        {
            "name": "Samsung 123",
            "type": "OFFER",
            "id": "73bc3b36-02d1-4245-ab35-3148c9ee1c65",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "date": "2022-02-03T16:00:00.000Z",
            "price": 29999,
            "children": None
        },
        {
            "name": "Samsung",
            "type": "CATEGORY",
            "id": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
            "date": "2022-02-03T16:00:00.000Z",
            "price": 65665,
            "children": [
                {
                    "name": "Телевизор 1",
                    "type": "OFFER",
                    "id": "59bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "date": "2022-02-03T16:00:00.000Z",
                    "price": 6999,
                    "children": None
                },
                {
                    "name": "Телевизор 3",
                    "type": "OFFER",
                    "id": "73bc3b36-02d1-4288-ab35-3106c9ee1c65",
                    "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "date": "2022-02-03T16:00:00.000Z",
                    "price": 19999,
                    "children": None
                },
                {
                    "name": "Телевизор 2",
                    "type": "OFFER",
                    "id": "73bc3b36-99d1-4245-ab35-3106c9ee1c65",
                    "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                    "date": "2022-02-03T16:00:00.000Z",
                    "price": 169999,
                    "children": None
                }
            ]
        }
    ]
}
CATEGORY_ID = "22bc3b36-02d1-4245-ab35-3106c9ee1c65"
NEW_CATEGORY_PARENT_ID = "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2"
UPDATE_PARENT_ID_FOR_CATEGORY = [
    {
        "items": [
            {
                "name": "Samsung",
                "type": "CATEGORY",
                "id": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": None
            }
        ],
        "updateDate": "2022-03-01T23:00:00.00Z"
    }
]

DELETE_OFFER_WITH_MULTIPLE_ANCESTORS = "73bc3b36-02d1-4245-ab35-3148c9ee1c65"

NEW_IMPORT_BATCH = [
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar 65\" LED UHD LOL Very Smart",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 69999
            },
            {
                "type": "OFFER",
                "name": "Телевизор 1",
                "id": "59bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "price": 6999
            },
            {
                "type": "OFFER",
                "name": "Телевизор 3",
                "id": "73bc3b36-02d1-4288-ab35-3106c9ee1c65",
                "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "price": 19999
            },
            {
                "type": "OFFER",
                "name": "Телевизор 2",
                "id": "73bc3b36-99d1-4245-ab35-3106c9ee1c65",
                "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "price": 169999
            },
            {
                "type": "OFFER",
                "name": "Samsung 123",
                "id": "73bc3b36-02d1-4245-ab35-3148c9ee1c65",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "price": 29999
            },
            {
                "type": "OFFER",
                "name": "jPhone 10",
                "id": "73bc3b36-02d1-4245-ab35-3996c9ee1c65",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 39999
            },
            {
                "type": "CATEGORY",
                "name": "Samsung",
                "id": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "price": ""
            }
        ],
        "updateDate": LAST_DATE_IN_IMPORT_BATCHES
    }
]

LAST_UPDATE_DATE = "2022-04-04T00:00:00Z"
LAST_UPDATE_DATE_PLUS_ONE_MS = "2022-04-04T00:00:00.001Z"


def request(path, method="GET", data=None, json_response=False):
    try:
        params = {
            "url": f"{API_BASEURL}{path}",
            "method": method,
            "headers": {},
        }

        if data:
            params["data"] = json.dumps(
                data, ensure_ascii=False).encode("utf-8")
            params["headers"]["Content-Length"] = len(params["data"])
            params["headers"]["Content-Type"] = "application/json"

        req = urllib.request.Request(**params)

        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode("utf-8")
            if json_response:
                res_data = json.loads(res_data)
            return res.getcode(), res_data
    except urllib.error.HTTPError as e:
        return e.getcode(), None


def deep_sort_children(node):
    if node.get("children"):
        node["children"].sort(key=lambda x: x["id"])

        for child in node["children"]:
            deep_sort_children(child)


def print_diff(expected, response):
    with open("expected.json", "w") as f:
        json.dump(expected, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    with open("response.json", "w") as f:
        json.dump(response, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    subprocess.run(["git", "--no-pager", "diff", "--no-index",
                    "expected.json", "response.json"])


def test_import():
    for batch in IMPORT_BATCHES:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    for batch in NEW_IMPORT_BATCH:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test import passed.")


def test_nodes():
    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    # print(json.dumps(response, indent=2, ensure_ascii=False))

    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(EXPECTED_TREE)
    if response != EXPECTED_TREE:
        print_diff(EXPECTED_TREE, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test nodes passed.")


def test_update_parent_id_for_item():
    for batch in UPDATE_PARENT_ID_FOR_CATEGORY:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, response = request(
        f"/nodes/{NEW_CATEGORY_PARENT_ID}", json_response=True
    )
    flag = False
    children = response.get('children')
    for item in children:
        if item.get('id') == CATEGORY_ID:
            flag = True
            break
    assert flag, (f'Updated item not in expected '
                  f'category: {NEW_CATEGORY_PARENT_ID}')
    print('Test update parent ID passed.')


def test_sales_return_correct_data():
    params = urllib.parse.urlencode({
        "date": LAST_UPDATE_DATE
    })
    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    for batch in NEW_IMPORT_BATCH:
        batch['updateDate'] = LAST_UPDATE_DATE
        status, _ = request("/imports", method="POST", data=batch)

    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    response_items_id = []
    for item in response['items']:
        response_items_id.append(item['id'])
    for item in NEW_IMPORT_BATCH[0]['items']:
        if item['type'] == 'OFFER':
            assert item['id'] in response_items_id
        else:
            assert item['id'] not in response_items_id

    for batch in NEW_IMPORT_BATCH:
        batch['updateDate'] = LAST_UPDATE_DATE_PLUS_ONE_MS
        status, _ = request("/imports", method="POST", data=batch)

    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test sales return correct data passed.")


def test_stats_show_correct_context():
    params = urllib.parse.urlencode({
        "dateStart": FIRST_DATE_IN_IMPORT_BATCHES,
        "dateEnd": LAST_DATE_IN_IMPORT_BATCHES
    })
    status, response = request(
        f"/node/{ROOT_ID}/statistic?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    expected_archive_versions = len(IMPORT_BATCHES) + len(
        NEW_IMPORT_BATCH)
    given_archive_versions = len(response['items'])
    assert expected_archive_versions == given_archive_versions, (
        f'Wrong count archive versions, expected: {expected_archive_versions}'
        f', given {given_archive_versions}'
    )

    params = urllib.parse.urlencode({
        "dateStart": FIRST_DATE_IN_IMPORT_BATCHES,
        "dateEnd": LAST_UPDATE_DATE
    })
    status, response = request(
        f"/node/{ROOT_ID}/statistic?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    new_import_batch_calls = 3
    expected_archive_versions = len(IMPORT_BATCHES) + len(
        NEW_IMPORT_BATCH) * new_import_batch_calls
    given_archive_versions = len(response['items'])
    assert expected_archive_versions == given_archive_versions, (
        f'Wrong count archive versions, expected: {expected_archive_versions}'
        f', given {given_archive_versions}'
    )

    print("Test stats show correct context passed.")


def test_parent_info_update_on_descendants_delete():
    status, response_before_delete = request(
        f"/nodes/{ROOT_ID}", json_response=True
    )

    status, _ = request(
        f"/delete/{DELETE_OFFER_WITH_MULTIPLE_ANCESTORS}", method="DELETE"
    )
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    status, response_after_delete = request(
        f"/nodes/{ROOT_ID}", json_response=True
    )
    assert response_before_delete['price'] != response_after_delete['price'], (
        f'Ancestors price doesnt change after descendant delete'
    )
    assert response_before_delete['date'] != response_after_delete['date'], (
        f'Ancestors date doesnt change after descendant delete'
    )
    print('Test parent info update on descendants delete passed')


def test_delete():
    status, _ = request(f"/delete/{ROOT_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test delete passed.")


def test_all():
    test_import()
    test_nodes()
    test_update_parent_id_for_item()
    test_sales_return_correct_data()
    test_stats_show_correct_context()
    test_parent_info_update_on_descendants_delete()
    test_delete()


def main():
    global API_BASEURL
    test_name = None

    for arg in sys.argv[1:]:
        if re.match(r"^https?://", arg):
            API_BASEURL = arg
        elif test_name is None:
            test_name = arg

    if API_BASEURL.endswith('/'):
        API_BASEURL = API_BASEURL[:-1]

    if test_name is None:
        test_all()
    else:
        test_func = globals().get(f"test_{test_name}")
        if not test_func:
            print(f"Unknown test: {test_name}")
            sys.exit(1)
        test_func()


if __name__ == "__main__":
    main()
