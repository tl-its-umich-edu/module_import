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

canvas = canvasapi.Canvas(config('CANVAS_API_URL', ''), config('CANVAS_API_KEY',''))

@api_view(['POST'])
def add_module_items(request):
    if request.method == 'POST':
        logger.debug(f"Request data: {request.data}")

        # target course id
        course_id = request.data['course_id']
        target_course = canvas.get_course(int(course_id))

        for itemId in request.data['modules']:
            logger.debug(f"Item id: {itemId}")
            # the itemId is of format courseId_moduleId_moduleItemId
            # parse out the courseId, moduleId and moduleItemId
            courseId, moduleId, moduleItemId = itemId.split('_')
            logger.info(f"Course Id: {courseId} Module Id: {moduleId} Module Item Id: {moduleItemId}")
            
            # get the module item
            course = canvas.get_course(int(courseId))
            module = course.get_module(int(moduleId))
            moduleItem = module.get_module_item(int(moduleItemId))
            logger.info(f"Module Item: {moduleItem.title} {moduleItem.module_id} {moduleItem.indent} {moduleItem.type}")

            # Step1: add the module item to the target course
            # check whether the module exists in the target course
            target_module = None
            for existing_module in target_course.get_modules():
                if existing_module.name == module.name:
                    target_module = existing_module
                    break
            if not target_module:
                target_module = target_course.create_module(module={"name": module.name})

            # Step 2: create the content linked to the module item
            # new content id after copying the content
            new_content_id = None
            # page url if the module item is a page
            page_url = None
            # get the type of module item
            type = moduleItem.type
            if type in ['File', 'Discussion', 'Assignment', 'Quiz', 'ExternalTool']:
                # get the content_id first
                content_id = moduleItem.content_id

                if type == 'File':
                    content = course.get_file(content_id)
                    # make a copy of the content file in the target course
                    new_file = target_course.upload(content.display_name, content.get_contents())
                    new_content_id = new_file.id
                elif type == 'Discussion':
                    content = course.get_discussion_topic(content_id)
                    # make a copy of the discussion in the target course
                    new_discussion = target_course.create_discussion_topic(
                        title=content.title,
                        message=content.message,
                        published=False,
                        allow_rating=content.allow_rating,
                        lock_at=content.lock_at,
                        pinned=content.pinned,
                        position_after=content.position_after,
                        position_before=content.position_before,
                        require_initial_post=content.require_initial_post,
                        delayed_post_at=content.delayed_post_at,
                        podcast_enabled=content.podcast_enabled,
                        podcast_has_student_posts=content.podcast_has_student_posts,
                        group_category_id=content.group_category_id,
                        assignment=content.assignment,
                        is_section_specific=content.is_section_specific,
                        user_name=content.user_name,
                        attachment=content.attachment,
                        locked=content.locked,
                        locked_for_user=content.locked_for_user,
                        lock_info=content.lock_info,
                        lock_explanation=content.lock_explanation
                    )
                    new_content_id = new_discussion.id
                elif type == 'Assignment':
                    content = course.get_assignment(content_id)
                    # make a copy of the assignment in the target course
                    # make a copy of the assignment in the target course
                    assignment_data = {
                        "name": content.name,
                        "description": content.description,
                        "points_possible": content.points_possible,
                        "due_at": content.due_at,
                        "lock_at": content.lock_at,
                        "unlock_at": content.unlock_at,
                        "course_id": target_course.id,
                        "assignment_group_id": content.assignment_group_id,
                        "grading_type": content.grading_type,
                        "submission_types": content.submission_types,
                        "integration_data": content.integration_data,
                        "peer_reviews": content.peer_reviews,
                        "automatic_peer_reviews": content.automatic_peer_reviews,
                        "position": content.position,
                        "grade_group_students_individually": content.grade_group_students_individually,
                        "anonymous_peer_reviews": content.anonymous_peer_reviews,
                        "group_category_id": content.group_category_id,
                        "post_to_sis": content.post_to_sis,
                        "moderated_grading": content.moderated_grading,
                        "omit_from_final_grade": content.omit_from_final_grade,
                        "intra_group_peer_reviews": content.intra_group_peer_reviews,
                        "anonymous_instructor_annotations": content.anonymous_instructor_annotations,
                        "anonymous_grading": content.anonymous_grading,
                        "graders_anonymous_to_graders": content.graders_anonymous_to_graders,
                    }
                    # Remove lti_context_id if it exists
                    assignment_data.pop('lti_context_id', None)
                    new_assignment = target_course.create_assignment(assignment=assignment_data)
                    new_content_id = new_assignment.id
                elif type == 'Quiz':
                    content = course.get_quiz(content_id)
                    # make a copy of the quiz in the target course
                    quiz = target_course.create_quiz(
                        quiz={
                            "title": content.title,
                            "description": content.description,
                            "quiz_type": content.quiz_type,
                            "assignment_group_id": content.assignment_group_id,
                            "time_limit": content.time_limit,
                            "shuffle_answers": content.shuffle_answers,
                            "hide_results": content.hide_results,
                            "show_correct_answers": content.show_correct_answers,
                            "show_correct_answers_last_attempt": content.show_correct_answers_last_attempt,
                            "show_correct_answers_at": content.show_correct_answers_at,
                            "hide_correct_answers_at": content.hide_correct_answers_at,
                            "allowed_attempts": content.allowed_attempts,
                            "scoring_policy": content.scoring_policy,
                            "one_question_at_a_time": content.one_question_at_a_time,
                            "question_count": content.question_count,
                            "points_possible": content.points_possible,
                            "cant_go_back": content.cant_go_back,
                            "access_code": content.access_code,
                            "ip_filter": content.ip_filter,
                            "due_at": content.due_at,
                            "lock_at": content.lock_at,
                            "unlock_at": content.unlock_at,
                            "published": False,
                            "one_time_results": content.one_time_results,
                            "only_visible_to_overrides": content.only_visible_to_overrides,
                        }
                    )
                    new_content_id = quiz.id
                elif type == 'ExternalTool':
                    content = course.get_external_tool(content_id)
                    # make a copy of the external tool in the target course
                    external_tool = target_course.create_external_tool(
                        external_tool={
                            "name": content.name,
                            "consumer_key": content.consumer_key,
                            "shared_secret": content.shared_secret,
                            "url": content.url,
                            "domain": content.domain,
                            "privacy_level": content.privacy_level,
                            "custom_fields": content.custom_fields,
                            "editor_button": content.editor_button,
                            "homework_submission": content.homework_submission,
                            "resource_selection": content.resource_selection,
                            "course_navigation": content.course_navigation,
                            "account_navigation": content.account_navigation,
                            "user_navigation": content.user_navigation,
                            "editor_button_new_window": content.editor_button_new_window,
                            "homework_submission_new_window": content.homework_submission_new_window,
                            "resource_selection_new_window": content.resource_selection_new_window,
                            "course_navigation_new_window": content.course_navigation_new_window,
                            "account_navigation_new_window": content.account_navigation_new_window,
                            "user_navigation_new_window": content.user_navigation_new_window,
                            "launch_url": content.launch_url,
                            "icon_url": content.icon_url,
                            "text": content.text,
                            "custom_params": content.custom_params,
                            "not_selectable": content.not_selectable,
                            "oauth_compliant": content.oauth_compliant,
                            "resource_selection_ids": content.resource_selection_ids,
                            "course": target_course
                        }
                    )
                    new_content_id = external_tool.id
            else:
                if type == 'Page':
                    content = course.get_page(moduleItem.page_url)
                    # make a copy of the page in the target course
                    new_page = target_course.create_page(
                        wiki_page={
                            "title": content.title,
                            "body": content.body,
                            "editing_roles": content.editing_roles,
                            "published": False,
                            "front_page": content.front_page,
                        }
                    )
                    page_url = new_page.url
            # Step 3: create the module item
            target_module_item = target_module.create_module_item(
                module_item = {
                    "type": moduleItem.type,
                    "content_id": new_content_id,
                    "title": moduleItem.title,
                    "position": moduleItem.position,
                    "indent": moduleItem.indent,
                    "page_url": page_url,
                    "external_url": moduleItem.external_url if hasattr(moduleItem, 'external_url') else None,
                    "new_tab": moduleItem.new_tab if hasattr(moduleItem, 'new_tab') else None,
                    "completion_requirement": moduleItem.completion_requirement if hasattr(moduleItem, 'completion_requirement') else None,
                    "published": False,
                    "iframe": moduleItem.iframe if hasattr(moduleItem, 'iframe') else None,
                }
            )
        return Response({'message': 'Module items added successfully'}, status=status.HTTP_200_OK)
        

# Create your views here.
def get_home_template(request, lti_launch_params=None):
    params = request.GET.dict()
    # array of template courses
    template_courses = []
    # get the list of template courses from config
    template_course_ids_string = config('TEMPLATE_COURSE_IDS', default=None)
    if template_course_ids_string:
        template_course_ids = template_course_ids_string.split(',')
        for tempate_course_id in template_course_ids:
            tempate_course = canvas.get_course(int(tempate_course_id))
            template_courses.append(
                {"id": tempate_course.id,
                 "name": tempate_course.name})
    # get course_id from lti_launch_params
    course_id = None
    if lti_launch_params:
        course_id = lti_launch_params['https://purl.imsglobal.org/spec/lti/claim/custom']['course_id']
    return render(
                    request,
                    'home.html',
                    {
                        'params': params,
                        'course_id': course_id,
                        'template_courses': template_courses
                    }
                )

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
        return get_home_template(request, launch_data)

    def handle_deep_linking_launch(self, request, lti_launch):
        ...  # Optional.

    def handle_submission_review_launch(self, request, lti_launch):
        ...  # Optional.

    def handle_data_privacy_launch(self, request, lti_launch):
        ...  # Optional.
        

