import json
from functools import partial
import asyncio
import aiohttp
from aiofile import async_open

from pbutils.request.utils import all_contexts, populate_profile, create_request_params
from pbutils.request.logs import log

json4 = partial(json.dumps, indent=4)


async def arun(profiles, environ=None):
    ''' create a task for each expanded profile '''
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(global_exception_handler)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for profile in profiles:
            for context in all_contexts(profile, environ):
                profile = populate_profile(profile, environ)
                req_params = create_request_params(profile)
                task = request_task(req_params, session)
                tasks.append(task)

        for task_result in asyncio.as_completed(tasks):
            try:
                _ = await task_result
            except Exception as e:
                print(F"caught {type(e)}: {e}")


def request_task(req_params, session):
    ''' create an asyncio.task from the profile '''
    async def do_arequest(req_params, session):
        output_path = req_params.pop('output_path', None)

        response = await session.request(**req_params)
        try:
            content = await response.json()
            content = json4(content)
        except Exception:
            content = await response.text()

        if output_path:
            async with async_open(output_path, "w") as aoutput:
                await aoutput.write(content)
                log.info(F"{output_path} written")
            req_params['output_path'] = output_path
        else:
            print(content)

    return asyncio.create_task(do_arequest(req_params, session))


def global_exception_handler(loop, signal=None):
    log.warning("global_exception_handler entered")
    if signal:
        log.info(F"Received signal {signal}")
