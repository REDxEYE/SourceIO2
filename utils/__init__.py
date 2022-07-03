from .file_utils import IBuffer, FileBuffer, MemoryBuffer, IFromFile

# According to the Valve documentation,
# one hammer unit is 1/16 of feet, and one feet is 30.48 cm
SOURCE1_HAMMER_UNIT_TO_METERS = ((1 / 16) * 30.48) / 100
# one hammer unit is 1/12 of feet, and one feet is 30.48 cm
SOURCE2_HAMMER_UNIT_TO_METERS = ((1 / 12) * 30.48) / 100