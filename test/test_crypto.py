from crypto.decrypt import decrypt


def test_decrypt():
    ciphertext = ('6a7495108a7f8c9ab4d0990854240242:'
                  'e05f0d25446be83fa92aa9586610496b:'
                  '560d3e8ff02f852104417a')
    key = 'shhhhhhh'

    expected = 'hello world'

    result = decrypt(ciphertext, key)

    assert result == expected
