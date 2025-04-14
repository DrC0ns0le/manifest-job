"""
Match analysis package for processing job postings and matching with profiles
"""

from match_analysis.processor import JobMatchProcessor
from match_analysis.queue import JobQueue

__all__ = ['JobMatchProcessor', 'JobQueue']