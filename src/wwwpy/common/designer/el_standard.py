from typing import List

from wwwpy.common.designer.element_library import ElementDef, Help, EventDef, AttributeDef


def _standard_elements_def() -> List[ElementDef]:
    res = [
        ElementDef(
            'button', 'js.HTMLButtonElement',
            help=Help('A clickable button.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button'),
            attributes=[
                AttributeDef('type', Help('The type of the button.', ''),
                             values=['submit', 'reset', 'button'], default_value='button'),
                AttributeDef('value', Help('The value of the button.', '')),
            ],
            events=[EventDef('click', Help('The button was clicked.',
                                           'https://developer.mozilla.org/en-US/docs/Web/API/Element/click_event')),
                    EventDef('dblclick', Help('The button was double-clicked.',
                                              'https://developer.mozilla.org/en-US/docs/Web/API/Element/dblclick_event'))],
        ),
        ElementDef(
            'input', 'js.HTMLInputElement',
            help=Help('A field for entering text.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input'),
            attributes=[
                AttributeDef('type', Help('The type of control to display. The default type is text.', ''),
                             values=['text', 'password', 'checkbox', 'radio', 'button', 'submit', 'reset', 'file',
                                     'hidden', 'image', 'date', 'datetime-local', 'month', 'time', 'week',
                                     'number', 'range', 'email', 'url', 'search', 'tel', 'color'],
                             default_value='text'),
                AttributeDef('value', Help('The value of the input field.', '')),
                AttributeDef('placeholder', Help('A hint to the user of what can be entered in the field.', '')),
                AttributeDef('disabled', Help('Whether the control is disabled.', ''), boolean=True),
                AttributeDef('readonly', Help('Whether the control is read-only.', ''), boolean=True),
                AttributeDef('required', Help('Whether the control is required for form submission.', ''),
                             boolean=True),
                AttributeDef('min', Help('The minimum value of the input field.', '')),
                AttributeDef('max', Help('The maximum value of the input field.', '')),
                AttributeDef('step', Help('The legal number intervals for the input field.', '')),
                AttributeDef('pattern', Help('A regular expression that the input\'s value is checked against.', '')),
                AttributeDef('autocomplete', Help('Whether the control is required for form submission.', ''),
                             values=['on', 'off']),
                AttributeDef('autofocus', Help('Whether the control should have input focus when the page loads.', ''),
                             boolean=True),
                AttributeDef('checked', Help('Whether the control is checked.', ''), boolean=True),
                AttributeDef('multiple', Help('Whether the user is allowed to enter more than one value.', ''),
                             boolean=True),

            ],
            events=[
                EventDef('input', Help('The input event fires when the value of the element has been changed '
                                       'as a direct result of a user action',
                                       'https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event')),
                EventDef('change')
            ]
        ),
        ElementDef(
            'div', 'js.HTMLDivElement',
            help=Help('A generic container element.',
                      'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div')
        ),
        ElementDef(
            'progress', 'js.HTMLProgressElement',
            help=Help('A progress bar.',
                      'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/progress'),
            attributes=[
                AttributeDef('value', Help('The current value of the progress bar.', '')),
                AttributeDef('max', Help('The maximum value of the progress bar.', '')),
            ],
            events=[
                EventDef('click', Help('The progress bar was clicked.', '')),
                ])


    ]


    for r in res:
        r.gen_html = _generateHtml
    return res


def _generateHtml(element_def: ElementDef, name: str) -> str:
    tag_name = element_def.tag_name

    def _def(placeHolder=False, add=''):
        def inner():
            pl = '' if not placeHolder else f' placeholder="{name}"'
            add1 = '' if not add else f' {add}'
            return f'<{tag_name} data-name="{name}"{pl}{add1}>{name}</{tag_name}>'

        return inner

    func = {
        'button': _def(),
        'input': lambda: f"""<input data-name="{name}" placeholder="{name}">""",
        'progress': lambda: f"""<progress data-name="{name}" value="70" max="100">70 %</progress>""",
    }
    gen_html = func.get(tag_name, None)
    html = '\n' + gen_html() if gen_html else '' + ElementDef.default_gen_html(element_def, name)
    return html

# [
#     _comp('input', 'js.HTMLInputElement', '<input type="text" data-name="#name#" value="#name#">'),
#     _comp('button', 'js.HTMLButtonElement', '<button data-name="#name#">#name#</button>'),
#     _comp('textarea', 'js.HTMLTextAreaElement', '<textarea data-name="#name#">#name#</textarea>'),
#     _comp('select', 'js.HTMLSelectElement',
#           '<select data-name="#name#"><option>#name#</option></select>'),
#     _comp('div', 'js.HTMLDivElement', '<div data-name="#name#">#name#</div>'),
#     _comp('p', 'js.HTMLParagraphElement', '<p data-name="#name#">#name#</p>'),
#     _comp('h1', 'js.HTMLHeadingElement', '<h1 data-name="#name#">#name#</h1>'),
#     _comp('h2', 'js.HTMLHeadingElement', '<h2 data-name="#name#">#name#</h2>'),
#     _comp('h3', 'js.HTMLHeadingElement', '<h3 data-name="#name#">#name#</h3>'),
#     _comp('a', 'js.HTMLAnchorElement', '<a href="#" data-name="#name#">#name#</a>'),
#     _comp('img', 'js.HTMLImageElement', '<img src="#" alt="#name#" data-name="#name#">'),
#     _comp('ul', 'js.HTMLUListElement', '<ul data-name="#name#"><li>#name#</li></ul>'),
#     _comp('ol', 'js.HTMLOListElement', '<ol data-name="#name#"><li>#name#</li></ol>'),
#     _comp('li', 'js.HTMLLIElement', '<li data-name="#name#">#name#</li>'),
#     _comp('table', 'js.HTMLTableElement', '<table data-name="#name#"><tr><td>#name#</td></tr></table>'),
#     _comp('form', 'js.HTMLFormElement', '<form data-name="#name#">#name#</form>'),
#     _comp('label', 'js.HTMLLabelElement', '<label data-name="#name#">#name#</label>'),
#
# ]
