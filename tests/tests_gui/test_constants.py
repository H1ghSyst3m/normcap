import dataclasses

from normcap.gui import constants
from normcap.gui.settings_defs import APPLICATION_LINKS


def test_languages_dimensions():
    language_dims = {len(lang) for lang in constants.LANGUAGES}
    assert len(constants.LANGUAGES) > 120
    assert language_dims == {4}


def test_urls_has_no_dynobo_references():
    for field in dataclasses.fields(constants.URLS):
        value = getattr(constants.URLS, field.name)
        assert "dynobo" not in value, f"Field {field.name!r} still contains 'dynobo'"


def test_application_links_has_no_faqs_or_donate():
    urls = [url for _, url in APPLICATION_LINKS]
    assert not any("#faqs" in url.lower() for url in urls)
    assert not any("buymeacoffee" in url.lower() for url in urls)
