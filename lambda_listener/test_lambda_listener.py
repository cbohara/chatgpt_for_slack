import lambda_handler

def test_start_chat():
    chat = lambda_handler.start_chat()
    assert len(chat) == 1
