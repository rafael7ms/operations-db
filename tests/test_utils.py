"""Tests for the utilities module."""
import sys
from pathlib import Path

# Add the app directory to the path for imports
app_path = Path(__file__).parent.parent / 'app'
sys.path.insert(0, str(app_path))

from app.utils.parsers import parse_name


class TestParseName:
    """Tests for the parse_name function."""

    def test_parse_name_first_last_format(self):
        """Test parsing 'First Last' format."""
        first, last = parse_name("John Doe")
        assert first == "John"
        assert last == "Doe"

    def test_parse_name_first_last_with_multiword_last(self):
        """Test parsing 'First Last' format with multi-word last name."""
        first, last = parse_name("Maria Garcia Lopez")
        assert first == "Maria"
        assert last == "Garcia Lopez"

    def test_parse_name_last_first_format(self):
        """Test parsing 'Last, First' format."""
        first, last = parse_name("Smith, Jane")
        assert first == "Jane"
        assert last == "Smith"

    def test_parse_name_last_first_with_comma_in_last_name(self):
        """Test parsing 'Last, First' format with comma in last name (e.g., Jr.)."""
        first, last = parse_name("Smith Jr., John")
        assert first == "John"
        assert last == "Smith Jr."

    def test_parse_name_with_extra_whitespace(self):
        """Test parsing with leading/trailing whitespace."""
        first, last = parse_name("  Bob Wilson  ")
        assert first == "Bob"
        assert last == "Wilson"

    def test_parse_name_with_spaces_around_comma(self):
        """Test parsing 'Last, First' format with spaces around comma."""
        first, last = parse_name("  Johnson , Mary  ")
        assert first == "Mary"
        assert last == "Johnson"

    def test_parse_name_single_name(self):
        """Test parsing single name (no last name)."""
        first, last = parse_name("Cher")
        assert first == "Cher"
        assert last == ""

    def test_parse_name_empty_string(self):
        """Test parsing empty string."""
        first, last = parse_name("")
        assert first == ""
        assert last == ""

    def test_parse_name_only_whitespace(self):
        """Test parsing string with only whitespace."""
        first, last = parse_name("   ")
        assert first == ""
        assert last == ""

    def test_parse_name_single_word_with_trailing_space(self):
        """Test parsing single name with trailing space."""
        first, last = parse_name("Madonna ")
        assert first == "Madonna"
        assert last == ""

    def test_parse_name_preserves_case(self):
        """Test that parse_name preserves the original case."""
        first, last = parse_name("jean-luc Picard")
        assert first == "jean-luc"
        assert last == "Picard"

    def test_parse_name_hyphenated_first_name(self):
        """Test parsing name with hyphenated first name."""
        first, last = parse_name("Jean-Pierre Renoir")
        assert first == "Jean-Pierre"
        assert last == "Renoir"

    def test_parse_name_hyphenated_last_name(self):
        """Test parsing name with hyphenated last name."""
        first, last = parse_name("Marie-Claire Dupont")
        assert first == "Marie-Claire"
        assert last == "Dupont"

    def test_parse_name_multiple_spaces_between_names(self):
        """Test parsing name with multiple spaces between first and last name."""
        first, last = parse_name("Alice   Bernard")
        assert first == "Alice"
        assert last == "Bernard"

    def test_parse_name_last_first_format_multiple_spaces(self):
        """Test parsing 'Last, First' format with multiple spaces."""
        first, last = parse_name("Walker  ,   Sarah")
        assert first == "Sarah"
        assert last == "Walker"
