from django.urls import path
from .views import BcoObjectsCreate, BcoObjectsByToken, ApiDescription, DraftObjectById, PublishedObjectById, CustomAuthToken, NewAccount, ActivateAccount

# Token-based authentication.
# Source: https://www.django-rest-framework.org/api-guide/authentication/#by-exposing-an-api-endpoint

# Validate an object.
# (POST) bco/objects/validate/

# Describe what's available on this API.
# (GET) api/description/

# Create an object.
# (POST) bco/objects/create/

# Read an object.
# (POST) bco/objects/read/

# Describe the permissions associated with an API key.
# (POST) api/account/permissions/

# Retrieve an object directly by its URI.
# (GET) <str:object_id_root>/<str:object_id_version>

# TODO: put in re_path for all of these, especially user
# activation and object retrieval.

urlpatterns = [
    path('api/accounts/activate/<str:username>/<str:temp_identifier>', ActivateAccount.as_view()),
    path('api/accounts/describe/', CustomAuthToken.as_view()),
    path('api/accounts/new/', NewAccount.as_view()),
    path('api/description/', ApiDescription.as_view()),  
    path('api/objects/create/', BcoObjectsCreate.as_view()),
    path('api/objects/token/', BcoObjectsByToken.as_view()),
    path('<str:object_id_root>/<str:object_id_version>', PublishedObjectById.as_view()),
    path('<str:draft_object_id>', DraftObjectById.as_view())
]

# path('bco/objects/validate/', BcoObjectsValidate.as_view()),
# path('api/account/permissions/', ApiAccountPermissions.as_view()),

# Future URLs:  account/services -> which services are available for your account?
# split bco/objects/create into multiple URLs?
# api/description/databases -> describe the available databases
# api/description/validations/schema -> what are the available templates for this API?
# path('api/description/validations/schema/', BcoGetObject.as_view()),
