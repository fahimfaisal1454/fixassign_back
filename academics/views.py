from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import FieldError
from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem, AttendanceRecord
)
from .serializers import (
    PeriodSerializer, ClassroomSerializer, TimetableEntrySerializer,
    ExamRoutineSerializer, SyllabusSerializer, ResultSerializer, RoutineSerializer,
    GalleryItemSerializer, AttendanceRecordSerializer
)
from master.models import ClassName, Subject
from people.models import Student, Teacher
from django.utils.dateparse import parse_date

# ─────────────────────────────────────────────────────────────────────────────
# Lightweight lookups for frontend (classes & subjects)
# ─────────────────────────────────────────────────────────────────────────────

class ClassNameMiniSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()

    class Meta:
        model = ClassName
        fields = ["id", "name", "sections"]

    def get_sections(self, obj):
        # Expecting a related_name like .sections
        return [{"id": s.id, "name": s.name} for s in obj.sections.all()]


class ClassNameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClassName.objects.all().order_by("name")
    serializer_class = ClassNameMiniSerializer


class SubjectMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "class_name"]


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/subjects/?class_id=ID  (preferred)
    /api/subjects/?class=ID     (fallback)
    """
    serializer_class = SubjectMiniSerializer

    def get_queryset(self):
        qs = Subject.objects.select_related("class_name").all().order_by("name")
        class_id = self.request.query_params.get("class") or self.request.query_params.get("class_id")
        if class_id:
            qs = qs.filter(class_name_id=class_id)
        return qs


# ─────────────────────────────────────────────────────────────────────────────
# Core CRUD endpointsssssss
# ─────────────────────────────────────────────────────────────────────────────

class PeriodViewSet(viewsets.ModelViewSet):
    queryset = Period.objects.all().order_by("order")
    serializer_class = PeriodSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all().order_by("name")
    serializer_class = ClassroomSerializer


class TimetableEntryViewSet(viewsets.ModelViewSet):

    queryset = (
        TimetableEntry.objects
        .select_related("class_name", "section", "subject", "teacher", "classroom")
        .all()
    )
    serializer_class = TimetableEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params

        # Accept both new + old param names
        class_name = q.get("class_name") or q.get("class_id")
        section = q.get("section") or q.get("section_id")
        subject_id = q.get("subject") or q.get("subject_id")
        user_id = q.get("user_id") or q.get("teacher")
        day = q.get("day_of_week") or q.get("day")
        classroom_id = q.get("classroom") or q.get("classroom_id")
      

        if class_name:
            qs = qs.filter(class_name_id=class_name)
        if section:
            qs = qs.filter(section_id=section)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
            
        
        if user_id:
            teacher = Teacher.objects.filter(user_id=user_id).first()
            qs = qs.filter(teacher=teacher)
            print("Filtered queryset:",list(qs.values()))
            
        if day:
            if day not in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}:
                return qs.none()
            qs = qs.filter(day_of_week=day)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        # student=me → filter by logged-in student's class & section
        if q.get("student") == "me":
            stu = Student.objects.filter(user=self.request.user).first()
            if not stu:
                return qs.none()
            qs = qs.filter(class_name=stu.class_name, section=stu.section)

        # 🔒 Default: if no teacher filter provided but logged-in user *is* a teacher
        if not user_id and not q.get("student"):
            teacher = Teacher.objects.filter(user=self.request.user).first()
            if teacher:
                qs = qs.filter(teacher=teacher)

        return qs.order_by("day_of_week", "start_time", "period")

    @action(detail=False, methods=["get"])
    def week(self, request):
        entries = self.get_queryset()
        serializer = TimetableEntrySerializer(entries, many=True)

        # Prepare dict with all days
        data_by_day = {k: [] for k in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}

        for r in serializer.data:
            day_code = r.get("day_of_week")  # 'Mon' etc
            if day_code in data_by_day:
                data_by_day[day_code].append(r)

        # Sort entries within each day
        for k, v in data_by_day.items():
            data_by_day[k] = sorted(
                v,
                key=lambda r: (
                    (r.get("start_time") or ""),
                    (r.get("period") or ""),
                ),
            )

        return Response(data_by_day)

    
class ExamRoutineViewSet(viewsets.ModelViewSet):
    queryset = ExamRoutine.objects.all()
    serializer_class = ExamRoutineSerializer


class SyllabusViewSet(viewsets.ModelViewSet):
    queryset = Syllabus.objects.all()
    serializer_class = SyllabusSerializer


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class RoutineViewSet(viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer


class GalleryItemViewSet(viewsets.ModelViewSet):
    queryset = GalleryItem.objects.all().order_by("-uploaded_at")
    serializer_class = GalleryItemSerializer




def _has_field(model, fname: str) -> bool:
    return any(getattr(f, "name", None) == fname for f in model._meta.get_fields())


class AttendanceViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"\d+"  # avoids 'roster' being parsed as a pk
    permission_classes = [IsAuthenticated]

    queryset = (
        AttendanceRecord.objects
        .select_related(
            "timetable",
            "timetable__class_name",
            "timetable__section",
            "timetable__subject",
            "timetable__teacher",
            "student",
        )
        .all()
    )
    serializer_class = AttendanceRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params

        date = q.get("date")
        timetable_id = q.get("timetable_id")
        class_id = q.get("class_name") or q.get("class_id")
        section_id = q.get("section") or q.get("section_id")
        subject_id = q.get("subject") or q.get("subject_id")
        # date_gte = q.get("date__gte")
        # date_lte = q.get("date__lte")

        if date:
            qs = qs.filter(date=date)
        if timetable_id:
            qs = qs.filter(timetable_id=timetable_id)
        if class_id:
            qs = qs.filter(timetable__class_name_id=class_id)
        if section_id:
            qs = qs.filter(timetable__section_id=section_id)
        if subject_id:
            qs = qs.filter(timetable__subject_id=subject_id)
        # if date_gte:
        #     qs = qs.filter(date__gte=date_gte)
        # if date_lte:
        #     qs = qs.filter(date__lte=date_lte)


        # default: teachers only see their own records unless a timetable is specified
        teacher = Teacher.objects.filter(user=self.request.user).first()
        if teacher and not timetable_id:
            qs = qs.filter(timetable__teacher=teacher)

        return qs

    @action(detail=False, methods=["get", "post"], url_path="roster")
    def roster(self, request):
        if request.method.lower() == "get":
            return self._roster_get(request)
        return self._roster_post(request)

    # -------- GET /attendance/roster/ --------
    def _roster_get(self, request):
        timetable_id = request.query_params.get("timetable_id")
        date = parse_date(request.query_params.get("date") or "")
        if not timetable_id or not date:
            return Response({"detail": "timetable_id and date are required."}, status=400)

        timetable = (
            TimetableEntry.objects
            .select_related("teacher", "class_name", "section", "subject")
            .filter(id=timetable_id)
            .first()
        )
        if not timetable:
            return Response({"detail": "Invalid timetable id."}, status=404)

        # auth: assigned teacher or admin
        if not request.user.is_superuser:
            teacher = getattr(timetable, "teacher", None)
            if not teacher or teacher.user_id != request.user.id:
                return Response({"detail": "Not allowed."}, status=403)

        # build student filters (works whether Student stores FK or CharField for class/section)
        student_filters = {}
        if _has_field(Student, "class_name"):
            student_filters["class_name"] = timetable.class_name
        elif _has_field(Student, "student_class"):
            student_filters["student_class"] = timetable.class_name

        if _has_field(Student, "section"):
            student_filters["section"] = timetable.section
        elif _has_field(Student, "student_section"):
            student_filters["student_section"] = timetable.section

        try:
            students = Student.objects.filter(**student_filters)
        except FieldError:
            students = Student.objects.all()

        students = students.order_by("roll_no", "id") if _has_field(Student, "roll_no") else students.order_by("id")

        # existing marks
        existing = {
            r.student_id: r
            for r in AttendanceRecord.objects.filter(timetable=timetable, date=date)
        }

        rows = []
        for s in students:
            rec = existing.get(s.id)
            rows.append({
                "student": s.id,
                "student_name": str(s),
                "status": rec.status if rec else "PRESENT",
                "remarks": rec.remarks if rec else "",
                "attendance_id": rec.id if rec else None,
            })

        def label(x):
            return getattr(x, "name", str(x))

        return Response({
            "timetable": {
                "id": timetable.id,
                "class_name": label(getattr(timetable, "class_name", "")),
                "section": label(getattr(timetable, "section", "")),
                "subject": label(getattr(timetable, "subject", "")),
            },
            "date": str(date),
            "rows": rows
        }, status=200)

    # -------- POST /attendance/roster/ --------
    def _roster_post(self, request):
        body = request.data or {}
        timetable_id = body.get("timetable") or body.get("timetable_id")
        date = parse_date((body.get("date") or "").strip())
        rows = body.get("rows")

        if not timetable_id or not date or not isinstance(rows, list):
            return Response(
                {"detail": "timetable (or timetable_id), date and rows[] are required."},
                status=400,
            )

        timetable = TimetableEntry.objects.select_related("teacher").filter(id=timetable_id).first()
        if not timetable:
            return Response({"detail": "Invalid timetable id."}, status=404)

        # auth: assigned teacher or admin
        if not request.user.is_superuser:
            teacher = getattr(timetable, "teacher", None)
            if not teacher or teacher.user_id != request.user.id:
                return Response({"detail": "Not allowed."}, status=403)

        valid_status = {"PRESENT", "ABSENT", "LATE", "EXCUSED"}
        created, updated = 0, 0

        for r in rows:
            sid = r.get("student")
            if not sid:
                continue
            status_val = (r.get("status") or "PRESENT").upper()
            if status_val not in valid_status:
                status_val = "PRESENT"
            remarks = r.get("remarks") or ""

            obj, was_created = AttendanceRecord.objects.update_or_create(
                timetable=timetable,
                date=date,
                student_id=sid,
                defaults={
                    "status": status_val,
                    "remarks": remarks,
                    "marked_by": request.user,
                },
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        return Response({"ok": True, "created": created, "updated": updated}, status=200)