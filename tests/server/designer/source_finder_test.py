from pathlib import Path

from playwright.sync_api import Page, expect

from tests import for_all_webservers
from tests.common import restore_sys_path
from wwwpy.server import configure
from wwwpy.webserver import Webserver

file_parent = Path(__file__).parent
support = file_parent / 'source_finder_support'


@for_all_webservers()
def test_find_component__when_using_convention(page: Page, webserver: Webserver, restore_sys_path):
    configure.convention(support, webserver)
    webserver.start_listen()

    page.goto(webserver.localhost_url())
    expect(page.locator('body')).to_have_text('path ok')
