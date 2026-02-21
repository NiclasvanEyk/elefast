def test_mock_docker_client_fixture(mock_docker_client):
    """Test that mock_docker_client fixture is properly configured."""
    assert mock_docker_client.containers.list.return_value is not None
    assert mock_docker_client.containers.run.return_value is not None
