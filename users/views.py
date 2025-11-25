
import csv

from rest_framework import generics, permissions, status, response, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse

from shared.permissions import IsLevel1User

from .models import User, UserMetaInfo, UserVerification
from .serializers import UserProfileSerializer, UserRegistrationSerializer


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
        print("Received token:", token)
        try:
            user_verification = UserVerification.objects.get(token=token)
            if (user_verification.created_at + timezone.timedelta(minutes=24)) > timezone.now():
                return response.Response({"message": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

            user_verification.user.is_active = True
            user_verification.user.save()
            user_verification.delete()
            return response.Response({"message": "User verified successfully"}, status=status.HTTP_200_OK)

        except UserVerification.DoesNotExist:
            return response.Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

# class UserFindView(generics.APIVi):
#     pass


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
                if not val: return ''
                choices = UserMetaInfo.Specialty.choices
                for k, v in choices:
                    if k == val: return v
                return ''

            writer.writerow([
                user.id,
                meta.korean_name if meta else '',
                user.username,
                user.display_name,
                '', # Icon
                user.date_joined.strftime('%Y-%m-%d'),
                user.level,
                0, # Point
                meta.postal_code if meta else '',
                meta.address if meta else '',
                '', # Resident ID
                meta.phone_primary if meta else '',
                meta.phone_secondary if meta else '',
                meta.birth_date.strftime('%Y-%m-%d') if meta and meta.birth_date else '',
                '', # Gender
                'Yes', # Email receive
                'Yes', # Note receive
                meta.photo.url if meta and meta.photo else '',
                '', # Admin memo
                '', # Recommender
                0, # Login count
                meta.english_name if meta else '',
                meta.appraiser_class if meta else '',
                get_specialty_display(meta.specialty_primary) if meta else '',
                get_specialty_display(meta.specialty_secondary) if meta else '',
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
            specialty_map = {label: value for value, label in UserMetaInfo.Specialty.choices}

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
                        birth_date = timezone.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
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
