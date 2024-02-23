from django.shortcuts import render, redirect
import os
from openai import OpenAI
from dotenv import load_dotenv
from django.http import HttpResponseRedirect
from .models import DataUpload, RequirementsList, RequirementDetail, UserData
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
        Requirement - {Requirement name}
        {Requirement description}
        \n
        Requirement - {Requirement name}
        {Requirement description}
        \n
        Requirement - {Requirement name}
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
                            "content": "Suggest three (3) requirements and output them in a structured way by using this template" + output_template + "and by using the provided input data. Requirement description should not be longer then two senctences. Do not add any information more than the template defines, but be precise as much as possible. The requirements should be different and not similar."
                        }
                    ],
                    model="gpt-4-1106-preview",
                    max_tokens=300,
                    temperature=0.5,
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

                    file_path = DataUpload.objects.order_by("-timestamp").first().inputData.name
                    file_name = os.path.basename(file_path)

                    return render(request, "GPTCommunication/reqgen.html", {
                        "FileUploaded": "FileUploaded",
                        "FileName": file_name
                    })
                else:
                    return render(request, "GPTCommunication/reqgen.html", {
                        "NoFile": "NoFile"
                    })
                
            if "ConfirmButton" in request.POST:
                userData = UserData(ReqGenDecision=1)
                userData.save()
                
                return RequirementGen.createRequirementsList(request)
                
            if "CancelButton" in request.POST:
                userData = UserData(ReqGenDecision=0)
                userData.save()

                return HttpResponseRedirect("/requirements")

            # Checks if the interaction form was used to generate requirements based on the input data and triggers function to generate them
            if "interaction_form" in request.POST:
                status_requirementslist = RequirementsList.objects.exists()
                status_userdata = UserData.objects.exists()

                if status_userdata == True:
                    recent_decision = UserData.objects.order_by("-timestamp")[0].ReqGenDecision
                else:
                    recent_decision = 0

                if status_requirementslist == True:
                    if recent_decision == 0:
                        return render(request, "GPTCommunication/generate_confirmation.html")
                    
                    if recent_decision == 1:
                        userData = UserData(ReqGenDecision=0)
                        userData.save()

                        return RequirementGen.createRequirementsList(request)
                
                elif status_requirementslist == False:
                    userData = UserData(ReqGenDecision=0)
                    userData.save()

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
class RequirementDisplay:
    # Gets requirements from the DB and displays them using the template
    def showRequirements(request):
        requirements = RequirementsList.objects.all()
        return render(request, "GPTCommunication/requirements.html", {
            "requirements": requirements
        })
    
    # Gets the requirement identified through the primary key and the details generated through GPT
    def getRequirementsDetail(request, pk):
        requirement = get_object_or_404(RequirementDetail, requirementID=pk)
        return render(request, "GPTCommunication/detailed_requirement.html", {
            "requirement": requirement
        })

# Class for the functionality of deleting requirement entries by users in the UI 
class RequirementDelete:
    def deleteRequirement(request, pk):
        requirement = RequirementsList.objects.get(requirementID=pk)
        if request.method == 'POST':
            if 'DeleteButton' in request.POST:
                requirement.delete()
                return redirect("Requirements")
            if 'CancelButton' in request.POST:
                return redirect("Requirements")
        return render(request, 'GPTCommunication/delete_confirmation.html', {
            "requirement": requirement
        })
    
class SoleDisplay:
    # Function to show the home screen
    def showHome(request):
        return render(request, "GPTCommunication/start.html")

    # Redirects from "" to home
    def redirectToHome(request):
        return HttpResponseRedirect("/home")
