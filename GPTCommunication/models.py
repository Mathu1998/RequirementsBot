from django.db import models

# Table to upload data inputs
class DataUpload(models.Model):
    inputData = models.FileField(upload_to="uploads")
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

# Table to upload and save through GPT generated requirements and their contents
class RequirementsList(models.Model):
    requirementID = models.IntegerField(primary_key=True)
    requirementName = models.CharField(max_length=100)
    requirementDescription = models.TextField()

    def __str__(self):
        return f"{self.requirementName} (ID: {self.requirementID})"

# Table to upload and save generated detailed information about the specific requirements
class RequirementDetail(models.Model):
    requirementID = models.ForeignKey(RequirementsList, on_delete=models.CASCADE)
    reqUserStory = models.TextField()
    reqAcceptanceCriteria = models.TextField()

    def __str__(self):
        return f"Detail for {self.requirementID.requirementName}"