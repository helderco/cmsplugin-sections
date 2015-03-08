# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, url
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.middleware.csrf import get_token
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.utils.plugins import downcast_plugins, build_plugin_tree
from cms.utils.urlutils import admin_reverse

from .models import (AbstractSectionContainerPluginModel,
                    SectionContainerPluginModel, SectionBasePluginModel, SectionsMenuPluginModel)


class SectionContainerPlugin(CMSPluginBase):
    """
    This is the container for all sections.
    """

    allow_children = True
    cache = True
    # TODO: Complete this, or set it in settings.
    # child_classes = ['...']
    model = SectionContainerPluginModel
    module = _('Sections')
    name = _('Section Container')
    render_template = 'cmsplugin_sections/section-container.html'
    text_enabled = False

    def get_children(self, instance):
        """
        This builds a dict for each child, containing the child, the next
        child and the previous child. This provides convenient linking between
        the sections.
        """

        children = []

        for i, child in enumerate(instance.child_plugin_instances):
            prev_child = None
            next_child = None

            if instance.section_links:
                if i > 0:
                    prev_child = instance.child_plugin_instances[i-1]

                if i < len(instance.child_plugin_instances) - 1:
                    next_child = instance.child_plugin_instances[i+1]

            children.append({
                'prev': prev_child,
                'child': child,
                'next': next_child,
            })

        return children

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['children'] = self.get_children(instance)

        if instance.menu:
            context['sections'] = instance.child_plugin_instances

        return context

plugin_pool.register_plugin(SectionContainerPlugin)


class BaseSectionPlugin(CMSPluginBase):
    """
    This is a base class for the plugins that make up the sections of the
    front page. It provides common configuration and behavior.
    """

    class Meta:
        abstract = True

    # These properties should NOT be overridden
    parent_classes = ['SectionContainerPlugin', ]
    text_enabled = False

    # These properties CAN be overridden
    cache = True
    model = SectionBasePluginModel
    module = _('Sections')
    render_template = "cmsplugin_sections/section-base.html"

    # These properties MUST be overridden
    name = _('Unnamed Section')


    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder
        return context

# NOTE: Don't register this, its abstract and only used for subclassing.


class SectionPlugin(BaseSectionPlugin):
    """
    This is a generic implementation of the BaseSectionPlugin and is more-or-
    less a section-compatible placeholder for generic content.
    """

    cache = True
    allow_children = True
    model = SectionBasePluginModel
    name = _('Section')
    render_template = "cmsplugin_sections/section.html"
    text_enabled = False

plugin_pool.register_plugin(SectionPlugin)


class SectionsMenuPlugin(CMSPluginBase):
    """
    Sections menu plugin created from an existing sections container. Allows
    rendering the menu in a separate placeholder or position in the page.
    """

    model = SectionsMenuPluginModel
    module = _('Sections')
    name = _('Sections Menu')
    render_template = "cmsplugin_sections/section-menu.html"
    allow_children = False
    parent_classes = [0] # so you will not be able to add it directly
    cache = True

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        context['placeholder'] = placeholder

        sections = []
        if instance.plugin_id:
            plugins = instance.plugin.get_descendants(include_self=True).order_by('placeholder', 'tree_id', 'level', 'position')
            plugins = downcast_plugins(plugins)
            plugins[0].parent_id = None
            plugins = build_plugin_tree(plugins)

            for section in plugins[0].child_plugin_instances:
                sections.append(section)

        context['sections'] = sections
        return context

    def get_extra_global_plugin_menu_items(self, request, plugin):
        if isinstance(plugin, AbstractSectionContainerPluginModel):
            return [
                PluginMenuItem(
                    _("Create Menu"),
                    admin_reverse("create_sections_menu"),
                    data={'plugin_id': plugin.pk, 'csrfmiddlewaretoken': get_token(request)},
                )
            ]

    def get_plugin_urls(self):
        urlpatterns = [
            url(r'^create_menu/$', self.create_menu, name='create_sections_menu'),
        ]
        return patterns('', *urlpatterns)

    def create_menu(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden("not enough privileges")

        if not 'plugin_id' in request.POST:
            return HttpResponseBadRequest("plugin_id POST parameter missing.")

        pk = request.POST['plugin_id']

        try:
            plugin = CMSPlugin.objects.get(pk=pk)
        except CMSPlugin.DoesNotExist:
            return HttpResponseBadRequest("plugin with id %s not found." % pk)

        clipboard = request.toolbar.clipboard
        clipboard.cmsplugin_set.all().delete()
        language = plugin.language

        menu = SectionsMenuPluginModel(language=language, placeholder=clipboard, plugin_type='SectionsMenuPlugin')
        menu.plugin = plugin
        menu.save()

        return HttpResponse("ok")

plugin_pool.register_plugin(SectionsMenuPlugin)
