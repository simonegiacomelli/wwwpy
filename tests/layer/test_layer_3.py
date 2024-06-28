from playwright.sync_api import Page, expect

from tests import for_all_webservers
from wwwpy.bootstrap import get_javascript_for, wrap_in_tryexcept, bootstrap_routes, bootstrap_javascript_placeholder
from wwwpy.http import HttpRoute, HttpResponse
from wwwpy.resources import StringResource, library_resources
from wwwpy.server.sse import SseServer
from wwwpy.webserver import Webserver


@for_all_webservers()
def test_python_execution(page: Page, webserver: Webserver):
    python_code = 'from js import document\ndocument.getElementById("tag1").value = "foo1"'
    javascript = get_javascript_for(python_code)
    html = f'<input id="tag1" value="bar"><script>{javascript}</script>'
    webserver.set_http_route(HttpRoute('/', lambda request: HttpResponse.text_html(html)))
    webserver.start_listen()
    page.goto(webserver.localhost_url())
    expect(page.locator('id=tag1')).to_have_value('foo1')


@for_all_webservers()
def test_zipped_python_execution_default(page: Page, webserver: Webserver):
    resources = [[StringResource(
        'remote.py',
        """from js import document\ndocument.body.innerHTML = '<input id="tag1" value="foo1">' """
    )]]
    webserver.set_http_route(*bootstrap_routes(resources))
    webserver.start_listen()
    page.goto(webserver.localhost_url())
    expect(page.locator('id=tag1')).to_have_value('foo1')


@for_all_webservers()
def test_zipped_python_execution_no_default(page: Page, webserver: Webserver):
    my_entrypoint = StringResource(
        'some_file.py',
        """from js import document\ndocument.body.innerHTML = '<input id="tag1" value="foo1">' """
    )
    html = f"""<input id="tag1" value="bar"><script> {bootstrap_javascript_placeholder}  </script>"""
    webserver.set_http_route(*bootstrap_routes(
        [[my_entrypoint]], html=html, python='import some_file', zip_route_path='/foo.zip'))
    webserver.start_listen()
    page.goto(webserver.localhost_url())
    expect(page.locator('id=tag1')).to_have_value('foo1')


def test_wrap_in_tryexcept():
    tmp = []
    code = wrap_in_tryexcept('1/0', (
        'tmp.append("executed")\n'
        'tmp.append("type=" + str(type(exception).__name__))'
    ))
    exec(code)
    assert ['executed', 'type=ZeroDivisionError'] == tmp


@for_all_webservers()
def test_sse_server_protocol(page: Page, webserver: Webserver):
    # language=python
    python_code = """

from js import document, EventSource
from pyodide.ffi import create_proxy
document.body.innerHTML = ''

def log(msg):
    document.body.innerHTML += f'|{msg}'

es = EventSource.new('/sse')
es.onopen = lambda e: log('open')
es.onmessage = lambda e: log(f'message:{e.data}')
es.addEventListener('type1', create_proxy(lambda e: log(f'type1:{e.data}')))

        """

    webserver.set_http_route(*bootstrap_routes(resources=[library_resources()], python=python_code))
    sse_server = SseServer('/sse')
    webserver.set_http_route(sse_server.http_route)
    webserver.start_listen()
    page.goto(webserver.localhost_url())

    expect(page.locator('body')).to_have_text('|open')
    assert len(sse_server.clients) == 1
    sse_server.clients[0].send_event('42')
    expect(page.locator('body')).to_have_text('|open|message:42')
    sse_server.clients[0].send_event('11', 'type1')
    expect(page.locator('body')).to_have_text('|open|message:42|type1:11')
