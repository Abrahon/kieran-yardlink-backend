from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Avg

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

        return Response(
            {
                "message": "Review submitted successfully",
                "created": created,
                "review": serializer.data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class LandscaperReviewListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, landscaper_id):
        landscaper = get_object_or_404(
            User,
            id=landscaper_id,
            role=RoleChoices.LANDSCAPER
        )

        reviews = LandscaperReview.objects.filter(
            landscaper=landscaper
        ).select_related("client")

        avg_rating = reviews.aggregate(
            avg=Avg("rating")
        )["avg"] or 0

        serializer = LandscaperReviewSerializer(reviews, many=True)

        return Response(
            {
                "average_rating": round(avg_rating, 1),
                "total_reviews": reviews.count(),
                "reviews": serializer.data
            },
            status=status.HTTP_200_OK
        )
        
class DeleteReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, review_id):
        review = get_object_or_404(
            LandscaperReview,
            id=review_id,
            client=request.user
        )
        review.delete()

        return Response(
            {"message": "Review deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
