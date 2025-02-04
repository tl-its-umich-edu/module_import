import random, logging
import string
import django.contrib.auth
from django.conf import settings
from django.shortcuts import redirect, render
from lti_tool.views import LtiLaunchBaseView
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from decouple import config

import canvasapi

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import ModuleItemSerializer

logger = logging.getLogger(__name__)

@api_view(['POST'])
def add_module_items(request):
    canvas = canvasapi.Canvas(config('canvas_api_url', ''), config('canvas_api_key',''))
    
    if request.method == 'POST':
        logger.info(f"Request data: {request.data}")
        for itemId in request.data['modules']:
            logger.info(f"Item id: {itemId}")
            # the itemId is of format courseId_moduleId_moduleItemId
            # parse out the courseId, moduleId and moduleItemId
            courseId, moduleId, moduleItemId = itemId.split('_')
            logger.info(f"Course Id: {courseId} Module Id: {moduleId} Module Item Id: {moduleItemId}")
            
            # get the module item
            course = canvas.get_course(int(courseId))
            module = course.get_module(int(moduleId))
            moduleItem = module.get_module_item(int(moduleItemId))
            logger.info(f"Module Item: {moduleItem.title} {moduleItem.module_id} {moduleItem.indent} {moduleItem.type}")



        '''
        serializer = ModuleItemSerializer(data=request.data)
        if serializer.is_valid():
            modules = serializer.validated_data['modules']
            logger.info(f"Modules: {modules}")
            # Perform action with the modules
            # For example, save them to the database or process them
            return Response({'message': 'Modules added successfully', 'modules': modules}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        '''
        return render(request, 'home.html')
        

# Create your views here.
def get_home_template(request):
  params = request.GET.dict()
  return render(request, 'home.html', {'params': params})

def error(request):
    return render(request, "error.html")

def validate_custom_lti_launch_data(lti_launch):
    expected_keys = [
    "roles", "term_id", "login_id", "term_end", "course_id", "term_name", "canvas_url", 
    "term_start", "redirect_url", "course_status", "user_canvas_id", 
    "course_account_name", "course_enroll_status", "course_sis_account_id", 
    "course_canvas_account_id", 'masquerade_user_canvas_id' ]
    main_key = "https://purl.imsglobal.org/spec/lti/claim/custom"
    if main_key not in lti_launch:
        logger.error(f"LTI custom '{main_key}' variables are not configured")
        return False
    
    custom_data = lti_launch[main_key]
    missing_keys = [key for key in expected_keys if key not in custom_data]
    if missing_keys:
        logger.error(f"LTI custom variables are missing in the '{main_key}' {', '.join(missing_keys)}")
        return False
    logger.debug("All keys are present.")
    return True

def login_user_from_lti(request, launch_data):
    try:
        first_name = launch_data.get('given_name')
        last_name = launch_data.get('family_name')
        email = launch_data.get('email')
        username = launch_data['https://purl.imsglobal.org/spec/lti/claim/custom']['login_id']
        logger.info(f'the user {first_name} {last_name} {email} {username} launch the tool')
        user_obj = User.objects.get(username=username)
    except User.DoesNotExist:
        logger.warn(f'user {username} never logged into the app, hence creating the user')
        password = ''.join(random.sample(string.ascii_letters, settings.RANDOM_PASSWORD_DEFAULT_LENGTH))
        user_obj = User.objects.create_user(username=username, email=email, password=password, first_name=first_name,
                                            last_name=last_name)
    except Exception as e:
        logger.error(f'error occured while getting the user info from auth_user table due to {e}')
        return False
        
        
    try: 
        django.contrib.auth.login(request, user_obj)
    except (ValueError, TypeError, Exception)  as e:
        logger.error(f'Logging user after LTI launch failed due to {e}')
        return False
    return True


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt  # Note: Ensure CSRF token handling in production
def submit_selection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_option = data.get('selected_option')

            if selected_option:
                # Process the selected option here (e.g., save to the database)

                # get canvas course
                canvas = canvasapi.Canvas(config('canvas_api_url', ''), config('canvas_api_key',''))
                course = canvas.get_course(int(selected_option))
                # get modules of the course
                modules = course.get_modules()
                # get all module items
                module_items = []

                # a list
                module_json_array = []
                for module in modules:
                    module_json = {
                        "name": module.name, 
                        "id": module.id, 
                        "indent": 0,
                        "module_id": module.id,
                        "course_id": course.id,
                        "type": "module",
                        }
                    module_json_array.append(module_json)
                    for module_item in module.get_module_items():
                        module_item_json = {
                            "name": module_item.title, 
                            "id": module_item.id, 
                            "indent": module_item.indent+1, 
                            "module_id": module_item.module_id,
                            "course_id": course.id, 
                            "type": module_item.type
                            }    
                        module_json_array.append(module_item_json)

                
                logger.info(f"Modules: {module_json_array}")
                return JsonResponse({'message': module_json_array})
            else:
                return JsonResponse({'error': 'No option selected'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)


class ApplicationLaunchView(LtiLaunchBaseView):
    
    def handle_resource_launch(self, request, lti_launch):
        ...  # Required. Typically redirects the users to the appropriate page.
        launch_data = lti_launch.get_launch_data()
        if not validate_custom_lti_launch_data(launch_data):
            return redirect("error")
        if not login_user_from_lti(request, launch_data):
            return redirect("error")
        return get_home_template(request)

    def handle_deep_linking_launch(self, request, lti_launch):
        ...  # Optional.

    def handle_submission_review_launch(self, request, lti_launch):
        ...  # Optional.

    def handle_data_privacy_launch(self, request, lti_launch):
        ...  # Optional.
        

