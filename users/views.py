
import csv

from rest_framework import generics, permissions, status, response
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse

from shared.permissions import IsLevel1User

from .models import User, UserVerification
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

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="level_1_users.csv"'

        writer = csv.writer(response)
        header = [
            'id', 'username', 'email', 'display_name', 'date_joined', 'last_login',
            'korean_name', 'english_name', 'postal_code', 'address', 'phone_primary', 'phone_secondary',
            'birth_date', 'photo', 'appraiser_class', 'specialty_primary', 'specialty_secondary', 'specialty_tertiary',
            'company_info', 'education', 'experience', 'certificate1', 'certificate2', 'homepage_url',
        ]
        writer.writerow(header)

        users = User.objects.filter(level=1).select_related('meta_info')
        for user in users:
            meta = getattr(user, 'meta_info', None)
            writer.writerow([
                user.id, user.username, user.email, user.display_name, user.date_joined, user.last_login,
                meta.korean_name if meta else '',
                meta.english_name if meta else '',
                meta.postal_code if meta else '',
                meta.address if meta else '',
                meta.phone_primary if meta else '',
                meta.phone_secondary if meta else '',
                meta.birth_date if meta else '',
                meta.photo.url if meta and meta.photo else '',
                meta.appraiser_class if meta else '',
                meta.get_specialty_primary_display() if meta else '',
                meta.get_specialty_secondary_display() if meta else '',
                meta.get_specialty_tertiary_display() if meta else '',
                meta.company_info if meta else '',
                meta.education if meta else '',
                meta.experience if meta else '',
                meta.certificate1 if meta else '',
                meta.certificate2 if meta else '',
                meta.homepage_url if meta else '',
            ])

        return response

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({"message": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            for row in reader:
                # Assuming the CSV has fields: username, email, display_name
                username = row.get('username')
                email = row.get('email')
                display_name = row.get('display_name')

                if username and email and display_name:
                    User.objects.create(
                        username=username, email=email, display_name=display_name, level=1)

            return Response({"message": "Users created successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": f"Error processing file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
