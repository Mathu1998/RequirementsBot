from django.contrib import admin
from .models import DataUpload, RequirementsList, RequirementDetail
    

# Configuration of tables and their displayment in the admin dialog
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