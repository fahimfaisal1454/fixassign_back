# academics/api_finals.py
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

from django.db import transaction
from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from academics.models import Exam, ExamMark, GradeScale
from people.models import Student
from master.models import ClassName, Section, Subject

def round2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def band_for(score: Decimal):
    """Map a score (0-100) to active GradeScale band (letter, gpa)."""
    scale = GradeScale.objects.filter(is_active=True).first()
    if not scale:
        return ("", None)
    band = scale.bands.filter(min_score__lte=score, max_score__gte=score).first()
    if not band:
        return ("", None)
    return (band.letter, Decimal(str(band.gpa)))

class FinalizeAndPublish(APIView):
    """
    POST /api/finals/finalize_publish/
    Body:
    {
      "class_id": 1,
      "section_id": 2,
      "year": 2025,
      "parts": [
        {"exam_id": 10, "weight": 25},
        {"exam_id": 11, "weight": 25},
        {"exam_id": 12, "weight": 50}
      ],
      "name": "Final Result 2025",     # optional
      "publish": true                  # optional, default true
    }
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=403)

        # ---- Parse & validate input ----
        try:
            class_id   = int(request.data.get("class_id"))
            section_id = int(request.data.get("section_id"))
            year       = int(request.data.get("year"))
        except Exception:
            return Response({"detail": "class_id, section_id, year are required integers."},
                            status=400)

        parts = request.data.get("parts") or []
        if not isinstance(parts, list) or not parts:
            return Response({"detail": "parts must be a non-empty list of {exam_id, weight}."},
                            status=400)

        # weights must sum to 100
        try:
            total_weight = sum(int(p.get("weight", 0)) for p in parts)
        except Exception:
            return Response({"detail": "All weights must be integers."}, status=400)
        if total_weight != 100:
            return Response({"detail": f"Weights must sum to 100 (got {total_weight})."}, status=400)

        # Resolve class/section
        try:
            cls = ClassName.objects.get(id=class_id)
            sec = Section.objects.get(id=section_id)
        except ClassName.DoesNotExist:
            return Response({"detail": "Invalid class_id."}, status=400)
        except Section.DoesNotExist:
            return Response({"detail": "Invalid section_id."}, status=400)

        # Ensure all exams exist and belong to the same class/section (optional but safer)
        exam_ids = [int(p["exam_id"]) for p in parts if "exam_id" in p]
        exams = list(Exam.objects.filter(id__in=exam_ids))
        if len(exams) != len(exam_ids):
            return Response({"detail": "One or more exam_id not found."}, status=400)

        # ---- Gather cohort ----
        students = list(Student.objects.filter(class_name=cls, section=sec))
        subjects = list(Subject.objects.filter(class_name=cls))
        if not students or not subjects:
            return Response({"detail": "No students or subjects found for this class/section."},
                            status=400)

        # ---- Pull all marks for all parts in one go ----
        # Prefetch marks per exam for speed
        exams = list(
            Exam.objects.filter(id__in=exam_ids)
            .prefetch_related(Prefetch("marks", queryset=ExamMark.objects.all(), to_attr="all_marks"))
        )

        # Build lookup: (exam_id, student_id, subject_id) -> score
        score_map = {}
        for ex in exams:
            for m in getattr(ex, "all_marks", []):
                score_map[(ex.id, m.student_id, m.subject_id)] = Decimal(str(m.score))

        # ---- Create or get the Final exam ----
        final_name = request.data.get("name") or f"Final Result {year}"
        final_exam, created = Exam.objects.get_or_create(
            class_name=cls, section=sec, name=final_name,
            defaults={"is_published": False}
        )

        # ---- Compute & upsert marks ----
        upserts = 0
        letter_map = {}  # cache per score to avoid repeated band lookup

        for stu in students:
            for sub in subjects:
                total = Decimal("0")
                for part in parts:
                    ex_id = int(part["exam_id"])
                    w     = Decimal(str(int(part["weight"]))) / Decimal("100")
                    sc    = score_map.get((ex_id, stu.id, sub.id), Decimal("0"))
                    total += sc * w

                final_score = round2(total)

                if final_score not in letter_map:
                    L, G = band_for(final_score)
                    letter_map[final_score] = (L, G)
                L, G = letter_map[final_score]

                # Upsert ExamMark for (final_exam, stu, sub)
                mark, mk_created = ExamMark.objects.get_or_create(
                    exam=final_exam, student=stu, subject=sub,
                    defaults={"score": final_score}
                )
                if not mk_created:
                    mark.score = final_score
                # If your serializer auto-fills letter/gpa from GradeScale, you can omit the two lines below.
                if hasattr(mark, "letter") and L is not None:
                    mark.letter = L or ""
                if hasattr(mark, "gpa") and G is not None:
                    mark.gpa = G
                mark.save()
                upserts += 1

        # ---- Publish (default true) ----
        if bool(request.data.get("publish", True)):
            if not final_exam.is_published:
                final_exam.is_published = True
                final_exam.save(update_fields=["is_published"])

        return Response({
            "status": "ok",
            "final_exam_id": final_exam.id,
            "final_exam_name": final_exam.name,
            "published": final_exam.is_published,
            "upserts": upserts,
        }, status=200)
