import re
import dns.resolver
import smtplib
from typing import Tuple, Dict, Any
import asyncio

class EmailValidator:
    def __init__(self):
        # Common disposable email domains
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'throwaway.email'
        }
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def is_disposable_email(self, email: str) -> bool:
        """Check if email is from a disposable email service"""
        domain = email.split('@')[1].lower()
        return domain in self.disposable_domains
    
    async def check_domain_mx_record(self, domain: str) -> bool:
        """Check if domain has valid MX records"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except Exception:
            return False
    
    async def validate_email_existence(self, email: str) -> Dict[str, Any]:
        """
        Comprehensive email validation
        Returns: {
            'is_valid': bool,
            'format_valid': bool,
            'domain_valid': bool,
            'not_disposable': bool,
            'message': str
        }
        """
        result = {
            'is_valid': False,
            'format_valid': False,
            'domain_valid': False,
            'not_disposable': True,
            'message': ''
        }
        
        # Check email format
        if not self.validate_email_format(email):
            result['message'] = 'Invalid email format'
            return result
        result['format_valid'] = True
        
        # Check if disposable email
        if self.is_disposable_email(email):
            result['not_disposable'] = False
            result['message'] = 'Disposable email addresses are not allowed'
            return result
        
        # Check domain MX records
        domain = email.split('@')[1]
        domain_valid = await self.check_domain_mx_record(domain)
        result['domain_valid'] = domain_valid
        
        if not domain_valid:
            result['message'] = 'Invalid email domain'
            return result
        
        # All checks passed
        result['is_valid'] = True
        result['message'] = 'Email is valid'
        return result
