"""
 author: @abhiyanhaze
 description: String utils

"""

def normalize_icd(code: str) -> str:
    """
    Normalize ICD code for reliable matching.
    """
    return code.strip().upper().replace(".", "")
