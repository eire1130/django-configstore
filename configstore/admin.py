from django.contrib import admin
from django.template.response import TemplateResponse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django import template
from django.template.response import TemplateResponse

from configstore.models import Configuration
from configstore.configs import CONFIGS


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'site')

    actions = ['run_setup']

    def run_setup(self, request, queryset):
        for item in queryset:
            form = self.get_form(request,item)(instance=item, key=item.key)
            r = form.config_task()
            if isinstance(r, HttpResponse):
                return r
            else:
                self.message_user(request, r)
    run_setup.short_description = "Run the setup task for the configuration"

    def get_fieldsets(self, request, obj=None):
        # consider it might be nice delegate more of
        # this functionality to the ConfigurationInstance
        form_builder = self.get_form(request, obj)
        return [(None, {'fields': form_builder().fields.keys()})]

    def get_form(self, request, obj=None, **kwargs):
        #use the key to get the form
        if obj:
            return CONFIGS[obj.key].get_form_builder()
        return CONFIGS[request.GET['key']].get_form_builder()

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label
        ordered_objects = opts.get_ordered_objects()
        context.update({
            'add': add,
            'change': change,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': True,
            # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': hasattr(self.model, 'get_absolute_url'),
            'ordered_objects': ordered_objects,
            'form_url': mark_safe(form_url),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
        })
        if add and self.add_form_template is not None:
            form_template = self.add_form_template
        else:
            form_template = self.change_form_template
        templates = [
            "admin/%s/%s/change_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/change_form.html" % app_label,
            "admin/change_form.html"
        ]
        if obj is not None and getattr(obj, 'key', None) is not None:
            templates = [
                'admin/{app_label}/{objtype}/{objname}/change_form.html'.format(
                    app_label=app_label,
                    objtype=opts.object_name.lower(),
                    objname=obj.key
                )
            ] + templates

        return TemplateResponse(
            request, form_template or templates,
            context, current_app=self.admin_site.name)


    
    def add_view(self, request, form_url='', extra_context=None):
        """
        This doesn't "Add a View to the Admin" - it IS THE "add" view - the
        view used to "add" new configstore elements.
        """
        if 'key' in request.GET:
            return super(ConfigurationAdmin, self).add_view(request, form_url, extra_context)
        #render a listing of links ?key={{configkey}}
        #consider can we also select the site?
        model = self.model
        opts = model._meta
        app_label = opts.app_label
        ordered_objects = opts.get_ordered_objects()
        obj = None
        configs = CONFIGS.items()
        def sort_by_label(a, b):
            return cmp(a[1].name, b[1].name)
        configs.sort(sort_by_label)
        context = {
            'title': _('Select %s') % force_text(opts.verbose_name),
            'configs': configs,
            'is_popup': request.REQUEST.has_key('_popup'),
            'show_delete': False,
            'app_label': app_label,
            'add': True,
            'change': False,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': False, # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': hasattr(self.model, 'get_absolute_url'),
            'ordered_objects': ordered_objects,
            'form_url': mark_safe(form_url),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
        }
        context.update(extra_context or {})
        return render_to_response(self.change_form_template or [
            "admin/%s/%s/add_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/add_form.html" % app_label,
        ], context, context_instance=template.RequestContext(request))

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label
        ordered_objects = opts.get_ordered_objects()
        configuration_key =  request.GET.get('key', None)
        if configuration_key is None:
            configuration_key = obj.key
        context.update({
            'add': add,
            'change': change,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': True, # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': hasattr(self.model, 'get_absolute_url'),
            'ordered_objects': ordered_objects,
            'form_url': mark_safe(form_url),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'object_id': obj.id if obj else None
        })
        if add and self.add_form_template is not None:
            form_template = self.add_form_template
        else:
            form_template = self.change_form_template
        return TemplateResponse(request, form_template or [
            "admin/%s/%s/%s/change_form.html" % (app_label, opts.object_name.lower(), configuration_key),
            "admin/%s/%s/change_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/change_form.html" % app_label,
            "admin/change_form.html"
        ], context, current_app=self.admin_site.name)


admin.site.register(Configuration, ConfigurationAdmin)
