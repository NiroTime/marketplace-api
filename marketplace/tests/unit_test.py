import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime
import uuid

from constants import *


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


def test_offer_cant_be_parent():
    for batch in EXIST_OFFER_SWAP_PARENT_TO_OFFER:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 400, f"Expected HTTP status code 400, got {status}"
    print('Test offer cant be parent passed.')


def test_cant_swap_item_type():
    for batch in EXIST_OFFER_SWAP_TO_CATEGORY:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 400, f"Expected HTTP status code 400, got {status}"
    print('Test cant swap item type passed.')


def test_cant_post_offer_without_price():
    for batch in OFFER_WITHOUT_PRICE:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 400, f"Expected HTTP status code 400, got {status}"
    print('Test cant post offer without price passed.')


def test_nodes_show_correct_context():
    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    # print(json.dumps(response, indent=2, ensure_ascii=False))

    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(EXPECTED_TREE)
    if response != EXPECTED_TREE:
        print_diff(EXPECTED_TREE, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test nodes show correct context passed.")


def test_all_items_in_batch_decline_if_one_item_invalid():
    for batch in NEW_IMPORT_BATCH_WITH_ONLY_ONE_INVALID_ITEM:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 400, f"Expected HTTP status code 400, got {status}"

    _, response = request(f"/nodes/{ROOT_ID}", json_response=True)

    deep_sort_children(response)
    deep_sort_children(EXPECTED_TREE)
    if response != EXPECTED_TREE:
        print_diff(EXPECTED_TREE, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test all items in batch decline if one item invalid passed.")


def test_update_parent_id_for_item():
    for batch in UPDATE_PARENT_ID_FOR_CATEGORY:
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    _, response = request(
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


def test_900_items_batch():
    cat = {
        "type": "CATEGORY",
        "name": "Товары",
        "id": "069cb8d7-bbdd-47d3-ad8f-39ef4c269df1",
        "parentId": None
    }
    batch = {
        "items": [cat],
        "updateDate": "2022-04-04T00:00:00.001Z"
    }
    for step in range(1, 900):
        item = {
            "id": str(uuid.uuid4()),
            "name": str(step),
            "parentId": "069cb8d7-bbdd-47d3-ad8f-39ef4c269df1",
            "price": step * 100,
            "type": "OFFER"
        }
        batch["items"].append(item)
    start = datetime.now()
    status, _ = request("/imports", method="POST", data=batch)
    end = datetime.now()
    print(end - start)
    start = datetime.now()
    status, _ = request("/nodes/069cb8d7-bbdd-47d3-ad8f-39ef4c269df1",
                        method="GET")
    end = datetime.now()
    print(end - start)
    status, _ = request("/delete/069cb8d7-bbdd-47d3-ad8f-39ef4c269df1",
                        method="DELETE")


def test_delete():
    status, _ = request(f"/delete/{ROOT_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test delete passed.")


def test_all():
    test_import()
    test_offer_cant_be_parent()
    test_cant_swap_item_type()
    test_cant_post_offer_without_price()
    test_nodes_show_correct_context()
    test_all_items_in_batch_decline_if_one_item_invalid()
    test_update_parent_id_for_item()
    test_sales_return_correct_data()
    test_stats_show_correct_context()
    test_900_items_batch()
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
