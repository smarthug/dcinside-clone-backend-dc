
import csv

from rest_framework import generics, permissions, status, response, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from shared.permissions import IsLevel1User

from .models import User, UserMetaInfo, UserVerification
from .serializers import UserProfileSerializer, UserRegistrationSerializer
from .utils import send_kica_email


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = (JSONParser, FormParser, MultiPartParser)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def get_object(self):
        return self.request.user

    # def put(self, request, *args, **kwargs):
    #     return response.Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    # def patch(self, request, *args, **kwargs):
    #     if request.data.get("meta", False):
    #         instance = UserMetaInfo.objects.get(user=request.user)
    #         serializer = UserMetaProfileSerializer(
    #             instance, data=request.data.get("UserMetaInfo"), partial=True)
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()

    #     return super().patch(request, *args, **kwargs)


class UserVerifyView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = kwargs.get('token')
        if not token:
            token = request.query_params.get('token')

        try:
            user_verification = UserVerification.objects.get(token=token)
            if (user_verification.created_at + timezone.timedelta(minutes=24)) < timezone.now():
                return response.Response({"message": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

            user_verification.user.is_active = True
            user_verification.user.save()
            user_verification.delete()
            return response.Response({"message": "User verified successfully"}, status=status.HTTP_200_OK)

        except UserVerification.DoesNotExist:
            return response.Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class UserFindIDView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            content_html = f"""
                <h2 style="color: #333; text-align: center;">아이디 찾기 안내</h2>
                <p style="color: #555; line-height: 1.6;">
                    안녕하세요.<br>
                    요청하신 아이디 정보를 안내해 드립니다.<br>
                    회원님의 아이디는 <strong>{user.username}</strong> 입니다.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONT_BASE_URL}/auth/login" style="background-color: #007bff; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">로그인 하러가기</a>
                </div>
            """

            send_kica_email(
                subject='[한국건설감정사회] 아이디 찾기 안내',
                recipient_list=[email],
                content_html=content_html
            )

            return Response({"message": "아이디가 이메일로 발송되었습니다."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # For security, we might want to return 200 even if user not found, but for UX we return 404 here as per typical requirement unless specified otherwise.
            # Given the previous context, explicit error seems preferred.
            return Response({"message": "해당 이메일로 가입된 계정을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLevelView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        level = user.level
        username = user.username
        display_name = user.display_name
        email = user.email
        return Response({"level": level, "username": username, "display_name": display_name, "email": email}, status=status.HTTP_200_OK)


class UserDataCSVView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsLevel1User]

    def post(self, request, *args, **kwargs):
        # If file is present, it's an import
        if 'file' in request.FILES:
            return self.handle_import(request)

        # Otherwise, assume export (e.g. if ids are provided or just requesting export)
        return self.handle_export(request)

    def handle_export(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="members.csv"'

        writer = csv.writer(response)
        header = [
            'No', '이름', '아이디', '별명', '아이콘', '등록일', '레벨', '포인트', '우편번호', '주소', '주민번호',
            'Tel1', 'Tel2', '생년월일', '성별', '메일수신', '쪽지수신', '사진', '관리메모', '추천인', '로그인',
            '영문이름', '건설감정사 기수', '전문분야 1순위', '전문분야 2순위', '전문분야 3순위',
            '직장명,부서,직급', '최종학력(학교,전공,학위)', '전공,전문분야 경력',
            '보유자격증1(자격증명,발급기관,취득년)', '보유자격증2(자격증명,발급기관,취득년)', 'HOME', 'MAIL'
        ]
        writer.writerow(header)

        users = User.objects.all().select_related('meta_info').order_by('id')

        # Get ids from request body (JSON or Form)
        ids = request.data.get('ids')
        if ids:
            # ids might be a list if JSON, or string if Form
            if isinstance(ids, str):
                id_list = [int(x) for x in ids.split(',') if x.isdigit()]
            elif isinstance(ids, list):
                id_list = [int(x) for x in ids if str(x).isdigit()]
            else:
                id_list = []

            if id_list:
                users = users.filter(id__in=id_list)

        for user in users:
            meta = getattr(user, 'meta_info', None)

            # Helper to get specialty display
            def get_specialty_display(val):
                if not val:
                    return ''
                choices = UserMetaInfo.Specialty.choices
                for k, v in choices:
                    if k == val:
                        return v
                return ''

            writer.writerow([
                user.id,
                meta.korean_name if meta else '',
                user.username,
                user.display_name,
                '',  # Icon
                user.date_joined.strftime('%Y-%m-%d'),
                user.level,
                0,  # Point
                meta.postal_code if meta else '',
                meta.address if meta else '',
                '',  # Resident ID
                meta.phone_primary if meta else '',
                meta.phone_secondary if meta else '',
                meta.birth_date.strftime(
                    '%Y-%m-%d') if meta and meta.birth_date else '',
                '',  # Gender
                'Yes',  # Email receive
                'Yes',  # Note receive
                meta.photo.url if meta and meta.photo else '',
                '',  # Admin memo
                '',  # Recommender
                0,  # Login count
                meta.english_name if meta else '',
                meta.appraiser_class if meta else '',
                get_specialty_display(meta.specialty_primary) if meta else '',
                get_specialty_display(
                    meta.specialty_secondary) if meta else '',
                get_specialty_display(meta.specialty_tertiary) if meta else '',
                meta.company_info if meta else '',
                meta.education if meta else '',
                meta.experience if meta else '',
                meta.certificate1 if meta else '',
                meta.certificate2 if meta else '',
                meta.homepage_url if meta else '',
                user.email,
            ])

        return response

    def handle_import(self, request):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({"message": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Handle encoding (cp949 is common for Korean CSVs, but utf-8 is standard)
            # We try utf-8 first, then cp949
            file_data = csv_file.read()
            try:
                decoded_file = file_data.decode('utf-8').splitlines()
            except UnicodeDecodeError:
                decoded_file = file_data.decode('cp949').splitlines()

            reader = csv.DictReader(decoded_file)

            # Specialty Reverse Mapping
            specialty_map = {label: value for value,
                             label in UserMetaInfo.Specialty.choices}

            created_count = 0
            updated_count = 0

            for row in reader:
                username = row.get('아이디')
                email = row.get('MAIL')

                if not username or not email:
                    continue

                # Prepare User data
                user_data = {
                    'email': email,
                    'display_name': row.get('별명', ''),
                    'level': 99,
                }

                # Create or Update User
                user, created = User.objects.update_or_create(
                    username=username,
                    defaults=user_data
                )

                if created:
                    user.set_unusable_password()
                    user.save()
                    created_count += 1
                else:
                    updated_count += 1

                # Prepare Meta Info
                birth_date_str = row.get('생년월일', '')
                birth_date = None
                if birth_date_str:
                    try:
                        birth_date = timezone.datetime.strptime(
                            birth_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass

                meta_data = {
                    'korean_name': row.get('이름', ''),
                    'english_name': row.get('영문이름', ''),
                    'postal_code': row.get('우편번호', ''),
                    'address': row.get('주소', ''),
                    'phone_primary': row.get('Tel1', ''),
                    'phone_secondary': row.get('Tel2', ''),
                    'birth_date': birth_date,
                    'appraiser_class': row.get('건설감정사 기수', ''),
                    'specialty_primary': specialty_map.get(row.get('전문분야 1순위', '')),
                    'specialty_secondary': specialty_map.get(row.get('전문분야 2순위', '')),
                    'specialty_tertiary': specialty_map.get(row.get('전문분야 3순위', '')),
                    'company_info': row.get('직장명,부서,직급', ''),
                    'education': row.get('최종학력(학교,전공,학위)', ''),
                    'experience': row.get('전공,전문분야 경력', ''),
                    'certificate1': row.get('보유자격증1(자격증명,발급기관,취득년)', ''),
                    'certificate2': row.get('보유자격증2(자격증명,발급기관,취득년)', ''),
                    'homepage_url': row.get('HOME', ''),
                }

                # Create or Update Meta Info
                UserMetaInfo.objects.update_or_create(
                    user=user,
                    defaults=meta_data
                )

            return Response({
                "message": f"Processed successfully. Created: {created_count}, Updated: {updated_count}"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"message": f"Error processing file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsersView(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsLevel1User]
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    filterset_fields = ['level', 'is_active']
    search_fields = ['username', 'email', 'display_name']


class UserPasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('resetEmail')

        if not all([username, email]):
            return Response({"message": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if user exists with matching details
            user = User.objects.get(username=username, email=email)

            # Create or update verification token
            verification, created = UserVerification.objects.update_or_create(
                user=user)

            # Send email
            reset_link = f"{settings.FRONT_BASE_URL}/auth/reset-password?token={verification.token}"

            content_html = f"""
                <h2 style="color: #333; text-align: center;">비밀번호 재설정 안내</h2>
                <p style="color: #555; line-height: 1.6;">
                    안녕하세요, {username}님.<br>
                    비밀번호 재설정을 요청하셔서 안내 메일을 보내드립니다.<br>
                    아래 버튼을 클릭하여 비밀번호를 재설정해 주세요.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #007bff; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">비밀번호 재설정</a>
                </div>
            """

            send_kica_email(
                subject='[한국건설감정사회] 비밀번호 재설정 안내',
                recipient_list=[email],
                content_html=content_html
            )

            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # For security, we might want to return 200 even if user not found,
            # but for this specific request "find user id and password", explicit error might be expected.
            # Let's return a generic error or specific one depending on requirements.
            # Given the context of "Find Password", telling them it's wrong is usually helpful UX vs security trade-off.
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        password = request.data.get('password')
        password_confirm = request.data.get('passwordConfirm')

        if not all([token, password, password_confirm]):
            return Response({"message": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if password != password_confirm:
            return Response({"message": "Passwords must match."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_verification = UserVerification.objects.get(token=token)

            # Check expiry (e.g., 24 hours)
            if (user_verification.created_at + timezone.timedelta(hours=24)) < timezone.now():
                return Response({"message": "Token expired."}, status=status.HTTP_400_BAD_REQUEST)

            user = user_verification.user
            
            try:
                validate_password(password, user=user)
            except ValidationError as e:
                return Response({"message": e.messages}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.save()

            # Delete verification token after use
            user_verification.delete()

            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        except UserVerification.DoesNotExist:
            return Response({"message": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except AuthenticationFailed as e:
            # Check if it's due to inactive user
            user = User.objects.filter(
                username=attrs.get(self.username_field)).first()
            if user and not user.is_active:
                # Check verification status
                verification, created = UserVerification.objects.get_or_create(
                    user=user)

                # If token expired or created new, resend email
                if created or (verification.created_at + timezone.timedelta(minutes=24)) < timezone.now():
                    # Update token (delete old and create new to refresh timestamp/token)
                    verification.delete()
                    verification = UserVerification.objects.create(user=user)

                    verification_link = f"{settings.FRONT_BASE_URL}/verify/?token={verification.token}"

                    content_html = f"""
                        <h2 style="color: #333; text-align: center;">이메일 인증 안내 (재발송)</h2>
                        <p style="color: #555; line-height: 1.6;">
                            안녕하세요, {user.display_name or user.username}님.<br>
                            이메일 인증이 완료되지 않아 로그인할 수 없습니다.<br>
                            아래 버튼을 클릭하여 이메일 인증을 완료해 주세요.
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_link}" style="background-color: #007bff; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">이메일 인증하기</a>
                        </div>
                    """

                    send_kica_email(
                        subject='[한국건설감정사회] 이메일 인증 안내 (재발송)',
                        recipient_list=[user.email],
                        content_html=content_html
                    )
                    raise AuthenticationFailed(
                        "이메일 인증이 완료되지 않았습니다. 인증 메일을 재발송했습니다. 이메일을 확인해 주세요.")
                else:
                    raise AuthenticationFailed(
                        "이메일 인증이 완료되지 않았습니다. 이미 발송된 인증 메일을 확인해 주세요.")

            raise e


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class DisputeSubmissionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Extract fields
        name = data.get('name', '')
        affiliation = data.get('affiliation', '')
        contact = data.get('contact', '')
        project_name = data.get('project_name', '')
        
        tech_major = data.get('tech_major', '')
        tech_minor = data.get('tech_minor', '')
        
        dispute_field = data.get('dispute_field', '')
        dispute_content = data.get('dispute_content', '')
        request_content = data.get('request_content', '')

        # Validate required fields (basic validation)
        if not all([name, contact, tech_major, dispute_field, dispute_content]):
             return Response({"message": "필수 항목을 모두 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)

        # Format email body
        email_body = f"""
1. 접수자 정보
 1) 성명 : {name}
 2) 소속 / 직급 : {affiliation}
 3) 휴대폰번호 / 이메일주소 : {contact}
 4) 과업명 또는 현장명 : {project_name}

2. 기술 분야
 1) 대분류 : {tech_major}
 2) 세분류 : {tech_minor}

3. 분쟁 분야 : {dispute_field}

4. 분쟁 내용
 {dispute_content}

5. 요청사항
 {request_content}
"""

        # Convert plain text body to HTML for the template
        content_html = f"<pre style='font-family: inherit; white-space: pre-wrap;'>{email_body}</pre>"

        subject = f"[분쟁접수 - {tech_major}] {name}님 분쟁 접수"
        
        try:
            send_kica_email(
                subject=subject,
                recipient_list=['kica0472@naver.com'],
                content_html=content_html
            )
            return Response({"message": "분쟁 접수가 완료되었습니다."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Email sending failed: {e}")
class AdvertisementSubmissionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Extract fields
        name = data.get('name', '')
        affiliation = data.get('affiliation', '')
        contact = data.get('contact', '')
        
        company_name = data.get('company_name', '')
        industry = data.get('industry', '')
        homepage = data.get('homepage', '')

        # Validate required fields
        if not all([name, contact, company_name]):
             return Response({"message": "필수 항목을 모두 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)

        # Format email body
        email_body = f"""
1. 접수자 정보
 1) 성명 : {name}
 2) 소속 / 직급 : {affiliation}
 3) 휴대폰번호 / 이메일주소 : {contact}

2. 기업 정보
 1) 기업명 : {company_name}
 2) 업종 / 주요 생산품 : {industry}
 3) 홈페이지 주소 : {homepage}
"""

        # Convert plain text body to HTML for the template
        content_html = f"<pre style='font-family: inherit; white-space: pre-wrap;'>{email_body}</pre>"

        subject = f"[광고신청] {name}님 광고 신청"
        
        try:
            send_kica_email(
                subject=subject,
                recipient_list=['kica0472@naver.com'],
                content_html=content_html
            )
            return Response({"message": "광고 신청이 완료되었습니다."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Email sending failed: {e}")
            return Response({"message": "메일 발송 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
