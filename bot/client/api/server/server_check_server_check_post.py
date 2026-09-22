from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.error_response import ErrorResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    *,
    x_api_secret: str | Unset = '',

) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_secret, Unset):
        headers["X-API-Secret"] = x_api_secret



    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/server/check",
    }


    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | ErrorResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if response.status_code == 502:
        response_502 = ErrorResponse.from_dict(response.json())



        return response_502

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | ErrorResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_api_secret: str | Unset = '',

) -> Response[Any | ErrorResponse | HTTPValidationError]:
    """ Run service health check

     Runs the management script 'check' command. Returns an empty 200 on success, otherwise an error DTO.

    Args:
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorResponse | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        x_api_secret=x_api_secret,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    x_api_secret: str | Unset = '',

) -> Any | ErrorResponse | HTTPValidationError | None:
    """ Run service health check

     Runs the management script 'check' command. Returns an empty 200 on success, otherwise an error DTO.

    Args:
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorResponse | HTTPValidationError
     """


    return sync_detailed(
        client=client,
x_api_secret=x_api_secret,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_api_secret: str | Unset = '',

) -> Response[Any | ErrorResponse | HTTPValidationError]:
    """ Run service health check

     Runs the management script 'check' command. Returns an empty 200 on success, otherwise an error DTO.

    Args:
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorResponse | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        x_api_secret=x_api_secret,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    x_api_secret: str | Unset = '',

) -> Any | ErrorResponse | HTTPValidationError | None:
    """ Run service health check

     Runs the management script 'check' command. Returns an empty 200 on success, otherwise an error DTO.

    Args:
        x_api_secret (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorResponse | HTTPValidationError
     """


    return (await asyncio_detailed(
        client=client,
x_api_secret=x_api_secret,

    )).parsed
