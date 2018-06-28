from django import forms
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.utils.html import escape
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.views.decorators.debug import sensitive_post_parameters
from django.forms import ModelMultipleChoiceField
from django.contrib.auth import get_user_model
from xadmin.layout import Fieldset, Main, Side, Row, FormHelper
from xadmin.sites import site
from xadmin.util import unquote
from xadmin.views import BaseAdminPlugin, ModelFormAdminView, ModelAdminView, CommAdminView, csrf_protect_m

from jwt_auth.models import UserManagement, UserAuthentication

User = get_user_model()

class HorizontalRadioRenderer(forms.RadioSelect):
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))

class UserChangeBaseForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    is_active = forms.TypedChoiceField(
        label='是否激活',
        coerce=lambda x: x == 'True',
        choices=((True, '是'), (False, '否')),
        initial=True,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = UserManagement
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserChangeBaseForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        user = super(UserChangeBaseForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(UserChangeBaseForm):
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
        required=False,
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)

class UserCreationForm(UserChangeBaseForm):
    email = forms.CharField(
        label=_('Email'),
    )
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)

def get_wrapped(name):
    count = len(name)
    chars = []
    for i in range(count):
        chars.append(name[i])
        if (i + 1) % 3 == 0:
            chars.append('<br />')
    return ''.join(chars)

class UserManagementAdmin(object):
    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    change_user_password_template = None
    list_filter = ('is_admin', 'is_active', 'roles', 'groups')
    list_display = ('username', 'email', 'is_active', 'is_admin', 'date_joined', 'last_login', 'modify')
    list_display_links = ('modify')
    search_fields = ('username', 'introduce_by', 'date_joined', 'email')
    fields = ['username', 'email', 'is_active']
    ordering = ('email',)
    model_icon = 'fa fa-user'
    relfield_style = 'fk-ajax'
    use_related_menu = False

    def get_model_form(self, **kwargs):
        if self.org_obj is None:
            self.form = UserCreationForm
        else:
            self.form = UserChangeForm
        return super(UserManagementAdmin, self).get_model_form(**kwargs)

    def get_readonly_fields(self, **kwargs):
        if self.org_obj is None:
            readonly_fields = []
        else:
            readonly_fields = ['email']
        return readonly_fields

    def queryset(self):
        qs = super(UserManagementAdmin, self).queryset().filter(is_superuser=False)
        return qs

from jwt_auth.models import Role
class RoleCheck:
    def __init__(self, role_id, role_name):
        self.role_id = role_id
        self.boolean = True
        self.allow_tags = True
        self.short_description = get_wrapped(role_name)
        self.name = 'role_%d' % role_id

    def __call__(self, obj):
        for r in obj.roles.all():
            if r.id == self.role_id:
                return True
        return False

class UserAuthenticationChangeForm(forms.ModelForm):
    is_admin = forms.TypedChoiceField(
        label='是否管理员',
        coerce=lambda x: x == 'True',
        choices=((True, '是'), (False, '否')),
        initial=True,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = UserAuthentication
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserAuthenticationChangeForm, self).__init__(*args, **kwargs)

class UserAuthenticationAdmin(object):
    def modify(self, instance):
        return '修改'
    modify.short_description = '操作'
    change_user_password_template = None
    base_list_display = []
    list_filter = ('is_admin', 'is_active', 'roles', 'groups')
    list_display_links = ('modify')
    search_fields = ('username', 'introduce_by', 'date_joined', 'email')
    fields = ['is_admin', 'roles', 'groups']
    ordering = ('email',)
    style_fields = {'roles': 'm2m_transfer'}
    model_icon = 'fa fa-user'
    relfield_style = 'fk-ajax'
    use_related_menu = False
    remove_permissions = ['add', 'delete']

    def get_list_display(self):
        list_display = ['username', 'is_admin', 'modify']
        from jwt_auth.models import Role
        for role in Role.objects.all():
            role_check = RoleCheck(role.id, role.name)
            setattr(self.__class__, role_check.name, role_check)
            list_display.insert(-1, role_check.name)
        return list_display

    def queryset(self):
        qs = super(UserAuthenticationAdmin, self).queryset().filter(is_superuser=False)
        return qs

    def get_model_form(self, **kwargs):
        self.form = UserAuthenticationChangeForm
        return super(UserAuthenticationAdmin, self).get_model_form(**kwargs)

site.unregister(User)
site.register(UserManagement, UserManagementAdmin)
site.register(UserAuthentication, UserAuthenticationAdmin)