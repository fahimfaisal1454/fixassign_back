from django.db import transaction
from django.db.models import Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ClassName, Subject, Section, ClassSubject
from .serializers import (
    ClassNameSerializer, SubjectSerializer,
    SectionSerializer,
    ClassSubjectSerializer, ClassSubjectListSerializer,
    BulkAssignPayloadSerializer,
)


# -------- Sections --------
class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all().order_by("name")
    serializer_class = SectionSerializer


# -------- Classes --------
class ClassNameViewSet(viewsets.ModelViewSet):
    """
    Supports:
      - GET /class-names/?year=2025  -> filter by year
      - POST {name, year, sections:[ids]} -> create class for a year
    """
    serializer_class = ClassNameSerializer

    def get_queryset(self):
        qs = ClassName.objects.prefetch_related("sections").order_by("year", "name")
        year = self.request.query_params.get("year")
        if year:
            try:
                qs = qs.filter(year=int(year))
            except ValueError:
                pass
        return qs

    @action(detail=False, methods=["get"])
    def years(self, request):
        """
        Small helper for frontend: list available years, newest first.
        GET /class-names/years/
        """
        years = (ClassName.objects.values_list("year", flat=True)
                 .order_by("-year")
                 .distinct())
        return Response(list(years))


# -------- Subjects --------
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().select_related("class_name").order_by("class_name__name", "name")
    serializer_class = SubjectSerializer

    # ?class=<id> filter to fetch only the subjects for a class
    def get_queryset(self):
        qs = super().get_queryset()
        class_id = self.request.query_params.get("class") or self.request.query_params.get("class_id")
        if class_id:
            qs = qs.filter(class_name_id=class_id)
        return qs


# -------- Assigned Subjects (ClassSubject) --------
class ClassSubjectViewSet(viewsets.ModelViewSet):
    queryset = (
        ClassSubject.objects
        .select_related("class_name", "section", "subject", "teacher")
        .order_by("class_name__name", "section__name", "order", "subject__name")
    )
    serializer_class = ClassSubjectSerializer

    # list uses richer serializer for convenience fields (names, flags)
    def list(self, request, *args, **kwargs):
        class_id = request.query_params.get("class_id")
        qs = self.get_queryset()
        if class_id:
            qs = qs.filter(class_name_id=class_id)

        page = self.paginate_queryset(qs)
        serializer = ClassSubjectListSerializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-assign")
    def bulk_assign(self, request):
        """
        POST body:
        {
          "class_id": 1,
          "section_ids": [2,3],
          "subject_ids": [10,11],
          "teacher_id": null
        }
        Creates ClassSubject if not existing for each (section, subject).
        """
        payload = BulkAssignPayloadSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        class_id = payload.validated_data["class_id"]
        section_ids = payload.validated_data["section_ids"]
        subject_ids = payload.validated_data["subject_ids"]
        teacher_id = payload.validated_data.get("teacher_id")

        # sanity: ensure sections belong to the class & subjects belong to the class
        cls = ClassName.objects.prefetch_related("sections").get(id=class_id)
        valid_section_ids = set(cls.sections.values_list("id", flat=True))
        for sid in section_ids:
            if sid not in valid_section_ids:
                return Response(
                    {"detail": f"Section id {sid} is not attached to class id {class_id}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        valid_subject_ids = set(Subject.objects.filter(class_name_id=class_id).values_list("id", flat=True))
        for sub in subject_ids:
            if sub not in valid_subject_ids:
                return Response(
                    {"detail": f"Subject id {sub} does not belong to class id {class_id}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        created = 0
        skipped = 0
        with transaction.atomic():
            for sid in section_ids:
                for sub in subject_ids:
                    # uniqueness is (section, subject)
                    obj, was_created = ClassSubject.objects.get_or_create(
                        class_name_id=class_id,
                        section_id=sid,
                        subject_id=sub,
                        defaults={"teacher_id": teacher_id},
                    )
                    if was_created:
                        created += 1
                    else:
                        skipped += 1

        return Response({"created": created, "skipped_existing": skipped})
