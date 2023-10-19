from web3 import AsyncHTTPProvider, Web3

from inspector.retry import http_retry_with_backoff_request_middleware


def get_base_provider(rpc: str, request_timeout: int = 500) -> Web3.AsyncHTTPProvider:
    base_provider = AsyncHTTPProvider(rpc, request_kwargs={"timeout": request_timeout})
    middlewares_list = list(base_provider.middlewares)
    middlewares_list.append(http_retry_with_backoff_request_middleware)
    base_provider.middlewares = tuple(middlewares_list)
    return base_provider
