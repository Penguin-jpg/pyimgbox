import io
import re

import pytest

from pyimgbox import _http


@pytest.fixture
async def client():
    async with _http.HTTPClient() as client:
        yield client


@pytest.mark.asyncio
async def test_get_sends_headers(client, httpserver):
    client.headers.update({'a': '123'})
    httpserver.expect_request(
        uri='/foo',
        method='GET',
        headers=client.headers,
    ).respond_with_data('bar')
    url = httpserver.url_for('/foo')
    response = await client.get(url)
    assert response == 'bar'

@pytest.mark.asyncio
async def test_get_sends_params(client, httpserver):
    params = {'a': 'asdf'}
    httpserver.expect_request(
        uri='/foo',
        method='GET',
        query_string=params,
    ).respond_with_data('bar')
    url = httpserver.url_for('/foo')
    response = await client.get(url, params=params)
    assert response == 'bar'

@pytest.mark.asyncio
async def test_get_gets_json(client, httpserver):
    json = {'bar': 'baz'}
    httpserver.expect_request(
        uri='/foo',
        method='GET',
    ).respond_with_json(json)
    url = httpserver.url_for('/foo')
    response = await client.get(url, json=True)
    assert response == json

@pytest.mark.asyncio
async def test_get_gets_http_error_status(client, httpserver):
    httpserver.expect_request(
        uri='/foo',
        method='GET',
    ).respond_with_data('No such URI', status=404)
    url = httpserver.url_for('/foo')
    with pytest.raises(ConnectionError, match=f'^{url}: No such URI$'):
        await client.get(url)

@pytest.mark.asyncio
async def test_get_cannot_connect(client):
    url = 'http://localhost:12345/foo/bar'
    with pytest.raises(ConnectionError, match=f'^{url}: Connection failed$'):
        await client.get(url)


@pytest.mark.asyncio
async def test_post_sends_headers(client, httpserver):
    client.headers.update({'a': '123'})
    httpserver.expect_request(
        uri='/foo',
        method='POST',
        headers=client.headers,
    ).respond_with_data('bar')
    url = httpserver.url_for('/foo')
    response = await client.post(url)
    assert response == 'bar'

@pytest.mark.asyncio
async def test_post_sends_data(client, httpserver):
    data = b'asdf'
    httpserver.expect_request(
        uri='/foo',
        method='POST',
        data=data,
    ).respond_with_data('bar')
    url = httpserver.url_for('/foo')
    response = await client.post(url, data=data)
    assert response == 'bar'

# FIXME: pytest-httpserver doesn't support multipart file uploads, but we can
#        hack something together by getting the request from the log attribute.
@pytest.mark.asyncio
async def test_post_sends_files(client, httpserver):
    files = {
        'files[]': ('asdf.jpg', io.BytesIO(b'image data'), 'image/jpeg'),
    }
    request_data_regex = re.compile(
        (
            rb'^--[0-9a-f]{32}'
            rb'\r\nContent-Disposition: form-data; name="files\[\]"; '
            rb'filename="asdf.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'
            rb'image data\r\n'
            rb'--[0-9a-f]{32}--\r\n$'
        ),
        flags=re.MULTILINE,
    )
    httpserver.expect_request(
        uri='/foo',
        method='POST',
    ).respond_with_data('bar')
    url = httpserver.url_for('/foo')
    response = await client.post(url, files=files)
    request_seen = httpserver.log[0][0]
    assert re.search(request_data_regex, request_seen.data)
    assert response == 'bar'

@pytest.mark.asyncio
async def test_post_gets_json(client, httpserver):
    json = {'bar': 'baz'}
    httpserver.expect_request(
        uri='/foo',
        method='POST',
    ).respond_with_json(json)
    url = httpserver.url_for('/foo')
    response = await client.post(url, json=True)
    assert response == json

@pytest.mark.asyncio
async def test_post_gets_http_error_status(client, httpserver):
    httpserver.expect_request(
        uri='/foo',
        method='POST',
    ).respond_with_data('Wat', status=500)
    url = httpserver.url_for('/foo')
    with pytest.raises(ConnectionError, match=f'^{url}: Wat$'):
        await client.post(url)

@pytest.mark.asyncio
async def test_post_gets_http_error_status_413(client, httpserver):
    httpserver.expect_request(
        uri='/foo',
        method='POST',
    ).respond_with_data('Something', status=413)
    url = httpserver.url_for('/foo')
    with pytest.raises(ConnectionError, match=f'^{url}: File too large$'):
        await client.post(url)

@pytest.mark.asyncio
async def test_post_cannot_connect(client):
    url = 'http://localhost:12345/foo/bar'
    with pytest.raises(ConnectionError, match=f'^{url}: Connection failed$'):
        await client.post(url)
