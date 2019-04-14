from django import forms
from django.db import models

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet


class HomePage(Page):
    banner_text = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('banner_text', classname="full"),
    ]

    @classmethod
    def can_create_at(cls, parent):
        # You can only create one of these!
        return super().can_create_at(parent) \
            and not cls.objects.exists()


class BlogIndexPage(Page):
    subpage_types = ['pages.BlogPage']

    def get_context(self, request):
        # Filter by tag
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request)
        context['pages'] = blogpages
        return context

    @classmethod
    def can_create_at(cls, parent):
        # You can only create one of these!
        return super(BlogIndexPage, cls).can_create_at(parent) \
            and not cls.objects.exists()


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
            verbose_name_plural = 'blog categories'


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )


class BlogPage(Page):
    date = models.DateField("Post date")
    body = RichTextField(blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField('pages.BlogCategory', blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('tags'),
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        ], heading="Blog information"),
        FieldPanel('body', classname="full"),
    ]

    parent_page_types = ['pages.BlogIndexPage']
    subpage_types = []
