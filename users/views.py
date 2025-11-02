
from rest_framework import generics, permissions, status, response
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from django.utils import timezone


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
        try:
            user_verification = UserVerification.objects.get(
                verification__token=token)
            if (user_verification.created_at + timezone.timedelta(minutes=24)) > timezone.now():
                return response.Response({"message": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

            user_verification.user.is_active = True
            user_verification.user.save()
            user_verification.delete()
            return response.Response({"message": "User verified successfully"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return response.Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

# class UserFindView(generics.APIVi):
#     pass
