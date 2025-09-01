from django.shortcuts import render
from rest_framework import viewsets
from .models import InstitutionInfo, PrincipalVicePrincipal,ManagingCommitteeMember, Notice
from .serializers import InstitutionInfoSerializer, PrincipalVicePrincipalSerializer, ManagingCommitteeMemberSerializer,NoticeSerializer

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
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
