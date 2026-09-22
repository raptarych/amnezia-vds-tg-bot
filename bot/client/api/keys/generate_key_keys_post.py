from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.key_generated import KeyGenerated
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    *,
    name: str,
    x_api_secret: str | Unset = '',

) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_secret, Unset):
        headers["X-API-Secret"] = x_api_secret



    

    params: dict[str, Any] = {}

    params["name"] = name


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/keys",
        "params": params,
    }


    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> HTTPValidationError | KeyGenerated | None:
    if response.status_code == 201:
        response_201 = KeyGenerated.from_dict(response.json())



        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[HTTPValidationError | KeyGenerated]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    x_api_secret: str | Unset = '',

) -> Response[HTTPValidationError | KeyGenerated]:
    """ Generate a new key

     Runs the management script 'add' command to create a key.

    Args:
        name (str): Name of the key to generate.
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | KeyGenerated]
     """


    kwargs = _get_kwargs(
        name=name,
x_api_secret=x_api_secret,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    x_api_secret: str | Unset = '',

) -> HTTPValidationError | KeyGenerated | None:
    """ Generate a new key

     Runs the management script 'add' command to create a key.

    Args:
        name (str): Name of the key to generate.
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | KeyGenerated
     """


    return sync_detailed(
        client=client,
name=name,
x_api_secret=x_api_secret,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    x_api_secret: str | Unset = '',

) -> Response[HTTPValidationError | KeyGenerated]:
    """ Generate a new key

     Runs the management script 'add' command to create a key.

    Args:
        name (str): Name of the key to generate.
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | KeyGenerated]
     """


    kwargs = _get_kwargs(
        name=name,
x_api_secret=x_api_secret,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    x_api_secret: str | Unset = '',

) -> HTTPValidationError | KeyGenerated | None:
    """ Generate a new key

     Runs the management script 'add' command to create a key.

    Args:
        name (str): Name of the key to generate.
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | KeyGenerated
     """


    return (await asyncio_detailed(
        client=client,
name=name,
x_api_secret=x_api_secret,

    )).parsed
