# utils/exceptions.py
class RFPError(Exception):
    """Base exception for all RFP-related errors"""
    pass

class DocumentError(RFPError):
    """Document processing errors"""
    pass

class TaskError(RFPError):
    """Task processing errors"""
    pass

class ValidationError(RFPError):
    """Data validation errors"""
    pass