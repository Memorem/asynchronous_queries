from aiohttp import ClientSession

import asyncio
from typing import AsyncGenerator, Any, NoReturn

from requester.decorators import connection_retry
from requester.metaclasses import Singleton
from requester.utils import Response, get_useragent


class Request(metaclass=Singleton):
    """
    A Singleton class that makes async request and getting data from url/urls
    <options> contents simple request options:

        auth, json, data, params, allow_redirects, cookies, headers...

    step is necessary to determine the number of requests that need to be made.
    NOTE:
        - Be careful using the step value above 100 (some servers can't handle a large number of requests)
        Usage:
            Request().fetch('https://google.com') -> returns the site data
            Request().collect_data(['https://google.com', 'https://youtube.com']) -> returns the list with sites data
    """
    def __init__(self, step: int = 10, with_session: bool = True) -> None:
        self.step = step 
        self.headers: dict = {
            'user-agent': get_useragent(),
        }
        self.__session: ClientSession = self._create_session(session=with_session)
        
    async def _create_session(self, session: bool) -> ClientSession:
        """Creating session"""
        if not session:
            async with ClientSession(headers=self.headers) as session:
                while True:
                    yield session
        else:
            async with ClientSession(headers=self.headers) as session:
                while True:
                    yield session
    

    async def close_session(self):
        session = await anext(self.__session)
        return await session.close()


    async def get(self, url: str, as_json: bool = False, **options) -> Response | NoReturn:
        return await self._fetch(url=url, method='get', json_data=as_json, **options)


    async def post(self, url: str, as_json: bool = False, **options) -> Response | NoReturn:
        return await self._fetch(url=url, method='post', json_data=as_json, **options)


    async def patch(self, url: str, as_json: bool = False, **options) -> Response | NoReturn:
        return await self._fetch(url=url, method='patch', json_data=as_json, **options)


    async def options(self, url: str, as_json: bool = False, **options) -> Response | NoReturn:
        return await self._fetch(url=url, method='options', json_data=as_json, **options)


    async def put(self, url: str, as_json: bool = False, **options) -> Response | NoReturn:
        return await self._fetch(url=url, method='put', json_data=as_json, **options)

    
    @connection_retry
    async def _fetch(
        self, 
        url: str, 
        method: str, 
        json_data: bool, 
        proxy=None,  
        **options
        ) -> Response:
        """
        Args:
            url (str): URL-address from which data will be obtained
            method (str, optional): request method. Defaults to 'get'.
            json_data (bool, optional): equal to .json() from basic request. Defaults to False.

        Raises:
            AttributeError: supports only get, post, put, patch, options methods

        Returns:
            response: a data from request
        """
        if not isinstance(method, str):
            raise TypeError(f'method should be a str, not {type(method)}')
        if not isinstance(json_data, bool):
            raise TypeError(f'Expected True/False, not {type(json_data)}')

        session = await anext(self.__session) # getting current session
        
        request = {
            'post': session.post,
            'get': session.get,
            'put': session.put,
            'options': session.options,
            'patch': session.patch,
        }
        
        if method not in request:
            raise AttributeError(f'Expected request method, got {method}')
        if not options.get('headers'):
            options['headers'] = self.headers
            
        async with request[method](url=url, proxy=proxy, **options) as response:
            if response.status == 200:
                return Response(
                    content=await response.read() if not json_data else await response.json(),
                    request_url=url,
                    response_url=response.url,
                    headers=response.headers,
                    cookies=response.cookies,
                    status_code=response.status
                )

            return Response(
                    request_url=url,
                    response_url=response.url,
                    headers=response.headers,
                    cookies=response.cookies,
                    status_code=response.status
                )

    async def _collect_tasks(
        self, 
        urls: list | tuple, 
        method: str, 
        json_data: bool = False, 
        **options
        ) -> AsyncGenerator[list[Response], Any]:
        """
        Args:
            urls (list | tuple): retrieval of data from multiple URLs
            method (str, optional): similar to ._fetch() method
            json_data (bool, optional): similar to ._fetch() method

        Yields:
            Iterator[list[Response]]: returns an AsyncGenerator with list of responses inside
        """
        if not isinstance(urls, (tuple, list)):
            urls = tuple(urls)
        step = self.step if len(urls) >= self.step else len(urls)
        tasks = set()
        for index in range(0, len(urls), step):
            for url in urls[index:index+step]:
                tasks.add(asyncio.create_task(self.fetch(url, method=method, json_data=json_data, **options)))
            yield await asyncio.gather(*tasks)
            tasks.clear()
            
    async def collect_data(
        self, 
        urls: list | tuple, 
        method: str = 'get', 
        json_data: bool = False, 
        **options
        ) -> AsyncGenerator[list[Response], Any]:
        return self._collect_tasks(urls, method=method, json_data=json_data, **options)