"""Text normalization for Spanish TTS."""

import re
from typing import Dict, List, Tuple


class SpanishTextNormalizer:
    """Comprehensive Spanish text normalizer for TTS."""

    # Number words
    UNITS = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    TENS = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
    TEENS = [
        "diez", "once", "doce", "trece", "catorce", "quince",
        "dieciséis", "diecisiete", "dieciocho", "diecinueve"
    ]
    TWENTIES = [
        "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco",
        "veintiséis", "veintisiete", "veintiocho", "veintinueve"
    ]
    HUNDREDS = [
        "", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos",
        "seiscientos", "setecientos", "ochocientos", "novecientos"
    ]

    # Common abbreviations
    ABBREVIATIONS = {
        "Sr.": "Señor",
        "Sra.": "Señora",
        "Dr.": "Doctor",
        "Dra.": "Doctora",
        "Prof.": "Profesor",
        "Profa.": "Profesora",
        "Ing.": "Ingeniero",
        "Lic.": "Licenciado",
        "Gral.": "General",
        "Tte.": "Teniente",
        "Av.": "Avenida",
        "Avda.": "Avenida",
        "C.": "Calle",
        "Apdo.": "Apartado",
        "núm.": "número",
        "pág.": "página",
        "tel.": "teléfono",
        "etc.": "etcétera",
        "p.ej.": "por ejemplo",
        "a.C.": "antes de Cristo",
        "d.C.": "después de Cristo",
        "S.A.": "Sociedad Anónima",
    }

    # Months
    MONTHS = {
        "01": "enero", "1": "enero",
        "02": "febrero", "2": "febrero",
        "03": "marzo", "3": "marzo",
        "04": "abril", "4": "abril",
        "05": "mayo", "5": "mayo",
        "06": "junio", "6": "junio",
        "07": "julio", "7": "julio",
        "08": "agosto", "8": "agosto",
        "09": "septiembre", "9": "septiembre",
        "10": "octubre",
        "11": "noviembre",
        "12": "diciembre",
    }

    # Time patterns
    TIME_PATTERN = re.compile(r'\b(\d{1,2}):(\d{2})\b')

    # Date patterns (dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy)
    DATE_PATTERN = re.compile(r'\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})\b')

    # Currency patterns
    CURRENCY_PATTERN = re.compile(r'\$\s*(\d+(?:[.,]\d+)?)')
    EURO_PATTERN = re.compile(r'€\s*(\d+(?:[.,]\d+)?)')

    # Number patterns
    NUMBER_PATTERN = re.compile(r'\b\d+\b')
    DECIMAL_PATTERN = re.compile(r'\b(\d+)[.,](\d+)\b')

    # Ordinal patterns
    ORDINAL_PATTERN = re.compile(r'(\d+)°')

    def __init__(self):
        """Initialize normalizer."""
        pass

    def normalize(self, text: str) -> str:
        """
        Normalize text for TTS.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Order matters - process in this sequence
        text = self._normalize_abbreviations(text)
        text = self._normalize_currency(text)
        text = self._normalize_time(text)
        text = self._normalize_dates(text)
        text = self._normalize_ordinals(text)
        text = self._normalize_decimals(text)
        text = self._normalize_numbers(text)
        text = self._clean_whitespace(text)

        return text

    def _normalize_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        for abbr, full in self.ABBREVIATIONS.items():
            # Use word boundary to avoid partial matches
            text = re.sub(r'\b' + re.escape(abbr), full, text)
        return text

    def _normalize_time(self, text: str) -> str:
        """Convert time format to words."""
        def replace_time(match):
            hour = int(match.group(1))
            minute = int(match.group(2))

            # Convert hour
            if hour == 0:
                hour_text = "cero"
            elif hour == 1:
                hour_text = "una"
            else:
                hour_text = self._number_to_words(hour)

            # Convert minute
            if minute == 0:
                return f"{hour_text} en punto"
            elif minute == 15:
                return f"{hour_text} y cuarto"
            elif minute == 30:
                return f"{hour_text} y media"
            elif minute == 45:
                next_hour = (hour % 12) + 1
                next_hour_text = "una" if next_hour == 1 else self._number_to_words(next_hour)
                return f"{next_hour_text} menos cuarto"
            else:
                minute_text = self._number_to_words(minute)
                return f"{hour_text} y {minute_text}"

        return self.TIME_PATTERN.sub(replace_time, text)

    def _normalize_dates(self, text: str) -> str:
        """Convert dates to words."""
        def replace_date(match):
            day = match.group(1)
            month = match.group(2)
            year = match.group(3)

            # Convert day
            day_num = int(day)
            if day_num == 1:
                day_text = "primero"
            else:
                day_text = self._number_to_words(day_num)

            # Convert month
            month_text = self.MONTHS.get(month, f"mes {month}")

            # Convert year
            year_text = self._year_to_words(int(year))

            return f"{day_text} de {month_text} de {year_text}"

        return self.DATE_PATTERN.sub(replace_date, text)

    def _normalize_currency(self, text: str) -> str:
        """Convert currency symbols to words."""
        # Dollar
        text = self.CURRENCY_PATTERN.sub(
            lambda m: f"{self._number_to_words(int(m.group(1).replace(',', '.').split('.')[0]))} dólares",
            text
        )

        # Euro
        text = self.EURO_PATTERN.sub(
            lambda m: f"{self._number_to_words(int(m.group(1).replace(',', '.').split('.')[0]))} euros",
            text
        )

        return text

    def _normalize_ordinals(self, text: str) -> str:
        """Convert ordinal numbers (1°, 2°, etc.)."""
        ordinal_words = [
            "", "primero", "segundo", "tercero", "cuarto", "quinto",
            "sexto", "séptimo", "octavo", "noveno", "décimo"
        ]

        def replace_ordinal(match):
            num = int(match.group(1))
            if num <= 10:
                return ordinal_words[num]
            else:
                return f"{self._number_to_words(num)}avo"

        return self.ORDINAL_PATTERN.sub(replace_ordinal, text)

    def _normalize_decimals(self, text: str) -> str:
        """Convert decimal numbers to words."""
        def replace_decimal(match):
            integer_part = int(match.group(1))
            decimal_part = match.group(2)

            integer_text = self._number_to_words(integer_part)
            decimal_text = " ".join([self.UNITS[int(d)] for d in decimal_part if d != '0'])

            return f"{integer_text} punto {decimal_text}"

        return self.DECIMAL_PATTERN.sub(replace_decimal, text)

    def _normalize_numbers(self, text: str) -> str:
        """Convert cardinal numbers to words."""
        return self.NUMBER_PATTERN.sub(
            lambda m: self._number_to_words(int(m.group())),
            text
        )

    def _number_to_words(self, n: int) -> str:
        """
        Convert number to Spanish words.

        Args:
            n: Number to convert (supports 0-999,999)

        Returns:
            Number as Spanish words
        """
        if n == 0:
            return "cero"

        if n < 0:
            return f"menos {self._number_to_words(-n)}"

        if n >= 1_000_000:
            millions = n // 1_000_000
            remainder = n % 1_000_000
            if millions == 1:
                result = "un millón"
            else:
                result = f"{self._number_to_words(millions)} millones"
            if remainder > 0:
                result += f" {self._number_to_words(remainder)}"
            return result

        if n >= 1000:
            thousands = n // 1000
            remainder = n % 1000
            if thousands == 1:
                result = "mil"
            else:
                result = f"{self._number_to_words(thousands)} mil"
            if remainder > 0:
                result += f" {self._number_to_words(remainder)}"
            return result

        if n >= 100:
            hundreds = n // 100
            remainder = n % 100
            if n == 100:
                return "cien"
            result = self.HUNDREDS[hundreds]
            if remainder > 0:
                result += f" {self._number_to_words(remainder)}"
            return result

        if n >= 30:
            tens = n // 10
            units = n % 10
            if units == 0:
                return self.TENS[tens]
            return f"{self.TENS[tens]} y {self.UNITS[units]}"

        if n >= 20:
            return self.TWENTIES[n - 20]

        if n >= 10:
            return self.TEENS[n - 10]

        return self.UNITS[n]

    def _year_to_words(self, year: int) -> str:
        """Convert year to Spanish words."""
        if year < 1000:
            return self._number_to_words(year)

        # Special handling for 2000+
        if year >= 2000:
            return f"dos mil {self._number_to_words(year % 1000)}" if year % 1000 > 0 else "dos mil"

        # For 1000-1999
        thousands = year // 1000
        remainder = year % 1000

        if thousands == 1:
            result = "mil"
        else:
            result = f"{self._number_to_words(thousands)} mil"

        if remainder > 0:
            result += f" {self._number_to_words(remainder)}"

        return result

    def _clean_whitespace(self, text: str) -> str:
        """Clean up extra whitespace."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove space before punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        return text.strip()


# Convenience function
def normalize_spanish_text(text: str) -> str:
    """
    Normalize Spanish text for TTS.

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    normalizer = SpanishTextNormalizer()
    return normalizer.normalize(text)
