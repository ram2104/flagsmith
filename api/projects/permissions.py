import typing

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework_api_key.permissions import BaseHasAPIKey

from organisations.models import Organisation
from organisations.permissions.permissions import CREATE_PROJECT
from projects.models import Project

from .models import ProjectAPIKey

# Maintain a list of permissions here
PROJECT_PERMISSIONS = [
    ("VIEW_PROJECT", "View permission for the given project."),
    ("CREATE_ENVIRONMENT", "Ability to create an environment in the given project."),
    ("DELETE_FEATURE", "Ability to delete features in the given project."),
    ("CREATE_FEATURE", "Ability to create features in the given project."),
    ("EDIT_FEATURE", "Ability to edit features in the given project."),
]


class ProjectPermissions(BasePermission):
    def has_permission(self, request, view):
        """Check if user has permission to list / create project"""
        if view.action == "create" and request.user.belongs_to(
            int(request.data.get("organisation"))
        ):
            organisation = Organisation.objects.get(
                id=int(request.data.get("organisation"))
            )
            if organisation.restrict_project_create_to_admin:
                return request.user.is_organisation_admin(organisation.pk)
            return request.user.has_organisation_permission(
                organisation, CREATE_PROJECT
            )

        if view.action in ("list", "permissions"):
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to view / edit / delete project"""
        if request.user.is_project_admin(obj):
            return True

        if view.action == "retrieve" and request.user.has_project_permission(
            "VIEW_PROJECT", obj
        ):
            return True

        if view.action in ("update", "destroy") and request.user.is_project_admin(obj):
            return True

        if view.action == "user_permissions":
            return True

        return False


class NestedProjectPermissions(BasePermission):
    def has_permission(self, request, view):
        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False

        project = Project.objects.get(pk=project_pk)

        if request.user.is_project_admin(project):
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        if request.user.is_project_admin(obj.project):
            return True

        return False


class IsProjectAdmin(BasePermission):
    def __init__(
        self, *args, project_pk_view_kwarg_attribute_name: str = "project_pk", **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._view_kwarg_name = project_pk_view_kwarg_attribute_name

    def has_permission(self, request, view):
        return request.user.is_project_admin(self._get_project(view))

    def _get_project(self, view) -> Project:
        try:
            project_pk = view.kwargs[self._view_kwarg_name]
            return Project.objects.get(id=project_pk)
        except KeyError:
            raise APIException(
                "`IsProjectAdmin` incorrectly configured. No project pk found."
            )
        except Project.DoesNotExist:
            raise PermissionDenied()


# TODO: this should really be environment permission
class HasProjectAPIKey(BaseHasAPIKey):
    model = ProjectAPIKey

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        key = self.get_key(request)
        if not key:
            return False
        try:
            key_obj = self.model.objects.get_from_key(key)
        except ObjectDoesNotExist:
            return False

        # TODO: should be part of authentication?
        request.api_key = key_obj

        # will be handled by has object permission
        if view.detail:
            return True

        if view.action == "permissions":
            # Allow access to permission since it
            # returns a generic response
            return True
        if view.action == "create":
            project = request.data.get("project")
            if project.isdigit() and int(project) == key_obj.project.id:
                return True
        return False

    def has_object_permission(
        self, request: HttpRequest, view: typing.Any, obj
    ) -> bool:
        return obj.project == request.api_key.project
