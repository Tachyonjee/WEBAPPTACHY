import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from extensions import db
from models.user import OTPVerification
from services.security import SecurityService

logger = logging.getLogger(__name__)

class OTPService:
    """Service for handling OTP generation and delivery"""
    
    def __init__(self):
        from config import Config
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.smtp_user = Config.SMTP_USER
        self.smtp_pass = Config.SMTP_PASS
        self.sender_email = Config.OTP_SENDER_EMAIL
    
    def send_otp(self, identifier, delivery_method='email'):
        """
        Send OTP to user via email or SMS
        
        Args:
            identifier: Email address or phone number
            delivery_method: 'email' or 'sms'
            
        Returns:
            {
                'success': bool,
                'message': str,
                'otp_id': int (if successful)
            }
        """
        # Check rate limits
        is_allowed, hourly_remaining, daily_remaining = SecurityService.check_otp_rate_limit(identifier)
        
        if not is_allowed:
            return {
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
                'hourly_remaining': hourly_remaining,
                'daily_remaining': daily_remaining
            }
        
        # Clean up expired OTPs
        SecurityService.clean_expired_otp_records()
        
        # Generate OTP
        otp_code = OTPVerification.generate_otp()
        
        # Create OTP record
        otp_record = OTPVerification(identifier=identifier)
        otp_record.set_otp(otp_code)
        
        db.session.add(otp_record)
        db.session.commit()
        
        # Send OTP
        try:
            if delivery_method == 'email':
                success = self._send_email_otp(identifier, otp_code)
            elif delivery_method == 'sms':
                success = self._send_sms_otp(identifier, otp_code)
            else:
                return {
                    'success': False,
                    'message': 'Invalid delivery method'
                }
            
            if success:
                # Increment rate limit counter
                SecurityService.increment_otp_rate_limit(identifier)
                
                return {
                    'success': True,
                    'message': f'OTP sent successfully via {delivery_method}',
                    'otp_id': otp_record.id
                }
            else:
                # Remove the OTP record if sending failed
                db.session.delete(otp_record)
                db.session.commit()
                
                return {
                    'success': False,
                    'message': f'Failed to send OTP via {delivery_method}'
                }
        
        except Exception as e:
            # Remove the OTP record if sending failed
            db.session.delete(otp_record)
            db.session.commit()
            
            logger.error(f"Error sending OTP to {identifier}: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to send OTP. Please try again.'
            }
    
    def verify_otp(self, identifier, otp_code):
        """
        Verify OTP code
        
        Args:
            identifier: Email address or phone number
            otp_code: OTP code to verify
            
        Returns:
            {
                'success': bool,
                'message': str,
                'is_expired': bool,
                'attempts_remaining': int
            }
        """
        # Find the most recent OTP record for this identifier
        otp_record = OTPVerification.query.filter_by(
            identifier=identifier,
            is_verified=False
        ).order_by(OTPVerification.created_at.desc()).first()
        
        if not otp_record:
            return {
                'success': False,
                'message': 'No active OTP found. Please request a new one.',
                'is_expired': True,
                'attempts_remaining': 0
            }
        
        # Check if expired
        if otp_record.is_expired():
            return {
                'success': False,
                'message': 'OTP has expired. Please request a new one.',
                'is_expired': True,
                'attempts_remaining': 0
            }
        
        # Check attempts
        if otp_record.attempts >= 3:
            return {
                'success': False,
                'message': 'Maximum attempts exceeded. Please request a new OTP.',
                'is_expired': False,
                'attempts_remaining': 0
            }
        
        # Verify OTP
        is_valid = otp_record.verify_otp(otp_code)
        
        if is_valid:
            return {
                'success': True,
                'message': 'OTP verified successfully',
                'is_expired': False,
                'attempts_remaining': 3 - otp_record.attempts
            }
        else:
            return {
                'success': False,
                'message': 'Invalid OTP. Please try again.',
                'is_expired': False,
                'attempts_remaining': 3 - otp_record.attempts
            }
    
    def _send_email_otp(self, email, otp_code):
        """Send OTP via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = 'Your OTP for Coaching App Login'
            
            # Create email body
            body = f"""
            Dear Student,
            
            Your OTP for login is: {otp_code}
            
            This OTP is valid for 5 minutes. Do not share this code with anyone.
            
            If you didn't request this OTP, please ignore this email.
            
            Best regards,
            Coaching App Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send
            if self.smtp_user and self.smtp_pass:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
                server.quit()
            else:
                # For development - just log the OTP
                logger.info(f"DEV MODE: OTP for {email} is {otp_code}")
                print(f"DEV MODE: OTP for {email} is {otp_code}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending email OTP: {str(e)}")
            return False
    
    def _send_sms_otp(self, phone, otp_code):
        """Send OTP via SMS (placeholder for future implementation)"""
        # TODO: Implement SMS sending using Twilio or similar service
        # For now, this is a placeholder that logs the OTP
        
        try:
            # In production, this would use Twilio or similar service:
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=f"Your OTP is: {otp_code}",
            #     from_='+1234567890',
            #     to=phone
            # )
            
            # For development - just log the OTP
            logger.info(f"DEV MODE: SMS OTP for {phone} is {otp_code}")
            print(f"DEV MODE: SMS OTP for {phone} is {otp_code}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending SMS OTP: {str(e)}")
            return False
    
    def cleanup_expired_otps(self):
        """Clean up expired OTP records (can be called by scheduler)"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        expired_count = OTPVerification.query.filter(
            OTPVerification.expires_at < cutoff_time
        ).delete()
        db.session.commit()
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired OTP records")
        
        return expired_count

# Singleton instance
otp_service = OTPService()
