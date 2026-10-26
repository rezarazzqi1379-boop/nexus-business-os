from io import BytesIO
from zipfile import ZipFile

import pytest

from authority_admission import AuthorityBinding, AuthorityBlocked, assert_consistent_authority_declarations


def docx(text):
    out = BytesIO()
    with ZipFile(out, "w") as archive:
        archive.writestr("word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body></w:document>')
    return out.getvalue()


def binding():
    return AuthorityBinding("v1.8", "a" * 64, "v2.1", "b" * 64,
                            "approved", "human", "approval-store/1")


def test_registry_conflicting_version_is_rejected():
    with pytest.raises(AuthorityBlocked, match="registry_declaration_conflict"):
        assert_consistent_authority_declarations(
            docx("Source Registry v1.6 governs"), docx("Master Context v2.1 governing"), binding())


def test_master_conflicting_version_is_rejected():
    with pytest.raises(AuthorityBlocked, match="master_declaration_conflict"):
        assert_consistent_authority_declarations(
            docx("Source Registry v1.8 governing"), docx("Master Context v1.9 active"), binding())


def test_consistent_declarations_accepted():
    assert_consistent_authority_declarations(
        docx("Source Registry v1.8 governing"), docx("Master Context v2.1 active"), binding())


def test_invalid_docx_blocks():
    with pytest.raises(AuthorityBlocked, match="document_unreadable"):
        assert_consistent_authority_declarations(b"not a docx", docx("Master Context v2.1"), binding())
