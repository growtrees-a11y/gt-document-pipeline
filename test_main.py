"""
PROJ-02 Tests — Phase 2: Automated validation.
Tests PDF merge/split and image compression.
"""
import os
import io
import tempfile
import pytest
from PIL import Image
from main import merge_pdfs, split_pdf, compress_pdf_images, compress_image, ensure_dirs


def test_ensure_dirs():
    input_dir = os.path.join(tempfile.mkdtemp(), "test_input")
    output_dir = os.path.join(tempfile.mkdtemp(), "test_output")
    in_d, out_d = ensure_dirs(input_dir, output_dir)
    assert os.path.isdir(in_d)
    assert os.path.isdir(out_d)


def test_compression_roundtrip():
    """Compress a dummy image, verify output size is smaller."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy image
        img = Image.new("RGB", (1000, 1000), color="red")
        img_path = os.path.join(tmpdir, "test.png")
        img.save(img_path)
        original_size = os.path.getsize(img_path)

        # Compress
        compressed_path = os.path.join(tmpdir, "compressed.jpg")
        compress_image(img_path, compressed_path, dpi=100)

        compressed_size = os.path.getsize(compressed_path)
        assert compressed_size < original_size or original_size < 100  # Original already tiny


def test_split_pdf_creates_pages():
    """Split a PDF and verify page count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdf = os.path.join(tmpdir, "test.pdf")
        output_dir = os.path.join(tmpdir, "pages")

        # Create minimal test PDF
        writer = pypdf.PdfWriter()
        for _ in range(3):
            writer.add_blank_page(width=100, height=100)
        with open(input_pdf, "wb") as f:
            writer.write(f)

        files = split_pdf(input_pdf, output_dir)
        assert len(files) == 3


def test_merge_pdfs():
    """Merge two PDFs and verify page count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two test PDFs
        for i in range(2):
            writer = pypdf.PdfWriter()
            writer.add_blank_page(width=100, height=100)
            path = os.path.join(tmpdir, f"test{i}.pdf")
            with open(path, "wb") as f:
                writer.write(f)

        output_path = os.path.join(tmpdir, "merged.pdf")
        merge_pdfs([os.path.join(tmpdir, "test0.pdf"), os.path.join(tmpdir, "test1.pdf")], output_path)

        # Verify merged PDF has 2 pages
        reader = pypdf.PdfReader(output_path)
        assert len(reader.pages) == 2


def test_compression_preserves_image():
    """Compression doesn't corrupt image data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        img = Image.new("RGB", (200, 200), color=(0, 128, 255))
        img_path = os.path.join(tmpdir, "test.png")
        img.save(img_path)

        compressed_path = os.path.join(tmpdir, "compressed.png")
        compress_image(img_path, compressed_path, dpi=100)

        # Verify it's a valid image
        recompressed = Image.open(compressed_path)
        assert recompressed.format == "PNG"
        assert recompressed.size[0] <= 200  # Should be same or smaller


def test_ensure_dirs_idempotent():
    """ensure_dirs doesn't fail if dirs already exist."""
    input_dir = os.path.join(tempfile.mkdtemp(), "exists")
    os.makedirs(input_dir, exist_ok=True)
    in_d, _ = ensure_dirs(input_dir, os.path.join(tempfile.mkdtemp(), "out2"))
    assert os.path.isdir(in_d)
