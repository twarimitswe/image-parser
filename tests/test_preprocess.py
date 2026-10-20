import pytest
from PIL import Image

from smart_form_parser import ImageLoadError, load, prepare
from smart_form_parser.preprocess import otsu_threshold


def test_loads_from_a_path_bytes_and_an_image(tmp_path):
    path = tmp_path / "form.png"
    Image.new("RGB", (40, 30), "white").save(path)
    assert load(path).size == (40, 30)
    assert load(path.read_bytes()).size == (40, 30)
    image = Image.new("RGB", (5, 5))
    assert load(image) is image


def test_undecodable_input_raises_image_load_error():
    with pytest.raises(ImageLoadError):
        load(b"this is not an image")


def test_prepare_upscales_narrow_scans_and_keeps_the_aspect_ratio():
    prepared = prepare(Image.new("RGB", (400, 600), "white"), binarize=False)
    assert prepared.width == 1600
    assert prepared.height == 2400
    assert prepared.mode == "L"


def test_prepare_leaves_wide_scans_at_their_own_size():
    assert prepare(Image.new("RGB", (2000, 1000), "white")).size == (2000, 1000)


def test_otsu_threshold_separates_ink_from_paper():
    page = Image.new("L", (100, 100), 240)
    page.paste(20, (0, 0, 100, 40))
    assert 20 <= otsu_threshold(page) < 240


def test_binarized_output_only_contains_black_and_white():
    page = Image.new("L", (1700, 100), 240)
    page.paste(20, (0, 0, 800, 100))
    assert set(prepare(page, binarize=True).tobytes()) <= {0, 255}
