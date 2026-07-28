from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.serializers import CompanySerializer, UserProfileSerializer, ProductSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    # Use the serializer that already nests the CompanySerializer
    serializer = UserProfileSerializer(user)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_company(request):
    company = request.user.company

    serializer = CompanySerializer(
        company,
        data=request.data,
        partial=True,
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)

