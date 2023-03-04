from lambda_listener import lambda_handler


def test_start_chat():
    assert len(lambda_handler.start_chat()) == 1
