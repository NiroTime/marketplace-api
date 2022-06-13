API_BASEURL = "http://127.0.0.1/"

ROOT_ID = "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"

FIRST_DATE_IN_IMPORT_BATCHES = "2022-02-01T12:00:00.000Z"

LAST_DATE_IN_IMPORT_BATCHES = "2022-02-03T16:00:00Z"

CATEGORY_ID = "22bc3b36-02d1-4245-ab35-3106c9ee1c65"
NEW_CATEGORY_PARENT_ID = "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2"

DELETE_OFFER_WITH_MULTIPLE_ANCESTORS = "73bc3b36-02d1-4245-ab35-3148c9ee1c65"

LAST_UPDATE_DATE = "2022-04-04T00:00:00Z"
LAST_UPDATE_DATE_PLUS_ONE_MS = "2022-04-04T00:00:00.001Z"

NONE_PRICE_FOR_OFFER = None

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
                "id": DELETE_OFFER_WITH_MULTIPLE_ANCESTORS,
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
        "updateDate": "2022-02-03T16:00:00Z"
    }
]

NEW_IMPORT_BATCH_WITH_ONLY_ONE_INVALID_ITEM = [
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar ery Smart",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 69999
            },
            {
                "type": "OFFER",
                "name": "Телевизор 1111111111111",
                "id": "59bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "price": 6999
            },
            {
                "type": "OFFER",
                "name": "Телевизор 33333333333",
                "id": "73bc3b36-02d1-4288-ab35-3106c9ee1c65",
                "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "price": 19999
            },
            {
                "type": "OFFER",
                "name": "Телевизор 22222222222",
                "id": "73bc3b36-99d1-4245-ab35-3106c9ee1c65",
                "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "price": 169999
            },
            {
                "type": "OFFER",
                "name": "Samsung 1233333333",
                "id": DELETE_OFFER_WITH_MULTIPLE_ANCESTORS,
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "price": 29999
            },
            {
                "type": "OFFER",
                "name": "jPhone 103333333333",
                "id": "73bc3b36-02d1-4245-ab35-3996c9ee1c65",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": NONE_PRICE_FOR_OFFER
            },
            {
                "type": "CATEGORY",
                "name": "Samsung22222",
                "id": "22bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "price": ""
            }
        ],
        "updateDate": LAST_DATE_IN_IMPORT_BATCHES
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
            "id": DELETE_OFFER_WITH_MULTIPLE_ANCESTORS,
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

EXIST_OFFER_SWAP_TO_CATEGORY = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "jPhone 10",
                "id": "73bc3b36-02d1-4245-ab35-3996c9ee1c65",
                "parentId": "22bc3b36-02d1-4245-ab35-3106c9ee1c65"
            }
        ],
        "updateDate": "2022-04-04T00:00:00Z"
    }
]

EXIST_OFFER_SWAP_PARENT_TO_OFFER = [
    {
        "items": [
            {
                "type": "OFFER",
                "name": "jPhone 10",
                "id": "73bc3b36-02d1-4245-ab35-3996c9ee1c65",
                "parentId": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                "price": 39999
            }
        ],
        "updateDate": "2022-04-04T00:00:00Z"
    }
]

OFFER_WITHOUT_PRICE = [
    {
        "items": [
            {
                "type": "OFFER",
                "name": "jPhone 5",
                "id": "73bc3b36-02d1-4245-ab35-3336c9ee1c65",
                "parentId": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                "price": None
            }
        ],
        "updateDate": "2022-04-04T00:00:00Z"
    }
]
