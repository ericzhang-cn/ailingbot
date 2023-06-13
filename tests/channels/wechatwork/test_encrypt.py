from ailingbot.channels.wechatwork.encrypt import signature, decrypt


def test_signature():
    sig = '0af7077e1d70aed01bf9a6f40b2b52a7536ec807'
    token = 'jF9WQd6XtH7'
    timestamp = 1647328566
    nonce = 1648278214
    msg_encrypt = '9eOdb3odwWMVTiGRTm+uiVrx3SGwzjGyq6oWu4b2tWC51YbHQasEVD9ZdS6Nx+XBxB2C/qxZ8bl8+qRBUb8CVg=='

    assert (
        signature(
            token=token,
            timestamp=timestamp,
            nonce=nonce,
            msg_encrypt=msg_encrypt,
        )
        == sig
    )


def test_decrypt():
    aes_key = '8tcbqHabYBnQ2N7ID8BXtkordA4b1MzossELoCPvK8z'
    msg_encrypt = '9eOdb3odwWMVTiGRTm+uiVrx3SGwzjGyq6oWu4b2tWC51YbHQasEVD9ZdS6Nx+XBxB2C/qxZ8bl8+qRBUb8CVg=='
    message, receive_id = decrypt(key=aes_key, msg_encrypt=msg_encrypt)

    assert message == '7205136330722672511'
    assert receive_id == 'ww54047ef57875c719'
