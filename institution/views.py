from django.shortcuts import render
from rest_framework import viewsets
from django.db.models import Q
from .models import InstitutionInfo, PrincipalVicePrincipal,ManagingCommitteeMember, Notice
from .serializers import InstitutionInfoSerializer, PrincipalVicePrincipalSerializer, ManagingCommitteeMemberSerializer,NoticeSerializer


# Try to import Teacher model; if not available, keep None and fall back to Group check
try:
    # ✅ adjust this path to wherever your Teacher model actually is
    from academics.models import Teacher
except Exception:
    Teacher = None

from django.contrib.auth.models import Group
# Create your views here.

class InstitutionInfoViewSet(viewsets.ModelViewSet):
    queryset = InstitutionInfo.objects.all()
    serializer_class = InstitutionInfoSerializer
    


class PrincipalVicePrincipalViewSet(viewsets.ModelViewSet):
    queryset = PrincipalVicePrincipal.objects.all()
    serializer_class = PrincipalVicePrincipalSerializer



class ManagingCommitteeMemberViewSet(viewsets.ModelViewSet):
    queryset = ManagingCommitteeMember.objects.all()
    serializer_class = ManagingCommitteeMemberSerializer


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all().order_by("-id")
    serializer_class = NoticeSerializer

    def _is_teacher_user(self, user):
        """
        True if user is a teacher by model relation or group membership.
        """
        if not user or not user.is_authenticated:
            return False
        if Teacher is not None:
            try:
                if Teacher.objects.filter(user=user).exists():
                    return True
            except Exception:
                # don’t crash view if Teacher lookup errors
                pass
        # Fallback via group membership (case-insensitive)
        return user.groups.filter(name__iexact="teacher").exists()

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params
        user = self.request.user

        # 1) Explicit category filter (e.g. ?category=teacher)
        cat = (q.get("category") or "").strip()
        if cat:
            return qs.filter(category__iexact=cat)

        # 2) Optional override to include teacher notices
        include_teacher = (q.get("include_teacher") or "").strip() in {"1", "true", "True"}

        # 3) Visibility rules
        if not user.is_authenticated:
            # anonymous users never see teacher notices
            return qs.exclude(category__iexact="teacher")

        if user.is_staff or self._is_teacher_user(user):
            # staff/teachers: full list unless they explicitly exclude
            if include_teacher:
                return qs
            # default remains full as well; keep return qs for clarity
            return qs

        # students/others: hide teacher notices
        return qs.exclude(category__iexact="teacher")
