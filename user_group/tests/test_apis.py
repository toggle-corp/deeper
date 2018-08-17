from deep.tests import TestCase
from user.models import User
from user_group.models import UserGroup, GroupMembership


class UserGroupApiTest(TestCase):
    def test_create_user_group(self):
        user_group_count = UserGroup.objects.count()

        url = '/api/v1/user-groups/'
        data = {
            'title': 'Test user group',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(UserGroup.objects.count(), user_group_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['memberships']), 1)
        self.assertEqual(response.data['memberships'][0]['member'],
                         self.user.pk)

        membership = GroupMembership.objects.get(
            pk=response.data['memberships'][0]['id'])
        self.assertEqual(membership.member.pk, self.user.pk)
        self.assertEqual(membership.role, 'admin')

    def test_member_of(self):
        user_group = self.create(UserGroup, role='admin')
        test_user = self.create(User)

        url = '/api/v1/user-groups/member-of/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], user_group.id)

        url = '/api/v1/user-groups/member-of/?user={}'.format(test_user.id)

        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

    def test_search_user_usergroups_validation_empty_query(self):
        url = '/api/v1/users-user-groups/?search='
        self.authenticate()
        response = self.client.get(url)
        self.assert_400(response)

    def test_search_user_usergroups(self):
        user_group = self.create(UserGroup, title="MyTestUserGroup")
        test_user = self.create(User, username="mytestuser")
        # Query should be mytest to match just
        # the above created usergroup and user
        url = '/api/v1/users-user-groups/?search=mytest'

        # should return both user and usergroup
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.json()

        assert 'results' in data
        self.assertEqual(len(data['results']), 2)

        for item in data['results']:
            assert 'id' in item
            assert 'type' in item
            assert item['type'] in ['user', 'user_group']

        users = [x for x in data['results'] if x['type'] == 'user']
        user_groups = [x for x in data['results'] if x['type'] == 'user_group']

        self.assertEqual(users[0]['id'], test_user.id)
        self.assertEqual(user_groups[0]['id'], user_group.id)

    def test_add_member(self):
        user_group = self.create(UserGroup, role='admin')
        test_user = self.create(User)

        url = '/api/v1/group-memberships/'
        data = {
            'member': test_user.pk,
            'group': user_group.pk,
            'role': 'normal',
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['group'], data['group'])
