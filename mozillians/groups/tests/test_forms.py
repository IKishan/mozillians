from nose.tools import eq_, ok_

from mozillians.common.tests import TestCase
from mozillians.groups.forms import GroupForm
from mozillians.groups.models import Group
from mozillians.groups.tests import GroupAliasFactory, GroupFactory
from mozillians.users.tests import UserFactory


class GroupFormTests(TestCase):
    def test_name_unique(self):
        group = GroupFactory.create()
        GroupAliasFactory.create(alias=group, name='bar')
        form = GroupForm({'name': 'bar'})
        ok_(not form.is_valid())
        ok_('name' in form.errors)
        msg = u'This name already exists.'
        ok_(msg in form.errors['name'])

    def test_by_request_group_without_new_member_criteria(self):
        form_data = {'name': 'test group', 'accepting_new_members': 'by_request'}
        form = GroupForm(data=form_data)
        eq_(False, form.is_valid())
        ok_('new_member_criteria' in form.errors)

    def test_by_request_group_with_new_member_criteria(self):
        user = UserFactory.create()
        form_data = {'name': 'test group',
                     'accepting_new_members': 'by_request',
                     'new_member_criteria': 'some criteria',
                     'curators': [user.userprofile.id]}
        form = GroupForm(data=form_data)
        ok_(form.is_valid())
        ok_('new_member_criteria' in form.cleaned_data)

    def test_no_saved_criteria(self):
        user = UserFactory.create()
        form_data = {'name': 'test group',
                     'accepting_new_members': 'no',
                     'new_member_criteria': 'some criteria',
                     'curators': [user.userprofile.id]}
        form = GroupForm(data=form_data)
        ok_(form.is_valid())
        eq_(u'', form.cleaned_data['new_member_criteria'])

    def test_legacy_group_curators_validation(self):
        group = GroupFactory.create()

        # Update form without adding curators
        form_data = {'name': 'test_group',
                     'accepting_new_members': 'by_request',
                     'new_member_criteria': 'some criteria'}
        form = GroupForm(instance=group, data=form_data)

        ok_(form.is_valid())

        # Ensure that groups has no curators
        group = Group.objects.get(id=group.id)
        ok_(not group.curators.exists())

    def test_group_curators_validation(self):
        group = GroupFactory.create()
        curator = UserFactory.create()
        group.curators.add(curator.userprofile)

        # Update form without adding curators
        form_data = {'name': 'test_group',
                     'accepting_new_members': 'by_request',
                     'new_member_criteria': 'some criteria',
                     'curators': []}
        form = GroupForm(instance=group, data=form_data)

        ok_(not form.is_valid())
        eq_(form.errors, {'curators': [u'The group must have at least one curator.']})

    def test_new_group_without_curators(self):
        # Create a new group without curators
        form_data = {'name': 'test_group',
                     'accepting_new_members': 'by_request',
                     'new_member_criteria': 'some criteria',
                     'curators': []}
        form = GroupForm(data=form_data)

        ok_(not form.is_valid())
        eq_(form.errors, {'curators': [u'The group must have at least one curator.']})

    def test_create_new_group(self):
        # Create a new group without curators
        curator = UserFactory.create(vouched=True)
        form_data = {'name': 'test_group',
                     'accepting_new_members': 'by_request',
                     'new_member_criteria': 'some criteria',
                     'curators': [curator.id]}
        form = GroupForm(data=form_data)

        ok_(form.is_valid())
        form.save()
        eq_(Group.objects.all().count(), 1)
