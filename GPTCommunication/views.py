# In here the view functions were defined, which are triggered by different activities and urls.

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

    # Creates details for specific requirements using GPT
    def createUserStory():
        # Gets all DB entries and saves them in a variable
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

        # The following code handles the connection to the OpenAI API, gets responses and saves responses
        # Condition to go further is that API Key is evident
        if RequirementGen.api_key is not None:

            # Gets a requirement of the DB and saves the name and description
            for requirement in requirements:
                requirement_name = requirement.requirementName
                requirement_description = requirement.requirementDescription

                # Handles the actual interaction with the OpenAI API, gives the stored information about the requirement to the model, the uploaded file 
                # and the template to orient on, for user story generation
                # A context, the prompt of the user, model specifications, the token number and the temperature are configured
                chatbot_response = RequirementGen.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Use the following already generated information such as Requirement name: " + requirement_name + "and requirement description: " + requirement_description + "in combination with this data input: " + RequirementGen.getRecentUpload()
                        },
                        {
                            "role": "user",
                            "content": "Generate a user story description and three (3) acceptance criteria for the requirements and output them in a structured way by using this template" + output_template + "and by using the provided input data and information. The user story description should not be longer than two sentences. Do not add more information than the template defines, be precise as much as possible."
                        }
                    ],
                    model="gpt-4-1106-preview",
                    max_tokens=300,
                    temperature=0.5,
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

    # Searches for recent upload and gives the content back if it exists otherwise it throws an error
    def getRecentUpload():
        try:
            # Orders according to current timestamp and stores path, only if the db is not empty
            recent_upload = DataUpload.objects.order_by("-timestamp")[0]
            if recent_upload is not None:
                file_path = recent_upload.inputData.path

            # Reads the contents of the uploaded file
            with open(file_path, "r") as file:
                data = file.read()
                return data
            
        # Throws several errors, if necessary
        except IndexError:
            print("No file uploaded!")
        except FileNotFoundError:
            print("File not found!")
        except IOError:
            print("Error while reading the file!")

    # Creates a requirement list by using the input and initiates user story generation
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
        # Goes only further if API Key is evident
        if RequirementGen.api_key is not None:

            # Checks if the upload file section was triggered
            if RequirementGen.getRecentUpload() is not None:
                
                # Handles the actual interaction with the OpenAI API
                # The file input, number of requirements to be generated and output template are given to the model
                # A context, the prompt of the user, model specifications, the token number and the temperature are configured
                chatbot_response = RequirementGen.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an assistant to a requirements engineer. Use the following input data to serve the engineer: " + RequirementGen.getRecentUpload()
                        },
                        {
                            "role": "user",
                            "content": "Suggest three (3) requirements and output them in a structured way by using this template" + output_template + "and by using the provided input data. The requirement description should not be longer than two sentences. Do not add more information than the template defines, be precise as much as possible. The requirements should be different and not similar."
                        }
                    ],
                    model="gpt-4-1106-preview",
                    max_tokens=300,
                    temperature=0.5,
                )

                # The necessary part of the response is chosen and saved
                response = chatbot_response.choices[0].message.content

                # Calls function to split and write requirements into the db
                RequirementGen.requirementFill(response)

                # Calls function to create, write user stories, and to safe them in the db
                RequirementGen.createUserStory()        

                # Returns response to the template, the template displays it on the UI
                return render(request, "GPTCommunication/reqgen.html", {
                    "response": response
                })
            
            # Prcedure for an empty file
            # It does show the main UI to the user again
            if RequirementGen.getRecentUpload() is None:
                return render(request, "GPTCommunication/reqgen.html", {
                    "NoFileNoReq" : "NoFileNoReq"
                })

    # Handles the general fields shown to the user and triggers the requirements list creation
    def handleProcess(request):

        # Checks if POST method was triggered
        if request.method == "POST":

            # Checks if the upload form was used to upload a data input and saves input in the DB
            # By getting the file from the request and storing, if there was a file given in the request
            if "upload_form" in request.POST:
                upload_file = request.FILES.get("file")

                if upload_file:
                    data = DataUpload(inputData=upload_file)
                    data.save()

                    # Stores file path of currently uploaded file to give the file name back to the user
                    # The user will be given a status of the uploading procedure
                    file_path = DataUpload.objects.order_by("-timestamp").first().inputData.name
                    file_name = os.path.basename(file_path)

                    return render(request, "GPTCommunication/reqgen.html", {
                        "FileUploaded": "FileUploaded",
                        "FileName": file_name
                    })
                # If no file was given through the request, the template is shown again and
                # The user gets information about the status 
                else:
                    return render(request, "GPTCommunication/reqgen.html", {
                        "NoFile": "NoFile"
                    })
                
            # Needed to write the user conformation of re-generating a requirement into the db
            # So user can re-generate again
            if "ConfirmButton" in request.POST:
                userData = UserData(ReqGenDecision=0)
                userData.save()
                
                # Initiates requirement and user story generation
                return RequirementGen.createRequirementsList(request)
            
            # Needed to write the user cancelation of re-generating a requirement into the db
            # So user cannot re-generate again, the conformation pops up again next time
            if "CancelButton" in request.POST:
                userData = UserData(ReqGenDecision=0)
                userData.save()

                # Redirects user to manage requirements dialog
                return RequirementDisplay.showRequirements(request)

            # Checks if the interaction form was used to generate requirements based on the input data and triggers function to generate them
            # This following block handles the logic of regenerating or generating as well.
            # For example, it checks if the user did conform a re-generation, then it will allow that by initiating the generation...
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
                
                # Can be considered as happy path
                elif status_requirementslist == False:
                    userData = UserData(ReqGenDecision=0)
                    userData.save()

                    return RequirementGen.createRequirementsList(request)

        # If no api key found or the request method is not POST it shows the html template again
        return render(request, "GPTCommunication/reqgen.html")

    # Assisting function to split the requirements into parts and save them into the DB
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
            "requirements": requirements,
            "requirementsCount": requirements.count()
        })
    
    # Gets the requirement identified through the primary key and the details generated through GPT
    def getRequirementsDetail(request, pk):
        requirement = get_object_or_404(RequirementDetail, requirementID=pk)
        return render(request, "GPTCommunication/detailed_requirement.html", {
            "requirement": requirement
        })

# Class for the functionality of deleting requirement entries by users in the UI 
class RequirementDelete:
    # This function gets the associated rquirement by using the request of the user
    # By using the primary key it gets the requirement, and it checks which button was triggered by the user,
    # to perform the needed action such as deleting, or canceling deletion and redirecting back to the list
    # Besides this, the function is used to display the delete conformation template first
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

# Class for display functionalities    
class SoleDisplay:
    # Function to show the home screen
    def showHome(request):
        return render(request, "GPTCommunication/start.html")

    # Redirects from "" to home
    def redirectToHome(request):
        return HttpResponseRedirect("/home")
