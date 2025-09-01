from django.contrib import admin
from .models import InstitutionInfo, PrincipalVicePrincipal, ManagingCommitteeMember, Notice

admin.site.register(InstitutionInfo)
admin.site.register(PrincipalVicePrincipal)
admin.site.register(ManagingCommitteeMember)
admin.site.register(Notice)