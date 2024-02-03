from django.shortcuts import render
import os
from openai import OpenAI
from dotenv import load_dotenv
from django.http import HttpResponseRedirect
from .models import DataUpload, RequirementsList, RequirementDetail
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

# Class for the functionalities of connecting to the OpenAI API, generating content and displaying content in the UI
class RequirementGen:

    # Loads environment variables from .env where the API key is stored
    load_dotenv()

    # Retrieves value from the environment variable "OPENAI_API_KEY"
    api_key = os.environ.get("OPENAI_API_KEY")

    # Intializes instance of the OpenAI class to interact with the OpenAI API and passes the api key
    client = OpenAI(api_key=api_key)

    # Creates details for the specific requirements using GPT
    def createUserStory():
        # Gets all DB entries and saves them
        requirements = RequirementsList.objects.all()

        # Template showing how GPT should generate requirements
        output_template = """
        Description:
        {User Story}
        \n
        Acceptance Criteria:
        {Acceptance Criteria 1}
        {Acceptance Criteria 2}
        {Acceptance Criteria 3}
        """

        # Handles connection to the OpenAI API, gets responses and saves them
        if RequirementGen.api_key is not None:

            # Gets a requirement of the DB and saves the name and description
            for requirement in requirements:
                requirement_name = requirement.requirementName
                requirement_description = requirement.requirementDescription

                # Handles the actual interaction with the OpenAI API
                # A context, the prompt of the user, model specifications, token number and temperature are configured
                chatbot_response = RequirementGen.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Use the following already generated information such as Requirement name: " + requirement_name + "and requirement description: " + requirement_description + "in combination with this data input: " + RequirementGen.getRecentUpload()
                        },
                        {
                            "role": "user",
                            "content": "Generate a user story description and three acceptance criteria requirements and output them in a structured way by using this template" + output_template + "and by using the provided input data and information. The user story description should not be longer then two sentences. Do not add any information more than the template defines."
                        }
                    ],
                    model="gpt-3.5-turbo-1106",
                    max_tokens=300,
                    temperature=1,
                )

                # The necessary part of the response is chosen and saved
                response = chatbot_response.choices[0].message.content
                
                # Splits response into the data items specified in models.py and cleanes the data before saving in the db
                requirement_story, requirement_criteria = response.split("Acceptance Criteria:")
                requirement_story = requirement_story.replace("Description:", "").strip()
                requirement_criteria = requirement_criteria.strip()

                # Identifies specific requirement entry and assigns the data to the entry in the DB
                requirements_list = RequirementsList.objects.get(requirementID=requirement.requirementID)
                requirement_detail = RequirementDetail(reqUserStory=requirement_story, reqAcceptanceCriteria=requirement_criteria)
                requirement_detail.requirementID = requirements_list
                requirement_detail.save()

    # Gets the requirement identified through the primary key and the details generated through GPT
    def getRequirementsDetail(request, pk):
        requirement = get_object_or_404(RequirementDetail, requirementID=pk)
        return render(request, "GPTCommunication/detailed_requirement.html", {
            "requirement": requirement
        })

    # Searches for recent upload and gives the content back if it exists otherwise it gives an error
    def getRecentUpload():
        try:
            recent_upload = DataUpload.objects.order_by("-timestamp")[0]
            if recent_upload is not None:
                file_path = recent_upload.inputData.path

            with open(file_path, "r") as file:
                data = file.read()
                return data
        except IndexError:
            print("No file uploaded!")
        except FileNotFoundError:
            print("File not found!")
        except IOError:
            print("Error while reading the file!")

    # Creates a requirement list by using the input
    def createRequirementsList(request):

        # Template showing how to generate requirements
        output_template = """
        Requirement 1 - {Requirement name}
        {Requirement description}
        \n
        Requirement 2 - {Requirment name}
        {Requirement description}
        \n
        Requirement 3 - {Requirment name}
        {Requirement description}
        \n
        Requirement 4 - {Requirment name}
        {Requirement description}
        \n
        ...
        """
                
        # Handles user input via form, prompting and displaying actual response from the api
        if RequirementGen.api_key is not None:

            if RequirementGen.getRecentUpload() is not None:

                # Handles the actual interaction with the OpenAI API
                # A context, the prompt of the user, model specifications, token number and temperature are configured
                chatbot_response = RequirementGen.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an assistant to a requirements engineer. Use the following input data to serve the engineer: " + RequirementGen.getRecentUpload()
                        },
                        {
                            "role": "user",
                            "content": "Suggest three (3) requirements and output them in a structured way by using this template" + output_template + "and by using the provided input data. Requirement description should not be longer then two senctences. Do not add any information more than the template defines."
                        }
                    ],
                    model="gpt-3.5-turbo-1106",
                    max_tokens=300,
                    temperature=1,
                )

                # The necessary part of the response is chosen and saved
                response = chatbot_response.choices[0].message.content

                # Calls function to write requirements into the db
                RequirementGen.requirementFill(response)

                # Calls function to create and write user stories and safe them in the db
                RequirementGen.createUserStory()        

                # Returns response to the template, the template displays it on the UI
                return render(request, "GPTCommunication/reqgen.html", {
                    "response": response
                })
            
            if RequirementGen.getRecentUpload() is None:
                return render(request, "GPTCommunication/reqgen.html", {
                    "NoFileNoReq" : "NoFileNoReq"
                })

    # Handles the general fields shown to the user and triggers the requirements list creation
    def handleProcess(request): 
        if request.method == "POST":

            # Checks if the upload form was used to upload a data input and saves input in the DB
            if "upload_form" in request.POST:
                upload_file = request.FILES.get("file")

                if upload_file:
                    data = DataUpload(inputData=upload_file)
                    data.save()
                else:
                    return render(request, "GPTCommunication/reqgen.html", {
                        "NoFile": "NoFile"
                    })

            # Checks if the interaction form was used to generate requirements based on the input data and triggers function to generate them
            if "interaction_form" in request.POST:
                return RequirementGen.createRequirementsList(request)

        # If no api key found or the request method is not POST it shows the html template again
        return render(request, "GPTCommunication/reqgen.html")

    # Function to split the requirements into parts and save them into the DB
    def requirementFill(requirement_text):

        # Splits overall requirements text into smaller junctions and saves them
        requirements = requirement_text.strip().split("\n\n")

        # Iterates through each junction and save the name and description of a requirement as well as cleanes data
        for requirement in requirements:
            name, description = requirement.split("\n", 1)
            name = name.strip()
            description = description.strip()

            # Writes attributes into the db
            requirements_list = RequirementsList(requirementName=name, requirementDescription=description)
            requirements_list.save()      

# Class for the functionality of showing generated requirements in the UI
class RequirementEdit:
    # Gets requirements from the DB and displays them using the template
    def showRequirements(request):
        requirements = RequirementsList.objects.all()
        return render(request, "GPTCommunication/requirements.html", {
            "requirements": requirements
        })

# Class for the functionality of deleting requirement entries by users in the UI 
class RequirementDelete(DeleteView):
    model = RequirementsList
    template_name = "GPTCommunication/requirements.html"
    success_url = reverse_lazy("Requirements")

# Overwrites get function so that object is deleted first before the success url is called
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)
    
class SoleDisplay:
    # Function to show the home screen
    def showHome(request):
        return render(request, "GPTCommunication/reqgen.html")

    # Redirects from "" to home
    def redirectToHome(request):
        return HttpResponseRedirect("/home")
