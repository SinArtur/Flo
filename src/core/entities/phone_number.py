import re
from dataclasses import dataclass


@dataclass
class PhoneNumber:
    value: str
    
    def __post_init__(self):
        if not self.is_valid():
            raise ValueError(f"Invalid phone number format: {self.value}")
    
    def is_valid(self) -> bool:
        # Russian phone number format: +7XXXXXXXXXX (11 digits after +7)
        pattern = r'^\+7\d{10}$'
        return bool(re.match(pattern, self.value))
    
    def normalized(self) -> str:
        """Returns normalized phone number"""
        return self.value
    
    def __str__(self) -> str:
        return self.value

