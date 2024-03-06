from django.urls import path
from . import views

# Integration of views and match them to urls
# If an url is used it will directly call or trigger the view function associate to that, in views.py
urlpatterns = [
    path("reqgen", views.RequirementGen.handleProcess, name="ReqGen"),
    path("home", views.SoleDisplay.showHome, name="Home"),
    path("requirements", views.RequirementDisplay.showRequirements, name="Requirements"),
    path("delete/req/<int:pk>/", views.RequirementDelete.deleteRequirement, name="ConfDelete"),
    path("requirement/<int:pk>", views.RequirementDisplay.getRequirementsDetail, name="RequirementDetail"),
    path("", views.SoleDisplay.redirectToHome)
    ]
