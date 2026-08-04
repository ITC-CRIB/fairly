from fairly.keychain import delete_token, get_token, set_token


def test_set_get_delete_token_round_trip():
	token_id = "test-token-id"
	token_value = "test-token-value"

	set_token(token_id, token_value)
	assert get_token(token_id) == token_value

	delete_token(token_id)
	assert get_token(token_id) is None


def test_get_token_returns_none_for_missing_id():
	assert get_token("missing-token-id") is None


def test_delete_token_is_noop_for_missing_id():
	delete_token("missing-token-id")
