from js import document


def test_first():
    document.body.innerHTML = '<input id="tag1" value="foo1">'
    assert document.getElementById('tag1').value == 'foo1'


def test_second():
    assert document.getElementById('tag2').value == 'foo1'


def test_third():
    print('ciao')
