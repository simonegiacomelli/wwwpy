from js import document


async def main():
    from wwwpy.remote import shoelace
    shoelace.setup_shoelace()

    from . import component1  # for component registration
    from . import upload_component  # for component registration
    document.body.innerHTML = '<component-1></component-1>'
