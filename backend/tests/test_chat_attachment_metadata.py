from pages.chat import _format_message_dict


def test_chat_history_exposes_attachment_metadata_without_file_contents():
    message = _format_message_dict({
        "id": "message-1",
        "role": "user",
        "content": "Review this report",
        "attachments": [{
            "filename": "report.pdf",
            "file_type": "application/pdf",
            "content_base64": "private-file-bytes",
        }],
    })

    assert message["attachments"] == [{
        "filename": "report.pdf",
        "file_type": "application/pdf",
    }]
    assert "content_base64" not in message["attachments"][0]
