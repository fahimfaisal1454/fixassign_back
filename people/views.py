from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from academics.models import TimetableEntry 
from django.db.models import Exists, OuterRef
from .models import Teacher, Staff, Student, PrincipalList, PresidentList
from .serializers import (
    TeacherSerializer,
    StaffSerializer,
    StudentSerializer,
    PrincipalListSerializer,
    PresidentListSerializer,
  
)


User = get_user_model()

@api_view(["GET"])
@permission_classes([IsAuthenticated])  # or AllowAny if you want it public
def check_username(request):
    username = request.query_params.get("username", "").strip().lower()
    if not username:
        return Response({"available": False, "detail": "Username required"}, status=status.HTTP_400_BAD_REQUEST)

    exists = User.objects.filter(username__iexact=username).exists()
    return Response({"available": not exists})

# -------------------------------
# Teacher
# -------------------------------
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
            return Response(
                {"detail": "This user is already linked to another teacher profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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


# -------------------------------
# Staff
# -------------------------------
class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all().order_by("full_name")
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]



class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            Student.objects
            .select_related("class_name", "section", "user")
            .order_by("class_name__name", "section__name", "roll_number", "full_name")
        )

        user = self.request.user

        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            pass
        else:
            teacher = getattr(user, "teacher_profile", None)
            if not teacher:
                teacher = Teacher.objects.filter(user=user).first()

            if teacher:
                qs = qs.filter(
                    Exists(
                        TimetableEntry.objects.filter(
                            teacher=teacher,
                            class_name_id=OuterRef("class_name_id"),
                            section_id=OuterRef("section_id"),
                        )
                    )
                )
            else:
                student_profile = getattr(user, "student_profile", None)
                if not student_profile:
                    student_profile = Student.objects.filter(user=user).first()

                if student_profile:
                    qs = qs.filter(pk=student_profile.pk)
                else:
                    qs = Student.objects.none()

        qp = self.request.query_params
        q = qp.get("q")
        class_id = qp.get("class_id")
        section_id = qp.get("section_id")
        linked = qp.get("linked")

        if q:
            qs = qs.filter(full_name__icontains=q)
        if class_id:
            qs = qs.filter(class_name_id=class_id)
        if section_id:
            qs = qs.filter(section_id=section_id)
        if linked is not None:
            is_linked = str(linked).lower() in ("1", "true", "yes", "y")
            qs = qs.filter(user__isnull=not is_linked)

        return qs

    @action(detail=True, methods=["post"], url_path="link-user")
    def link_user(self, request, pk=None):
        student = self.get_object()
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        role = getattr(user, "role", None)
        if role and str(role).lower() != "student":
            return Response({"detail": "Selected user is not a Student."}, status=status.HTTP_400_BAD_REQUEST)

        existing = getattr(user, "student_profile", None)
        if not existing:
            existing = Student.objects.filter(user=user).first()

        if existing and existing.id != student.id:
            return Response(
                {"detail": "This user is already linked to another student profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student.user = user
        student.save(update_fields=["user"])
        return Response(StudentSerializer(student).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="unlink-user")
    def unlink_user(self, request, pk=None):
        student = self.get_object()
        student.user = None
        student.save(update_fields=["user"])
        return Response(StudentSerializer(student).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        student = Student.objects.filter(user=request.user).first()
        if not student:
            return Response({"detail": "No student profile linked."}, status=status.HTTP_404_NOT_FOUND)
        return Response(StudentSerializer(student).data, status=status.HTTP_200_OK)


# -------------------------------
# Principal & President
# -------------------------------
class PrincipalListViewSet(viewsets.ModelViewSet):
    queryset = PrincipalList.objects.all().order_by("-to_date")
    serializer_class = PrincipalListSerializer
    permission_classes = [IsAuthenticated]


class PresidentListViewSet(viewsets.ModelViewSet):
    queryset = PresidentList.objects.all().order_by("-to_date")
    serializer_class = PresidentListSerializer
    permission_classes = [IsAuthenticated]
