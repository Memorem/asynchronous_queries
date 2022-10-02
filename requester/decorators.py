import os, sys, asyncio

from requester.utils import info


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

proxy = None

with open(f'{os.getcwd()}\\ok_proxy.txt') as f:
    proxy_list = f.read().split('\n')

def rotate_proxy(proxy):
    '''Proxy rotator'''
    return proxy_list[0] if proxy == proxy_list[-1] else proxy_list[proxy_list.index(proxy) + 1]

def connection_retry(func):
    """
    A simple decorator 
    handle errors that may appear due to the abundance of requests or incorrect data
    If error appear -> tries to retry request 5 times with 2 seconds delay
    """
    async def wrap(*args, **kwargs):
        retrying = 0
        while True:
            if ...:
                proxy = proxy_list[0]
                if retrying < len(proxy_list)*10:
                    break
            else:
                if retrying < 6:
                    break
            try:
                result = await func(proxy=proxy, *args, **kwargs)
            except Exception as ex:
                info(f'Got unexpected error {ex}'
                      f'Retrying to connect...{retries}')
                retries += 1
                await asyncio.sleep(2)
                if proxy:
                    proxy = rotate_proxy(proxy=proxy)
            else:
                return result
        raise Exception('Maximum connections retries exceeded')
    return wrap

# def connection_retry(func):
#     """
#     A simple decorator 
#     handle errors that may appear due to the abundance of requests or incorrect data
#     If error appear -> tries to retry request 5 times with 2 seconds delay
#     """
#     async def wrap(*args, **kwargs):
#         retries = 1
#         while retries < 6:
#             try:
#                 result = await func(*args, **kwargs)
#             except Exception as ex:
#                 info(f'Got unexpected error {ex}'
#                       f'Retrying to connect...{retries}')
#                 retries += 1
#                 await asyncio.sleep(2)
#             else:
#                 return result
#         raise Exception('Maximum connections retries exceeded')
#     return wrap

def event_loop(f):
    """A decorator that checks on existing event loop and starts it, otherwise doing nothing"""
    def decorator(*args, **kwargs):
        try:
            asyncio.get_running_loop()
        except RuntimeError: 
            return asyncio.run(f(*args, **kwargs))
        
        return f(*args, **kwargs)
    
    return decorator