from django.core.mail import send_mail
from django.conf import settings

def send_kica_email(subject, recipient_list, content_html):
    """
    Sends an email with the standard KICA branding and layout.
    
    Args:
        subject (str): The subject of the email.
        recipient_list (list): List of recipient email addresses.
        content_html (str): The main content of the email (HTML).
    """
    
    # Logo URLs (assuming they are hosted at these paths or similar)
    # If not, these should be updated to valid public URLs.
    # Using the domain from settings.FRONT_BASE_URL if available, or hardcoded.
    base_url = getattr(settings, 'FRONT_BASE_URL', 'https://kica.or.kr')
    logo_img_url = f"{base_url}/media/logo/logo_img.svg"
    logo_text_url = f"{base_url}/media/logo/logo_text.svg"

    full_html_message = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>{subject}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="font-family: 'Malgun Gothic', dotum, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 20px auto; padding: 40px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="display: inline-flex; align-items: center; justify-content: center;">
                    <img src="{logo_img_url}" alt="KICA Logo" style="height: 50px; margin-right: 10px;">
                    <img src="{logo_text_url}" alt="한국건설감정사회" style="height: 30px;">
                </div>
            </div>
            
            <div style="padding: 10px 0;">
                {content_html}
            </div>

            <p style="font-size: 12px; color: #999; text-align: center; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
                본 메일은 발신 전용입니다.<br>
                한국건설감정사회 | Korea Insurance & Construction Appraisers
            </p>
        </div>
    </body>
    </html>
    """

    send_mail(
        subject=subject,
        message='',  # Plain text fallback could be generated here
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
        html_message=full_html_message
    )
