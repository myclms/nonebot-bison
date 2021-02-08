import os
import nonebot
from nonebot import logger
import base64
from pyppeteer import launch
from html import escape
from hashlib import sha256

from . import plugin_config

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

supported_target_type = ('weibo', 'bilibili', 'rss')

class Render(metaclass=Singleton):

    def __init__(self):
        self.browser = None

    async def init(self):
        if plugin_config.hk_reporter_use_local:
            self.browser = await launch(executablePath='/usr/bin/chromium', args=['--no-sandbox'])
        else:
            self.browser = await launch(args=['--no-sandbox'])
        # self.page = await browser.newPage()

    async def text_to_pic(self, text: str) -> str:
        page = await self.browser.newPage()
        hash_text = sha256(text.encode()).hexdigest()[:20]
        lines = text.split('\n')
        parsed_lines = list(map(lambda x: '<p>{}</p>'.format(escape(x)), lines))
        html_text = '<div style="width:17em;padding:1em">{}</div>'.format(''.join(parsed_lines))
        with open('/tmp/text-{}.html'.format(hash_text), 'w') as f:
            f.write(html_text)
        await page.goto('file:///tmp/text-{}.html'.format(hash_text))
        div = await page.querySelector('div')
        data = await div.screenshot(type='jpeg', encoding='base64')
        await page.close()
        os.remove('/tmp/text-{}.html'.format(hash_text))
        return data

    async def text_to_pic_cqcode(self, text:str) -> str:
        data = await self.text_to_pic(text)
        # logger.debug('file size: {}'.format(len(data)))
        code = '[CQ:image,file=base64://{}]'.format(data)
        # logger.debug(code)
        return code

async def _start():
    if plugin_config.hk_reporter_use_pic:
        r = Render()
        await r.init()

nonebot.get_driver().on_startup(_start)
async def parse_text(text: str):
    if plugin_config.hk_reporter_use_pic:
        r = Render()
        return await r.text_to_pic_cqcode(text)
    else:
        return text
         
