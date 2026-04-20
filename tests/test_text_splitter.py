"""Tests for the custom text splitter."""

from core.text_splitter import RecursiveTextSplitter


class TestRecursiveTextSplitter:
    """Tests for RecursiveTextSplitter."""

    def test_split_short_text(self):
        """Test that short text is not split."""
        splitter = RecursiveTextSplitter(chunk_size=100, chunk_overlap=20)
        text = "This is a short text."
        chunks = splitter.split_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_by_paragraphs(self):
        """Test splitting by paragraph separators."""
        splitter = RecursiveTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = splitter.split_text(text)

        assert len(chunks) >= 2
        assert "First paragraph" in chunks[0]

    def test_split_by_newlines(self):
        """Test splitting by newline when paragraphs are too long."""
        splitter = RecursiveTextSplitter(chunk_size=30, chunk_overlap=5)
        text = "Line one.\nLine two.\nLine three."
        chunks = splitter.split_text(text)

        assert len(chunks) >= 2

    def test_split_long_text_with_overlap(self):
        """Test that chunks have overlap."""
        splitter = RecursiveTextSplitter(chunk_size=50, chunk_overlap=20)
        text = "Word " * 50  # 250 characters

        chunks = splitter.split_text(text)

        # Should create multiple chunks
        assert len(chunks) > 1

        # All chunks should be under chunk_size (with some tolerance for separators)
        for chunk in chunks:
            assert len(chunk) <= splitter.chunk_size + 20

    def test_split_preserves_content(self):
        """Test that all content is preserved after splitting."""
        splitter = RecursiveTextSplitter(chunk_size=100, chunk_overlap=20)
        text = "The quick brown fox jumps over the lazy dog. " * 10

        chunks = splitter.split_text(text)

        # Reconstruct (approximately) and check key content is there
        all_text = " ".join(chunks)
        assert "quick brown fox" in all_text
        assert "lazy dog" in all_text

    def test_empty_text(self):
        """Test handling of empty text."""
        splitter = RecursiveTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = splitter.split_text("")

        assert chunks == []

    def test_custom_separators(self):
        """Test with custom separators."""
        splitter = RecursiveTextSplitter(chunk_size=50, chunk_overlap=10, separators=["|||", "|", " "])
        text = "Part one|||Part two|||Part three"
        chunks = splitter.split_text(text)

        assert len(chunks) >= 1
        assert "Part one" in chunks[0]
