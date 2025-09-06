# people/views.py
from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Teacher, Staff, Student, PrincipalList, PresidentList
from .serializers import (
    TeacherSerializer,
    StaffSerializer,
    StudentSerializer,
    PrincipalListSerializer,
    PresidentListSerializer,
)

User = get_user_model()


class TeacherViewSet(viewsets.ModelViewSet):
    """
    CRUD for Teacher profiles + link/unlink to login User accounts.
    Query params:
      - q=<text>     : search in name/email/phone/subject/designation
      - linked=true  : only teachers linked to a user
      - linked=false : only teachers NOT linked to a user
    """
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Teacher.objects.all().order_by("full_name")

        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(
                Q(full_name__icontains=q)
                | Q(contact_email__icontains=q)
                | Q(contact_phone__icontains=q)
                | Q(subject__icontains=q)
                | Q(designation__icontains=q)
            )

        linked = self.request.query_params.get("linked")
        if linked is not None:
            is_linked = str(linked).lower() in ("1", "true", "yes", "y")
            if is_linked:
                qs = qs.filter(user__isnull=False)
            else:
                qs = qs.filter(user__isnull=True)

        return qs

    @action(detail=True, methods=["post"], url_path="link-user", permission_classes=[IsAuthenticated])
    def link_user(self, request, pk=None):
        """
        Link this teacher profile to an existing User (role should be 'Teacher').
        Body: { "user_id": <int> }
        """
        teacher = self.get_object()
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Optional: guard that the user is a Teacher account
        role = (getattr(user, "role", "") or "").lower()
        if role != "teacher":
            return Response({"detail": "Selected user is not a Teacher."}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce one-to-one: if this user is already linked to a different teacher, block
        existing = getattr(user, "teacher_profile", None)
        if existing and existing.id != teacher.id:
            return Response({"detail": "This user is already linked to another teacher profile."},
                            status=status.HTTP_400_BAD_REQUEST)

        teacher.user = user
        teacher.save()
        return Response(TeacherSerializer(teacher).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="unlink-user", permission_classes=[IsAuthenticated])
    def unlink_user(self, request, pk=None):
        """
        Unlink any associated User account from this teacher profile.
        """
        teacher = self.get_object()
        teacher.user = None
        teacher.save()
        return Response(TeacherSerializer(teacher).data, status=status.HTTP_200_OK)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all().order_by("full_name")
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by("class_name", "section", "full_name")
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


class PrincipalListViewSet(viewsets.ModelViewSet):
    queryset = PrincipalList.objects.all().order_by("-to_date")
    serializer_class = PrincipalListSerializer
    permission_classes = [IsAuthenticated]


class PresidentListViewSet(viewsets.ModelViewSet):
    queryset = PresidentList.objects.all().order_by("-to_date")
    serializer_class = PresidentListSerializer
    permission_classes = [IsAuthenticated]
