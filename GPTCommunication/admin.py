# In here the data tables (models) defined in models.py can be integrated into the admin panel,
# also with specific configurations, if necessary or desired

from django.contrib import admin
from .models import DataUpload, RequirementsList, RequirementDetail, UserData
    

# Configuration of tables and their displayment in the admin dialog
class UserDataAdmin(admin.ModelAdmin):
    list_display = ("ReqGenDecision","timestamp", )

class RequirementsListAdmin(admin.ModelAdmin):
    list_display = ("requirementID", "requirementName",)

class DataUploadAdmin(admin.ModelAdmin):
    list_display = ("timestamp",) 

class RequirementDetailAdmin(admin.ModelAdmin):
    list_display = ("requirementID",)

# Integration of the configuration and tables in general into the dialog
admin.site.register(DataUpload, DataUploadAdmin)
admin.site.register(RequirementsList, RequirementsListAdmin)
admin.site.register(RequirementDetail, RequirementDetailAdmin)
admin.site.register(UserData, UserDataAdmin)