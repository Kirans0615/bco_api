# Utilities
from ...models import meta_table

# Checking versioning rules
from ...models import bco

# For writing objects to the database.
from ...serializers import getGenericSerializer

# (OPTIONAL) For sending user information to userdb.
import json
import requests
from . import UserUtils

# For checking datetimes
import datetime

# For getting the model.
from django.apps import apps

# For getting object naming information.
from django.conf import settings

# For getting the API models.
from django.contrib.contenttypes.models import ContentType

# For checking for and creating users.
from django.contrib.auth.models import Group, User

# For recording the creation time.
from django.utils import timezone

# For user IDs.
import random

# Regular expressions
import re

# For user passwords.
import uuid


class DbUtils:


    # Class Description
    # -----------------

    # These methods are for interacting with our sqlite database.
    
    
    # Checking whether or not an object exists.
    def check_object_id_exists(
        self, 
        p_app_label, 
        p_model_name, 
        p_object_id
    ):

        # Simple existence check.
        # Source: https://stackoverflow.com/a/9089028
        # Source: https://docs.djangoproject.com/en/3.1/ref/models/querysets/#exists
        
        if apps.get_model(
                app_label = p_app_label, 
                model_name = p_model_name
            ).objects.filter(
                object_id = p_object_id
            ).exists():
            return None
        else:
            return 1
    


    # Checking whether or not a user exists.
    def check_user_exists(
        self, 
        p_app_label, 
        p_model_name, 
        p_email
    ):

        # Simple existence check.
        # Source: https://stackoverflow.com/a/9089028
        # Source: https://docs.djangoproject.com/en/3.1/ref/models/querysets/#exists
        
        if apps.get_model(
                app_label = p_app_label, 
                model_name = p_model_name
            ).objects.filter(
                email = p_email
            ).exists():

            return 1

        else:

            return None
    


    # Check version rules
    def check_version_rules(
        self,
        published_id
    ):
    
        # Potentially publishing a new version
        # of a published object, but we have to check to 
        # see if the provided URI exists in the publishing table.

        # We can take the exact version of the object ID OR
        # only the root version.  For example, 'http://hostname/some/other/paths/BCO_5' and 'http://hostname/some/other/paths/BCO_5/3.4' would 
        # invoke the same logic here, assuming that version 3.4 of BCO_5 is
        # the latest version.

        # Does the provided object ID exist?
        if bco.objects.filter(
            object_id = published_id
        ).exists():
        
            # The provided published object ID
            # was found, and will be used to create
            # the object ID for the new published
            # object.

            # Only the minor version is changed as the
            # API is not responsible for enforcing versioning
            # rules beyond differentiating between submissions
            # of the same root URI.
            
            # First split so that we can do some processing.
            split_up = published_id.split('/')
            
            # Get the version.
            version = split_up[-1:][0]

            # Increment the minor version.
            incremented = version.split('.')
            incremented[1] = int(incremented[1]) + 1
            incremented = incremented[0] + '.' + str(incremented[1])

            # Create the object ID.
            split_up[len(split_up)-1] = incremented
            
            # Kick back the minor-incremented object ID.
            return {
                'published_id': '/'.join(split_up)
            }

        else:

            # If the EXACT object ID wasn't found, then
            # the user may have provided either a root version
            # of the URI or a version of the same root URI.

            # If the provided version is larger
            # than the version that would be generated automatically,
            # then that provided version is used.

            # First determine whether or not the provided URI
            # only has the root or has the root and the version.

            # Should do this by using settings.py root_uri
            # information...

            # Split up the URI into the root ID and the version.
            root_uri = ''
            version = ''

            if re.match(
                r"(.*?)/[A-Z]+_(\d+)$", 
                published_id
            ):

                # Only the root ID was passed.
                root_uri = published_id
            
            elif re.match(
                r"(.*?)/[A-Z]+_(\d+)/(\d+)\.(\d+)$", 
                published_id
            ):

                # The root ID and the version were passed.
                split_up = published_id.split('/')

                root_uri = '/'.join(
                    split_up[:-1]
                )

                version = split_up[-1:]
            
            # See if the root ID even exists.

            # Note the trailing slash in the regex search to prevent
            # sub-string matches (e.g. http://127.0.0.1:8000/BCO_5 and
            # http://127.0.0.1:8000/BCO_53 would both match the regex
            # http://127.0.0.1:8000/BCO_5 if we did not have the trailing
            # slash).
            all_versions = list(
                bco.objects.filter(
                    object_id__regex = rf'{root_uri}/',
                    state = 'PUBLISHED'
                ).values_list(
                    'object_id',
                    flat = True
                )
            )

            # Get the latest version for this object if we have any.
            if len(all_versions) > 0:
                
                # There was at least one version of the root ID,
                # so now perform some logic based on whether or
                # not a version was also passed.
                
                # First find the latest version of the object.
                latest_major = 0
                latest_minor = 0

                latest_version = [
                    i.split('/')[-1:][0] for i in all_versions
                ]

                for i in latest_version:
                    
                    major_minor_split = i.split('.')
                    
                    if int(major_minor_split[0]) >= latest_major:
                        if int(major_minor_split[1]) >= latest_minor:
                            latest_major = int(major_minor_split[0])
                            latest_minor = int(major_minor_split[1])

                
                # The version provided may fail, so create a flag to
                # track this.
                failed_version = False
                
                # If the root ID and the version were passed, check
                # to see if the version given is greater than that which would 
                # be generated automatically.
                if version != '':

                    # We already have the automatically generated version
                    # number.  Now we just need to compare it with the
                    # number that was provided.
                    if int(version[0].split('.')[0]) > latest_major & int(version[0].split('.')[1]) > latest_minor:

                        latest_major = int(version[0].split('.')[0])
                        latest_minor = int(version[0].split('.')[1])
                    
                        # Write with the version provided.
                        published_id = published_id + '/' + str(latest_major) + '.' + str(latest_minor)
                    
                    else:

                        # Bad version provided.
                        failed_version = True

                else:

                    # If only the root ID was passed, find the latest
                    # version in the database, then increment the version.
                    
                    # Write with the minor version incremented.
                    published_id = published_id + '/' + str(latest_major) + '.' + str(latest_minor + 1)
                    
                # Did everything go properly with the version provided?
                if failed_version == False:
                
                    # The version was valid.
                    return {
                        'published_id': published_id
                    }
                
                else:

                    # Bad request.
                    return 'bad_version_number'

            else:

                # If all_versions has 0 length, then the
                # the root ID does not exist at all.
                # In this case, we have to return a failure flag
                # because we cannot create a version for
                # a root ID that does not exist.
                return 'non_root_id'
    



    # Checking whether or not a user exists and their 
    # temp identifier matches.
    def check_activation_credentials(
        self, 
        p_app_label, 
        p_model_name, 
        p_email, 
        p_temp_identifier
    ):

        # Simple existence check.
        # Source: https://stackoverflow.com/a/9089028
        # Source: https://docs.djangoproject.com/en/3.1/ref/models/querysets/#exists
        
        user_info = apps.get_model(
            app_label = p_app_label, 
            model_name = p_model_name
        ).objects.filter(
            email = p_email,
            temp_identifier = p_temp_identifier
        )
        
        if user_info.exists():

            # The credentials exist, but is the request timely?
            # Source: https://stackoverflow.com/a/7503368
            
            # Take the time and add 10 minutes.
            time_check = list(
                user_info.values_list(
                    'created', 
                    flat = True
                )
            )[0]
            
            # Source: https://www.kite.com/python/answers/how-to-add-hours-to-the-current-time-in-python
            time_check = time_check + datetime.timedelta(
                minutes = 10
            )

            # Crappy timezone problems.
            # Source: https://stackoverflow.com/a/25662061

            # Is the time now less than the time check?
            if datetime.datetime.now(datetime.timezone.utc) < time_check:

                # We can return that this user is OK to be activated.
                return 1
            
            else:

                # The time stamp has expired, so delete
                # the entry in new_users.
                user_info.delete()

                # We can't activate this user.
                return None

        else:

            return None
    
    


    def get_api_models(
        self
    ):

        # Get all the ACCESSIBLE models in the API.
        # Source: https://stackoverflow.com/a/9407979
        
        api_models = []

        # Define any tables to exclude here.
        exclude = ['meta', 'new_users']

        for ct in ContentType.objects.all():
            m = ct.model_class()

            if m.__module__ == 'api.models':
                if m.__name__ not in exclude:
                    api_models.append(m.__name__)
        
        # Returns flat list...
        return api_models



    def activate_account(
        self, 
        p_email
    ):

        # p_email: which e-mail to activate.
        
        # Activation means creating an entry in User.

        # To comply with GDPR, we can't keep an e-mail
        # directly.  So, split off the username part
        # of the e-mail and assign a random number.
        valid_username = False

        while valid_username == False:
            
            new_username = p_email.split('@')[0] + str(
                random.randrange(
                    1, 
                    100
                )
            )

            # Does this username exist (not likely)?
            if User.objects.filter(
                username = new_username
            ):
                
                valid_username = False
            
            else:

                valid_username = True

        # We can't use the generic serializer here because of how
        # django processes passwords.
        # Source: https://docs.djangoproject.com/en/3.2/topics/auth/default/#changing-passwords

        # The password is also randomly generated.
        new_password = uuid.uuid4().hex

        # Save the user.
        # Source: https://docs.djangoproject.com/en/3.2/topics/auth/default/#creating-users

        user = User.objects.create_user(
            new_username
        )

        # Setting the password has to be done manually in 
        # order to encrypt it.
        # Source: https://stackoverflow.com/a/39211961
        # Source: https://stackoverflow.com/questions/28347200/django-rest-http-400-error-on-getting-token-authentication-view
        user.set_password(
            new_password
        )

        # Save the user.
        user.save()

        # Automatically add the user to the bco_drafter and bco_publisher groups.
        user.groups.add(
            Group.objects.get(
                name = 'bco_drafter'
            )
        )
        user.groups.add(
            Group.objects.get(
                name = 'bco_publisher'
            )
        )

        # (OPTIONAL) Make a request to userdb on the portal so that
        # the user's information can be stored there.

        # If a token was provided with the initial request,
        # use it to make the update call to userdb.
        token = apps.get_model(
            app_label = 'api', 
            model_name = 'new_users'
        ).objects.get(
            email = p_email
        ).token

        if token is not None:
            
            # Send the new information to userdb.

            # Get the user's information from the database.
            uu = UserUtils.UserUtils()

            # Set the headers.
            # Source: https://docs.python-requests.org/en/master/user/quickstart/#custom-headers
            headers = {
                'Authorization': 'JWT ' + token,
                'Content-type': 'application/json; charset=UTF-8'
            }

            # Set the data properly.
            # Source: https://stackoverflow.com/a/56562567
            r = requests.post(
                data = json.dumps(
                    uu.get_user_info(
                        username = new_username
                    ), 
                    default = str
                ),
                headers = headers,
                url = 'http://127.0.0.1:8080/users/add_api/'
            )
        
        # Delete the record in the temporary table.
        apps.get_model(
            app_label = 'api', 
            model_name = 'new_users'
        ).objects.filter(
            email = p_email
        ).delete()

        # Return the username in a list, as this is
        # easily checked for upstream (as opposed to
        # some regex solution to check for username
        # information).
        return [new_username]

    


    # Messages associated with results.
    def messages(
        self, 
        parameters, 
        p_content = False
    ):
        
        # Define the return messages, if they don't
        # come in defined.
        definable = ['errors', 'group', 'object_id', 'object_perms', 'prefix', 'published_id', 'table', 'contents']

        for i in definable:
            if i not in parameters:
                parameters[i] = ''
        
        return {
            '200_found': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'The object with ID \'' + parameters['object_id'] + '\' was found on table \'' + parameters['table'] + '\'.',
                'content': p_content
            },
            '200_OK_group_delete': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'The group \'' + parameters['group'] + '\' was deleted.'
            },
            '200_OK_group_modify': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'The group \'' + parameters['group'] + '\' was succesfully modified.'
            },
            '200_OK_object_delete': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'The object with ID \'' + parameters['object_id'] + '\' was deleted.'
            },
            '200_OK_object_read': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'contents': parameters['contents'],
                'message': 'The object with ID \'' + parameters['object_id'] + '\' was found on the server.'
            },
            '200_OK': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'The prefix \'' + parameters['prefix'] + '\' was deleted.'
            },
            '200_OK_object_permissions': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'Permissions for the object with ID \'' + parameters['object_id'] + '\' were found on the server.',
                'object_id': parameters['object_id'],
                'permissions': parameters['object_perms']
            },
            '200_OK_object_permissions_set': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'Permissions for the object with ID \'' + parameters['object_id'] + '\' were set on the server.',
                'object_id': parameters['object_id']
            },
            '200_OK_object_publish': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'Successfully published  \'' + parameters['published_id'] + '\' on the server.',
                'published_id': parameters['published_id']
            },
            '200_prefix_update': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'The prefix \'' + parameters['prefix'] + '\' was updated.'
            },
            '200_update': {
                'request_status': 'SUCCESS', 
                'status_code': '200',
                'message': 'The object with ID \'' + parameters['object_id'] + '\' was updated.'
            },
            '201_create': {
                'request_status': 'SUCCESS', 
                'status_code': '201',
                'message': 'The object with ID \'' + parameters['object_id'] + '\' was created on the server.',
                'object_id': parameters['object_id']
            },
            '201_group_create': {
                'request_status': 'SUCCESS', 
                'status_code': '201',
                'message': 'The group \'' + parameters['group'] + '\' was successfully created.'
            },
            '201_prefix_create': {
                'request_status': 'SUCCESS', 
                'status_code': '201',
                'message': 'The prefix \'' + parameters['prefix'] + '\' was successfully created.'
            },
            '400_bad_request': {
                'request_status': 'FAILURE',
                'status_code': '400',
                'message': 'The request could not be processed with the parameters provided.'
            },
            '400_bad_version_number': {
                'request_status': 'FAILURE',
                'status_code': '400',
                'message': 'The provided version number for this object is not greater than the number that would be generated automatically and therefore the request to publish was denied.'
            },
            '400_non_publishable_object': {
                'request_status': 'FAILURE',
                'status_code': '400',
                'message': 'The object provided was not valid against the schema provided.  See key \'errors\' for specifics of the non-compliance.',
                'errors': parameters['errors']
            },
            '400_non_root_id': {
                'request_status': 'FAILURE',
                'status_code': '400',
                'message': 'The provided object ID does not contain a URI with a valid prefix.'
            },
            '401_prefix_unauthorized': {
                'request_status': 'FAILURE',
                'status_code': '401',
                'message': 'The token provided does not have draft permissions for prefix \'' + parameters['prefix'] + '\'.'
            },
            '403_insufficient_permissions': {
                'request_status': 'FAILURE',
                'status_code': '403',
                'message': 'The token provided does not have sufficient permissions for the requested object.'
            },
            '403_invalid_token': {
                'request_status': 'FAILURE',
                'status_code': '403',
                'message': 'The token provided was not able to be used on this object.'
            },
            '404_missing_prefix': {
                'request_status': 'FAILURE', 
                'status_code': '404',
                'message': 'The prefix \'' + parameters['prefix'] + '\' was not found on the server.'
            },
            '404_object_id': {
                'request_status': 'FAILURE', 
                'status_code': '404',
                'message': 'The object ID \'' + parameters['object_id'] + '\' was not found on the server.'
            },
            '404_table': {
                'request_status': 'FAILURE', 
                'status_code': '404',
                'message': 'The table with name \'' + parameters['table'] + '\' was not found on the server.'
            },
            '409_group_conflict': {
                'request_status': 'FAILURE', 
                'status_code': '409',
                'message': 'The provided group \'' + parameters['group'] + '\' has already been created on this server.'
            },
            '409_prefix_conflict': {
                'request_status': 'FAILURE', 
                'status_code': '409',
                'message': 'The provided prefix \'' + parameters['prefix'] + '\' has already been created on this server.'
            },
        }
    



    # Publish an object.
    def publish(
        self,
        og,
        ou,
        prfx,
        publishable,
        publishable_id
    ):

        # publishable is a draft object.

        # Define the object naming information.
        object_naming_info = settings.OBJECT_NAMING

        # Define a variable to hold all information
        # about the published object.
        published = {}

        # A new published object or an existing one?
        if publishable_id == 'new':

            # TODO: put new object ID logic in its own function
            # like check_version_rules()...
            
            # Define a variable which will hold the constructed name.
            constructed_name = ''

            # Create the constructed name based on whether or not
            # we're on a production server.
            if settings.PRODUCTION == 'True':

                constructed_name = object_naming_info['uri_regex'].replace(
                'prod_root_uri', 
                object_naming_info['prod_root_uri']
                )

            elif settings.PRODUCTION == 'False':

                constructed_name = object_naming_info['uri_regex'].replace(
                'root_uri', 
                object_naming_info['root_uri']
                )
            
            constructed_name = constructed_name.replace(
                'prefix', 
                prfx
            )

            # Get rid of the rest of the regex for the name.
            prefix_location = constructed_name.index(
                prfx
            )
            prefix_length = len(
                prfx
            )
            constructed_name = constructed_name[0:prefix_location+prefix_length]

            # Get the object number counter from meta information about the prefix.
            prefix_counter = meta_table.objects.get(prefix = prfx)

            # Create the contents field.
            published['contents'] = publishable

            # Create a new ID based on the prefix counter.
            published['object_id'] =  constructed_name + '_' + '{:06d}'.format(prefix_counter.n_objects) + '/1.0'
            
            # Make sure to create the object ID field in our draft.
            published['contents']['object_id'] = published['object_id']

            # Django wants a primary key for the Group...
            published['owner_group'] = og

            # Django wants a primary key for the User...
            published['owner_user'] = ou

            # The prefix is passed through.
            published['prefix'] = prfx

            # Schema is hard-coded for now...
            published['schema'] = 'IEEE'

            # This is PUBLISHED.
            published['state'] = 'PUBLISHED'

            # Set the datetime properly.
            published['last_update'] = timezone.now()
            
            # Publish.
            self.write_object(
                p_app_label = 'api', 
                p_model_name = 'bco',
                p_fields = ['contents', 'last_update', 'object_id', 'owner_group', 'owner_user', 'prefix', 'schema', 'state'],
                p_data = published
            )

          
            # Update the meta information about the prefix.
            prefix_counter.n_objects = prefix_counter.n_objects + 1
            prefix_counter.save()

            # Successfuly saved the object.
            return {
                'published_id': published['object_id']
            }
        
        else:

            # An object ID was provided, so go straight to publishing.

            # Create the contents field.
            published['contents'] = publishable

            # Set the object ID.
            published['object_id'] =  publishable_id
            
            # Make sure to create the object ID field in the BCO.
            published['contents']['object_id'] = publishable_id

            # Django wants a primary key for the Group...
            published['owner_group'] = og

            # Django wants a primary key for the User...
            published['owner_user'] = ou

            # The prefix is passed through.
            published['prefix'] = prfx

            # Schema is hard-coded for now...
            published['schema'] = 'IEEE'

            # Mark the object as published.
            published['state'] = 'PUBLISHED'

            # Set the datetime properly.
            published['last_update'] = timezone.now()

            # Publish.
            self.write_object(
                p_app_label = 'api', 
                p_model_name = 'bco',
                p_fields = ['contents', 'last_update', 'object_id', 'owner_group', 'owner_user', 'prefix', 'schema', 'state'],
                p_data = publishable
            )

            # Successfuly saved the object.
            return {
                'published_id': published['object_id']
            }
            


    
    # Write (update) either a draft or a published object to the database.
    def write_object(
        self, 
        p_app_label, 
        p_model_name, 
        p_fields, 
        p_data, 
        p_update = False,
        p_update_field = False
    ):

        # Source: https://docs.djangoproject.com/en/3.1/topics/db/queries/#topics-db-queries-update
        
        # Serialize our data.
        serializer = getGenericSerializer(
            incoming_model = apps.get_model(
                app_label = p_app_label, 
                model_name = p_model_name
            ), 
            incoming_fields = p_fields
        )

        serialized = serializer(
            data = p_data
        )
        
        # Save (update) it.
        if p_update is False:

            # Write a new object.
            if serialized.is_valid():
                serialized.save()
            else:
                print(serialized.errors)
        
        else:

            # Update an existing object.
            # apps.get_model(
            #     app_label = p_app_label, 
            #     model_name = p_model_name
            # ).objects.filter(
            #     object_id = p_data['object_id']
            # ).update(
            #     contents = p_data['contents']
            # )

            apps.get_model(
                app_label = p_app_label, 
                model_name = p_model_name
            ).objects.filter(
                object_id = p_data['object_id']
            ).update(
                contents = p_data['contents']
            )
    def convert_id_form(oi_root):
        return oi_root.split("_")[0] +  '{:06d}'.format(int(oi_root.split("_")[1]))