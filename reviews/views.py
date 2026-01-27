from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from accounts.models import User
from accounts.enums import RoleChoices
from .models import LandscaperReview
from .serializers import LandscaperReviewSerializer


class AddOrUpdateReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, landscaper_id):
        landscaper = get_object_or_404(
            User,
            id=landscaper_id,
            role=RoleChoices.LANDSCAPER
        )

        review, created = LandscaperReview.objects.update_or_create(
            client=request.user,
            landscaper=landscaper,
            defaults={
                "rating": request.data.get("rating"),
                "comment": request.data.get("comment", "")
            }
        )

        serializer = LandscaperReviewSerializer(
            review,
            context={
                "request": request,
                "landscaper": landscaper
            }
        )

        return Response({
            "message": "Review submitted successfully",
            "review": serializer.data
        })


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from accounts.models import User
from accounts.enums import RoleChoices
from .models import LandscaperReview
from .serializers import LandscaperReviewSerializer


class AddOrUpdateReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, landscaper_id):
        landscaper = get_object_or_404(
            User,
            id=landscaper_id,
            role=RoleChoices.LANDSCAPER
        )

        review, created = LandscaperReview.objects.update_or_create(
            client=request.user,
            landscaper=landscaper,
            defaults={
                "rating": request.data.get("rating"),
                "comment": request.data.get("comment", "")
            }
        )

        serializer = LandscaperReviewSerializer(
            review,
            context={
                "request": request,
                "landscaper": landscaper
            }
        )

        return Response({
            "message": "Review submitted successfully",
            "review": serializer.data
        })


# delete 
class DeleteReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, review_id):
        review = get_object_or_404(
            LandscaperReview,
            id=review_id,
            client=request.user
        )
        review.delete()
        return Response({"message": "Review deleted"})
