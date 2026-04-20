"""Simple text splitter for chunking documents."""


class RecursiveTextSplitter:
    """
    A simple recursive text splitter that splits text into chunks with overlap.

    Similar to LangChain's RecursiveCharacterTextSplitter but without the dependency.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks using recursive character splitting."""
        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using the list of separators."""
        final_chunks: list[str] = []

        # Get the appropriate separator
        separator = separators[-1]  # Default to last (empty string)
        new_separators: list[str] = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        # Split the text
        splits = self._split_by_separator(text, separator)

        # Process each split
        good_splits: list[str] = []
        for split in splits:
            if len(split) < self.chunk_size:
                good_splits.append(split)
            else:
                # If we have accumulated good splits, merge them first
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []

                # Recursively split the large chunk
                if new_separators:
                    other_chunks = self._split_text_recursive(split, new_separators)
                    final_chunks.extend(other_chunks)
                else:
                    final_chunks.append(split)

        # Merge any remaining good splits
        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return final_chunks

    def _split_by_separator(self, text: str, separator: str) -> list[str]:
        """Split text by separator, keeping non-empty parts."""
        if separator:
            splits = text.split(separator)
            # Add separator back to maintain text integrity (except for last)
            result = []
            for i, split in enumerate(splits):
                if split:  # Skip empty strings
                    if i < len(splits) - 1:
                        result.append(split + separator)
                    else:
                        result.append(split)
            return result
        else:
            # Character-level split
            return list(text)

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Merge splits into chunks respecting chunk_size and overlap."""
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for split in splits:
            split_len = len(split)

            # If adding this split exceeds chunk_size, save current chunk
            if current_length + split_len > self.chunk_size and current_chunk:
                chunk_text = "".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)

                # Keep overlap from the end of current chunk
                overlap_length = 0
                overlap_splits: list[str] = []
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_splits.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                current_chunk = overlap_splits
                current_length = overlap_length

            current_chunk.append(split)
            current_length += split_len

        # Add the last chunk
        if current_chunk:
            chunk_text = "".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks
